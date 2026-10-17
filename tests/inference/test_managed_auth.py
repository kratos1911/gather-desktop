"""Mocked Google responses and synthetic RSA keys; no external requests."""
import asyncio
from email.message import Message
from email.utils import formatdate
import json
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from services.inference.managed_auth import ManagedGoogleServiceAuth
from services.inference.asgi import create_app
from services.worker.cloud_identity import IdentityConfig
from services.worker.service_transport import _certificate_response, request_google_certificates
from tests.inference import test_service_auth as fixtures


class ManagedAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ServiceAuthTests.setUpClass()

    def setUp(self):
        self.fixture = fixtures.ServiceAuthTests()
        self.fixture.setUp()
        self.auth = ManagedGoogleServiceAuth(self.fixture.identity, fixtures.SUB)
        self.fetch = patch('services.inference.managed_auth.request_google_certificates',
                           return_value={'certificates':{'fixture':self.fixture.pem},'ttl':240}).start()
        self.addCleanup(patch.stopall)

    def headers(self, kid='fixture'):
        return [(b'authorization', b'Bearer '+self.fixture.token(header=dict(alg='RS256',kid=kid)))]

    def test_unknown_ids_never_fetch_and_refresh_cooldown(self):
        self.assertFalse(self.auth.ready)
        self.assertFalse(self.auth(self.headers()))
        self.fetch.assert_not_called()
        self.assertTrue(self.auth._refresh())
        for i in range(50):
            self.assertFalse(self.auth(self.headers('unknown-'+str(i))))
        self.assertFalse(self.auth._refresh())
        self.assertEqual(self.fetch.call_count,1)
        self.assertTrue(self.auth(self.headers()))

    def test_rotation_replaces_keyset(self):
        self.assertTrue(self.auth._refresh())
        self.fetch.return_value = {'certificates':{'rotated':self.fixture.pem},'ttl':240}
        with patch('services.inference.managed_auth.time.monotonic',return_value=time.monotonic()+31):
            self.assertTrue(self.auth._refresh())
        self.assertFalse(self.auth(self.headers()))
        self.assertTrue(self.auth(self.headers('rotated')))

    def test_failed_refresh_does_not_extend_existing_snapshot(self):
        self.assertTrue(self.auth._refresh())
        snapshot = self.auth._snapshot
        deadline = snapshot._deadline
        self.fetch.side_effect = OSError('private fixture error')
        with patch('services.inference.managed_auth.time.monotonic',return_value=time.monotonic()+31):
            self.assertFalse(self.auth._refresh())
        self.assertIs(self.auth._snapshot,snapshot)
        self.assertEqual(snapshot._deadline,deadline)
        self.assertTrue(self.auth(self.headers()))
        with patch('services.inference.managed_auth.time.monotonic',return_value=deadline+1):
            self.assertFalse(self.auth.ready)
            self.assertFalse(self.auth(self.headers()))

    def test_invalid_partial_snapshot_and_single_flight(self):
        self.assertTrue(self.auth._refresh())
        original = self.auth._snapshot
        self.fetch.return_value = {'certificates':{'broken':'not a certificate'},'ttl':240}
        with patch('services.inference.managed_auth.time.monotonic',return_value=time.monotonic()+31):
            self.assertFalse(self.auth._refresh())
        self.assertIs(self.auth._snapshot,original)
        with self.auth._lock:
            self.assertFalse(self.auth._refresh())
        self.assertEqual(self.fetch.call_count,2)

    def test_shutdown_during_fetch_cannot_publish(self):
        def stop(**kwargs):
            kwargs['cancel'].set()
            return {'certificates':{'fixture':self.fixture.pem},'ttl':240}
        self.fetch.side_effect = stop
        self.assertFalse(self.auth._refresh())
        self.assertIsNone(self.auth._snapshot)

    def test_lifecycle_keys_before_model_and_stops_refresh_thread(self):
        runtime = MagicMock(request_timeout=1,ready=True)
        runtime.start.side_effect = lambda **kwargs: self.assertTrue(self.auth.ready)
        app = create_app(runtime,self.auth)
        async def run():
            async with app.router.lifespan_context(app):
                self.assertTrue(self.auth.ready)
                self.assertTrue(self.auth._thread.is_alive())
            self.assertFalse(self.auth.ready)
            self.assertFalse(self.auth._thread.is_alive())
        asyncio.run(run())
        runtime.start.assert_called_once()
        runtime.close.assert_called_once()
        self.assertEqual(self.fetch.call_count,1)

    def test_startup_failure_never_loads_model(self):
        self.fetch.side_effect = OSError('offline')
        runtime = MagicMock(request_timeout=1)
        app = create_app(runtime,self.auth)
        async def run():
            with self.assertRaisesRegex(ValueError,'trusted_keys_unavailable'):
                async with app.router.lifespan_context(app):
                    self.fail('must not start')
        asyncio.run(run())
        runtime.start.assert_not_called()
        self.assertFalse(self.auth.ready)


class CertificateTransportTests(unittest.TestCase):
    def response(self, **changes):
        headers = Message()
        for key,value in {'Content-Type':'application/json','Cache-Control':'public, max-age=120',
                          'Date':formatdate(time.time(),usegmt=True),'Age':'10',**changes}.items():
            headers[key] = value
        response = MagicMock(status=200,headers=headers)
        response.read.return_value = b'{"fixture":"synthetic certificate"}'
        return response

    def invoke(self,response):
        with patch('services.worker.service_transport.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value = response
            result = _certificate_response()
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,'https://www.googleapis.com/oauth2/v1/certs')
            self.assertIsNone(request.get_header('Authorization'))
            self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'],5)
            return result

    def test_fixed_endpoint_and_freshness(self):
        response = self.response()
        result = self.invoke(response)
        value = json.loads(result[3:])
        self.assertEqual(value['ttl'],110)
        response.read.assert_called_once_with(65537)
        with patch('services.worker.service_transport._exchange',return_value=value) as exchange:
            request_google_certificates()
            self.assertEqual(exchange.call_args.args,(b'{"google_certificates":true}',))
            self.assertEqual(exchange.call_args.kwargs['timeout'],5)

    def test_stale_or_noncacheable_responses_rejected(self):
        for headers in [{'Cache-Control':'no-store, max-age=120'}, {'Cache-Control':'no-cache="x", max-age=120'},
                        {'Cache-Control':'public'}, {'Cache-Control':'max-age=1, max-age=99'},
                        {'Age':'121'}, {'Age':'-1'}, {'Content-Encoding':'gzip'},
                        {'Date':formatdate(time.time()-500,usegmt=True)},
                        {'Date':formatdate(time.time()+1000,usegmt=True)}]:
            with self.subTest(headers=headers):
                self.assertEqual(self.invoke(self.response(**headers)),b'ERR\ninvalid_response')

    def test_oversize_or_invalid_keyset_rejected(self):
        response = self.response()
        response.read.return_value = b'x'*65537
        self.assertEqual(self.invoke(response),b'ERR\nresponse_too_large')
        for raw in [b'{}',b'[]',json.dumps({str(i):'key' for i in range(9)}).encode()]:
            response.read.return_value = raw
            self.assertEqual(self.invoke(response),b'ERR\ninvalid_response')


if __name__ == '__main__':
    unittest.main()
