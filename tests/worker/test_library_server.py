"""Actual loopback HTTP; simulated Auth/database/vectors, no cloud calls."""
import base64
import http.client
import json
import socket
import threading
import time
import unittest
from unittest.mock import Mock, patch

from services.worker.library_api import LibraryAPI
from services.worker.library_server import create_server
from services.worker.library_session import LibrarySession
from services.worker.service_clients import SessionClient
from tests.worker.test_search import Session, Provider, OWNER


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.data, self.provider = Session(), Provider()
        self.sid = next(iter(self.data.docs))
        self.vid = self.data.docs[self.sid][0]['version_id']
        self.calls = []
        self.deleted = False
        self.repo = Mock()
        self.repo.call.return_value = {'source_id': self.sid, 'version_id': self.vid,
                                      'job_id': OWNER, 'state':'queued'}
        def factory(token, cancel):
            api = Mock(spec=SessionClient)
            def request(method, path, payload=None):
                self.calls.append((token,path))
                if path == '/auth/v1/user':
                    if token not in ('test-a','test-b'):
                        raise ValueError('secret token')
                    return {'id':OWNER}
                if token == 'test-b' or self.deleted:
                    return []
                if path.endswith('source_processing_status'):
                    return [{'state':'ready'}]
                if path.endswith('request_source_deletion'):
                    self.deleted = True
                    return True
                return self.data(method,path,payload)
            api.side_effect = request
            return LibrarySession(api,lambda owner: self.repo,self.provider)
        self.app = LibraryAPI(factory)
        self.server = create_server(self.app,port=0)
        self.thread = threading.Thread(target=self.server.run,daemon=True)
        self.thread.start()
        end = time.monotonic()+5
        while not self.server.started and self.thread.is_alive() and time.monotonic()<end:
            time.sleep(.01)
        self.assertTrue(self.server.started)
        self.port = self.server.servers[0].sockets[0].getsockname()[1]

    def tearDown(self):
        self.app.stop()
        self.server.should_exit = True
        self.thread.join(8)
        self.assertFalse(self.thread.is_alive())

    def request(self,path,value,*,token='test-a',headers=None):
        connection = http.client.HTTPConnection('127.0.0.1',self.port,timeout=4)
        try:
            connection.request('POST',path,json.dumps(value),headers or {
                'Authorization':'Bearer '+token,'Content-Type':'application/json'})
            response = connection.getresponse()
            return response.status,json.loads(response.read())
        finally:
            connection.close()

    def test_five_routes_preserve_bytes_citations_and_hide_deleted_source(self):
        raw = '\ufeffA synthetic note\r\nwith unicode 🌟'.encode()
        submission = {'request_id':OWNER,'title':'Synthetic','media':'text/markdown',
                      'content_base64':base64.b64encode(raw).decode()}
        first = self.request('/v1/import',submission)
        self.assertEqual(first[0],202)
        self.assertEqual(first,self.request('/v1/import',submission))
        self.assertEqual(self.repo.call.call_args.args[3],raw)
        self.assertEqual(self.request('/v1/status',{'source_id':self.sid})[1][0]['state'],'ready')
        status,result = self.request('/v1/search',{'query':'stars'})
        self.assertEqual(status,200)
        self.assertEqual(result['windows'][0]['text'],self.data.docs[self.sid][0]['body'])
        self.assertEqual(self.request('/v1/open',{'source_id':self.sid,'version_id':self.vid})[1],self.data.docs[self.sid])
        self.assertEqual(self.request('/v1/open',{'source_id':self.sid,'version_id':self.vid},token='test-b')[1],[])
        self.assertEqual(self.request('/v1/delete',{'source_id':self.sid})[1],True)
        self.assertEqual(self.request('/v1/search',{'query':'stars'})[1]['windows'],[])

    def test_auth_rejected_before_admission_and_input_errors_are_safe(self):
        self.assertEqual(self.request('/v1/status',{'source_id':self.sid},token='forged')[0],401)
        self.assertEqual(self.request('/v1/import',{'user_id':OWNER})[0],400)
        self.repo.call.assert_not_called()
        self.assertEqual(self.provider.calls,[])

    def test_origin_host_public_bind_and_dependency_guards(self):
        for headers in ({'Origin':'https://evil.invalid'}, {'Host':'evil.invalid'}):
            self.assertEqual(self.request('/v1/status',{'source_id':self.sid},headers=headers)[0],403)
        self.assertEqual(self.calls,[])
        with self.assertRaisesRegex(ValueError,'loopback_library_only'):
            create_server(self.app,host='0.0.0.0')
        with patch('services.worker.library_server.version',return_value='old'):
            with self.assertRaisesRegex(ValueError,'unverified_server_dependencies'):
                create_server(self.app)

    def test_explicit_operator_origin_preflight_is_narrow(self):
        self.app.operator_origin = 'http://localhost:1420'
        for origin,method,headers,status in (
            ('http://localhost:1420','POST','authorization, content-type',204),
            ('https://evil.invalid','POST','authorization',403),
            ('http://localhost:1420','GET','authorization',403),
            ('http://localhost:1420','POST','x-owner-id',403)):
            conn = http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
            try:
                conn.request('OPTIONS','/v1/status',headers={'Origin':origin,
                    'Access-Control-Request-Method':method,'Access-Control-Request-Headers':headers})
                response = conn.getresponse()
                self.assertEqual(response.status,status)
                if status == 204:
                    self.assertEqual(response.getheader('Access-Control-Allow-Origin'),origin)
                    self.assertIsNone(response.getheader('Access-Control-Allow-Credentials'))
                response.read()
            finally: conn.close()
        self.assertEqual(self.calls,[])
        headers = {'Origin':'http://localhost:1420','Authorization':'Bearer test-a','Content-Type':'application/json'}
        self.assertEqual(self.request('/v1/status',{'source_id':self.sid},headers=headers)[0],200)

    def test_slow_headers_close_and_oversized_headers_do_no_work(self):
        for fragment in (b'POST /v1/import HTTP/1.1\r\nX: '+b'a'*17000, b'POST /v1/status HTTP/1.1\r\n'):
            peer = socket.create_connection(('127.0.0.1',self.port),timeout=7)
            try:
                peer.sendall(fragment)
                self.assertEqual(peer.recv(1024),b'')
            finally:
                peer.close()
        self.assertEqual(self.calls,[])

    def test_shutdown_cancels_active_request_and_rejects_new_work(self):
        entered = threading.Event()
        original = self.app.factory
        def factory(token,cancel):
            session = original(token,cancel)
            def status(source_id):
                entered.set()
                cancel.wait(3)
                return []
            session.status = status
            return session
        self.app.factory = factory
        responses = []
        caller = threading.Thread(target=lambda:responses.append(self.request('/v1/status',{'source_id':self.sid})))
        caller.start()
        self.assertTrue(entered.wait(2))
        self.server.servers[0].get_loop().call_soon_threadsafe(self.app.stop)
        caller.join(3)
        self.assertFalse(caller.is_alive())
        self.assertEqual(self.request('/v1/status',{'source_id':self.sid})[0],503)
