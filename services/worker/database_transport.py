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
from contextlib import contextmanager

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
    def __init__(self, config, *, owner=None, operation_timeout=DEADLINE, reuse_worker=False):
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
        if type(reuse_worker) is not bool or (reuse_worker and owner is not None):
            raise ValueError('worker_reuse_only')
        self._config, self._owner = config, owner
        self.operation_timeout = operation_timeout
        self.cleanup_wait_seconds = operation_timeout+1
        self._reuse_worker = reuse_worker
        self._scope = None
        self._scope_lock = threading.Lock()
        self._thread_timing = threading.local()
        self.last_job_metrics = {}

    @contextmanager
    def job_scope(self):
        from services.worker.database_session import WorkerSession
        with self._scope_lock:
            if self._scope is not None: raise RuntimeError('worker_scope_busy')
            scope = self._scope = WorkerSession(self,reuse=self._reuse_worker)
        try:
            yield
        finally:
            try:
                scope.close()
            finally:
                self.last_job_metrics = scope.summary()
                with self._scope_lock: self._scope = None

    def call(self, function, *args):
        admission = {'submit_text','submit_automatic_text'}
        allowed = admission if self._owner else set(FUNCTIONS)-admission
        if function not in allowed or len(args) != FUNCTIONS[function]:
            raise ValueError('unsupported_repository_operation')
        if self._scope is not None:
            return self._scope.call(function,*args)
        return self._call_once(function,*args)

    def _call_once(self,function,*args):
        started=time.monotonic()
        measurements=dict(operations=1,helpers_started=0,connects=0,total_ms=0.0,
                          connect_ms=0.0,context_ms=0.0,execute_ms=0.0)
        self._thread_timing.value=measurements
        values = [{'bytes_hex':a.hex()} if type(a) is bytes else a for a in args]
        wire = json.dumps({'config':asdict(self._config),'owner':self._owner,
                           'function':function,'args':values,'operation_timeout':self.operation_timeout},allow_nan=False).encode()
        if len(wire) > MAX_WIRE:
            raise RepositoryError('invalid_input')
        from services.worker.database_session import acquire_slot
        if not acquire_slot():
            raise RepositoryError('temporarily_unavailable')
        process = None
        deadline = started+self.operation_timeout
        try:
            code = f'import sys; sys.path.insert(0,{str(ROOT)!r}); from services.worker.database_transport import child_main; child_main()'
            env = {k:os.environ[k] for k in ('SYSTEMROOT','WINDIR') if k in os.environ}
            process = subprocess.Popen([sys.executable,'-I','-B','-u','-c',code],cwd=ROOT,
                env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            measurements['helpers_started']=1
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise RepositoryError('temporarily_unavailable')
            output,_ = process.communicate(input=wire,timeout=remaining)
            if time.monotonic()>=deadline or process.returncode or len(output)>MAX_REPLY:
                raise RepositoryError('temporarily_unavailable')
            value = strict_json(output)
            from services.worker.database_session import validated_timing
            measurements.update(validated_timing(value.pop('timing',{})))
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
                measurements['total_ms']=(time.monotonic()-started)*1000
                self._thread_timing.value=measurements


def open_connection(config,owner=None):
    import psycopg2
    kwargs = dict(host=config.host,port=config.port,user=config.user,password=config.password,
        dbname='postgres',connect_timeout=config.connect_timeout,options='-c search_path= -c statement_timeout=5000 -c lock_timeout=3000',
        application_name='gather-worker' if owner is None else 'gather-admission',
        sslmode='disable' if config.test_loopback else 'verify-full',gssencmode='disable')
    if not config.test_loopback:
        kwargs['sslrootcert'] = config.root_certificate
    return psycopg2.connect(**kwargs)


def configure_connection(connection, owner, *, batch_context=False):
    try:
        with connection.cursor() as cursor:
            role = 'gather_ingestion_coordinator' if owner else 'gather_ingestion_worker'
            if batch_context:
                # Fixed server-side guard, with no interpolated request values.
                # It executes before SET ROLE, preserving the original login check
                # without another network round trip.
                cursor.execute("set local statement_timeout='5s'; set local lock_timeout='3s'; "+
                    "do $gather_guard$ begin if not exists(select 1 from pg_catalog.pg_roles "+
                    "where rolname=current_user and not rolsuper and not rolbypassrls "+
                    "and not rolcreaterole and not rolcreatedb and not rolreplication) then "+
                    "raise exception 'restricted_login_required' using errcode='P0001'; end if; end $gather_guard$; "+
                    'set local role '+role+"; select pg_catalog.set_config('request.jwt.claim.sub',%s,true)",
                    (owner or '',))
            else:
                cursor.execute('select rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication '
                               'from pg_catalog.pg_roles where rolname=current_user')
                if cursor.fetchone() != (False,False,False,False,False):
                    raise ValueError('privileged_database_login')
                cursor.execute('set local role '+role)  # Fixed identifiers only.
                cursor.execute("select pg_catalog.set_config('request.jwt.claim.sub',%s,true)",(owner or '',))
        return connection
    except Exception:
        connection.close()
        raise


def connect(config, owner):
    return configure_connection(open_connection(config,owner),owner)


def encode_result(value):
    if isinstance(value,UUID):
        return str(value)
    if isinstance(value,datetime) and value.tzinfo is not None:
        return value.isoformat()
    raise TypeError()


def child_main():
    output = {'error':'temporarily_unavailable'}
    timing=dict(connects=0,connect_ms=0.0,context_ms=0.0,execute_ms=0.0)
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
        def factory():
            started=time.monotonic()
            connection=open_connection(config,value['owner'])
            timing['connect_ms']=(time.monotonic()-started)*1000
            timing['connects']=1
            started=time.monotonic()
            configure_connection(connection,value['owner'])
            timing['context_ms']=(time.monotonic()-started)*1000
            return connection
        started=time.monotonic()
        result = PostgresRepository(factory).call(function,*args)
        timing['execute_ms']=max(0,(time.monotonic()-started)*1000-timing['connect_ms']-timing['context_ms'])
        output = {'result':result}
    except RepositoryError as error:
        output = {'error':error.code}
        if error.reason is not None:
            output['reason'] = error.reason
    except Exception:
        pass
    try:
        output['timing']=timing
        raw = json.dumps(output,allow_nan=False,default=encode_result).encode()
        if len(raw)>MAX_REPLY:
            raise ValueError()
    except Exception:
        raw = b'{"error":"temporarily_unavailable"}'
    sys.stdout.buffer.write(raw)
