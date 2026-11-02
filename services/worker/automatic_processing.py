"""One bounded dispatcher over durable, opted-in jobs. No second job ledger.

Wake on startup/import/explicit recovery; never poll to retry a failed model.
Database requested-attempt markers and lease fences remain authoritative.
"""
import threading
import time


class AutomaticAdmission:
    def __init__(self, repository):
        self.repository = repository

    def call(self, function, *args):
        if function != 'submit_text':
            raise ValueError('unsupported_repository_operation')
        return self.repository.call('submit_automatic_text',*args)


class StartupProvider:
    """Startup is separate from inference's 15s; the coordinator renews its lease."""
    def __init__(self, provider, prepare, *, background=False):
        if type(background) is not bool:raise ValueError('invalid_startup_mode')
        self.provider, self.prepare = provider, prepare
        self.count_tokens = provider.count_tokens
        self.prepared = False
        self.startup_error = None
        self.background=background
        self.preparation_ms=0.0
        self._thread=None
        self._done=threading.Event()
        self._lock=threading.Lock()
        self._preparation_deadline=None

    def start_prepare(self, *, cancel):
        if not self.background:return
        with self._lock:
            if self._thread is not None or self.prepared:return
            self._preparation_deadline=time.monotonic()+60
            self._thread=threading.Thread(target=self._prepare,args=(cancel,),daemon=True,
                                          name='gather-model-prepare')
            self._thread.start()

    def _prepare(self,cancel):
        started=time.monotonic()
        try:
            if cancel.is_set():return
            self.prepare(cancel)
            if not cancel.is_set():self.prepared=True
        except Exception as error:
            self.startup_error=self._safe_error(error)
        finally:
            self.preparation_ms=(time.monotonic()-started)*1000
            self._done.set()

    @staticmethod
    def _safe_error(error):
        allowed={'cloud_identity_unavailable','cloud_startup_deadline_exceeded',
            'cloud_startup_probe_failed','cloud_startup_http_401','cloud_startup_http_403',
            'cloud_startup_http_429','cloud_startup_http_503','cloud_startup_network_timeout',
            'cloud_startup_tls_failed','cloud_startup_dns_failed','cloud_startup_connection_failed',
            'cloud_startup_readiness_probe_failed'}
        return str(error) if str(error) in allowed else 'startup_unavailable'

    def close_preparation(self):
        # The production prepare callback has the existing 60s deadline and
        # cancellation kills/reaps its helper. Three seconds cover its existing
        # two-second reap plus polling; this does not extend startup or inference.
        if self._thread is not None and self._thread.ident is not None:
            self._thread.join(3)
            if self._thread.is_alive():raise RuntimeError('startup_cleanup_incomplete')

    def infer(self, request, *, cancel):
        from services.inference.runtime import InferenceError
        if cancel.is_set(): raise InferenceError('cancelled')
        if not self.prepared:
            if self.background:
                self.start_prepare(cancel=cancel)
                while not self._done.wait(.05):
                    if cancel.is_set():raise InferenceError('cancelled')
                    if time.monotonic()>=self._preparation_deadline:
                        self.startup_error='cloud_startup_deadline_exceeded'
                        raise InferenceError('service_unavailable')
                if not self.prepared:
                    raise InferenceError('cancelled' if cancel.is_set() else 'service_unavailable')
            else:
                started=time.monotonic()
                try:
                    self.prepare(cancel)
                except Exception as error:
                    self.startup_error=self._safe_error(error)
                    raise InferenceError('cancelled' if cancel.is_set() else 'service_unavailable') from None
                finally:
                    self.preparation_ms=(time.monotonic()-started)*1000
                self.prepared=True
        if cancel.is_set(): raise InferenceError('cancelled')
        return self.provider.infer(request,cancel=cancel)


class AutomaticDispatcher:
    def __init__(self, repository, worker_factory, available, record=lambda *_:None):
        self.repository, self.worker_factory = repository, worker_factory
        self.available, self.record = available, record
        self.pending, self.stopping = threading.Event(), threading.Event()
        self.lock = threading.Lock()
        self.worker = None
        self.thread = None

    def start(self):
        if self.thread is not None: raise RuntimeError('dispatcher_already_started')
        self.thread = threading.Thread(target=self._serve,name='gather-import-worker',daemon=True)
        self.thread.start()
        self.wake()  # Recover committed, unclaimed opted-in jobs after restart.

    def wake(self):
        if not self.stopping.is_set(): self.pending.set()

    def stop(self):
        self.stopping.set()
        with self.lock:
            if self.worker is not None: self.worker.stop()
        self.pending.set()

    def join(self):
        if self.thread is not None:
            self.thread.join(17)  # Existing bounded DB operation + cleanup allowance.
            if self.thread.is_alive(): raise RuntimeError('dispatcher_shutdown_incomplete')

    def _serve(self):
        while True:
            self.pending.wait()
            self.pending.clear()
            if self.stopping.is_set(): return
            # Existing worker lifecycle maximum; no unbounded drain/poll loop.
            for _ in range(3):
                if self.stopping.is_set() or not self.available(): break
                try:
                    selection_started=time.monotonic()
                    job = self.repository.call('next_automatic_text_job')
                    selection_ms=(time.monotonic()-selection_started)*1000
                    if job is None: break
                    with self.lock:
                        if self.stopping.is_set(): return
                        self.worker = self.worker_factory(job)
                    result = self.worker.run()
                    for outcome in result.get('outcomes',[]):
                        if type(outcome) is dict and type(outcome.get('timing')) is dict:
                            outcome['timing'].update(selection_ms=round(selection_ms,2),
                                dispatch_total_ms=round((time.monotonic()-selection_started)*1000,2))
                    startup_error = getattr(self.worker.provider,'startup_error',None)
                    if isinstance(startup_error,str): result = dict(result,startup_error=startup_error)
                    self.record(job,result)
                    if not result['outcomes'] or result['outcomes'][-1]['state'] != 'ready': break
                except Exception:
                    # No exception text, content or credentials in operator output.
                    self.record(None,{'outcomes':[{'state':'unavailable','error_code':'automatic_dispatch_unavailable'}]})
                    break
                finally:
                    with self.lock: self.worker = None
