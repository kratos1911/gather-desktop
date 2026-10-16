"""Bounded JSON requests to operator-configured services, never bookmark URLs.

One isolated helper per request bounds DNS/TLS/body time as well as socket time.
No retry, proxy inheritance, redirect, implicit credential or model startup.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, build_opener

from services.worker.embedding_client import _NoRedirect

MAX_REQUEST = 65536
MAX_RESPONSE = 4 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]
_SLOT = threading.BoundedSemaphore(1)


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


def request_json(base, path, headers, payload, *, timeout, cancel=None):
    """Internal call: validated fixed base/path/header configuration required."""
    if type(timeout) not in (int, float) or not 0 < timeout <= 15:
        raise TransportError('invalid_configuration')
    try:
        body = None if payload is None else json.dumps(payload, allow_nan=False).encode('utf-8')
        if body is not None and len(body) > MAX_REQUEST:
            raise ValueError()
        wire = json.dumps(dict(url=base+path, headers=headers,
                               body=None if body is None else body.decode('utf-8'))).encode()
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise TransportError('invalid_request') from None
    if cancel is not None and cancel.is_set():
        raise TransportError('cancelled')
    if not _SLOT.acquire(blocking=False):
        raise TransportError('busy')
    process = None
    deadline = time.monotonic() + timeout
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
                 b'invalid_response', b'service_unavailable'}
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


def child_main():
    # Only called by the fixed trusted parent; private payload arrives via stdin.
    output = b'ERR\nservice_unavailable'
    try:
        raw = sys.stdin.buffer.read(2 * MAX_REQUEST + 32769)
        if len(raw) > 2 * MAX_REQUEST + 32768:
            raise ValueError()
        args = strict_json(raw)
        body = args['body']
        headers = dict(args['headers'], **{'Accept': 'application/json',
            'Accept-Encoding': 'identity', 'Content-Type': 'application/json'})
        request = Request(args['url'], headers=headers,
            data=None if body is None else body.encode('utf-8'),
            method='GET' if body is None else 'POST')
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(request, timeout=15) as response:
            if response.status != 200 or response.headers.get_content_type() != 'application/json':
                output = b'ERR\ninvalid_response'
            elif response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                output = b'ERR\ninvalid_response'
            else:
                data = response.read(MAX_RESPONSE + 1)
                output = b'ERR\nresponse_too_large' if len(data) > MAX_RESPONSE else b'OK\n'+data
    except HTTPError as error:
        output = b'ERR\n' + (b'authentication_failed' if error.code in (401,403) else
                  b'rate_limited' if error.code == 429 else b'service_unavailable')
        error.close()  # Do not read or log remote error bodies.
    except Exception:
        pass
    sys.stdout.buffer.write(output)
