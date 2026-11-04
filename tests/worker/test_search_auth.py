"""Synthetic Auth/REST replies: count real adapter calls, not live JWT/RLS proof."""
import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import Mock, patch

from scripts.operator_library import PilotSession, PILOT_USERS, QUERY
from services.worker.library_session import LibraryError
from services.worker.service_clients import SessionClient
from services.worker.service_transport import TransportError
from tests.worker.test_search import Session, Provider, OWNER


def client(owner=OWNER, cancel=None):
    body=base64.urlsafe_b64encode(json.dumps({'role':'authenticated','sub':owner}).encode()).decode().rstrip('=')
    return SessionClient('https://auth-fixture.example','sb_publishable_fixture',
                         'fixture.'+body+'.unsigned',cancel=cancel)


class SearchAuthenticationTests(unittest.TestCase):
    def test_loopback_counts_one_real_http_auth_request_per_scope(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):
                self.server.auth_calls+=1
                raw=json.dumps({'id':OWNER}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.auth_calls=0
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            api=SessionClient(f'http://127.0.0.1:{server.server_port}','sb_publishable_fixture',
                              client()._headers['Authorization'][7:],_test_loopback=True)
            for expected in (1,2):
                with api.search_authentication():
                    self.assertEqual(api('GET','/auth/v1/user')['id'],OWNER)
                    self.assertEqual(api('GET','/auth/v1/user')['id'],OWNER)
                self.assertEqual(server.auth_calls,expected)
        finally:
            server.shutdown();server.server_close();worker.join(timeout=2)

    def test_duplicate_auth_is_shared_only_inside_one_scope(self):
        api=client()
        with patch('services.worker.service_clients.request_json',return_value={'id':OWNER,'email':'private'}) as send:
            with api.search_authentication():
                first=api('GET','/auth/v1/user')
                first['id']='changed locally'
                second=api('GET','/auth/v1/user')
                self.assertEqual(second,{'id':OWNER})
                second['id']='also changed locally'
                self.assertEqual(api('GET','/auth/v1/user'),{'id':OWNER})
                self.assertEqual(send.call_count,1)
            api('GET','/auth/v1/user')
            self.assertEqual(send.call_count,2)

    def test_exception_clears_identity_and_next_scope_reauthenticates(self):
        api=client()
        with patch('services.worker.service_clients.request_json',return_value={'id':OWNER}) as send:
            with self.assertRaises(RuntimeError):
                with api.search_authentication():
                    api('GET','/auth/v1/user')
                    raise RuntimeError('stop')
            send.side_effect=TransportError('authentication_failed')
            with self.assertRaises(TransportError):
                with api.search_authentication():api('GET','/auth/v1/user')
            self.assertEqual(send.call_count,2)

    def test_other_rpc_reads_are_never_cached(self):
        api=client()
        with patch('services.worker.service_clients.request_json',side_effect=[{'id':OWNER},['current'],[]]) as send:
            with api.search_authentication():
                api('GET','/auth/v1/user')
                args={'p_source':OWNER,'p_version':OWNER}
                self.assertEqual(api('POST','/rest/v1/rpc/open_published_text',args),['current'])
                self.assertEqual(api('POST','/rest/v1/rpc/open_published_text',args),[])
            self.assertEqual(send.call_count,3)

    def test_header_or_origin_mutation_cannot_reuse_verified_identity(self):
        for field in ('_headers','_base'):
            api=client()
            with patch('services.worker.service_clients.request_json',return_value={'id':OWNER}) as send:
                with api.search_authentication():
                    api('GET','/auth/v1/user')
                    if field=='_headers':api._headers=dict(api._headers,Authorization='Bearer another')
                    else:api._base='https://another.example'
                    with self.assertRaisesRegex(TransportError,'^invalid_configuration$'):
                        api('GET','/auth/v1/user')
                self.assertEqual(send.call_count,1)

    def test_cancellation_prevents_cached_auth_and_scope_still_clears(self):
        cancel=threading.Event();api=client(cancel=cancel)
        with patch('services.worker.service_clients.request_json',return_value={'id':OWNER}) as send:
            with api.search_authentication():
                api('GET','/auth/v1/user');cancel.set()
                with self.assertRaisesRegex(TransportError,'^cancelled$'):api('GET','/auth/v1/user')
            cancel.clear();api('GET','/auth/v1/user')
            self.assertEqual(send.call_count,2)

    def test_nested_or_cross_thread_use_cannot_borrow_identity(self):
        api=client();failures=[]
        def other():
            try:api('GET','/auth/v1/user')
            except TransportError as error:failures.append(str(error))
        with patch('services.worker.service_clients.request_json',return_value={'id':OWNER}) as send:
            with api.search_authentication():
                api('GET','/auth/v1/user')
                with self.assertRaisesRegex(TransportError,'^busy$'):
                    with api.search_authentication():pass
                worker=threading.Thread(target=other);worker.start();worker.join(timeout=1)
                self.assertFalse(worker.is_alive());self.assertEqual(failures,['busy'])
                self.assertEqual(send.call_count,1)

    def test_malformed_auth_response_is_never_memoized(self):
        for result in ({'id':'bad'}, {'id':None},[],{}):
            api=client()
            with patch('services.worker.service_clients.request_json',return_value=result) as send:
                with api.search_authentication():
                    api('GET','/auth/v1/user');api('GET','/auth/v1/user')
                self.assertEqual(send.call_count,2)

    def test_pilot_search_with_cached_vector_has_one_auth_per_request(self):
        owner=sorted(PILOT_USERS)[0];api=client(owner);data=Session();provider=Provider()
        cached=Mock();cached.get.return_value=[1.]+[0.]*511
        denied=False
        def remote(base,path,headers,payload,**options):
            if path=='/auth/v1/user':
                if denied:raise TransportError('authentication_failed')
                return {'id':owner}
            return data('POST',path,payload)
        library=PilotSession(api,Mock(),provider,text_files=True,query_cache=cached)
        with patch('services.worker.service_clients.request_json',side_effect=remote) as send:
            for count in (1,2):
                self.assertEqual(len(library.search('query')['windows']),1)
                self.assertEqual(sum(c.args[1]=='/auth/v1/user' for c in send.call_args_list),count)
            self.assertEqual(cached.get.call_count,2)
            denied=True
            with self.assertRaisesRegex(LibraryError,'^session_unavailable$'):library.search('query')
            self.assertEqual(cached.get.call_count,2)
            self.assertEqual(sum(c.args[1]=='/auth/v1/user' for c in send.call_args_list),3)
        self.assertFalse(provider.calls)

    def test_private_user_and_fixture_guards_still_run_before_model_or_reads(self):
        for owner,query,code in [(OWNER,QUERY,'session_unavailable'),
                                  (sorted(PILOT_USERS)[0],'arbitrary','pilot_fixture_only')]:
            api=client(owner);provider=Provider();cache=Mock()
            library=PilotSession(api,Mock(),provider,query_cache=cache)
            with patch('services.worker.service_clients.request_json',return_value={'id':owner}) as send:
                with self.assertRaisesRegex(LibraryError,'^'+code+'$'):library.search(query)
                self.assertEqual(send.call_count,1)
                self.assertEqual(send.call_args.args[1],'/auth/v1/user')
            self.assertFalse(provider.calls);cache.get.assert_not_called()


if __name__=='__main__':unittest.main()
