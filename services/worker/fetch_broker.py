"""Host-side fetch process deadline. Not a filesystem/network security sandbox.

The fixed child uses only the restricted transport. No desktop/API route enables
this module; operator code owns invocation, timeout and cancellation.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from services.worker.bookmarks import normalize_url
from services.worker.restricted_fetch import FetchedPage, MAX_BODY, CONTENT_TYPES, MAX_REDIRECTS

MAX_WIRE = 128 * 1024
_SLOT = threading.BoundedSemaphore(1)
ROOT = Path(__file__).resolve().parents[2]


class BrokerError(RuntimeError):
    """Content-free outcome for callers; raw child diagnostics are discarded."""


def child_main():
    """Fixed entrypoint. One bounded URL in; bounded JSON/base64 page out."""
    from services.worker.restricted_fetch import fetch_page
    try:
        raw = sys.stdin.buffer.read(8193)
        if len(raw) > 8192:
            raise ValueError()
        request = json.loads(raw)
        if not isinstance(request, dict) or set(request) != {'url'}:
            raise ValueError()
        page = fetch_page(normalize_url(request['url']))
        result = {'status': 'fetched', 'final_url': page.final_url,
                  'content_type': page.content_type, 'redirects': page.redirects,
                  'body_base64': base64.b64encode(page.body).decode('ascii')}
        encoded = json.dumps(result).encode()
        if len(encoded) > MAX_WIRE:
            raise ValueError()
    except Exception:
        # No URL, exception message, response header or page content in errors.
        encoded = b'{"status":"error"}'
    sys.stdout.buffer.write(encoded)


def _page(raw):
    try:
        def unique(pairs):
            values = {}
            for key, value in pairs:
                if key in values:
                    raise ValueError()
                values[key] = value
            return values
        value = json.loads(raw, object_pairs_hook=unique)
        if value == {'status': 'error'}:
            raise BrokerError('FETCH_FAILED')
        if (not isinstance(value, dict) or set(value) != {
                'status', 'final_url', 'content_type', 'redirects', 'body_base64'}
                or value['status'] != 'fetched'
                or value['content_type'] not in CONTENT_TYPES
                or type(value['redirects']) is not int
                or not 0 <= value['redirects'] <= MAX_REDIRECTS):
            raise ValueError()
        final_url = normalize_url(value['final_url'])
        body = base64.b64decode(value['body_base64'], validate=True)
        if len(body) > MAX_BODY:
            raise ValueError()
        return FetchedPage(final_url, value['content_type'], body, value['redirects'])
    except (ValueError, TypeError, KeyError, RecursionError):
        raise BrokerError('FETCH_INVALID_RESULT') from None


class FetchBroker:
    # Test subclasses can replace trusted code; URL/job data cannot.
    _CHILD_CODE = 'from services.worker.fetch_broker import child_main; child_main()'

    def fetch(self, url, *, timeout=15, cancel=None):
        try:
            url = normalize_url(url)
        except ValueError:
            raise BrokerError('FETCH_INPUT_DENIED') from None
        if type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('FETCH_TIMEOUT_INVALID')
        payload = json.dumps({'url': url}).encode()
        if len(payload) > 8192:
            raise BrokerError('FETCH_INPUT_DENIED')
        if cancel is not None and cancel.is_set():
            raise BrokerError('FETCH_CANCELLED')
        if not _SLOT.acquire(blocking=False):
            raise BrokerError('FETCH_BUSY')
        process = None
        threads = []
        deadline = time.monotonic() + timeout
        try:
            code = f'import sys; sys.path.insert(0, {str(ROOT)!r}); ' + self._CHILD_CODE
            # Do not inherit provider secrets, proxy settings or Python startup hooks.
            environment = {key: os.environ[key] for key in ('SYSTEMROOT', 'WINDIR') if key in os.environ}
            process = subprocess.Popen([sys.executable, '-I', '-B', '-u', '-c', code],
                                       cwd=ROOT, env=environment, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = bytearray()
            overflow = threading.Event()
            io_error = threading.Event()

            def read(stream, limit, keep=False):
                count = 0
                try:
                    while chunk := stream.read1(8192):
                        count += len(chunk)
                        if count > limit:
                            overflow.set()
                        elif keep:
                            output.extend(chunk)
                except (OSError, ValueError):
                    io_error.set()

            def write():
                try:
                    process.stdin.write(payload)
                    process.stdin.close()
                except (OSError, ValueError):
                    io_error.set()

            threads = [threading.Thread(target=read, args=(process.stdout, MAX_WIRE, True)),
                       threading.Thread(target=read, args=(process.stderr, 8192)),
                       threading.Thread(target=write)]
            for thread in threads:
                thread.daemon = True
                thread.start()
            while process.poll() is None:
                self._check(deadline, cancel, overflow)
                overflow.wait(.01)
            for thread in threads:
                thread.join(timeout=max(0, min(.1, deadline - time.monotonic())))
            self._check(deadline, cancel, overflow)
            if any(t.is_alive() for t in threads) or io_error.is_set() or process.returncode:
                raise BrokerError('FETCH_PROCESS_FAILED')
            return _page(bytes(output))
        except (OSError, subprocess.SubprocessError):
            raise BrokerError('FETCH_PROCESS_FAILED') from None
        finally:
            try:
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=2)
                    for thread in threads:
                        thread.join(timeout=2)
                    if any(t.is_alive() for t in threads):
                        raise BrokerError('FETCH_CLEANUP_FAILED')
                    for stream in (process.stdin, process.stdout, process.stderr):
                        stream.close()
            except (OSError, subprocess.SubprocessError):
                raise BrokerError('FETCH_CLEANUP_FAILED') from None
            finally:
                _SLOT.release()

    @staticmethod
    def _check(deadline, cancel, overflow):
        if cancel is not None and cancel.is_set():
            raise BrokerError('FETCH_CANCELLED')
        if time.monotonic() >= deadline:
            raise BrokerError('FETCH_TIMEOUT')
        if overflow.is_set():
            raise BrokerError('FETCH_OUTPUT_LIMIT')
