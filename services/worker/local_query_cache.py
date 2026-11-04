"""Operator-only Windows protected cache setup; never shipped desktop secrets."""
import base64
import json
from pathlib import Path

from services.worker.local_credentials import dpapi
from services.worker.query_cache import QueryCache
from services.worker.service_transport import strict_json

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT/'output/credentials/upstash-query-cache.dpapi'
MAX_BYTES = 16384


def validate(value):
    if (type(value) is not dict or set(value) != {'version','endpoint','token','key','database_id'}
            or type(value['version']) is not int or value['version'] != 1
            or value['database_id'] != '40316b37-032e-4eb6-984b-ae6ad3dfffe9'):
        raise ValueError('invalid_cache_credentials')
    key = base64.b64decode(value['key'],validate=True)
    cache = QueryCache(value['endpoint'],value['token'],key)
    if cache.endpoint != 'https://relaxing-goshawk-225370.upstash.io':
        raise ValueError('unexpected_gather_cache_endpoint')
    return value


def save(value):
    validate(value)
    raw=json.dumps(value,allow_nan=False).encode()
    if len(raw) > MAX_BYTES:
        raise ValueError('invalid_cache_credentials')
    protected=dpapi(raw)
    if dpapi(protected,decrypt=True) != raw:
        raise ValueError('cache_credential_protection_failed')
    STORE.parent.mkdir(parents=True,exist_ok=True)
    with STORE.open('xb') as stream:
        stream.write(protected)


def load():
    if STORE.is_symlink() or not STORE.is_file() or STORE.stat().st_size > MAX_BYTES:
        raise ValueError('cache_credentials_unavailable')
    return validate(strict_json(dpapi(STORE.read_bytes(),decrypt=True)))
