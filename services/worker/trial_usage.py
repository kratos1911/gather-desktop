"""Durable admission for one model attempt, bound to a trusted quota operation."""
import threading

from services.inference.runtime import InferenceError
from services.worker.model_availability import ModelServiceError, TRIAL_EXHAUSTED


def read_usage(operation, *, charged=False):
    try:
        usage = operation()
        if type(usage) is not dict or set(usage) != {'state', 'used', 'limit'}:
            raise ValueError('invalid_usage')
        state, used, limit = usage['state'], usage['used'], usage['limit']
        if (state not in {'available', *TRIAL_EXHAUSTED} or type(used) is not int
                or type(limit) is not int or not 0 <= used <= limit <= 10000 or limit == 0
                or (state == 'trial_quota_exhausted' and used != limit)
                or (state == 'trial_capacity_exhausted' and used == limit)
                or (state == 'available' and not charged and used == limit)
                or (state == 'available' and charged and used == 0)):
            raise ValueError('invalid_usage')
        return usage
    except Exception:
        # A timeout may have consumed a reservation. Never retry or send an
        # embedding without a confirmed reservation.
        raise ModelServiceError('service_unavailable', 'model_unavailable') from None


class TrialModel:
    def __init__(self, provider):
        self.provider = provider
        self.count_tokens = provider.count_tokens
        self._slot = threading.Lock()

    def bind(self, reserve):
        return TrialAttempt(self, reserve)

    def infer(self, request, *, reserve, cancel):
        if cancel.is_set():
            raise InferenceError('cancelled')
        if not self._slot.acquire(blocking=False):
            raise ModelServiceError('service_unavailable', 'model_busy')
        try:
            usage = read_usage(reserve, charged=True)
            if usage['state'] != 'available':
                raise ModelServiceError('service_unavailable', usage['state'])
            if cancel.is_set():
                raise InferenceError('cancelled')
            return self.provider.infer(request, cancel=cancel)
        finally:
            self._slot.release()

    def status(self, read, *, cancel):
        usage = read_usage(read)
        if cancel is not None and cancel.is_set():
            raise InferenceError('cancelled')
        if usage['state'] == 'available':
            usage = dict(usage, state=self.provider.check_ready(cancel=cancel))
        return dict(usage, period='utc_day')


class TrialAttempt:
    def __init__(self, model, reserve):
        self._model, self._reserve = model, reserve
        self.count_tokens = model.count_tokens

    def infer(self, request, *, cancel):
        return self._model.infer(request, reserve=self._reserve, cancel=cancel)
