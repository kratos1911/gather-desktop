"""Server-only fixed-service adapters. No hosted inference endpoint is deployed."""
import base64
import time
from uuid import UUID

from services.inference.runtime import validate_request, InferenceError
from services.worker.service_transport import (
    TransportError, credential, origin, request_json, strict_json,
)


def _claims(token, role):
    # Local rejection of privileged/wrong-shaped credentials, NOT verification.
    # Supabase Auth/PostgREST still verifies signatures, expiry and ownership.
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError()
        claims = strict_json(base64.urlsafe_b64decode(parts[1]+'='*((-len(parts[1])) % 4)))
        if claims['role'] != role:
            raise ValueError()
        if role == 'authenticated':
            UUID(claims['sub'])
    except Exception:
        raise TransportError('invalid_configuration') from None


class SessionClient:
    """One bearer session, three read-only endpoints, five-second I/O deadline."""
    def __init__(self, base, public_key, token, *, cancel=None, _test_loopback=False):
        self._base = origin(base, test_loopback=_test_loopback)
        credential(public_key)
        credential(token)
        if not public_key.startswith('sb_publishable_'):
            _claims(public_key, 'anon')
        _claims(token, 'authenticated')
        self._headers = {'apikey': public_key, 'Authorization': 'Bearer '+token}
        self._cancel = cancel

    def __call__(self, method, path, payload=None):
        routes = {
            '/auth/v1/user': ('GET', None),
            '/rest/v1/rpc/search_published_text': ('POST',
                {'p_query','p_model','p_revision','p_dimensions','p_limit'}),
            '/rest/v1/rpc/open_published_text': ('POST', {'p_source','p_version'}),
        }
        if path not in routes:
            raise TransportError('invalid_request')
        expected, fields = routes[path]
        if method != expected or (payload is not None if fields is None else
                not isinstance(payload, dict) or set(payload) != fields):
            raise TransportError('invalid_request')
        return request_json(self._base, path, self._headers, payload,
                            timeout=5, cancel=self._cancel)


class InferenceClient:
    """Client for the trusted /embed endpoint using Runtime's JSON.

    count_tokens must use the pinned tokenizer, supplied by trusted server code.
    Local handler verified; managed identity, TLS and deployment remain separate.
    """
    def __init__(self, base, credential_value, count_tokens, *, _test_loopback=False):
        self._base = origin(base, test_loopback=_test_loopback)
        self._headers = {'Authorization': 'Bearer '+credential(credential_value)}
        if not callable(count_tokens):
            raise TransportError('invalid_configuration')
        self.count_tokens = count_tokens

    def infer(self, request, *, cancel):
        texts = validate_request(request)
        try:
            counts = [self.count_tokens(text) for text in texts]
            if any(type(n) is not int or not 0 < n <= 2048 for n in counts) or sum(counts) > 4096:
                raise InferenceError('token_limit')
            return self._send(request,cancel=cancel)
        except InferenceError:
            raise
        except TransportError as error:
            code = {'timeout':'deadline_exceeded', 'cancelled':'cancelled', 'busy':'busy'}.get(str(error), 'service_unavailable')
            raise InferenceError(code) from None
        except Exception:
            raise InferenceError('service_unavailable') from None

    def _send(self, request, *, cancel):
        return request_json(self._base, '/embed', self._headers, request,
                            timeout=15,cancel=cancel)


class CloudInferenceClient(InferenceClient):
    """Explicit managed identity client; no local secret or credential fallback."""
    def __init__(self, identity, count_tokens):
        from services.worker.cloud_identity import IdentityConfig, MetadataTokenProvider
        if not isinstance(identity,IdentityConfig) or not callable(count_tokens):
            raise TransportError('invalid_identity_configuration')
        self._base = identity.audience
        self.count_tokens = count_tokens
        self._identity = MetadataTokenProvider(identity)

    def _send(self, request, *, cancel):
        deadline = time.monotonic()+15
        token = self._identity.get(cancel=cancel,timeout=5)
        # Two copies must fit the receiver's unchanged 16 KiB header budget,
        # leaving room for Host, content framing and platform forwarding headers.
        if len(credential(token)) > 7168:
            raise TransportError('invalid_identity_token')
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise TransportError('timeout')
        try:
            headers = {'Authorization':'Bearer '+token,
                       'X-Serverless-Authorization':'Bearer '+token}
            return request_json(self._base,'/embed',headers,
                                request,timeout=remaining,cancel=cancel)
        except TransportError as error:
            if str(error)=='authentication_failed':
                self._identity.invalidate()
            raise
