import socket
import socketserver
import ssl
import threading
import time
import unittest
from unittest.mock import Mock, patch

from services.worker.network_policy import Destination
from services.worker.restricted_fetch import FetchError, MAX_BODY, connect, fetch_page


class LocalPeer:
    """Trusted test connector maps approved public addresses to a loopback fixture.

    Production policy is not relaxed. No public DNS or website is contacted.
    """
    def __init__(self, responses):
        self.requests = []
        self.destinations = []
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                request = bytearray()
                while line := self.rfile.readline(8192):
                    request.extend(line)
                    if line == b'\r\n':
                        break
                owner.requests.append(bytes(request))
                index = len(owner.requests) - 1
                self.wfile.write(responses[min(index, len(responses) - 1)])

        self.server = socketserver.ThreadingTCPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01})

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def dial(self, destination, timeout):
        self.destinations.append(destination)
        return socket.create_connection(self.server.server_address, timeout)


def page(body=b'fixture', headers=b''):
    return b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n' + headers + b'Connection: close\r\n\r\n' + body


class FetchTests(unittest.TestCase):
    def fetch(self, peer, url='http://public.example/page', resolver=None):
        return fetch_page(url, resolver=resolver or (lambda *_: ['8.8.8.8']), connector=peer.dial)

    def test_real_http_preserves_host_without_cookies_proxy_or_assets(self):
        body = b'<img src="http://169.254.169.254/latest"><script>fetch("/other")</script>'
        with LocalPeer([page(body)]) as peer, patch.dict('os.environ', {'HTTP_PROXY': 'http://127.0.0.1:1'}):
            result = self.fetch(peer, 'http://public.example/page?q=hello#fragment')
            self.assertEqual(result.body, body)
            self.assertEqual(len(peer.requests), 1)
            request = peer.requests[0]
            self.assertIn(b'Host: public.example\r\n', request)
            self.assertIn(b'GET /page?q=hello HTTP/1.1', request)
            self.assertNotIn(b'fragment', request)
            self.assertNotIn(b'Cookie:', request)
            self.assertEqual(peer.destinations[0].addresses, ('8.8.8.8',))

    def test_private_and_mixed_dns_are_blocked_before_dial(self):
        for values in [['127.0.0.1'], ['169.254.169.254'], ['8.8.8.8', '10.0.0.1']]:
            dial = Mock()
            with self.subTest(values=values), self.assertRaises(FetchError):
                fetch_page('http://public.example', resolver=lambda *_: values, connector=dial)
            dial.assert_not_called()

    def test_relative_redirect_rechecks_dns_and_does_not_forward_cookie(self):
        redirect = b'HTTP/1.1 302 Found\r\nLocation: /next\r\nSet-Cookie: secret=yes\r\n\r\n'
        resolver = Mock(return_value=['8.8.8.8'])
        with LocalPeer([redirect, page()]) as peer:
            result = self.fetch(peer, resolver=resolver)
            self.assertEqual(result.redirects, 1)
            self.assertEqual(result.final_url, 'http://public.example/next')
            self.assertEqual(resolver.call_count, 2)
            self.assertNotIn(b'Cookie:', peer.requests[1])

    def test_rebinding_on_redirect_never_connects_to_second_address(self):
        redirect = b'HTTP/1.1 302 Found\r\nLocation: /next\r\n\r\n'
        resolver = Mock(side_effect=[['8.8.8.8'], ['127.0.0.1']])
        with LocalPeer([redirect]) as peer, self.assertRaises(FetchError):
            self.fetch(peer, resolver=resolver)
        self.assertEqual(len(peer.destinations), 1)

    def test_redirect_to_metadata_is_blocked(self):
        with LocalPeer([b'HTTP/1.1 302 Found\r\nLocation: http://169.254.169.254/latest\r\n\r\n']) as peer:
            with self.assertRaises(FetchError):
                self.fetch(peer)
            self.assertEqual(len(peer.requests), 1)

    def test_redirect_limit_and_https_downgrade(self):
        redirect = b'HTTP/1.1 302 Found\r\nLocation: /again\r\n\r\n'
        with LocalPeer([redirect]) as peer:
            with self.assertRaisesRegex(FetchError, 'REDIRECT_DENIED'):
                self.fetch(peer)
            self.assertEqual(len(peer.requests), 4)
        with LocalPeer([b'HTTP/1.1 302 Found\r\nLocation: http://public.example\r\n\r\n']) as peer:
            with self.assertRaisesRegex(FetchError, 'REDIRECT_DENIED'):
                self.fetch(peer, 'https://public.example')

    def test_compressed_wrong_type_duplicate_framing_and_truncated_denied(self):
        responses = [page(headers=b'Content-Encoding: gzip\r\n'),
                     b'HTTP/1.1 200 OK\r\nContent-Type: video/mp4\r\n\r\n',
                     page(headers=b'Content-Length: 7\r\nContent-Length: 7\r\n'),
                     page(headers=b'Content-Length: 7\r\nTransfer-Encoding: chunked\r\n'),
                     page(headers=b'Content-Length: 100\r\n')]
        for response in responses:
            with self.subTest(response=response[:90]), LocalPeer([response]) as peer:
                with self.assertRaises(FetchError):
                    self.fetch(peer)

    def test_body_limit_with_declared_and_streamed_lengths(self):
        for response in [page(headers=b'Content-Length: 999999\r\n'), page(b'x' * (MAX_BODY + 1))]:
            with LocalPeer([response]) as peer, self.assertRaisesRegex(FetchError, 'BODY_TOO_LARGE'):
                self.fetch(peer)

    def test_chunked_response_has_same_body_budget(self):
        chunk = b'x' * (MAX_BODY + 1)
        encoded = f'{len(chunk):x}\r\n'.encode() + chunk + b'\r\n0\r\n\r\n'
        with LocalPeer([page(encoded, b'Transfer-Encoding: chunked\r\n')]) as peer:
            with self.assertRaisesRegex(FetchError, 'BODY_TOO_LARGE'):
                self.fetch(peer)

    def test_error_messages_do_not_expose_url(self):
        with self.assertRaisesRegex(FetchError, '^FETCH_DENIED$'):
            fetch_page('http://user:secret@public.example')

    def test_numeric_dial_never_resolves_again_and_tls_checks_hostname(self):
        destination = Destination('https://public.example/', 'public.example', 443, ('8.8.8.8',))
        with patch('services.worker.restricted_fetch.socket.socket') as factory, \
                patch('services.worker.restricted_fetch.socket.getaddrinfo', side_effect=AssertionError('second DNS')), \
                patch('services.worker.restricted_fetch.ssl.create_default_context', wraps=ssl.create_default_context) as create:
            sock = factory.return_value
            sock.getpeername.return_value = ('8.8.8.8', 443)
            context = ssl.create_default_context()
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            create.return_value = context
            with patch.object(context, 'wrap_socket', return_value=sock) as wrap:
                self.assertIs(connect(destination, 2), sock)
                sock.connect.assert_called_once_with(('8.8.8.8', 443))
                wrap.assert_called_once_with(sock, server_hostname='public.example')

    def test_wrong_peer_is_rejected_and_socket_closed(self):
        destination = Destination('http://public.example/', 'public.example', 80, ('8.8.8.8',))
        with patch('services.worker.restricted_fetch.socket.socket') as factory:
            sock = factory.return_value
            sock.getpeername.return_value = ('127.0.0.1', 80)
            with self.assertRaisesRegex(FetchError, 'PEER_DENIED'):
                connect(destination, 2)
            sock.close.assert_called_once()

    def test_stalled_response_is_interrupted_and_socket_closed(self):
        left, right = socket.socketpair()
        try:
            with patch('services.worker.restricted_fetch.TIMEOUT', .1):
                with self.assertRaisesRegex(FetchError, 'TIMEOUT'):
                    fetch_page('http://public.example', resolver=lambda *_: ['8.8.8.8'],
                               connector=lambda *_: left)
            self.assertEqual(left.fileno(), -1)
        finally:
            left.close()
            right.close()

    def test_tls_verification_failure_is_not_retried_in_plaintext(self):
        destination = Destination('https://public.example/', 'public.example', 443, ('8.8.8.8',))
        with patch('services.worker.restricted_fetch.socket.socket') as factory, \
                patch('services.worker.restricted_fetch.ssl.create_default_context') as create:
            sock = factory.return_value
            sock.getpeername.return_value = ('8.8.8.8', 443)
            create.return_value.wrap_socket.side_effect = ssl.SSLCertVerificationError('fixture')
            with self.assertRaises(ssl.SSLCertVerificationError):
                connect(destination, 2)
            sock.connect.assert_called_once()
            sock.close.assert_called_once()

    def test_slow_header_cannot_extend_response_deadline(self):
        left, right = socket.socketpair()
        stop = threading.Event()
        def drip():
            try:
                for byte in page():
                    if stop.wait(.02):
                        break
                    right.sendall(bytes([byte]))
            except OSError:
                pass
        writer = threading.Thread(target=drip, daemon=True)
        writer.start()
        started = time.monotonic()
        try:
            with patch('services.worker.restricted_fetch.TIMEOUT', .1):
                # A partial status line may be rejected as malformed before the
                # deadline; either rejection must be prompt and content-free.
                with self.assertRaises(FetchError):
                    fetch_page('http://public.example', resolver=lambda *_: ['8.8.8.8'],
                               connector=lambda *_: left)
            self.assertLess(time.monotonic() - started, .8)
        finally:
            stop.set()
            left.close()
            right.close()
            writer.join(timeout=1)
