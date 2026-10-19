"""Explicit Cloud Run entry point. Validates intended policy, not deployed IAM."""
import re

from services.inference.startup import load_identity, build_verified_app
from services.worker.cloud_identity import IdentityConfig
from services.worker.service_transport import strict_json


def load_cloud_policy(raw, identity):
    try:
        if not isinstance(raw, bytes) or not 1 <= len(raw) <= 4096:
            raise ValueError()
        value = strict_json(raw)
        if (not isinstance(value, dict) or set(value) != {
                'audience', 'invoker_members', 'invoker_check_required'}
                or not isinstance(value['invoker_members'], list)):
            raise ValueError()
        policy = IdentityConfig(value['audience'], identity.callers[0][0],
                                tuple(value['invoker_members']), value['invoker_check_required'])
        if (policy.audience != identity.audience or set(policy.invoker_members) != {
                'serviceAccount:'+email for email, _ in identity.callers}):
            raise ValueError()
        return policy
    except Exception:
        raise ValueError('invalid_cloud_policy') from None


def cloud_port(value):
    if (not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,5}', value)
            or not 1 <= int(value) <= 65535):
        raise ValueError('invalid_cloud_port')
    return int(value)


def build_cloud_server(raw_identity, raw_policy, snapshot, port_value):
    # Reject operator configuration before reading model artifacts or loading it.
    identity = load_identity(raw_identity)
    policy = load_cloud_policy(raw_policy, identity)
    port = cloud_port(port_value)
    app = build_verified_app(raw_identity, snapshot)
    from services.inference.asgi import create_server
    return create_server(app, host='0.0.0.0', port=port, cloud_policy=policy)


def main():
    import argparse
    import os
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Explicit managed-identity Cloud Run startup')
    parser.add_argument('--identity', type=Path, required=True)
    parser.add_argument('--deployment-policy', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.identity.open('rb') as stream:
            raw_identity = stream.read(4097)
        with args.deployment_policy.open('rb') as stream:
            raw_policy = stream.read(4097)
        server = build_cloud_server(raw_identity, raw_policy, args.model, os.environ.get('PORT'))
    except Exception:
        raise SystemExit('cloud_startup_validation_failed') from None
    server.run()
    if not server.started:
        raise SystemExit('cloud_startup_failed')


if __name__ == '__main__':
    main()
