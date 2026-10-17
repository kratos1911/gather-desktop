"""Offline receiving verifier; trusted Google key retrieval is a separate gate.

Never load key URLs or caller identities from a request. No implicit credentials,
network calls or fallback authentication. Snapshot provenance belongs to trusted
startup code; synthetic snapshots are used only by tests.
"""
import base64
from importlib.metadata import version
import re
import time
from types import MappingProxyType

from google.auth import jwt

from services.worker.cloud_identity import IdentityConfig
from services.worker.service_transport import strict_json


class GoogleServiceAuth:
    """One allowed service identity; bounded, immutable public-key snapshot.

    key_ttl must not exceed the authenticated key response's remaining freshness.
    Maximum local lifetime is five minutes. Recreate the verifier on key rotation.
    This verifies signatures; it does NOT establish Cloud Run IAM permissions.
    """
    def __init__(self, identity, caller_subject, certificates, *, key_ttl):
        if (not isinstance(identity, IdentityConfig)
                or not isinstance(caller_subject, str)
                or not re.fullmatch(r'[0-9]{1,32}', caller_subject)
                or type(key_ttl) not in (int, float) or not 0 < key_ttl <= 300
                or not isinstance(certificates, dict) or not 1 <= len(certificates) <= 8):
            raise ValueError('invalid_verifier_configuration')
        if version('google-auth') != '2.59.1' or version('cryptography') != '50.0.2':
            raise ValueError('unverified_auth_dependencies')
        copied = {}
        try:
            for kid, pem in certificates.items():
                if (not isinstance(kid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', kid)
                        or not isinstance(pem, str) or not 1 <= len(pem) <= 8192):
                    raise ValueError()
                # Validate the trusted snapshot before admitting requests.
                # Require a bounded RSA key before admitting any requests.
                from cryptography import x509
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import rsa
                raw = pem.encode('ascii')
                key = (x509.load_pem_x509_certificate(raw).public_key()
                       if raw.startswith(b'-----BEGIN CERTIFICATE-----')
                       else serialization.load_pem_public_key(raw))
                if not isinstance(key, rsa.RSAPublicKey) or not 2048 <= key.key_size <= 4096:
                    raise ValueError()
                copied[kid] = pem
        except Exception:
            raise ValueError('invalid_verifier_configuration') from None
        self._identity = identity
        self._subject = caller_subject
        self._certificates = MappingProxyType(copied)
        self._deadline = time.monotonic() + key_ttl
        self._expires = time.time() + key_ttl

    @property
    def ready(self):
        return time.monotonic() < self._deadline and time.time() < self._expires

    def __call__(self, headers):
        try:
            if not self.ready:
                return False
            values = [v for k, v in headers if k == b'authorization']
            if len(values) != 1 or not isinstance(values[0], bytes):
                return False
            value = values[0]
            if not value.startswith(b'Bearer ') or not 1 <= len(value) - 7 <= 8192:
                return False
            token = value[7:].decode('ascii')
            parts = token.split('.')
            if len(parts) != 3 or any(not re.fullmatch(r'[A-Za-z0-9_-]+', p) for p in parts):
                return False
            header, claims = [strict_json(base64.urlsafe_b64decode(p+'='*((-len(p)) % 4)))
                              for p in parts[:2]]
            if (not isinstance(header, dict) or not isinstance(claims, dict)
                    or set(header) - {'alg','kid','typ'} or header.get('alg') != 'RS256'
                    or header.get('typ', 'JWT') != 'JWT'
                    or header.get('kid') not in self._certificates):
                return False
            now = time.time()
            if (claims.get('iss') not in ('https://accounts.google.com', 'accounts.google.com')
                    or claims.get('aud') != self._identity.audience
                    or claims.get('sub') != self._subject
                    or claims.get('email') != self._identity.caller_email
                    or claims.get('email_verified') is not True
                    or type(claims.get('iat')) is not int or type(claims.get('exp')) is not int
                    or not claims['iat'] <= now < claims['exp']
                    or not 0 < claims['exp'] - claims['iat'] <= 3660
                    or ('nbf' in claims and (type(claims['nbf']) is not int or claims['nbf'] > now))):
                return False
            # Unverified fields above only reject. Only library signature success
            # can authorize; algorithm/key ID are restricted before this call.
            jwt.decode(token, certs=dict(self._certificates), verify=True,
                       audience=self._identity.audience, clock_skew_in_seconds=0)
            return self.ready and time.time() < claims['exp']
        except Exception:
            return False  # No token/claim details in errors or logs.
