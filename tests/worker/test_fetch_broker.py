import base64
import json
import subprocess
import threading
import time
import unittest
from unittest.mock import patch

from services.worker.fetch_broker import FetchBroker, BrokerError, _SLOT


def broker(code):
    class FixtureBroker(FetchBroker):
        _CHILD_CODE = code
    return FixtureBroker()


def result(body=b'fixture'):
    return {'status': 'fetched', 'final_url': 'https://public.example/final',
            'content_type': 'text/html', 'redirects': 1,
            'body_base64': base64.b64encode(body).decode()}


def emit(value):
    return 'import sys; sys.stdin.buffer.read(); print(' + repr(json.dumps(value)) + ')'


class FetchBrokerTests(unittest.TestCase):
    def test_success_round_trip_and_child_is_reaped(self):
        real_popen = subprocess.Popen
        children = []
        def start(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child
        with patch('services.worker.fetch_broker.subprocess.Popen', side_effect=start):
            page = broker(emit(result(b'<p>local fixture</p>'))).fetch('https://public.example')
        self.assertEqual(page.body, b'<p>local fixture</p>')
        self.assertEqual(page.redirects, 1)
        self.assertIsNotNone(children[0].poll())
        self.assertTrue(children[0].stdout.closed)

    def test_hanging_dns_and_connect_are_killed_and_slot_recovers(self):
        codes = [
            'import time; from services.worker import restricted_fetch as r; '
            'r.socket.getaddrinfo=lambda *a,**k: time.sleep(120); '
            'from services.worker.fetch_broker import child_main; child_main()',
            'import time; from unittest.mock import Mock; from services.worker import restricted_fetch as r; '
            'r.socket.getaddrinfo=lambda *a,**k: [(2,1,6,"",("8.8.8.8",443))]; '
            'r.socket.socket=Mock(return_value=Mock(getpeername=Mock(return_value=("8.8.8.8",443)))); '
            'r.ssl.create_default_context=lambda: Mock(wrap_socket=lambda *a,**k: time.sleep(120)); '
            'from services.worker.fetch_broker import child_main; child_main()',
            'import time; from services.worker import restricted_fetch as r; '
            'original=r.fetch_page; r.fetch_page=lambda u: original(u, '
            'resolver=lambda *a: ["8.8.8.8"], connector=lambda *a: time.sleep(120)); '
            'from services.worker.fetch_broker import child_main; child_main()',
        ]
        for code in codes:
            real_popen = subprocess.Popen
            children = []
            def start(*args, **kwargs):
                child = real_popen(*args, **kwargs)
                children.append(child)
                return child
            with self.subTest(code=code[:40]), patch('services.worker.fetch_broker.subprocess.Popen', side_effect=start) as launch:
                started = time.monotonic()
                with self.assertRaisesRegex(BrokerError, '^FETCH_TIMEOUT$'):
                    broker(code).fetch('https://public.example', timeout=.8)
                self.assertLess(time.monotonic() - started, 5)
                self.assertTrue(launch.called)
                self.assertIsNotNone(children[0].poll())
                self.assertTrue(children[0].stdout.closed)
        self.assertEqual(broker(emit(result())).fetch('https://public.example').body, b'fixture')

    def test_valid_output_from_a_still_running_child_is_not_published(self):
        code = emit(result()) + '; import time; time.sleep(120)'
        with self.assertRaisesRegex(BrokerError, '^FETCH_TIMEOUT$'):
            broker(code).fetch('https://public.example', timeout=.8)

    def test_cancellation_terminates_running_process(self):
        cancel = threading.Event()
        timer = threading.Timer(.5, cancel.set)
        timer.start()
        try:
            with self.assertRaisesRegex(BrokerError, 'CANCELLED'):
                broker('import time; time.sleep(120)').fetch('https://public.example', cancel=cancel)
        finally:
            timer.cancel()

    def test_oversized_stdout_and_stderr_are_bounded(self):
        for stream, size in [('stdout', 300000), ('stderr', 20000)]:
            with self.subTest(stream=stream), self.assertRaisesRegex(BrokerError, 'OUTPUT_LIMIT'):
                broker(f'import sys; sys.stdin.buffer.read(); sys.{stream}.write("x"*{size})').fetch('https://public.example')

    def test_invalid_partial_duplicate_and_oversized_body_rejected(self):
        large_body = ('import sys,json,base64; sys.stdin.buffer.read(); value=' + repr(result()) +
                      '; value["body_base64"]=base64.b64encode(b"x"*65537).decode(); print(json.dumps(value))')
        codes = ['print("{")', 'print(\'{"status":"error","status":"fetched"}\')',
                 large_body, emit({**result(), 'redirects': True})]
        for code in codes:
            with self.subTest(length=len(code)), self.assertRaisesRegex(BrokerError, 'INVALID_RESULT'):
                broker(code).fetch('https://public.example')

    def test_child_error_is_content_free(self):
        for code, expected in [(emit({'status': 'error'}), 'FETCH_FAILED'),
                               ('raise RuntimeError("fixture-secret")', 'FETCH_PROCESS_FAILED')]:
            with self.assertRaisesRegex(BrokerError, '^' + expected + '$'):
                broker(code).fetch('https://public.example/?private=fixture')

    def test_secrets_proxy_and_pythonpath_are_not_inherited(self):
        code = 'import os; assert "GATHER_TEST_SECRET" not in os.environ; assert "HTTP_PROXY" not in os.environ; assert "PYTHONPATH" not in os.environ; ' + emit(result())
        with patch.dict('os.environ', {'GATHER_TEST_SECRET': 'fixture', 'HTTP_PROXY': 'fixture', 'PYTHONPATH': 'fixture'}):
            self.assertEqual(broker(code).fetch('https://public.example').body, b'fixture')

    def test_busy_invalid_and_precancelled_do_not_start(self):
        with patch('services.worker.fetch_broker.subprocess.Popen') as launch:
            with self.assertRaises(BrokerError):
                FetchBroker().fetch('http://127.0.0.1')
            with self.assertRaises(ValueError):
                FetchBroker().fetch('https://public.example', timeout=float('nan'))
            cancel = threading.Event(); cancel.set()
            with self.assertRaisesRegex(BrokerError, 'CANCELLED'):
                FetchBroker().fetch('https://public.example', cancel=cancel)
            _SLOT.acquire()
            try:
                with self.assertRaisesRegex(BrokerError, 'BUSY'):
                    FetchBroker().fetch('https://public.example')
            finally:
                _SLOT.release()
            launch.assert_not_called()
