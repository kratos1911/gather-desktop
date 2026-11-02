"""Bounded JSON requests to operator-configured services, never bookmark URLs.

One isolated helper per request bounds DNS/TLS/body time as well as socket time.
No retry, proxy inheritance, redirect, implicit credential or model startup.
"""
import json
from email.utils import parsedate_to_datetime
import os
import re
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlencode
from urllib.request import Request, ProxyHandler, build_opener

from services.worker.embedding_client import _NoRedirect

MAX_REQUEST = 65536
MAX_RESPONSE = 4 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]
_SLOT = threading.BoundedSemaphore(1)
AUTH_CODES = {b'auth_'+code.encode() for code in (
    'invalid_credentials','email_not_confirmed','user_banned','email_provider_disabled','captcha_failed')}


class TransportError(Exception):
    """Fixed safe error codes only."""


def origin(value, *, test_loopback=False):
    try:
        url = urlsplit(value)
        local = test_loopback and url.scheme == 'http' and url.hostname == '127.0.0.1'
        if (not isinstance(value, str) or any(c.isspace() for c in value)
                or '\\' in value or not url.hostname or url.username or url.password
                or url.path not in ('', '/') or url.query or url.fragment
                or (url.scheme != 'https' and not local)):
            raise ValueError()
        url.port  # Reject malformed ports before any request.
        return value.rstrip('/')
    except (ValueError, TypeError, AttributeError):
        raise TransportError('invalid_configuration') from None


def credential(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 8192
            or any(ord(c) < 33 or ord(c) > 126 for c in value)):
        raise TransportError('invalid_configuration')
    return value


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError()
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def request_json(base, path, headers, payload, *, timeout, cancel=None, wait_for_slot=False, expected_status=200):
    """Internal call: validated fixed base/path/header configuration required."""
    if type(timeout) not in (int, float) or not 0 < timeout <= 15:
        raise TransportError('invalid_configuration')
    if type(expected_status) is not int or expected_status not in (200,202):
        raise TransportError('invalid_configuration')
    try:
        body = None if payload is None else json.dumps(payload, allow_nan=False).encode('utf-8')
        if body is not None and len(body) > MAX_REQUEST:
            raise ValueError()
        value=dict(url=base+path, headers=headers,body=None if body is None else body.decode('utf-8'))
        if expected_status!=200:value['expected_status']=expected_status
        wire = json.dumps(value).encode()
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise TransportError('invalid_request') from None
    return _exchange(wire, timeout=timeout, cancel=cancel, wait_for_slot=wait_for_slot)


def request_identity_token(audience, *, timeout=5, cancel=None):
    """Explicit Google-runtime-only operation; no ADC/key files or URL injection."""
    from services.worker.cloud_identity import validate_audience
    validate_audience(audience)
    if type(timeout) not in (int,float) or not 0 < timeout <= 15:
        raise TransportError('invalid_configuration')
    return _exchange(json.dumps({'metadata_audience':audience}).encode(),
                     timeout=min(5,timeout), cancel=cancel)


def request_google_certificates(*, cancel=None):
    """Fixed public Google certificate endpoint; no caller tokens sent."""
    return _exchange(b'{"google_certificates":true}', timeout=5, cancel=cancel)


def _exchange(wire, *, timeout, cancel, wait_for_slot=False):
    if type(timeout) not in (int,float) or not 0 < timeout <= 15:
        raise TransportError('invalid_configuration')
    if cancel is not None and cancel.is_set():
        raise TransportError('cancelled')
    deadline = time.monotonic() + timeout
    if type(wait_for_slot) is not bool: raise TransportError('invalid_configuration')
    while not _SLOT.acquire(blocking=False):
        if not wait_for_slot: raise TransportError('busy')
        if cancel is not None and cancel.is_set(): raise TransportError('cancelled')
        remaining = deadline-time.monotonic()
        if remaining<=0: raise TransportError('timeout')
        if cancel is not None: cancel.wait(min(.05,remaining))
        else: time.sleep(min(.05,remaining))
    process = None
    try:
        code = f'import sys; sys.path.insert(0, {str(ROOT)!r}); from services.worker.service_transport import child_main; child_main()'
        env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR') if k in os.environ}
        process = subprocess.Popen([sys.executable, '-I', '-B', '-u', '-c', code],
            cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL)
        first = True
        while True:
            if cancel is not None and cancel.is_set():
                raise TransportError('cancelled')
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise TransportError('timeout')
            try:
                output, _ = process.communicate(input=wire if first else None,
                                                timeout=min(.05, remaining))
                break
            except subprocess.TimeoutExpired:
                first = False
        if cancel is not None and cancel.is_set():
            raise TransportError('cancelled')
        if time.monotonic() >= deadline:
            raise TransportError('timeout')
        if process.returncode or len(output) > MAX_RESPONSE+3:
            raise TransportError('service_unavailable')
        if output.startswith(b'OK\n'):
            try:
                return strict_json(output[3:])
            except (ValueError, UnicodeError, RecursionError):
                raise TransportError('invalid_response') from None
        codes = {b'authentication_failed', b'rate_limited', b'response_too_large',
                 b'invalid_response', b'service_unavailable', b'model_busy',
                 b'model_not_ready',b'inference_deadline'} | AUTH_CODES
        if output.startswith(b'ERR\n') and output[4:] in codes:
            raise TransportError(output[4:].decode())
        raise TransportError('service_unavailable')
    except OSError:
        raise TransportError('service_unavailable') from None
    finally:
        try:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=2)
        except (OSError, subprocess.SubprocessError):
            raise TransportError('cleanup_failed') from None
        finally:
            _SLOT.release()


def auth_error_code(url, error):
    """Only fixed Auth codes escape a bounded password-grant error response."""
    try:
        target = urlsplit(url)
        if (target.path!='/auth/v1/token' or target.query!='grant_type=password'
                or error.code not in (400,401,403,422)
                or error.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json'
                or error.headers.get('Content-Encoding','identity').lower()!='identity'):
            return None
        raw = error.read(4097)
        if len(raw)>4096:
            return None
        value = strict_json(raw)
        code = value.get('error_code',value.get('code'))
        if not isinstance(code,str):
            return None
        encoded = b'auth_'+code.encode('ascii')
        return encoded if encoded in AUTH_CODES else None
    except Exception:
        return None


def inference_error_code(url, error):
    """Read only a tiny, exact diagnostic shape from existing inference routes."""
    try:
        path = urlsplit(url).path
        if (path not in ('/embed','/ready') or error.code not in (429,503,504)
            or error.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json'
            or error.headers.get('Content-Encoding','identity').lower()!='identity'):
            return None
        raw = error.read(4097)
        if len(raw)>4096: return None
        value = strict_json(raw)
        if path=='/ready' and error.code==503 and type(value) is dict and set(value)=={'ready'} and value['ready'] is False:
            return b'model_not_ready'
        if type(value) is not dict or set(value)!={'error'}: return None
        return {(429,'busy'):b'model_busy',(503,'model_unavailable'):b'model_not_ready',
                (504,'deadline_exceeded'):b'inference_deadline'}.get((error.code,value['error']))
    except Exception:
        return None


def child_main():
    # Only called by the fixed trusted parent; private payload arrives via stdin.
    output = b'ERR\nservice_unavailable'
    try:
        raw = sys.stdin.buffer.read(2 * MAX_REQUEST + 32769)
        if len(raw) > 2 * MAX_REQUEST + 32768:
            raise ValueError()
        args = strict_json(raw)
        if args == {'google_certificates': True}:
            sys.stdout.buffer.write(_certificate_response())
            return
        if set(args) == {'metadata_audience'}:
            output = _metadata_response(args['metadata_audience'])
            sys.stdout.buffer.write(output)
            return
        body = args['body']
        expected_status=args.get('expected_status',200)
        if type(expected_status) is not int or expected_status not in (200,202):
            raise ValueError()
        headers = dict(args['headers'], **{'Accept': 'application/json',
            'Accept-Encoding': 'identity', 'Content-Type': 'application/json'})
        request = Request(args['url'], headers=headers,
            data=None if body is None else body.encode('utf-8'),
            method='GET' if body is None else 'POST')
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(request, timeout=15) as response:
            if response.status != expected_status or response.headers.get_content_type() != 'application/json':
                output = b'ERR\ninvalid_response'
            elif response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                output = b'ERR\ninvalid_response'
            else:
                data = response.read(MAX_RESPONSE + 1)
                output = b'ERR\nresponse_too_large' if len(data) > MAX_RESPONSE else b'OK\n'+data
    except HTTPError as error:
        try:
            safe_code = auth_error_code(args.get('url',''),error) or inference_error_code(args.get('url',''),error)
            output = b'ERR\n' + (safe_code or (b'authentication_failed' if error.code in (401,403) else
                      b'rate_limited' if error.code == 429 else b'service_unavailable'))
        finally:
            error.close()  # Auth reads only bounded known codes; never logs bodies.
    except Exception:
        pass
    sys.stdout.buffer.write(output)


def _metadata_response(audience):
    from services.worker.cloud_identity import validate_audience
    validate_audience(audience)
    url = ('http://metadata.google.internal/computeMetadata/v1/instance/'
           'service-accounts/default/identity?' + urlencode({'audience':audience,'format':'full'}))
    request = Request(url,headers={'Metadata-Flavor':'Google','Accept-Encoding':'identity'})
    opener = build_opener(ProxyHandler({}),_NoRedirect())
    with opener.open(request,timeout=5) as response:
        if (response.status != 200 or response.headers.get('Metadata-Flavor') != 'Google'
                or response.headers.get('Content-Encoding','identity') != 'identity'):
            return b'ERR\ninvalid_response'
        data = response.read(8193)
        if len(data)>8192:
            return b'ERR\nresponse_too_large'
        token = data.decode('ascii')
        credential(token)
        return b'OK\n'+json.dumps(token).encode('ascii')


def _certificate_response():
    request = Request('https://www.googleapis.com/oauth2/v1/certs',
                      headers={'Accept':'application/json','Accept-Encoding':'identity'})
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=5) as response:
        if (response.status != 200 or response.headers.get_content_type() != 'application/json'
                or response.headers.get('Content-Encoding','identity').lower() != 'identity'):
            return b'ERR\ninvalid_response'
        raw = response.read(65537)
        if len(raw) > 65536:
            return b'ERR\nresponse_too_large'
        certificates = strict_json(raw)
        if not isinstance(certificates, dict) or not 1 <= len(certificates) <= 8:
            return b'ERR\ninvalid_response'
        # Honor upstream freshness rather than inventing a cache lifetime.
        directives = [d.strip().lower() for d in response.headers.get('Cache-Control','').split(',')]
        if any(d.split('=')[0] in ('no-store','no-cache','private') for d in directives):
            return b'ERR\ninvalid_response'
        ages = [d.split('=',1)[1] for d in directives if d.startswith('max-age=')]
        age = response.headers.get('Age','0')
        dates = response.headers.get_all('Date', [])
        if (len(ages) != 1 or not re.fullmatch(r'[0-9]{1,9}', ages[0])
                or not re.fullmatch(r'[0-9]{1,9}', age) or len(dates) != 1):
            return b'ERR\ninvalid_response'
        date = parsedate_to_datetime(dates[0])
        if date.tzinfo is None or date.timestamp() > time.time()+60:
            return b'ERR\ninvalid_response'
        ttl = min(300, int(ages[0])-max(int(age), max(0,time.time()-date.timestamp())))
        if ttl <= 0:
            return b'ERR\ninvalid_response'
        return b'OK\n'+json.dumps({'certificates':certificates,'ttl':ttl},allow_nan=False).encode()
