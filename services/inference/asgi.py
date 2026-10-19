"""Bounded server adapter; intended cloud policy is not deployed IAM evidence.

Only trusted code constructs runtime and authentication. No import-time model load.
"""
import asyncio
from contextlib import asynccontextmanager
import hmac
from importlib.metadata import version
import json
import threading
import time

from fastapi import FastAPI, Request
from starlette.responses import Response
import uvicorn
from uvicorn.protocols.http.h11_impl import H11Protocol

from services.inference.runtime import InferenceError, validate_request
from services.worker.service_transport import strict_json

READ_SECONDS = 5
MAX_BODY = 65536
MAX_HEADERS = 16384


class LocalBearer:
    """Local tests only; cannot be used for a public server bind."""
    def __init__(self, secret):
        if (not isinstance(secret, str) or not 32 <= len(secret) <= 256
                or any(ord(c) < 33 or ord(c) > 126 for c in secret)):
            raise ValueError('invalid_auth_configuration')
        self._expected = ('Bearer '+secret).encode('ascii')

    def __call__(self, headers):
        values = [v for k,v in headers if k == b'authorization']
        return len(values) == 1 and hmac.compare_digest(values[0], self._expected)


def create_app(runtime, authenticate):
    if not callable(authenticate) or not 0 < runtime.request_timeout <= 15:
        raise ValueError('invalid_configuration')
    stopping = threading.Event()
    state = {'started':False, 'busy':False}

    @asynccontextmanager
    async def lifespan(app):
        try:
            if hasattr(authenticate, 'start'):
                await authenticate.start(cancel=stopping)
            await asyncio.to_thread(runtime.start, cancel=stopping)
            state['started'] = True
            yield
        finally:
            state['started'] = False
            stopping.set()
            try:
                await asyncio.to_thread(runtime.close)
            finally:
                if hasattr(authenticate, 'close'):
                    await authenticate.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.stopping = stopping
    app.state.runtime = runtime
    app.state.local_auth = isinstance(authenticate, LocalBearer)
    app.state.authenticate = authenticate

    def reply(status, value):
        raw = json.dumps(value, allow_nan=False).encode()
        if len(raw) > 128*1024:
            status, raw = 503, b'{"error":"invalid_model_output"}'
        return Response(raw,status_code=status,media_type='application/json',
                        headers={'Cache-Control':'no-store','Connection':'close'})

    @app.get('/ready')
    async def ready():
        ok = (state['started'] and runtime.ready and not stopping.is_set()
              and getattr(authenticate, 'ready', True))
        return reply(200 if ok else 503, {'ready':ok})

    @app.post('/embed')
    async def embed(request: Request):
        try:
            if not authenticate(request.scope['headers']):
                return reply(401, {'error':'authentication_failed'})
        except Exception:
            return reply(401, {'error':'authentication_failed'})
        if not state['started'] or stopping.is_set() or not runtime.ready:
            return reply(503, {'error':'model_unavailable'})
        if state['busy']:
            return reply(429, {'error':'busy'})
        headers = request.headers
        lengths = headers.getlist('content-length')
        if (request.scope['query_string'] or len(lengths) != 1
                or not lengths[0].isascii() or not lengths[0].isdecimal()
                or len(lengths[0]) > 6 or not 0 < int(lengths[0]) <= MAX_BODY
                or headers.getlist('transfer-encoding')
                or headers.getlist('content-type') != ['application/json']
                or headers.getlist('content-encoding') not in ([],['identity'])):
            return reply(400, {'error':'invalid_request'})
        async def body():
            raw = bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > MAX_BODY:
                    raise ValueError()
            if len(raw) != int(lengths[0]):
                raise ValueError()
            value = strict_json(raw)
            validate_request(value)
            return value
        try:
            remaining = request.scope.get('gather.deadline', time.monotonic()+READ_SECONDS)-time.monotonic()
            value = await asyncio.wait_for(body(), max(0,remaining))
        except Exception:
            return reply(400, {'error':'invalid_request'})
        if state['busy']:
            return reply(429, {'error':'busy'})
        if stopping.is_set():
            return reply(503, {'error':'model_unavailable'})
        state['busy'] = True  # No await between admission check and reservation.
        request.scope.get('gather.body_complete', lambda:None)()
        task = asyncio.create_task(asyncio.to_thread(runtime.infer, value, cancel=stopping))
        try:
            result = await asyncio.shield(task)
            return reply(200,result)
        except asyncio.CancelledError:
            # Do not release admission while a cancelled request still computes.
            stopping.set()
            try:
                await asyncio.shield(task)
            except InferenceError:
                pass
            raise
        except InferenceError as error:
            code = str(error)
            status = {'busy':429,'deadline_exceeded':504,'token_limit':400}.get(code,503)
            return reply(status, {'error':code if status != 503 else 'model_unavailable'})
        except Exception:
            return reply(503, {'error':'model_unavailable'})
        finally:
            state['busy'] = False
    return app


class BoundedProtocol(H11Protocol):
    """Pinned Uvicorn hook: total receive deadline starts at TCP acceptance."""
    def connection_made(self, transport):
        super().connection_made(transport)
        self._header = bytearray()
        self._headers_done = False
        self._received = 0
        self._deadline = time.monotonic()+READ_SECONDS
        self._receive_timer = self.loop.call_later(READ_SECONDS, transport.close)
        if len(self.connections) > 4:
            transport.close()
        original = self.app
        async def bounded(scope, receive, send):
            scope['gather.deadline'] = self._deadline
            scope['gather.body_complete'] = self._receive_timer.cancel
            async def bounded_send(message):
                await asyncio.wait_for(send(message),5)
            await original(scope, receive, bounded_send)
        self.app = bounded

    def data_received(self, data):
        self._received += len(data)
        if self._received > MAX_HEADERS+MAX_BODY:
            self.transport.close()
            return
        if not self._headers_done:
            self._header.extend(data[:MAX_HEADERS+4])
            end = self._header.find(b'\r\n\r\n')
            if (end < 0 and len(self._header)>MAX_HEADERS) or end+4>MAX_HEADERS:
                self.transport.close()
                return
            if end >= 0:
                self._headers_done = True
                self._header.clear()
        super().data_received(data)

    def connection_lost(self, exc):
        self._receive_timer.cancel()
        super().connection_lost(exc)


class InferenceASGIServer(uvicorn.Server):
    def handle_exit(self, sig, frame):
        self.config.app.state.stopping.set()
        super().handle_exit(sig, frame)


def create_server(app, *, host='127.0.0.1', port=8080, cloud_policy=None):
    if host != '127.0.0.1':
        from services.inference.managed_auth import ManagedGoogleServiceAuth
        from services.worker.cloud_identity import IdentityConfig
        auth = getattr(app.state, 'authenticate', None)
        if (host != '0.0.0.0' or type(auth) is not ManagedGoogleServiceAuth
                or type(cloud_policy) is not IdentityConfig
                or cloud_policy.audience != auth.identity.audience
                or set(cloud_policy.invoker_members) != {
                    'serviceAccount:'+email for email, _ in auth.identity.callers}):
            raise ValueError('cloud_identity_not_configured')
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('invalid_cloud_port')
    # Protocol hooks are tied to the reviewed version; never silently run with
    # the older shared h11 parser or an unreviewed Uvicorn hook implementation.
    if version('uvicorn') != '0.54.0' or version('h11') != '0.16.0':
        raise ValueError('unverified_server_dependencies')
    config = uvicorn.Config(app, host=host, port=port, workers=1,
        http=BoundedProtocol, ws='none', lifespan='on', proxy_headers=False,
        access_log=False, log_config=None, server_header=False,
        limit_concurrency=5, backlog=4, timeout_keep_alive=0,
        timeout_graceful_shutdown=5, h11_max_incomplete_event_size=MAX_HEADERS)
    return InferenceASGIServer(config)
