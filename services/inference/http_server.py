"""Authenticated loopback HTTP boundary for an explicitly started Runtime.

Local integration server only. Public ingress/TLS and managed-service identity
must be implemented and reviewed separately before cloud deployment.
"""
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
from socketserver import ThreadingMixIn
import threading
import time

from services.inference.runtime import InferenceError, validate_request
from services.worker.service_transport import strict_json

MAX_BODY = 65536
MAX_HEADERS = 16384
MAX_CONNECTIONS = 4
READ_DEADLINE = 5


class _HeaderBudget:
    def __init__(self, stream):
        self.stream, self.remaining = stream, MAX_HEADERS

    def readline(self, size=-1):
        data = self.stream.readline(min(size if size >= 0 else self.remaining+1,
                                        self.remaining+1))
        self.remaining -= len(data)
        if self.remaining < 0:
            raise ValueError('header_limit')
        return data

    def read(self, size):
        return self.stream.read(size)

    def close(self):
        self.stream.close()


class InferenceServer(ThreadingMixIn, HTTPServer):
    """No implicit model start, download, restart, or public bind."""
    daemon_threads = False
    block_on_close = True
    request_queue_size = MAX_CONNECTIONS

    def __init__(self, runtime, secret, *, port=0):
        if (not isinstance(secret, str) or not 32 <= len(secret) <= 256
                or any(ord(c) < 33 or ord(c) > 126 for c in secret)
                or not 0 < runtime.request_timeout <= 15):
            raise ValueError('invalid_server_configuration')
        self.runtime, self._secret = runtime, secret
        self._slots = threading.BoundedSemaphore(MAX_CONNECTIONS)
        super().__init__(('127.0.0.1', port), _Handler)

    def process_request(self, request, address):
        if not self._slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self._slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self._slots.release()

    def handle_error(self, *_):
        pass  # Never print request data or exception diagnostics.


class _Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'  # One request per connection, no pipelining.

    def setup(self):
        super().setup()
        self.rfile = _HeaderBudget(self.rfile)

    def log_message(self, *_):
        pass

    def handle(self):
        self.close_connection = True
        self.deadline = time.monotonic()+READ_DEADLINE
        self.connection.settimeout(READ_DEADLINE)
        self.timer = threading.Timer(READ_DEADLINE, self._expire)
        self.timer.daemon = True
        self.timer.start()
        try:
            super().handle()
        except (OSError, ValueError):
            pass
        finally:
            self.timer.cancel()

    def _expire(self):
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def reply(self, status, value):
        body = json.dumps(value, allow_nan=False).encode('utf-8')
        if len(body) > 128*1024:
            status, body = 503, b'{"error":"invalid_model_output"}'
        self.send_response_only(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def send_error(self, code, message=None, explain=None):
        self.reply(code, {'error':'invalid_request'})

    def do_POST(self):
        auth = self.headers.get_all('Authorization', [])
        if len(auth) != 1 or not hmac.compare_digest(
                auth[0].encode('utf-8'), ('Bearer '+self.server._secret).encode('ascii')):
            self.reply(401, {'error':'authentication_failed'})
            return
        if self.path != '/embed':
            self.reply(404, {'error':'not_found'})
            return
        lengths = self.headers.get_all('Content-Length', [])
        if (self.headers.get_all('Transfer-Encoding') or len(lengths) != 1
                or not lengths[0].isascii() or not lengths[0].isdecimal()
                or len(lengths[0]) > 6 or not 0 < int(lengths[0]) <= MAX_BODY
                or self.headers.get_all('Content-Type') != ['application/json']
                or self.headers.get_all('Content-Encoding') not in (None, ['identity'])):
            self.reply(400, {'error':'invalid_request'})
            return
        try:
            raw = self.rfile.read(int(lengths[0]))
            if len(raw) != int(lengths[0]) or time.monotonic() >= self.deadline:
                return
            value = strict_json(raw)
            validate_request(value)
        except (ValueError, UnicodeError, RecursionError, InferenceError):
            self.reply(400, {'error':'invalid_request'})
            return
        # Receiving bytes has its own deadline; model compute is independently
        # bounded and reaped by Runtime, even if the HTTP client disconnects.
        self.timer.cancel()
        try:
            result = self.server.runtime.infer(value)
            self.reply(200, result)
        except InferenceError as error:
            code = str(error)
            if code == 'busy':
                self.reply(429, {'error':'busy'})
            elif code == 'deadline_exceeded':
                self.reply(504, {'error':'deadline_exceeded'})
            elif code == 'token_limit':
                self.reply(400, {'error':'token_limit'})
            else:
                self.reply(503, {'error':'model_unavailable'})
        except Exception:
            self.reply(503, {'error':'model_unavailable'})
