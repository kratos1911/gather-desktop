"""Real Uvicorn HTTP and Runtime process, synthetic engine only."""
import http.client
import json
import signal
import socket
import threading
import time
import unittest
from unittest.mock import patch

from services.inference.asgi import create_app, create_server, LocalBearer
from services.inference.runtime import Runtime, InferenceError
from services.worker.service_clients import InferenceClient

SECRET = 'synthetic-asgi-service-secret-32-characters'


class Engine:
    def __init__(self, mode):
        if mode == 'startup_hang':
            time.sleep(30)
        self.mode = mode

    def count_tokens(self, text):
        return 3000 if 'oversized' in text else 10

    def embed(self, text):
        if 'hang' in text:
            time.sleep(30)
        if 'slow' in text:
            time.sleep(.3)
        return [1.]*512


class ASGITests(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime(Engine, request_timeout=.8)
        self.app = create_app(self.runtime,LocalBearer(SECRET))
        self.server = create_server(self.app,port=0)
        self.thread = threading.Thread(target=self.server.run,daemon=True)
        self.thread.start()
        deadline = time.monotonic()+8
        while not self.server.started and self.thread.is_alive() and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertTrue(self.server.started)
        self.port = self.server.servers[0].sockets[0].getsockname()[1]

    def tearDown(self):
        self.app.state.stopping.set()
        self.server.should_exit = True
        self.thread.join(8)
        self.assertFalse(self.thread.is_alive())
        self.assertIsNone(self.runtime.pid)

    def request(self, text='fixture', *, path='/embed', token=SECRET, raw=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port,timeout=4)
        try:
            conn.request('GET' if path=='/ready' else 'POST',path,
                None if path=='/ready' else raw if raw is not None else json.dumps({'role':'query','texts':[text]}),
                {'Authorization':'Bearer '+token,'Content-Type':'application/json'})
            result = conn.getresponse()
            return result.status,json.loads(result.read())
        finally:
            conn.close()

    def test_readiness_existing_client_and_one_child(self):
        pid = self.runtime.pid
        self.assertEqual(self.request(path='/ready'),(200,{'ready':True}))
        client = InferenceClient(f'http://127.0.0.1:{self.port}',SECRET,lambda t:10,_test_loopback=True)
        result = client.infer({'role':'query','texts':['fixture']},cancel=threading.Event())
        self.assertEqual(len(result['data'][0]['embedding']),512)
        self.assertEqual(self.runtime.pid,pid)

    def test_auth_input_token_and_disabled_docs(self):
        self.assertEqual(self.request(token='wrong')[0],401)
        for raw in ('{}','{"role":"query","role":"query","texts":["x"]}','x'*65537):
            self.assertEqual(self.request(raw=raw)[0],400)
        self.assertEqual(self.request('oversized')[0],400)
        self.assertEqual(self.request(path='/docs')[0],404)
        with self.assertRaisesRegex(ValueError,'cloud_identity_not_configured'):
            create_server(self.app,host='0.0.0.0')
        with patch('services.inference.asgi.version',return_value='0.14.0'):
            with self.assertRaisesRegex(ValueError,'unverified_server_dependencies'):
                create_server(self.app)

    def test_busy_and_health_stays_responsive(self):
        entered = threading.Event()
        original = self.runtime.infer
        def observed(*args,**kwargs):
            entered.set()
            return original(*args,**kwargs)
        with patch.object(self.runtime,'infer',side_effect=observed):
            results=[]
            thread=threading.Thread(target=lambda:results.append(self.request('slow')))
            thread.start()
            self.assertTrue(entered.wait(2))
            self.assertEqual(self.request()[0],429)
            self.assertEqual(self.request(path='/ready')[0],200)
            thread.join(3)
            self.assertEqual(results[0][0],200)

    def test_deadline_unready_and_no_auto_restart(self):
        self.assertEqual(self.request('hang')[0],504)
        self.assertIsNone(self.runtime.pid)
        self.assertEqual(self.request(path='/ready'),(503,{'ready':False}))
        self.assertEqual(self.request()[0],503)

    def test_shutdown_signal_cancels_active_work(self):
        entered=threading.Event()
        original=self.runtime.infer
        def observed(*args,**kwargs):
            entered.set()
            return original(*args,**kwargs)
        with patch.object(self.runtime,'infer',side_effect=observed):
            results=[]
            thread=threading.Thread(target=lambda:results.append(self.request('hang')))
            thread.start()
            self.assertTrue(entered.wait(2))
            self.server.handle_exit(signal.SIGTERM,None)
            thread.join(5)
            self.server.should_exit=True
            self.thread.join(5)
            self.assertFalse(self.thread.is_alive())
            self.assertIsNone(self.runtime.pid)
            self.assertEqual(results[0][0],503)

    def test_slow_headers_closed_and_header_limit(self):
        with patch('services.inference.asgi.READ_SECONDS',.2):
            with socket.create_connection(('127.0.0.1',self.port),timeout=2) as peer:
                peer.sendall(b'POST /embed HTTP/1.1\r\n')
                self.assertEqual(peer.recv(1),b'')
        with socket.create_connection(('127.0.0.1',self.port),timeout=2) as peer:
            peer.sendall(b'POST /embed HTTP/1.1\r\nX: '+b'x'*16384+b'\r\n\r\n')
            try:
                self.assertEqual(peer.recv(1),b'')
            except ConnectionResetError:
                pass
        self.assertEqual(self.request()[0],200)

    def test_slow_body_total_deadline(self):
        with patch('services.inference.asgi.READ_SECONDS',.2):
            with socket.create_connection(('127.0.0.1',self.port),timeout=2) as peer:
                peer.sendall(('POST /embed HTTP/1.1\r\nHost: localhost\r\nAuthorization: Bearer '+SECRET+
                    '\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{').encode())
                self.assertEqual(peer.recv(1),b'')
        self.assertEqual(self.request()[0],200)

    def test_startup_can_be_cancelled(self):
        runtime=Runtime(Engine,'startup_hang')
        cancel=threading.Event()
        cancel.set()
        with self.assertRaisesRegex(InferenceError,'cancelled'):
            runtime.start(cancel=cancel)
        self.assertIsNone(runtime.pid)


if __name__=='__main__':
    unittest.main()
