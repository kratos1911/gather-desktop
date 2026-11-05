"""Request-local readiness before the single embedding attempt, never a retry."""
from services.worker.model_availability import ModelServiceError
from services.inference.runtime import InferenceError


class SearchStartupProvider:
    def __init__(self, provider, prepare):
        self.provider, self.prepare = provider, prepare
        self.count_tokens = provider.count_tokens

    def infer(self, request, *, cancel):
        if cancel.is_set(): raise InferenceError('cancelled')
        calls = getattr(self.provider, 'calls', 0)
        if type(calls) is int and calls >= 3:
            raise ModelServiceError('service_unavailable', 'model_budget_exhausted')
        try:
            self.prepare(cancel)
        except Exception as error:
            if cancel.is_set(): raise InferenceError('cancelled') from None
            reason = {
                'cloud_identity_unavailable':'model_identity_unavailable',
                'cloud_startup_http_401':'model_access_denied',
                'cloud_startup_http_403':'model_access_denied',
                'cloud_startup_http_429':'model_rate_limited',
                'cloud_startup_http_503':'model_not_ready',
                'cloud_startup_deadline_exceeded':'model_deadline',
                'cloud_startup_network_timeout':'model_deadline',
            }.get(str(error), 'model_unavailable')
            raise ModelServiceError('service_unavailable', reason) from None
        if cancel.is_set(): raise InferenceError('cancelled')
        return self.provider.infer(request, cancel=cancel)
