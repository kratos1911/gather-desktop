"""Trusted composition only; no public bind, import-time I/O or environment fallback."""
from services.worker.cloud_identity import ReceiverIdentity
from services.worker.service_transport import strict_json


def load_identity(raw):
    """Operator-owned JSON, never request input. Values are not credentials."""
    try:
        if not isinstance(raw, bytes) or not 1 <= len(raw) <= 4096:
            raise ValueError()
        value = strict_json(raw)
        if (not isinstance(value, dict) or set(value) != {'audience', 'callers'}
                or not isinstance(value['callers'], list) or not 1 <= len(value['callers']) <= 2
                or any(not isinstance(c, dict) or set(c) != {'email', 'subject'}
                       for c in value['callers'])):
            raise ValueError()
        return ReceiverIdentity(value['audience'], tuple(
            (c['email'], c['subject']) for c in value['callers']))
    except Exception:
        raise ValueError('invalid_startup_identity') from None


def create_trusted_app(raw_identity, runtime):
    """Runtime is supplied by trusted artifact-loading code, not user requests.

    Reuse the ASGI lifespan: acquire keys before model startup, close both on exit.
    The deployment entry point/artifact verification remains separately gated.
    """
    identity = load_identity(raw_identity)
    from services.inference.managed_auth import ManagedGoogleServiceAuth
    from services.inference.asgi import create_app
    return create_app(runtime, ManagedGoogleServiceAuth(identity))
