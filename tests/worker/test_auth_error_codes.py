import io
import unittest
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError
from unittest.mock import Mock

from services.worker.service_transport import auth_error_code, request_json, TransportError

URL = 'https://project.supabase.co/auth/v1/token?grant_type=password'


class AuthErrorTests(unittest.TestCase):
    def test_actual_http_helper_passes_only_safe_auth_code(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                raw = b'{"error_code":"invalid_credentials","msg":"private error fixture"}'
                self.send_response(400)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        server = HTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            base = 'http://127.0.0.1:'+str(server.server_port)
            with self.assertRaisesRegex(TransportError,'^auth_invalid_credentials$'):
                request_json(base,'/auth/v1/token?grant_type=password',{},
                             {'email':'fixture@example.invalid','password':'synthetic'},timeout=3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)

    def error(self,raw,status=400):
        return HTTPError(URL,status,'fixture',{'Content-Type':'application/json'},io.BytesIO(raw))

    def test_only_allowlisted_codes_escape_not_description_or_credentials(self):
        raw = b'{"error_code":"invalid_credentials","msg":"private password user details"}'
        self.assertEqual(auth_error_code(URL,self.error(raw)),b'auth_invalid_credentials')
        self.assertEqual(auth_error_code(URL,self.error(b'{"code":"email_not_confirmed"}')),
                         b'auth_email_not_confirmed')
        self.assertIsNone(auth_error_code(URL,self.error(b'{"error_code":"private-secret"}')))

    def test_non_auth_endpoints_do_not_read_error_body(self):
        error = self.error(b'private body')
        error.read = Mock(side_effect=AssertionError('must not read'))
        self.assertIsNone(auth_error_code('https://project.supabase.co/rest/v1/rpc/private',error))
        error.read.assert_not_called()

    def test_malformed_oversized_and_duplicate_errors_are_not_exposed(self):
        for raw in (b'private',b'x'*4097,b'[]',b'{"error_code":"invalid_credentials","error_code":"email_not_confirmed"}'):
            with self.subTest(raw_length=len(raw)):
                self.assertIsNone(auth_error_code(URL,self.error(raw)))

    def test_error_read_is_bounded(self):
        error = self.error(b'')
        error.read = Mock(return_value=b'{"error_code":"invalid_credentials"}')
        auth_error_code(URL,error)
        error.read.assert_called_once_with(4097)


if __name__=='__main__':
    unittest.main()
