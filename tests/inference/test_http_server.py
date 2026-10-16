"""Local HTTP integration with a synthetic process engine, never real weights."""
import http.client
import json
import socket
import threading
import time
import unittest
from unittest.mock import patch

from services.inference.http_server import InferenceServer
from services.inference.runtime import Runtime, MODEL, REVISION, DIMENSIONS
from services.worker.service_clients import InferenceClient

SECRET = 'synthetic-test-credential-32-characters'


class Engine:
    def __init__(self, mode):
        self.mode = mode

    def count_tokens(self, text):
        return 3000 if 'oversized' in text else 10

    def embed(self, text):
        if self.mode == 'hang':
            time.sleep(20)
        return [1.]*512


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime(Engine, request_timeout=.5)
        self.runtime.start()
        self.server = InferenceServer(self.runtime, SECRET)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.runtime.close()

    def request(self, body=None, *, token=SECRET, path='/embed', headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=4)
        payload = json.dumps({'role':'query','texts':['fixture']}) if body is None else body
        values = {'Authorization':'Bearer '+token, 'Content-Type':'application/json'}
        values.update(headers or {})
        try:
            conn.request('POST',path,payload,values)
            result = conn.getresponse()
            return result.status, json.loads(result.read())
        finally:
            conn.close()

    def test_existing_inference_client_round_trip(self):
        client = InferenceClient(f'http://127.0.0.1:{self.port}', SECRET, lambda text:10,
                                 _test_loopback=True)
        result = client.infer({'role':'query','texts':['fixture']}, cancel=threading.Event())
        self.assertEqual((result['model'],result['revision'],result['dimensions']), (MODEL,REVISION,DIMENSIONS))
        self.assertEqual(len(result['data'][0]['embedding']),512)
        self.assertTrue(self.runtime.ready)

    def test_authentication_precedes_model_and_body(self):
        with patch.object(self.runtime,'infer', side_effect=AssertionError('must not run')):
            self.assertEqual(self.request('not json',token='wrong')[0],401)
            self.assertEqual(self.request(path='/other')[0],404)
        conn = http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
        try:
            conn.putrequest('POST','/embed')
            conn.putheader('Authorization','Bearer wrong')
            conn.putheader('Content-Length','100')
            conn.endheaders()  # No body sent; authentication must reject immediately.
            self.assertEqual(conn.getresponse().status,401)
        finally:
            conn.close()

    def test_invalid_json_contract_and_framing(self):
        for body in ('{}','{"role":"query","role":"document","texts":["x"]}',
                     '{"role":"query","texts":[NaN]}', 'not json'):
            self.assertEqual(self.request(body)[0],400)
        self.assertEqual(self.request(headers={'Transfer-Encoding':'chunked'})[0],400)
        self.assertEqual(self.request(headers={'Content-Encoding':'gzip'})[0],400)
        self.assertEqual(self.request(' '*65537)[0],400)
        self.assertEqual(self.request()[0],200)

    def test_server_token_limit_even_if_client_bypassed(self):
        self.assertEqual(self.request(json.dumps({'role':'document','texts':['oversized']})),
                         (400,{'error':'token_limit'}))
        self.assertTrue(self.runtime.ready)

    def test_hung_model_is_reaped_and_requires_explicit_restart(self):
        self.runtime.close()
        self.runtime.configuration = 'hang'
        self.runtime.start()
        self.assertEqual(self.request(),(504,{'error':'deadline_exceeded'}))
        self.assertIsNone(self.runtime.pid)
        self.assertEqual(self.request(),(503,{'error':'model_unavailable'}))

    def test_model_busy_is_not_queued(self):
        self.runtime._lock.acquire()
        try:
            self.assertEqual(self.request(),(429,{'error':'busy'}))
        finally:
            self.runtime._lock.release()

    def test_client_disconnect_does_not_remove_server_compute_deadline(self):
        self.runtime.close()
        self.runtime.configuration = 'hang'
        self.runtime.start()
        started = threading.Event()
        original = self.runtime.infer
        def observed(request):
            started.set()
            return original(request)
        with patch.object(self.runtime, 'infer', side_effect=observed):
            peer = socket.create_connection(('127.0.0.1',self.port),timeout=2)
            body = b'{"role":"query","texts":["fixture"]}'
            peer.sendall(('POST /embed HTTP/1.0\r\nAuthorization: Bearer '+SECRET+
                '\r\nContent-Type: application/json\r\nContent-Length: '+str(len(body))+
                '\r\n\r\n').encode()+body)
            self.assertTrue(started.wait(2))
            peer.close()
            deadline = time.monotonic()+3
            while self.runtime.pid is not None and time.monotonic()<deadline:
                time.sleep(.02)
            self.assertIsNone(self.runtime.pid)
            self.assertFalse(self.runtime.ready)

    def test_slow_headers_are_closed_by_total_read_deadline(self):
        with patch('services.inference.http_server.READ_DEADLINE',.2):
            with socket.create_connection(('127.0.0.1',self.port),timeout=2) as peer:
                peer.sendall(b'POST /embed HTTP/1.0\r\n')
                time.sleep(.35)
                self.assertEqual(peer.recv(1),b'')
        self.assertTrue(self.runtime.ready)
        self.assertEqual(self.request()[0],200)

    def test_header_budget_and_duplicate_authorization(self):
        with socket.create_connection(('127.0.0.1',self.port),timeout=2) as peer:
            peer.sendall(b'POST /embed HTTP/1.0\r\nX: '+b'x'*16384+b'\r\n\r\n')
            try:
                self.assertEqual(peer.recv(1),b'')
            except ConnectionResetError:
                pass
        conn = http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
        try:
            conn.putrequest('POST','/embed')
            conn.putheader('Authorization','Bearer '+SECRET)
            conn.putheader('Authorization','Bearer '+SECRET)
            conn.endheaders()
            self.assertEqual(conn.getresponse().status,401)
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
