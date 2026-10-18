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


def build_verified_app(raw_identity, snapshot):
    # Reject bad policy/artifacts before constructing any model runtime.
    load_identity(raw_identity)
    from services.inference.artifacts import verify_snapshot
    from services.inference.qwen import QwenEngine
    from services.inference.runtime import Runtime
    verified = verify_snapshot(snapshot)
    return create_trusted_app(raw_identity, Runtime(QwenEngine, str(verified)))


def main():
    import argparse
    from pathlib import Path
    from services.inference.asgi import create_server
    parser = argparse.ArgumentParser(description='Verified local serving; public cloud bind remains gated')
    parser.add_argument('--identity', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    try:
        if not 1 <= args.port <= 65535:
            raise ValueError()
        with args.identity.open('rb') as stream:
            raw = stream.read(4097)
        app = build_verified_app(raw, args.model)
        server = create_server(app, port=args.port)  # Loopback only, never infer public mode.
    except Exception:
        raise SystemExit('startup_validation_failed') from None
    server.run()
    if not server.started:
        raise SystemExit('startup_failed')


if __name__ == '__main__':
    main()
