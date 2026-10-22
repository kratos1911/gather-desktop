"""Synthetic ASGI requests; no network, models or hosted database."""
import asyncio
import base64
import json
import threading
import unittest
from unittest.mock import Mock

from services.worker.library_api import LibraryAPI
from services.worker.library_session import LibrarySession, LibraryError

ID = '00000000-0000-0000-0000-000000000001'


class APITests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = Mock(spec=LibrarySession)
        for name in ('import_text', 'search', 'status', 'open', 'delete'):
            getattr(self.session, name).return_value = {'ok': True}
        self.factory = Mock(return_value=self.session)
        self.app = LibraryAPI(self.factory)

    async def request(self, path='/v1/status', value=None, raw=None, headers=None, method='POST'):
        raw = raw if raw is not None else json.dumps(value or {'source_id': ID}).encode()
        scope = {'type':'http','path':path,'method':method,'query_string':b'',
                 'headers':headers if headers is not None else [
                     (b'authorization', b'Bearer synthetic-token'),
                     (b'content-type', b'application/json'),
                     (b'content-length', str(len(raw)).encode())]}
        queue = asyncio.Queue()
        await queue.put({'type':'http.request','body':raw})
        output = []
        async def send(event): output.append(event)
        await self.app(scope, queue.get, send)
        await asyncio.sleep(0)
        return output

    async def test_all_five_routes(self):
        cases = [('/v1/import', {'request_id':ID,'title':'Note','media':'text/plain',
                  'content_base64':base64.b64encode(b'hello').decode()},202),
                 ('/v1/search',{'query':'security'},200),
                 ('/v1/status',{'source_id':ID},200),
                 ('/v1/open',{'source_id':ID,'version_id':ID},200),
                 ('/v1/delete',{'source_id':ID},200)]
        for path, value, status in cases:
            with self.subTest(path=path):
                result = await self.request(path,value)
                self.assertEqual(result[0]['status'],status)
        self.assertEqual(self.session.import_text.call_args.kwargs['original'], b'hello')
        self.assertIn('cancel',self.session.search.call_args.kwargs)

    async def test_reject_owner_override_and_invalid_inputs_before_factory(self):
        cases = [('/v1/status',{'source_id':ID,'user_id':ID}),
                 ('/v1/open',{'source_id':ID}),
                 ('/v1/delete',{'source_id':'invalid'}),
                 ('/v1/search',{'query':'x','limit':True}),
                 ('/v1/import',{'request_id':ID,'title':'x','media':'text/html','content_base64':'eA=='})]
        for path,value in cases:
            self.assertEqual((await self.request(path,value))[0]['status'],400)
        self.factory.assert_not_called()

    async def test_missing_and_duplicate_auth(self):
        for headers in ([],[(b'authorization',b'Bearer a'),(b'authorization',b'Bearer b')]):
            self.assertEqual((await self.request(headers=headers))[0]['status'],401)
        self.factory.assert_not_called()

    async def test_strict_json_and_size(self):
        for raw in (b'{"source_id":"a","source_id":"b"}',b'{"limit":NaN}',b'x'*98305):
            self.assertEqual((await self.request(raw=raw))[0]['status'],400)
        self.factory.assert_not_called()

    async def test_errors_are_redacted_and_no_store(self):
        self.session.status.side_effect = RuntimeError('secret password')
        output = await self.request()
        self.assertEqual(output[0]['status'],503)
        self.assertNotIn(b'secret',output[1]['body'])
        self.assertIn((b'cache-control',b'no-store'),output[0]['headers'])
        self.session.status.side_effect = LibraryError('session_unavailable')
        self.assertEqual((await self.request())[0]['status'],401)

    async def test_unknown_route_and_method(self):
        self.assertEqual((await self.request('/nope'))[0]['status'],404)
        self.assertEqual((await self.request(method='GET'))[0]['status'],405)
        self.factory.assert_not_called()

    async def test_invalid_output_hidden(self):
        self.session.status.return_value = {'bad':float('nan')}
        self.assertEqual((await self.request())[0]['status'],503)

    async def test_disconnect_cancels_and_holds_slot_until_thread_returns(self):
        started, finish = threading.Event(), threading.Event()
        def work(**kwargs):
            started.set()
            finish.wait(2)
            return {'ok':True}
        self.session.status.side_effect = work
        queue = asyncio.Queue()
        raw = json.dumps({'source_id':ID}).encode()
        await queue.put({'type':'http.request','body':raw})
        scope = {'type':'http','method':'POST','path':'/v1/status','query_string':b'',
                 'headers':[(b'authorization',b'Bearer test'),(b'content-type',b'application/json'),
                            (b'content-length',str(len(raw)).encode())]}
        async def send(event): pass
        task = asyncio.create_task(self.app(scope,queue.get,send))
        try:
            for _ in range(100):
                if started.is_set(): break
                await asyncio.sleep(.005)
            self.assertTrue(started.is_set())
            await queue.put({'type':'http.disconnect'})
            await task
            self.assertTrue(self.factory.call_args.args[1].is_set())
            self.assertEqual((await self.request())[0]['status'],429)
        finally:
            finish.set()
            await asyncio.sleep(.05)
        self.session.status.side_effect = None
        self.assertEqual((await self.request())[0]['status'],200)

    async def test_real_library_boundary_keeps_each_bearer_owner_isolated(self):
        from services.worker.service_clients import SessionClient
        calls = []
        def factory(token, cancel):
            api = Mock(spec=SessionClient)
            def call(method, path, payload=None):
                calls.append((token,path))
                if path == '/auth/v1/user':
                    if token == 'forged': raise RuntimeError('invalid JWT')
                    return {'id':ID}
                # Simulate authoritative SQL/RLS refusal for another owner.
                return [] if token == 'other' else [{'source_id':ID}]
            api.side_effect = call
            return LibrarySession(api,Mock(),Mock())
        self.app = LibraryAPI(factory)
        for token, expected in (('owner',200),('other',200),('forged',401)):
            raw = json.dumps({'source_id':ID}).encode()
            result = await self.request(raw=raw,headers=[
                (b'authorization',('Bearer '+token).encode()),
                (b'content-type',b'application/json'),(b'content-length',str(len(raw)).encode())])
            self.assertEqual(result[0]['status'],expected)
            if token == 'other': self.assertEqual(json.loads(result[1]['body']),[])
        self.assertNotIn(('forged','/rest/v1/rpc/source_processing_status'),calls)

    async def test_response_deadline_cancels_without_releasing_active_worker(self):
        from unittest.mock import patch
        finish = threading.Event()
        self.session.status.side_effect = lambda **kwargs: finish.wait(2)
        async def deadline(*args, **kwargs):
            await asyncio.sleep(.01)
            return set(), set(args[0])
        try:
            with patch('services.worker.library_api.asyncio.wait',side_effect=deadline):
                result = await self.request()
            self.assertEqual(result[0]['status'],504)
            self.assertTrue(self.factory.call_args.args[1].is_set())
            self.assertEqual((await self.request())[0]['status'],429)
        finally:
            finish.set()
            await asyncio.sleep(.05)

    async def test_deep_json_and_invalid_base64_are_rejected(self):
        raw = b'['*1500+b'0'+b']'*1500
        self.assertEqual((await self.request(raw=raw))[0]['status'],400)
        result = await self.request('/v1/import', {'request_id':ID,'title':'x',
                     'media':'text/plain','content_base64':'%%%invalid'})
        self.assertEqual(result[0]['status'],400)
        self.factory.assert_not_called()
