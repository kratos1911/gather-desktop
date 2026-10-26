"""Internal ASGI library adapter. No listener, deployment, signup or credentials.

Trusted composition constructs a fresh LibrarySession for (bearer, cancel).
All remote dependencies must retain their existing bounded transports.
"""
import asyncio
import base64
import binascii
import json
import sys
import threading
import time

from services.worker.library_session import LibrarySession, LibraryError, identifier
from services.worker.service_transport import strict_json, credential
from services.worker.ingestion import parse
from services.worker.text_processing import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES
from services.worker.source_listing import parameters
from services.worker.model_availability import MODEL_HTTP

ROUTES = {
    '/v1/import': ({'request_id', 'title', 'media', 'content_base64'}, {'source_id','confirm_cloud_storage'}),
    '/v1/search': ({'query'}, {'limit'}),
    '/v1/status': ({'source_id'}, set()),
    '/v1/open': ({'source_id', 'version_id'}, set()),
    '/v1/delete': ({'source_id'}, set()),
    '/v1/list': (set(), {'limit','cursor'}),
    '/v1/model-status': (set(), set()),
}


def validate(path, value):
    required, optional = ROUTES[path]
    if type(value) is not dict or not required <= value.keys() or value.keys()-required-optional:
        raise ValueError()
    for key in ('request_id', 'source_id', 'version_id'):
        if key in value:
            identifier(value[key])
    if path == '/v1/list':
        parameters(**value)
    if path == '/v1/import':
        if 'confirm_cloud_storage' in value and type(value['confirm_cloud_storage']) is not bool:
            raise ValueError()
        title = value['title']
        if not isinstance(title, str) or not title.strip() or len(title) > 500:
            raise ValueError()
        raw = base64.b64decode(value.pop('content_base64'), validate=True)
        parse(raw, value['media'])
        value['original'] = raw
    if path == '/v1/search':
        if (not isinstance(value['query'], str) or not value['query'].strip()
                or len(value['query'].encode('utf-8')) > 8192
                or type(value.get('limit', 20)) is not int
                or not 1 <= value.get('limit', 20) <= 20):
            raise ValueError()
    return value


class LibraryAPI:
    """Single-flight per instance; no automatic retry or background worker launch."""
    def __init__(self, session_factory):
        if not callable(session_factory):
            raise ValueError('invalid_configuration')
        self.factory = session_factory
        self.slot = threading.BoundedSemaphore(1)
        self.stopping = threading.Event()
        self._active = set()
        self._operations = set()

    def stop(self):
        """Called on the server event loop; retain slots until work returns."""
        self.stopping.set()
        for event in tuple(self._active):
            event.set()

    async def drain(self):
        self.stop()
        if self._operations:
            _, pending = await asyncio.wait(tuple(self._operations), timeout=17)
            if pending:
                raise RuntimeError('library_shutdown_incomplete')

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                event = await receive()
                if event['type'] == 'lifespan.startup':
                    await send({'type':'lifespan.startup.complete'})
                elif event['type'] == 'lifespan.shutdown':
                    try:
                        await self.drain()
                        await send({'type':'lifespan.shutdown.complete'})
                    except RuntimeError:
                        await send({'type':'lifespan.shutdown.failed', 'message':'library_shutdown_incomplete'})
                    return
        if scope['type'] != 'http':
            raise ValueError('http_only')

        async def reply(status, value):
            try:
                raw = json.dumps(value, allow_nan=False).encode('utf-8')
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError()
            except (ValueError, TypeError, RecursionError):
                status, raw = 503, b'{"error":"invalid_service_output"}'
            await send({'type':'http.response.start', 'status':status, 'headers':[
                (b'content-type', b'application/json'), (b'cache-control', b'no-store'),
                (b'x-content-type-options', b'nosniff')]})
            await send({'type':'http.response.body', 'body':raw})

        path = scope.get('path')
        if self.stopping.is_set():
            return await reply(503, {'error':'server_stopping'})
        if path not in ROUTES:
            return await reply(404, {'error':'not_found'})
        if scope['method'] != 'POST':
            return await reply(405, {'error':'method_not_allowed'})
        headers = {}
        for key, value in scope.get('headers', []):
            headers.setdefault(key.lower(), []).append(value)
        auth = headers.get(b'authorization', [])
        try:
            if len(auth) != 1 or not auth[0].startswith(b'Bearer '):
                raise ValueError()
            token = auth[0][7:].decode('ascii')
            credential(token)
        except (ValueError, UnicodeError):
            return await reply(401, {'error':'authentication_required'})
        except Exception:
            return await reply(401, {'error':'authentication_required'})
        try:
            lengths = headers.get(b'content-length', [])
            if (scope.get('query_string') or len(lengths) != 1
                    or len(lengths[0]) > 6 or not lengths[0].isdigit()
                    or not 0 < int(lengths[0]) <= MAX_REQUEST_BYTES
                    or headers.get(b'content-type') != [b'application/json']
                    or headers.get(b'content-encoding', []) not in ([], [b'identity'])
                    or b'transfer-encoding' in headers
                    or sum(len(k)+len(v) for k,v in scope['headers']) > 16384):
                raise ValueError()
            expected = int(lengths[0])
        except (ValueError, TypeError, RecursionError):
            return await reply(400, {'error':'invalid_request'})
        if not self.slot.acquire(blocking=False):
            return await reply(429, {'error':'busy'})
        cancel = threading.Event()
        self._active.add(cancel)
        operation = watcher = None
        try:
            async def read():
                raw = bytearray()
                while True:
                    event = await receive()
                    if event['type'] != 'http.request':
                        raise ValueError()
                    raw.extend(event.get('body', b''))
                    if len(raw) > expected:
                        raise ValueError()
                    if not event.get('more_body', False):
                        break
                if len(raw) != expected:
                    raise ValueError()
                return validate(path, strict_json(bytes(raw)))
            try:
                remaining = min(5, scope.get('gather.deadline', time.monotonic()+5)-time.monotonic())
                value = await asyncio.wait_for(read(), max(.001, remaining))
                scope.get('gather.body_complete', lambda: None)()
            except (ValueError, TypeError, KeyError, binascii.Error, UnicodeError, RecursionError):
                return await reply(400, {'error':'invalid_request'})
            except asyncio.TimeoutError:
                return await reply(408, {'error':'request_timeout'})

            def invoke():
                session = self.factory(token, cancel)
                if not isinstance(session, LibrarySession):
                    raise ValueError('invalid_configuration')
                if cancel.is_set():
                    raise LibraryError('cancelled')
                method = getattr(session, {'/v1/import':'import_text','/v1/list':'list_sources',
                    '/v1/model-status':'model_status'}.get(path, path[4:]))
                if path in ('/v1/search','/v1/model-status'):
                    return method(**value, cancel=cancel)
                return method(**value)

            async def disconnected():
                while (await receive())['type'] != 'http.disconnect':
                    pass
                cancel.set()

            operation = asyncio.create_task(asyncio.to_thread(invoke))
            self._operations.add(operation)
            watcher = asyncio.create_task(disconnected())
            done, _ = await asyncio.wait([operation, watcher], timeout=30,
                                         return_when=asyncio.FIRST_COMPLETED)
            if watcher in done:
                return
            if operation not in done:
                return await reply(504, {'error':'operation_timeout'})
            try:
                result = operation.result()
            except LibraryError as error:
                code = str(error)
                status = 401 if code == 'session_unavailable' else 503
                if code in MODEL_HTTP: status = MODEL_HTTP[code]
                elif code == 'library_unavailable': status = 503
                elif code in ('file_import_disabled','file_confirmation_required'): status = 403
                elif code in ('file_invalid','file_exceeds_pilot_budget'): status = 400
                safe_codes = {'session_unavailable','library_unavailable',
                              'search_failed','invalid_query','cancelled','operation_failed'} | MODEL_HTTP.keys()
                print('Operator request failed: '+(code if code in safe_codes else 'operation_failed'),file=sys.stderr,flush=True)
                return await reply(status, {'error': code if code in MODEL_HTTP or code=='session_unavailable' else 'operation_failed'})
            except Exception:
                return await reply(503, {'error':'operation_failed'})
            await reply(202 if path == '/v1/import' else 200, result)
        finally:
            cancel.set()
            if watcher:
                watcher.cancel()
            if operation:
                # Cancelling a thread await does not kill its thread. Retain the
                # slot until the bounded dependency has actually returned.
                def release(task):
                    self._operations.discard(task)
                    self._active.discard(cancel)
                    if not task.cancelled():
                        task.exception()
                    self.slot.release()
                operation.add_done_callback(release)
            else:
                self._active.discard(cancel)
                self.slot.release()



def create_app(*, supabase_url, publishable_key, admission_factory, provider):
    """Trusted server composition only; never take these values from a request.

    Worker scheduling, secret loading, listening and TLS are separate gates.
    """
    from services.worker.service_clients import SessionClient
    def session(token, cancel):
        api = SessionClient(supabase_url, publishable_key, token, cancel=cancel)
        return LibrarySession(api, admission_factory, provider)
    return LibraryAPI(session)
