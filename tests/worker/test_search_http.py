"""Real local HTTP/1.1 exchanges with synthetic responses and no model calls."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
import time
import unittest

from services.worker.search_http import SearchHTTP
from services.worker.service_clients import SessionClient
from services.worker.service_transport import TransportError
from services.worker.source_listing import parameters
from tests.worker.test_search_auth import client, OWNER

AUTH = '/auth/v1/user'
LISTING = '/rest/v1/rpc/list_library_sources'
PREVIEWS = '/rest/v1/rpc/search_published_previews'


@contextmanager
def fixture(*, close=False, status=200, stalled=False):
    entered = threading.Event()
    release = threading.Event()
    calls = []
    ports = set()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'
        disable_nagle_algorithm = True

        def log_message(self, *_):
            pass

        def handle(self):
            try:
                super().handle()
            except ConnectionResetError:
                pass  # Cancellation deliberately terminates the transport.

        def do_GET(self):
            self.do_POST()

        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length', 0)))
            ports.add(self.client_address[1])
            calls.append((self.path, self.headers.get('Authorization')))
            if stalled:
                entered.set()
                release.wait(4)
                return
            if not status:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.close_connection = True
                return
            raw = json.dumps({'id': OWNER} if self.path == AUTH else {}).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            if close:
                self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(raw)
            except OSError:
                pass

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .05}, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{server.server_port}', calls, ports, entered
        finally:
            release.set()
            server.shutdown()
            thread.join(timeout=2)


def session(base, *, reuse, owner=OWNER):
    return SessionClient(base, 'sb_publishable_fixture', client(owner)._headers['Authorization'][7:],
                         _test_loopback=True, reuse_search_http=reuse)


def search_requests(api):
    with api.search_authentication():
        api('GET', AUTH)
        api('GET', AUTH)  # Second auth read is memoized only within this search.
        api('POST', LISTING, parameters())
        api('POST', PREVIEWS, dict(p_text='fixture', p_model='test', p_revision='test',
                                  p_dimensions=512, p_query=[1.]+[0.]*511, p_limit=5))


class SearchHTTPTests(unittest.TestCase):
    def test_same_three_requests_use_one_connection_per_search(self):
        with fixture() as (base, calls, ports, _):
            search_requests(session(base, reuse=False))
            self.assertEqual(len(ports), 3)
            api = session(base, reuse=True)
            search_requests(api)
            self.assertEqual(len(ports), 4)
            search_requests(api)
            self.assertEqual(len(ports), 5)
            search_requests(session(base, reuse=True, owner='00000000-0000-0000-0000-000000000002'))
            self.assertEqual(len(ports), 6)
            self.assertEqual([path for path, _ in calls], [AUTH, LISTING, PREVIEWS]*4)
            self.assertEqual(len({bearer for _, bearer in calls[:9]}), 1)
            self.assertEqual(len({bearer for _, bearer in calls[9:]}), 1)
            self.assertNotEqual(calls[0][1], calls[9][1])

    def test_connection_close_before_next_request_reconnects(self):
        with fixture(close=True) as (base, calls, ports, _):
            search_requests(session(base, reuse=True))
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(ports), 3)

    def test_redirect_or_lost_response_is_never_replayed(self):
        for status in (302, 0):
            with self.subTest(status=status), fixture(status=status) as (base, calls, _, _):
                with self.assertRaisesRegex(TransportError, '^service_unavailable$'):
                    search_requests(session(base, reuse=True))
                self.assertEqual(len(calls), 1)

    def test_cancellation_reaps_child_and_releases_transport_slot(self):
        cancel = threading.Event()
        with fixture(stalled=True) as (base, _, _, entered):
            transport = SearchHTTP(base, {}, cancel, test_loopback=True)

            def stop():
                if entered.wait(3):
                    cancel.set()

            thread = threading.Thread(target=stop, daemon=True)
            thread.start()
            start = time.monotonic()
            try:
                with self.assertRaisesRegex(TransportError, '^cancelled$'):
                    transport.request(AUTH, None)
                self.assertLess(time.monotonic()-start, 3)
                self.assertIsNone(transport.process)
            finally:
                transport.close()
                thread.join(timeout=3)
        with fixture() as (base, _, _, _):
            search_requests(session(base, reuse=True))
