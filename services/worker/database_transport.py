"""Bounded trusted PostgreSQL transport. Secrets travel only through child stdin.

No raw SQL, caller-selected DSN, pool, automatic retry or public entry point.
Reuses PostgresRepository for statements, transactions and safe error mapping.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from uuid import UUID

from services.worker.ingestion_repository import FUNCTIONS, PostgresRepository, RepositoryError
from services.worker.service_transport import strict_json

ROOT = Path(__file__).resolve().parents[2]
MAX_WIRE = 2 * 1024 * 1024
MAX_REPLY = 1024 * 1024
DEADLINE = 5
SLOTS = threading.BoundedSemaphore(2)  # One operation plus lease heartbeat.


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str = field(repr=False)
    root_certificate: str = ''
    test_loopback: bool = False
    connect_timeout: int = 3

    def __post_init__(self):
        local = self.test_loopback is True and self.host == '127.0.0.1'
        hostname = r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?'
        if (type(self.test_loopback) is not bool or type(self.port) is not int
                or type(self.connect_timeout) is not int or self.connect_timeout not in (3,10)
                or not 1 <= self.port <= 65535
                or not isinstance(self.host,str) or not re.fullmatch(hostname,self.host)
                or (self.test_loopback and not local)
                or (not local and self.port not in (5432,6543))
                or not isinstance(self.user,str) or not re.fullmatch(r'gather_(?:admission|worker)(?:\.[a-z0-9]{20})?',self.user)
                or not isinstance(self.password,str) or not 1 <= len(self.password) <= 1024
                or '\x00' in self.password
                or (not local and (not isinstance(self.root_certificate,str)
                    or not Path(self.root_certificate).is_absolute()
                    or not Path(self.root_certificate).is_file()))):
            raise ValueError('invalid_database_configuration')


class DatabaseRepository:
    def __init__(self, config, *, owner=None, operation_timeout=DEADLINE):
        if not isinstance(config,DatabaseConfig):
            raise ValueError('invalid_database_configuration')
        if type(operation_timeout) is not int or operation_timeout not in (DEADLINE,15):
            raise ValueError('invalid_database_deadline')
        if config.connect_timeout==10 and operation_timeout!=15:
            raise ValueError('pilot_connection_requires_pilot_deadline')
        if owner is not None and (not isinstance(owner,str) or str(UUID(owner)) != owner):
            raise ValueError('invalid_database_owner')
        expected = 'gather_admission' if owner else 'gather_worker'
        if config.user.split('.')[0] != expected:
            raise ValueError('database_role_mismatch')
        self._config, self._owner = config, owner
        self.operation_timeout = operation_timeout
        self.cleanup_wait_seconds = operation_timeout+1

    def call(self, function, *args):
        admission = {'submit_text','submit_automatic_text'}
        allowed = admission if self._owner else set(FUNCTIONS)-admission
        if function not in allowed or len(args) != FUNCTIONS[function]:
            raise ValueError('unsupported_repository_operation')
        values = [{'bytes_hex':a.hex()} if type(a) is bytes else a for a in args]
        wire = json.dumps({'config':asdict(self._config),'owner':self._owner,
                           'function':function,'args':values,'operation_timeout':self.operation_timeout},allow_nan=False).encode()
        if len(wire) > MAX_WIRE:
            raise RepositoryError('invalid_input')
        if not SLOTS.acquire(blocking=False):
            raise RepositoryError('temporarily_unavailable')
        process = None
        deadline = time.monotonic()+self.operation_timeout
        try:
            code = f'import sys; sys.path.insert(0,{str(ROOT)!r}); from services.worker.database_transport import child_main; child_main()'
            env = {k:os.environ[k] for k in ('SYSTEMROOT','WINDIR') if k in os.environ}
            process = subprocess.Popen([sys.executable,'-I','-B','-u','-c',code],cwd=ROOT,
                env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise RepositoryError('temporarily_unavailable')
            output,_ = process.communicate(input=wire,timeout=remaining)
            if time.monotonic()>=deadline or process.returncode or len(output)>MAX_REPLY:
                raise RepositoryError('temporarily_unavailable')
            value = strict_json(output)
            if set(value)=={'result'}:
                return value['result']
            if set(value) in ({'error'},{'error','reason'}) and value['error'] in ('stale_lease','invalid_input','temporarily_unavailable'):
                raise RepositoryError(value['error'],reason=value.get('reason'))
            raise RepositoryError('temporarily_unavailable')
        except subprocess.TimeoutExpired:
            raise RepositoryError('temporarily_unavailable',reason='operation_deadline_exceeded') from None
        except RepositoryError:
            raise
        except Exception:
            # Commit may already have happened. Caller reuses idempotency IDs;
            # worker lease fencing/recovery decides the authoritative outcome.
            raise RepositoryError('temporarily_unavailable') from None
        finally:
            try:
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    process.communicate(timeout=1)
            except Exception:
                raise RepositoryError('temporarily_unavailable') from None
            finally:
                SLOTS.release()


def connect(config, owner):
    import psycopg2
    kwargs = dict(host=config.host,port=config.port,user=config.user,password=config.password,
        dbname='postgres',connect_timeout=config.connect_timeout,options='-c search_path= -c statement_timeout=5000 -c lock_timeout=3000',
        application_name='gather-worker' if owner is None else 'gather-admission',
        sslmode='disable' if config.test_loopback else 'verify-full',gssencmode='disable')
    if not config.test_loopback:
        kwargs['sslrootcert'] = config.root_certificate
    connection = psycopg2.connect(**kwargs)
    try:
        with connection.cursor() as cursor:
            cursor.execute('select rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication '
                           'from pg_catalog.pg_roles where rolname=current_user')
            if cursor.fetchone() != (False,False,False,False,False):
                raise ValueError('privileged_database_login')
            role = 'gather_ingestion_coordinator' if owner else 'gather_ingestion_worker'
            cursor.execute('set local role '+role)  # Fixed identifiers only.
            cursor.execute("select pg_catalog.set_config('request.jwt.claim.sub',%s,true)",(owner or '',))
        return connection
    except Exception:
        connection.close()
        raise


def encode_result(value):
    if isinstance(value,UUID):
        return str(value)
    if isinstance(value,datetime) and value.tzinfo is not None:
        return value.isoformat()
    raise TypeError()


def child_main():
    output = {'error':'temporarily_unavailable'}
    try:
        raw = sys.stdin.buffer.read(MAX_WIRE+1)
        if len(raw)>MAX_WIRE:
            raise ValueError()
        value = strict_json(raw)
        config = DatabaseConfig(**value['config'])
        validated = DatabaseRepository(config,owner=value['owner'],operation_timeout=value.get('operation_timeout',DEADLINE))
        function, args = value['function'], value['args']
        admission = {'submit_text','submit_automatic_text'}
        allowed = admission if validated._owner else set(FUNCTIONS)-admission
        if function not in allowed or len(args)!=FUNCTIONS[function]:
            raise ValueError()
        args = [bytes.fromhex(a['bytes_hex']) if isinstance(a,dict) and set(a)=={'bytes_hex'} else a for a in args]
        result = PostgresRepository(lambda:connect(config,value['owner'])).call(function,*args)
        output = {'result':result}
    except RepositoryError as error:
        output = {'error':error.code}
        if error.reason is not None:
            output['reason'] = error.reason
    except Exception:
        pass
    try:
        raw = json.dumps(output,allow_nan=False,default=encode_result).encode()
        if len(raw)>MAX_REPLY:
            raise ValueError()
    except Exception:
        raw = b'{"error":"temporarily_unavailable"}'
    sys.stdout.buffer.write(raw)
