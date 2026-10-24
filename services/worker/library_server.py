"""Operator-only loopback HTTP server. No public bind or cloud provisioning."""
import asyncio
from importlib.metadata import version
import time

import uvicorn
from uvicorn.protocols.http.h11_impl import H11Protocol

from services.worker.library_api import LibraryAPI, ROUTES
from services.worker.text_processing import MAX_REQUEST_BYTES

MAX_HEADERS = 16384


class LibraryProtocol(H11Protocol):
    """Reviewed Uvicorn hooks: bounded TCP/header/body lifetime and connections."""
    def connection_made(self, transport):
        super().connection_made(transport)
        self._header = bytearray()
        self._headers_done = False
        self._received = 0
        self._deadline = time.monotonic()+5
        self._receive_timer = self.loop.call_later(5, transport.close)
        if len(self.connections) > 4:
            transport.close()
        original = self.app

        async def bounded(scope, receive, send):
            # Restrict Host against DNS rebinding; browsers may not use this
            # operator endpoint yet. CORS is not an authentication mechanism.
            headers = scope['headers']
            hosts = [v for k,v in headers if k == b'host']
            port = transport.get_extra_info('sockname')[1]
            origins = [v for k,v in headers if k == b'origin']
            configured = getattr(self.config.app,'operator_origin',None)
            allowed_origin = configured and origins == [configured.encode()]
            if hosts != [('127.0.0.1:'+str(port)).encode()] or (origins and not allowed_origin):
                await send({'type':'http.response.start','status':403,
                            'headers':[(b'content-type',b'application/json'),(b'cache-control',b'no-store')]})
                await send({'type':'http.response.body','body':b'{"error":"origin_not_allowed"}'})
                return
            scope['gather.deadline'] = self._deadline
            scope['gather.body_complete'] = self._receive_timer.cancel

            async def bounded_send(message):
                if allowed_origin and message['type'] == 'http.response.start':
                    message = dict(message, headers=list(message.get('headers',[]))+[
                        (b'access-control-allow-origin',configured.encode()),(b'vary',b'Origin')])
                await asyncio.wait_for(send(message), 5)
            if scope['method'] == 'OPTIONS':
                methods = [v for k,v in headers if k == b'access-control-request-method']
                requested = [v for k,v in headers if k == b'access-control-request-headers']
                valid = (allowed_origin and scope['path'] in ROUTES and not scope['query_string']
                    and methods == [b'POST'] and len(requested)<=1
                    and all(h.strip().lower() in (b'authorization',b'content-type')
                            for v in requested for h in v.split(b',')))
                await bounded_send({'type':'http.response.start','status':204 if valid else 403,
                    'headers':[(b'access-control-allow-methods',b'POST'),
                               (b'access-control-allow-headers',b'Authorization, Content-Type'),
                               (b'cache-control',b'no-store')] if valid else []})
                await bounded_send({'type':'http.response.body','body':b''})
                return
            await original(scope, receive, bounded_send)
        self.app = bounded

    def data_received(self, data):
        self._received += len(data)
        if self._received > MAX_HEADERS+MAX_REQUEST_BYTES:
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


class LibraryServer(uvicorn.Server):
    def handle_exit(self, sig, frame):
        self.config.app.stop()
        super().handle_exit(sig, frame)


def create_server(app, *, host='127.0.0.1', port=8765, operator_origin=None):
    if not isinstance(app, LibraryAPI) or host != '127.0.0.1':
        raise ValueError('loopback_library_only')
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('invalid_port')
    if version('uvicorn') != '0.54.0' or version('h11') != '0.16.0':
        raise ValueError('unverified_server_dependencies')
    if operator_origin not in (None,'http://localhost:1420'):
        raise ValueError('invalid_operator_origin')
    app.operator_origin = operator_origin
    return LibraryServer(uvicorn.Config(app, host=host, port=port, workers=1,
        http=LibraryProtocol, ws='none', lifespan='on', proxy_headers=False,
        access_log=False, log_config=None, log_level='critical', server_header=False,
        limit_concurrency=5, backlog=4, timeout_keep_alive=0,
        timeout_graceful_shutdown=5, h11_max_incomplete_event_size=MAX_HEADERS))
