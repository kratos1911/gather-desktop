"""Fixed availability diagnostics, not raw provider errors or readiness promises."""
from services.inference.runtime import InferenceError
from services.worker.embedding_client import EmbeddingError

PILOT_REQUEST_LIMIT = 3
TRIAL_EXHAUSTED = {'trial_quota_exhausted', 'trial_capacity_exhausted'}
MODEL_HTTP = {
    'model_unavailable':502, 'model_identity_unavailable':502,
    'model_access_denied':502, 'model_busy':429, 'model_rate_limited':429,
    'model_deadline':504, 'model_not_ready':503, 'model_budget_exhausted':429,
    'trial_quota_exhausted':429, 'trial_capacity_exhausted':429,
}


class ModelServiceError(InferenceError, EmbeddingError):
    """Retain a safe reason through both existing inference/embedding contracts."""
    def __init__(self, code, reason):
        super().__init__(code)
        self.reason = reason if reason in MODEL_HTTP else 'model_unavailable'


def transport_failure(code):
    if code == 'cancelled':
        return InferenceError('cancelled')
    reason = {'authentication_failed':'model_access_denied',
        'rate_limited':'model_rate_limited','busy':'model_busy',
        'timeout':'model_deadline','inference_deadline':'model_deadline',
        'model_busy':'model_busy','model_not_ready':'model_not_ready'}.get(code,'model_unavailable')
    legacy = 'deadline_exceeded' if reason=='model_deadline' else 'busy' if reason=='model_busy' else 'service_unavailable'
    return ModelServiceError(legacy,reason)


def status_reply(value):
    if type(value) is dict and set(value) == {'state', 'used', 'limit', 'period'}:
        state, used, limit = value['state'], value['used'], value['limit']
        if (value['period'] == 'utc_day' and state in {'ready', *MODEL_HTTP}
                and state != 'model_budget_exhausted' and type(used) is int
                and type(limit) is int and 1 <= limit <= 10000 and 0 <= used <= limit
                and (state == 'trial_quota_exhausted') == (used == limit)):
            return value
        raise ValueError('invalid_model_status')
    if (type(value) is not dict or set(value)!={'state','used','limit'}
        or value['state'] not in {'ready',*MODEL_HTTP} or value['state'] in TRIAL_EXHAUSTED
        or type(value['used']) is not int or type(value['limit']) is not int
        or value['limit']!=PILOT_REQUEST_LIMIT or not 0<=value['used']<=value['limit']
        or (value['state']=='model_budget_exhausted') != (value['used']==value['limit'])):
        raise ValueError('invalid_model_status')
    return value
