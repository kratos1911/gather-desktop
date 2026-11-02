"""Job-scoped worker helpers. No admission reuse, public SQL or automatic replay.

Two physical DB helpers remain the global maximum. A fresh operation can evict
an idle cached helper; active operations and the heartbeat never share a socket.
"""
from dataclasses import asdict
import json
import os
import queue
import struct
import subprocess
import sys
import threading
import time
import weakref

from services.worker.database_transport import (ROOT, MAX_WIRE, MAX_REPLY, SLOTS,
    DatabaseConfig, DatabaseRepository, configure_connection, open_connection, encode_result)
from services.worker.ingestion_repository import FUNCTIONS, PostgresRepository, RepositoryError
from services.worker.service_transport import strict_json

_CACHED = weakref.WeakSet()
_REGISTRY = threading.RLock()
MAX_OPERATIONS = 128


def validated_timing(value):
    if type(value) is not dict or set(value)-{'connects','connect_ms','context_ms','execute_ms'}:
        raise ValueError('invalid_database_timing')
    result={}
    for name in ('connect_ms','context_ms','execute_ms'):
        number=value.get(name,0.0)
        if type(number) not in (int,float) or not 0<=number<=15000:
            raise ValueError('invalid_database_timing')
        result[name]=number
    connects=value.get('connects',0)
    if type(connects) is not int or connects not in (0,1): raise ValueError('invalid_database_timing')
    result['connects']=connects
    return result


def acquire_slot():
    if SLOTS.acquire(blocking=False): return True
    with _REGISTRY:
        for helper in list(_CACHED):
            if helper.evict_idle():
                if SLOTS.acquire(blocking=False): return True
    return False


def _frame(stream, value, maximum):
    raw=json.dumps(value,allow_nan=False,default=encode_result,separators=(',',':')).encode()
    if len(raw)>maximum: raise ValueError('database_wire_limit')
    stream.write(struct.pack('!I',len(raw))+raw)
    stream.flush()


def _read(stream, maximum):
    header=stream.read(4)
    if not header: return None
    if len(header)!=4: raise ValueError('database_wire_invalid')
    length=struct.unpack('!I',header)[0]
    if not 0<length<=maximum: raise ValueError('database_wire_limit')
    data=bytearray()
    while len(data)<length:
        chunk=stream.read(length-len(data))
        if not chunk: raise ValueError('database_wire_invalid')
        data.extend(chunk)
    return strict_json(bytes(data))


class _Helper:
    def __init__(self, repository):
        self.repository=repository
        self.operation=threading.Lock()
        self.process=None
        self.sequence=0
        self.slot=False
        self.closed=False
        self.metrics={'operations':0,'helpers_started':0,'connects':0,
                      'total_ms':0.0,'connect_ms':0.0,'context_ms':0.0,'execute_ms':0.0}
        with _REGISTRY: _CACHED.add(self)

    def _stop(self,graceful=False):
        process=self.process
        if process is not None:
            cleanup_deadline=time.monotonic()+1
            try:
                if process.poll() is None:
                    if graceful:
                        process.stdin.close()
                        try:process.wait(timeout=.1)
                        except subprocess.TimeoutExpired:process.kill()
                    else:process.kill()
                process.wait(timeout=max(.001,cleanup_deadline-time.monotonic()))
            finally:
                for stream in (process.stdin,process.stdout):
                    if stream is not None:
                        try: stream.close()
                        except Exception: pass
            self.process=None
        if self.slot:
            self.slot=False
            SLOTS.release()

    def evict_idle(self):
        if not self.operation.acquire(blocking=False): return False
        try:
            if self.process is None: return False
            self._stop(graceful=True)
            return True
        finally: self.operation.release()

    def close(self):
        with self.operation:
            self.closed=True
            self._stop(graceful=True)
        with _REGISTRY: _CACHED.discard(self)

    def call(self,function,args):
        started=time.monotonic()
        deadline=started+self.repository.operation_timeout
        with self.operation:
            if self.closed: raise RepositoryError('temporarily_unavailable')
            if self.process is not None and self.process.poll() is not None:self._stop()
            sequence=self.sequence+1 if self.process is not None else 1
            wire={'config':asdict(self.repository._config),'owner':None,
                'operation_timeout':self.repository.operation_timeout,
                'sequence':sequence,'function':function,
                'args':[{'bytes_hex':v.hex()} if type(v) is bytes else v for v in args]}
            try:
                if len(json.dumps(wire,allow_nan=False).encode())>MAX_WIRE:raise ValueError()
            except (ValueError,TypeError,UnicodeError):
                raise RepositoryError('invalid_input') from None
            try:
                if self.process is None:
                    if not acquire_slot(): raise RepositoryError('temporarily_unavailable')
                    self.slot=True
                    code='from services.worker.database_session import child_main; child_main()'
                    code=f'import sys; sys.path.insert(0,{str(ROOT)!r}); '+code
                    self.process=subprocess.Popen([sys.executable,'-I','-B','-u','-c',code],
                        cwd=ROOT,env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR') if k in os.environ},
                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                    self.sequence=0
                    self.metrics['helpers_started']+=1
                self.sequence=sequence
                output=queue.Queue(maxsize=1)
                process=self.process
                def exchange():
                    try:
                        _frame(process.stdin,wire,MAX_WIRE)
                        output.put((True,_read(process.stdout,MAX_REPLY)))
                    except Exception:
                        output.put((False,None))
                thread=threading.Thread(target=exchange,daemon=True)
                thread.start()
                try:
                    valid,value=output.get(timeout=max(.001,deadline-time.monotonic()))
                except queue.Empty:
                    cleanup_started=time.monotonic()
                    self._stop()
                    thread.join(max(0,1-(time.monotonic()-cleanup_started)))
                    raise RepositoryError('temporarily_unavailable',reason='operation_deadline_exceeded') from None
                thread.join(1)
                if (not valid or time.monotonic()>=deadline or type(value) is not dict
                    or type(value.get('sequence')) is not int or value.get('sequence')!=self.sequence):
                    raise RepositoryError('temporarily_unavailable')
                for name,number in validated_timing(value.pop('timing',{})).items():
                    self.metrics[name]+=number
                if set(value)=={'sequence','result'}: return value['result']
                if set(value) in ({'sequence','error'},{'sequence','error','reason'}) and value['error'] in (
                    'stale_lease','invalid_input','temporarily_unavailable'):
                    raise RepositoryError(value['error'],reason=value.get('reason'))
                raise RepositoryError('temporarily_unavailable')
            except RepositoryError:
                self._stop()
                raise
            except Exception:
                self._stop()
                raise RepositoryError('temporarily_unavailable') from None
            finally:
                self.metrics['operations']+=1
                self.metrics['total_ms']+=(time.monotonic()-started)*1000


class WorkerSession:
    def __init__(self, repository, *, reuse=True):
        if repository._owner is not None: raise ValueError('worker_reuse_only')
        self.repository=repository
        self.reuse=reuse
        self.helpers={}
        self.lock=threading.Lock()
        self.closed=False
        self.fresh_metrics=dict(operations=0,helpers_started=0,connects=0,total_ms=0.0,
                               connect_ms=0.0,context_ms=0.0,execute_ms=0.0)

    def call(self,function,*args):
        if function in ('submit_text','submit_automatic_text') or function not in FUNCTIONS or len(args)!=FUNCTIONS[function]:
            raise ValueError('unsupported_repository_operation')
        key=threading.get_ident()
        if not self.reuse:
            try:
                return self.repository._call_once(function,*args)
            finally:
                with self.lock:
                    for name,number in getattr(self.repository._thread_timing,'value',{}).items():
                        self.fresh_metrics[name]+=number
        with self.lock:
            if self.closed: raise RepositoryError('temporarily_unavailable')
            if key not in self.helpers:
                if len(self.helpers)>=2: raise RepositoryError('temporarily_unavailable')
                self.helpers[key]=_Helper(self.repository)
            helper=self.helpers[key]
        return helper.call(function,args)

    def summary(self):
        with self.lock:
            return {name:round(self.fresh_metrics[name]+sum(h.metrics[name] for h in self.helpers.values()),2)
                    for name in ('operations','helpers_started','connects','total_ms','connect_ms','context_ms','execute_ms')}

    def close(self):
        with self.lock:
            self.closed=True
            helpers=list(self.helpers.values())
        for helper in helpers: helper.close()


def child_main():
    connection=None
    configuration=None
    sequence=0
    try:
        for _ in range(MAX_OPERATIONS):
            value=_read(sys.stdin.buffer,MAX_WIRE)
            if value is None: break
            output={'sequence':value.get('sequence'),'error':'temporarily_unavailable'}
            timing={'connects':0,'connect_ms':0.0,'context_ms':0.0,'execute_ms':0.0}
            try:
                if set(value)!={'config','owner','operation_timeout','sequence','function','args'} or value['owner'] is not None:
                    raise ValueError()
                if type(value['sequence']) is not int or value['sequence']!=sequence+1: raise ValueError()
                sequence=value['sequence']
                config=DatabaseConfig(**value['config'])
                DatabaseRepository(config,operation_timeout=value['operation_timeout'])
                if configuration is None: configuration=value['config'],value['operation_timeout']
                if configuration!=(value['config'],value['operation_timeout']): raise ValueError()
                function,args=value['function'],value['args']
                if function in ('submit_text','submit_automatic_text') or function not in FUNCTIONS or len(args)!=FUNCTIONS[function]:
                    raise ValueError()
                args=[bytes.fromhex(a['bytes_hex']) if type(a) is dict and set(a)=={'bytes_hex'} else a for a in args]
                def factory():
                    nonlocal connection
                    started=time.monotonic()
                    fresh=connection is None or connection.closed
                    if fresh:
                        connection=open_connection(config)
                        timing['connects']=1
                        timing['connect_ms']=(time.monotonic()-started)*1000
                    started=time.monotonic()
                    if not fresh:connection.reset()  # Rollback/reset role and session authorization.
                    configure_connection(connection,None,batch_context=True)
                    timing['context_ms']=(time.monotonic()-started)*1000
                    return connection
                started=time.monotonic()
                result=PostgresRepository(factory,close_connection=False,context_limits_set=True).call(function,*args)
                timing['execute_ms']=max(0,(time.monotonic()-started)*1000-timing['connect_ms']-timing['context_ms'])
                output={'sequence':sequence,'result':result}
            except RepositoryError as error:
                output={'sequence':sequence,'error':error.code}
                if error.reason is not None: output['reason']=error.reason
                if connection is not None: connection.close(); connection=None
            except Exception:
                if connection is not None: connection.close(); connection=None
            output['timing']=timing
            _frame(sys.stdout.buffer,output,MAX_REPLY)
    except Exception:
        pass  # Parent treats EOF/protocol failure as uncertain, never as success.
    finally:
        if connection is not None: connection.close()
