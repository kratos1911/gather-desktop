"""Optional encrypted Upstash cache for query vectors, never source results/Auth.

Trusted backend configuration only. Fixed commands, TTL and operation deadlines;
no redirects/retries, raw query keys, plaintext vectors, or credential logging.
"""
import base64
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from uuid import UUID

from services.inference.runtime import MODEL, REVISION, DIMENSIONS, QUERY_TEMPLATE
from services.worker.service_transport import credential, origin, request_json, strict_json, TransportError

TTL_SECONDS = 600
OPERATION_SECONDS = 1
BACKOFF_SECONDS = 30
MAX_RECORD_BYTES = 24576
SAFE_FAILURES = frozenset(('timeout','authentication_failed','rate_limited','invalid_response',
                          'service_unavailable','busy','cleanup_failed'))
EVENTS = frozenset(('hit', 'miss', 'invalid', 'error', 'stored', 'write_error', 'backoff')) | frozenset(
    'transport_'+reason for reason in SAFE_FAILURES)


def valid_vector(vector):
    return (type(vector) is list and len(vector) == DIMENSIONS
            and all(type(n) in (int, float) and math.isfinite(n) for n in vector)
            and abs(math.hypot(*vector)-1) <= .001)


class QueryCache:
    def __init__(self, endpoint, token, master_key, *, _transport=request_json,
                 _clock=time.time, _monotonic=time.monotonic, record=None):
        self.endpoint = origin(endpoint)
        url = urlsplit(self.endpoint)
        if (not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.upstash\.io', url.hostname or '')
                or url.port not in (None, 443) or type(master_key) is not bytes or len(master_key) != 32):
            raise ValueError('invalid_query_cache_configuration')
        self._headers = {'Authorization': 'Bearer '+credential(token)}
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        material = HKDF(algorithm=hashes.SHA256(),length=64,salt=None,
                        info=b'gather-query-cache-v1').derive(master_key)
        self._cipher, self._hmac = AESGCM(material[:32]), material[32:]
        self._send, self._clock, self._monotonic = _transport, _clock, _monotonic
        self._record, self._retry_at = record, 0

    def _event(self, event):
        if event not in EVENTS:
            raise ValueError('invalid_cache_event')
        if self._record is not None:
            try:
                self._record(event)
            except Exception:
                pass  # Diagnostics never alter search behavior.

    def _key(self, owner, query):
        if (type(owner) is not str or str(UUID(owner)) != owner
                or type(query) is not str or not query.strip() or len(query.encode('utf-8')) > 8192):
            raise ValueError('invalid_cache_identity')
        identity = json.dumps([1,owner,MODEL,REVISION,DIMENSIONS,QUERY_TEMPLATE,query],
                              ensure_ascii=False,separators=(',', ':')).encode()
        return 'gather:qv:1:'+hmac.new(self._hmac,identity,hashlib.sha256).hexdigest()

    def _available(self, cancel):
        if cancel is not None and cancel.is_set():
            return False
        if self._monotonic() < self._retry_at:
            self._event('backoff')
            return False
        return True

    def _error(self, event, error=None):
        self._retry_at = self._monotonic()+BACKOFF_SECONDS
        self._event(event)
        if isinstance(error,TransportError) and str(error) in SAFE_FAILURES:
            self._event('transport_'+str(error))

    def _command(self, command, cancel):
        reply = self._send(self.endpoint,'',self._headers,command,
                           timeout=OPERATION_SECONDS,cancel=cancel)
        if type(reply) is not dict or set(reply) != {'result'}:
            raise ValueError('invalid_cache_response')
        return reply['result']

    def get(self, owner, query, *, cancel=None):
        if not self._available(cancel):
            return None
        try:
            key = self._key(owner,query)
            value = self._command(['GET',key],cancel)
        except Exception as error:
            self._error('error',error)
            return None
        if value is None:
            self._event('miss')
            return None
        try:
            if type(value) is not str or not 40 <= len(value) <= MAX_RECORD_BYTES:
                raise ValueError('invalid_cache_record')
            raw = base64.b64decode(value,validate=True)
            plain = self._cipher.decrypt(raw[:12],raw[12:],key.encode())
            if len(plain) > 16384:
                raise ValueError('invalid_cache_record')
            payload = strict_json(plain)
            now = self._clock()
            if (type(payload) is not dict or set(payload) != {'v','created','expires','vector'}
                    or type(payload['v']) is not int or payload['v'] != 1
                    or type(payload['created']) is not int or type(payload['expires']) is not int
                    or payload['expires']-payload['created'] != TTL_SECONDS
                    or not payload['created'] <= now < payload['expires']
                    or not valid_vector(payload['vector'])):
                raise ValueError('invalid_cache_record')
            self._event('hit')
            return payload['vector']
        except Exception:
            # A corrupt/expired record is a miss that the next valid PUT repairs.
            self._event('invalid')
            return None

    def put(self, owner, query, vector, *, cancel=None):
        if not self._available(cancel):
            return
        try:
            if not valid_vector(vector):
                raise ValueError('invalid_cache_vector')
            key, now = self._key(owner,query), int(self._clock())
            plain = json.dumps(dict(v=1,created=now,expires=now+TTL_SECONDS,vector=vector),
                               allow_nan=False,separators=(',', ':')).encode()
            if len(plain) > 16384:
                raise ValueError('invalid_cache_record')
            nonce = os.urandom(12)
            value = base64.b64encode(nonce+self._cipher.encrypt(nonce,plain,key.encode())).decode()
            if len(value) > MAX_RECORD_BYTES:
                raise ValueError('invalid_cache_record')
            if self._command(['SET',key,value,'EX',TTL_SECONDS],cancel) != 'OK':
                raise ValueError('cache_write_failed')
            self._event('stored')
        except Exception as error:
            self._error('write_error',error)


def from_environment(environment, *, record=None):
    """Default off. Enabled startup requires explicit endpoint and mounted secrets."""
    enabled = environment.get('GATHER_QUERY_CACHE','0')
    if enabled == '0':
        return None
    if enabled != '1':
        raise ValueError('invalid_query_cache_configuration')
    def secret(path, maximum):
        value = Path(path)
        if value.is_symlink() or not value.is_file() or value.stat().st_size > maximum:
            raise ValueError('query_cache_secret_unavailable')
        return value.read_text(encoding='utf-8')
    key = base64.b64decode(secret('/secrets/gather_query_cache/key',128).strip(),validate=True)
    return QueryCache(environment.get('GATHER_UPSTASH_URL',''),
        secret('/secrets/gather_upstash/token',8192),key,record=record)
