"""Bounded worker lifecycle over existing durable jobs. Never sleeps to retry.

Run in a dedicated operator process. Durable leases/backoff belong to PostgreSQL;
this driver does not hold an HTTP request open or create another job ledger.
"""
import threading
from contextlib import nullcontext

from services.worker.ingestion import run_once
from services.worker.ingestion_repository import RepositoryError


class WorkerStartError(Exception):
    """Fixed safe operator guard codes; never forward exception text."""
    def __init__(self, code):
        self.code = code if code in ('different_job_claimed','pilot_user_only') else 'worker_start_failed'
        super().__init__(self.code)


class WorkerRun:
    def __init__(self, repository, provider, *, record_timings=False):
        if type(record_timings) is not bool:raise ValueError('invalid_timing_mode')
        self.repository, self.provider = repository, provider
        self.cancel = threading.Event()
        self._slot = threading.BoundedSemaphore(1)
        self.record_timings=record_timings

    def stop(self):
        self.cancel.set()

    def run(self, *, max_jobs=1):
        if type(max_jobs) is not int or not 1 <= max_jobs <= 3:
            raise ValueError('invalid_job_budget')
        if not self._slot.acquire(blocking=False):
            raise RuntimeError('worker_busy')
        outcomes = []
        try:
            for _ in range(max_jobs):
                if self.cancel.is_set():
                    break
                from services.worker.processing_timing import StageClock
                clock=StageClock() if self.record_timings else None
                try:
                    scope=(self.repository.job_scope() if callable(getattr(type(self.repository),'job_scope',None))
                           else nullcontext())
                    with scope:
                        try:
                            options={'cancel':self.cancel}
                            if clock is not None:options['timing']=clock
                            result = run_once(self.repository, self.provider, **options)
                        finally:
                            if callable(getattr(type(self.provider),'close_preparation',None)):
                                self.provider.close_preparation()
                except Exception as error:
                    # An uncertain claim outcome must wait for lease recovery.
                    result = {'state':'unavailable', 'error_code':'worker_start_failed',
                              'diagnostic':{'step':'claim_text_job'}}
                    if isinstance(error, WorkerStartError):
                        result['error_code'] = error.code
                    elif isinstance(error, RepositoryError):
                        result['error_code'] = error.code if error.code in (
                            'stale_lease','invalid_input','temporarily_unavailable') else 'worker_start_failed'
                        if error.reason is not None:
                            result['diagnostic']['reason'] = error.reason
                if clock is not None:
                    measurements=clock.finish()
                    database=getattr(self.repository,'last_job_metrics',None)
                    if type(database) is dict:measurements['database']=database
                    duration=getattr(self.provider,'preparation_ms',None)
                    if type(duration) in (int,float):measurements['preparation_ms']=round(duration,2)
                    measurements['early_prepare']=getattr(self.provider,'background',False) is True
                    result=dict(result,timing=measurements)
                outcomes.append(result)
                # No immediate re-claim after failure or uncertainty.
                if result['state'] != 'ready':
                    break
            return {'stopped':self.cancel.is_set(), 'outcomes':outcomes}
        finally:
            self._slot.release()
