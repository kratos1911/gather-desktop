"""Controlled loopback peers only: no external services, models or real secrets."""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import threading
import time
import unittest
from unittest.mock import patch

from services.inference.runtime import InferenceError, QUERY_TEMPLATE
from services.worker.service_clients import SessionClient, InferenceClient
from services.worker.service_transport import TransportError, request_json, MAX_RESPONSE


def token(role):
    body = json.dumps(dict(role=role, sub='00000000-0000-0000-0000-000000000001')).encode()
    return 'fixture.'+base64.urlsafe_b64encode(body).decode().rstrip('=')+'.unsigned'


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.server.received.append((self.path, dict(self.headers), body))
        status, content_type, data, headers = 200, 'application/json', b'{"ok":true}', {}
        if self.path == '/redirect':
            status, headers = 302, {'Location': self.server.base+'/should-not-follow'}
        elif self.path == '/unauthorized':
            status, data = 401, b'PRIVATE TOKEN document'
        elif self.path == '/rate':
            status = 429
        elif self.path == '/invalid':
            data = b'{"x":NaN}'
        elif self.path == '/duplicate':
            data = b'{"x":1,"x":2}'
        elif self.path == '/html':
            content_type = 'text/html'
        elif self.path == '/compressed':
            headers['Content-Encoding'] = 'gzip'
        elif self.path == '/large':
            data = b' ' * (MAX_RESPONSE+1)
        elif self.path == '/slow':
            time.sleep(1)
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (OSError, ConnectionError):
            pass


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.server.received = []

    def request(self, path, **kwargs):
        return request_json(self.server.base, path, {}, None, timeout=kwargs.pop('timeout', 3), **kwargs)

    def session(self, **kwargs):
        return SessionClient(self.server.base, token('anon'), token('authenticated'),
                             _test_loopback=True, **kwargs)

    def test_session_routes_and_credentials(self):
        client = self.session()
        self.assertEqual(client('GET', '/auth/v1/user'), {'ok': True})
        client('POST', '/rest/v1/rpc/open_published_text', {'p_source':'source', 'p_version':'version'})
        path, headers, body = self.server.received[-1]
        self.assertEqual(json.loads(body), {'p_source':'source', 'p_version':'version'})
        self.assertEqual(headers['Authorization'], 'Bearer '+token('authenticated'))
        self.assertEqual(headers['Apikey'], token('anon'))
        self.assertEqual(headers['Accept-Encoding'], 'identity')

    def test_configuration_rejects_unsafe_origins_and_privileged_tokens(self):
        for base in ('http://example.com', 'https://user:pass@example.com', 'https://example.com/path',
                     'https://example.com?token=x', 'https://example.com/#x', 'https://exa mple.com'):
            with self.assertRaises(TransportError):
                SessionClient(base, token('anon'), token('authenticated'))
        for public, user in ((token('service_role'), token('authenticated')),
                             (token('anon'),token('service_role')), ('sb_secret_bad',token('authenticated')),
                             (token('anon'),'bad\r\nheader')):
            with self.assertRaises(TransportError):
                SessionClient('https://example.invalid', public, user)
        with self.assertRaises(TransportError):
            SessionClient('http://localhost:9999', token('anon'),token('authenticated'), _test_loopback=True)

    def test_wrong_methods_routes_and_owner_fields_never_leave_process(self):
        client = self.session()
        for method, path, payload in (('POST','/auth/v1/user',{}),('GET','https://other.test',None),
                ('POST','/rest/v1/rpc/submit_text',{}),
                ('POST','/rest/v1/rpc/open_published_text',dict(p_source='x',p_version='y',owner='x'))):
            with self.assertRaises(TransportError):
                client(method,path,payload)
        self.assertEqual(self.server.received, [])

    def test_redirect_is_not_followed(self):
        with self.assertRaisesRegex(TransportError, '^service_unavailable$'):
            self.request('/redirect')
        self.assertEqual([r[0] for r in self.server.received], ['/redirect'])

    def test_http_failures_are_safe_and_not_retried(self):
        for path, code in (('/unauthorized','authentication_failed'),('/rate','rate_limited')):
            with self.assertRaisesRegex(TransportError, '^'+code+'$'):
                self.request(path)
        self.assertEqual(len(self.server.received), 2)

    def test_response_shape_encoding_size_and_json(self):
        for path in ('/invalid','/duplicate','/html','/compressed'):
            with self.subTest(path=path), self.assertRaisesRegex(TransportError, '^invalid_response$'):
                self.request(path)
        with self.assertRaisesRegex(TransportError, '^response_too_large$'):
            self.request('/large')

    def test_request_bounds_before_network(self):
        for payload in ({'text':'x'*65536}, {'vector':[float('nan')]}):
            with self.assertRaisesRegex(TransportError, '^invalid_request$'):
                request_json(self.server.base,'/embed',{},payload,timeout=3)
        self.assertEqual(self.server.received, [])

    def test_whole_request_deadline_and_slot_recovery(self):
        start = time.monotonic()
        children = []
        spawn = subprocess.Popen
        def record(*args, **kwargs):
            child = spawn(*args, **kwargs)
            children.append(child)
            self.assertNotIn('Authorization', str(args))
            self.assertLessEqual(set(kwargs['env']), {'SYSTEMROOT','WINDIR'})
            return child
        with patch('services.worker.service_transport.subprocess.Popen', side_effect=record):
            with self.assertRaisesRegex(TransportError, '^timeout$'):
                self.request('/slow', timeout=.3)
        self.assertIsNotNone(children[0].poll())
        self.assertTrue(children[0].stdin.closed and children[0].stdout.closed)
        self.assertLess(time.monotonic()-start, 2.5)
        self.assertEqual(self.request('/ok'), {'ok':True})

    def test_cancellation_and_busy(self):
        cancel = threading.Event()
        timer = threading.Timer(.2, cancel.set)
        timer.start()
        try:
            with self.assertRaisesRegex(TransportError, '^cancelled$'):
                self.request('/slow',cancel=cancel)
        finally:
            timer.cancel()
        with self.assertRaisesRegex(TransportError, '^cancelled$'):
            self.request('/ok',cancel=cancel)
        from services.worker.service_transport import _SLOT
        with _SLOT:
            with self.assertRaisesRegex(TransportError, '^busy$'):
                self.request('/ok')
        self.assertEqual(self.request('/ok'), {'ok':True})

    def test_inference_preserves_raw_request_and_preflights_template(self):
        counted = []
        client = InferenceClient(self.server.base, 'fixture-secret',
            lambda text: counted.append(text) or 30, _test_loopback=True)
        request = {'role':'query','texts':['hello']}
        client.infer(request,cancel=threading.Event())
        self.assertEqual(counted, [QUERY_TEMPLATE.format(text='hello')])
        self.assertEqual(json.loads(self.server.received[0][2]), request)
        self.assertEqual(self.server.received[0][0], '/embed')
        client.count_tokens = lambda text: 2049
        with self.assertRaisesRegex(InferenceError, '^token_limit$'):
            client.infer(request,cancel=threading.Event())
        self.assertEqual(len(self.server.received), 1)

    def test_inference_timeout_maps_to_existing_error(self):
        client = InferenceClient('https://example.invalid', 'fixture', lambda text: 1)
        with patch('services.worker.service_clients.request_json', side_effect=TransportError('timeout')):
            with self.assertRaisesRegex(InferenceError, '^deadline_exceeded$'):
                client.infer({'role':'query','texts':['hello']},cancel=threading.Event())


if __name__ == '__main__':
    unittest.main()
