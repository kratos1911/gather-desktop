"""One bounded dispatcher over durable, opted-in jobs. No second job ledger.

Wake on startup/import/explicit recovery; never poll to retry a failed model.
Database requested-attempt markers and lease fences remain authoritative.
"""
import threading


class AutomaticAdmission:
    def __init__(self, repository):
        self.repository = repository

    def call(self, function, *args):
        if function != 'submit_text':
            raise ValueError('unsupported_repository_operation')
        return self.repository.call('submit_automatic_text',*args)


class StartupProvider:
    """Startup is separate from inference's 15s; the coordinator renews its lease."""
    def __init__(self, provider, prepare):
        self.provider, self.prepare = provider, prepare
        self.count_tokens = provider.count_tokens
        self.prepared = False
        self.startup_error = None

    def infer(self, request, *, cancel):
        from services.inference.runtime import InferenceError
        if cancel.is_set(): raise InferenceError('cancelled')
        if not self.prepared:
            try:
                self.prepare(cancel)
            except Exception as error:
                # Operational startup failures must not become invalid document
                # errors in the generic embedding validator.
                allowed = {'cloud_identity_unavailable','cloud_startup_deadline_exceeded',
                    'cloud_startup_probe_failed','cloud_startup_http_401','cloud_startup_http_403',
                    'cloud_startup_http_429','cloud_startup_network_timeout','cloud_startup_tls_failed',
                    'cloud_startup_dns_failed','cloud_startup_connection_failed','cloud_startup_readiness_probe_failed'}
                self.startup_error = str(error) if str(error) in allowed else 'startup_unavailable'
                raise InferenceError('cancelled' if cancel.is_set() else 'service_unavailable') from None
            self.prepared = True
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
                    job = self.repository.call('next_automatic_text_job')
                    if job is None: break
                    with self.lock:
                        if self.stopping.is_set(): return
                        self.worker = self.worker_factory(job)
                    result = self.worker.run()
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
