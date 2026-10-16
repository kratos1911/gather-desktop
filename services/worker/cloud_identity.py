"""Outbound Cloud Run identity. Claims checks here are NOT JWT verification.

Only a trusted metadata fetch supplies tokens. Google IAM validates invocation.
Local configuration validation does not prove a deployed IAM policy exists.
"""
import base64
from dataclasses import dataclass
import re
import threading
import time

from services.worker.service_transport import TransportError, strict_json, request_identity_token


def validate_audience(value):
    if not isinstance(value,str) or not re.fullmatch(r'https://[a-z0-9][a-z0-9-]{0,200}\.run\.app',value):
        raise TransportError('invalid_identity_configuration')
    return value


@dataclass(frozen=True)
class IdentityConfig:
    audience: str
    caller_email: str
    invoker_members: tuple[str,...]
    invoker_check_required: bool = True

    def __post_init__(self):
        validate_audience(self.audience)
        pattern = r'[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z][a-z0-9-]{4,28}[a-z0-9]\.iam\.gserviceaccount\.com'
        if (not isinstance(self.caller_email,str) or not re.fullmatch(pattern,self.caller_email)
                or self.invoker_check_required is not True
                or not isinstance(self.invoker_members,tuple) or not 1 <= len(self.invoker_members) <= 2
                or any(not isinstance(m,str) for m in self.invoker_members)
                or len(set(self.invoker_members)) != len(self.invoker_members)
                or 'serviceAccount:'+self.caller_email not in self.invoker_members
                or any(not isinstance(m,str) or not m.startswith('serviceAccount:')
                       or not re.fullmatch(pattern,m.removeprefix('serviceAccount:')) for m in self.invoker_members)):
            raise TransportError('invalid_identity_configuration')


def _claims(token, config, now):
    try:
        if not isinstance(token,str) or len(token)>8192:
            raise ValueError()
        pieces = token.split('.')
        if len(pieces)!=3 or any(not re.fullmatch(r'[A-Za-z0-9_-]+',p) for p in pieces):
            raise ValueError()
        header, claims = [strict_json(base64.urlsafe_b64decode(p+'='*((-len(p))%4))) for p in pieces[:2]]
        if (header.get('alg')!='RS256' or not isinstance(header.get('kid'),str) or not header['kid']
                or claims.get('iss') not in ('https://accounts.google.com','accounts.google.com')
                or claims.get('aud') != config.audience or claims.get('email') != config.caller_email
                or claims.get('email_verified') is not True
                or not isinstance(claims.get('sub'),str) or not claims['sub'].isdigit()
                or type(claims.get('exp')) is not int or type(claims.get('iat')) is not int
                or claims['iat'] > now+60 or claims['iat'] >= claims['exp']
                or not now+60 < claims['exp'] <= now+3660
                or claims['exp']-claims['iat']>3660):
            raise ValueError()
        return claims['exp']
    except Exception:
        raise TransportError('invalid_identity_token') from None


class MetadataTokenProvider:
    def __init__(self, config):
        if not isinstance(config,IdentityConfig):
            raise TransportError('invalid_identity_configuration')
        self._config = config
        self._token = None
        self._expiry = self._deadline = 0
        self._lock = threading.Lock()

    @property
    def config(self):
        return self._config

    def invalidate(self):
        with self._lock:
            self._token = None
            self._expiry = self._deadline = 0

    def get(self, *, cancel=None, timeout=5):
        if not self._lock.acquire(blocking=False):
            raise TransportError('busy')
        try:
            if cancel is not None and cancel.is_set():
                raise TransportError('cancelled')
            if self._token and time.time()+60 < self._expiry and time.monotonic()<self._deadline:
                return self._token
            self._token = None
            token = request_identity_token(self.config.audience,timeout=timeout,cancel=cancel)
            if cancel is not None and cancel.is_set():
                raise TransportError('cancelled')
            now = time.time()
            expiry = _claims(token,self.config,now)
            self._token, self._expiry = token, expiry
            self._deadline = time.monotonic()+(expiry-now-60)
            return token
        except TransportError:
            raise
        except Exception:
            raise TransportError('identity_unavailable') from None
        finally:
            self._lock.release()
