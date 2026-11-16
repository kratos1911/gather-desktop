"""Reuse a fixed Supabase HTTPS connection within one synchronous search."""
import http.client
import json
import os
import queue
import select
import struct
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

from services.worker.service_transport import (
    MAX_REQUEST, MAX_RESPONSE, ROOT, TransportError, _SLOT, origin, strict_json,
)

SEARCH_PATHS = frozenset('/rest/v1/rpc/'+name for name in (
    'list_library_sources', 'search_published_previews', 'search_published_text',
    'search_published_keywords', 'open_published_text', 'read_published_pdf',
    'read_published_docx', 'read_published_image',
)) | {'/auth/v1/user'}
MAX_FRAME = 2 * MAX_REQUEST + 32768
HEADER = struct.Struct('!I')
ERRORS = {'authentication_failed', 'rate_limited', 'response_too_large',
          'invalid_response', 'service_unavailable'}


def read_frame(stream, limit):
    header = stream.read(HEADER.size)
    if not header:
        return None
    size, = HEADER.unpack(header)
    if size > limit:
        raise ValueError()
    value = stream.read(size)
    if len(value) != size:
        raise ValueError()
    return value


def write_frame(stream, value):
    stream.write(HEADER.pack(len(value)))
    stream.write(value)
    stream.flush()


class SearchHTTP:
    def __init__(self, base, headers, cancel, *, test_loopback=False):
        self.base, self.headers, self.cancel = base, dict(headers), cancel
        self.test_loopback = test_loopback
        self.process = None

    def close(self, *, graceful=True):
        process, self.process = self.process, None
        if process is None:
            return
        try:
            if graceful:
                process.stdin.close()
                try:
                    process.wait(timeout=.2)
                except subprocess.TimeoutExpired:
                    pass
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
        except (OSError, subprocess.SubprocessError):
            raise TransportError('cleanup_failed') from None
        finally:
            process.stdin.close()
            process.stdout.close()

    def request(self, path, payload, *, timeout=5):
        try:
            body = None if payload is None else json.dumps(payload, allow_nan=False)
            if (path not in SEARCH_PATHS or (path == '/auth/v1/user') != (body is None)
                    or (body is not None and len(body) > MAX_REQUEST)):
                raise ValueError()
            wire = json.dumps([self.base, self.headers, path, body, self.test_loopback]).encode()
            if len(wire) > MAX_FRAME:
                raise ValueError()
        except (ValueError, TypeError, RecursionError):
            raise TransportError('invalid_request') from None
        deadline = time.monotonic() + timeout
        if self.cancel is not None and self.cancel.is_set():
            raise TransportError('cancelled')
        if not _SLOT.acquire(blocking=False):
            raise TransportError('busy')
        try:
            if self.process is None:
                code = (f'import sys; sys.path.insert(0, {str(ROOT)!r}); '
                        'from services.worker.search_http import child_main; child_main()')
                env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR') if k in os.environ}
                self.process = subprocess.Popen([sys.executable, '-I', '-B', '-u', '-c', code],
                    cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL)
            process = self.process
            reply = queue.Queue(maxsize=1)

            def exchange():
                try:
                    write_frame(process.stdin, wire)
                    reply.put(read_frame(process.stdout, MAX_RESPONSE+1))
                except (OSError, ValueError, struct.error):
                    reply.put(None)

            threading.Thread(target=exchange, daemon=True).start()
            while True:
                if self.cancel is not None and self.cancel.is_set():
                    raise TransportError('cancelled')
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise TransportError('timeout')
                try:
                    result = reply.get(timeout=min(.05, remaining))
                    break
                except queue.Empty:
                    pass
            if self.cancel is not None and self.cancel.is_set():
                raise TransportError('cancelled')
            if time.monotonic() >= deadline:
                raise TransportError('timeout')
            if result and result[:1] == b'+':
                try:
                    return strict_json(result[1:])
                except (ValueError, UnicodeError, RecursionError):
                    raise TransportError('invalid_response') from None
            reason = result[1:].decode('ascii', errors='replace') if result and result[:1] == b'-' else ''
            raise TransportError(reason if reason in ERRORS else 'service_unavailable')
        except (OSError, TransportError) as error:
            self.close(graceful=False)
            if isinstance(error, TransportError):
                raise
            raise TransportError('service_unavailable') from None
        finally:
            _SLOT.release()


def exchange_http(connection, path, body, headers):
    # An idle peer may close during model startup. Discard its socket before
    # sending the next operation. Once sent, a failed operation is never replayed.
    if connection.sock is not None and select.select([connection.sock], [], [], 0)[0]:
        connection.close()
    connection.request('GET' if body is None else 'POST', path, body, headers)
    with connection.getresponse() as response:
        if response.status != 200:
            raise TransportError({401:'authentication_failed',403:'authentication_failed',
                                  429:'rate_limited'}.get(response.status,'service_unavailable'))
        if (response.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json'
                or response.headers.get('Content-Encoding', 'identity').lower() != 'identity'):
            raise TransportError('invalid_response')
        expected = response.length
        raw = response.read(MAX_RESPONSE+1)
        if len(raw) > MAX_RESPONSE:
            raise TransportError('response_too_large')
        if expected is not None and len(raw) != expected:
            raise TransportError('invalid_response')
        return raw


def child_main():
    connection = None
    try:
        for _ in range(16):
            wire = read_frame(sys.stdin.buffer, MAX_FRAME)
            if wire is None:
                return
            base, headers, path, body, test_loopback = strict_json(wire)
            if path not in SEARCH_PATHS or (path == '/auth/v1/user') != (body is None):
                raise ValueError()
            if connection is None:
                target = urlsplit(origin(base, test_loopback=test_loopback is True))
                connection_type = http.client.HTTPSConnection if target.scheme == 'https' else http.client.HTTPConnection
                connection = connection_type(target.hostname, target.port, timeout=5)
                binding = (base, headers, test_loopback)
            if (base, headers, test_loopback) != binding:
                raise ValueError()
            raw = exchange_http(connection, path, body, {
                **headers, 'Accept':'application/json', 'Content-Type':'application/json',
            })
            write_frame(sys.stdout.buffer, b'+'+raw)
    except TransportError as error:
        write_frame(sys.stdout.buffer, b'-'+str(error).encode('ascii'))
    except (OSError, http.client.HTTPException, ValueError, struct.error, RecursionError):
        pass
    finally:
        if connection is not None:
            connection.close()
