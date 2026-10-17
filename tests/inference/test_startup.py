"""Synthetic signed identities/mocked keys only; no Google or model loading."""
import asyncio
import json
import unittest
from unittest.mock import MagicMock, patch

from services.inference.startup import create_trusted_app, load_identity
from services.inference.managed_auth import ManagedGoogleServiceAuth
from services.worker.cloud_identity import IdentityConfig
from tests.inference import test_service_auth as fixtures

WORKER = 'gather-worker@sample-project.iam.gserviceaccount.com'
WORKER_SUB = '987654321'


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ServiceAuthTests.setUpClass()

    def setUp(self):
        self.fixture = fixtures.ServiceAuthTests()
        self.fixture.setUp()
        self.config = {'audience': fixtures.AUD, 'callers': [
            {'email': fixtures.EMAIL, 'subject': fixtures.SUB},
            {'email': WORKER, 'subject': WORKER_SUB}]}
        self.raw = json.dumps(self.config).encode()

    def test_paired_callers_share_refresh_and_reject_cross_pairing(self):
        auth = ManagedGoogleServiceAuth(load_identity(self.raw))
        with patch('services.inference.managed_auth.request_google_certificates',
                   return_value={'certificates': {'fixture': self.fixture.pem}, 'ttl': 240}) as fetch:
            self.assertTrue(auth._refresh())
            for email, sub, expected in [(fixtures.EMAIL, fixtures.SUB, True),
                    (WORKER, WORKER_SUB, True), (WORKER, fixtures.SUB, False),
                    (fixtures.EMAIL, WORKER_SUB, False), (WORKER, '999', False)]:
                token = self.fixture.token({'email': email, 'sub': sub})
                self.assertEqual(auth([(b'authorization', b'Bearer '+token)]), expected)
            self.assertEqual(fetch.call_count, 1)
            with patch('services.inference.service_auth.time.monotonic',
                       return_value=auth._snapshot._deadline+1):
                self.assertFalse(auth.ready)
                self.assertFalse(auth([(b'authorization', b'Bearer '+self.fixture.token())]))

    def test_configuration_fails_closed(self):
        variants = [b'{}', b'x'*4097, b'{"audience":"x","audience":"y","callers":[]}']
        for callers in [[], self.config['callers']*2,
                        [self.config['callers'][0]]*2,
                        [self.config['callers'][0], {'email': WORKER, 'subject': fixtures.SUB}],
                        [{'email': 'allUsers', 'subject': '123'}],
                        [{'email': WORKER, 'subject': 123}]]:
            variants.append(json.dumps(dict(self.config, callers=callers)).encode())
        variants.append(json.dumps(dict(self.config, secret='no fallback')).encode())
        for raw in variants:
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'invalid_startup_identity'):
                load_identity(raw)
        legacy = IdentityConfig(fixtures.AUD, fixtures.EMAIL,
            ('serviceAccount:'+fixtures.EMAIL, 'serviceAccount:'+WORKER))
        with self.assertRaises(ValueError):
            ManagedGoogleServiceAuth(legacy, fixtures.SUB)

    def test_composition_loads_keys_before_runtime_and_closes_both(self):
        runtime = MagicMock(request_timeout=1, ready=True)
        with patch('services.inference.managed_auth.request_google_certificates',
                   return_value={'certificates': {'fixture': self.fixture.pem}, 'ttl': 240}) as fetch:
            app = create_trusted_app(self.raw, runtime)
            fetch.assert_not_called()
            runtime.start.side_effect = lambda **kw: self.assertEqual(fetch.call_count, 1)
            async def lifecycle():
                async with app.router.lifespan_context(app):
                    runtime.start.assert_called_once()
            asyncio.run(lifecycle())
            runtime.close.assert_called_once()
            self.assertTrue(app.state.stopping.is_set())

    def test_missing_keys_never_starts_runtime(self):
        runtime = MagicMock(request_timeout=1)
        app = create_trusted_app(self.raw, runtime)
        with patch('services.inference.managed_auth.request_google_certificates', side_effect=OSError()):
            async def lifecycle():
                with self.assertRaisesRegex(ValueError, 'trusted_keys_unavailable'):
                    async with app.router.lifespan_context(app):
                        self.fail('must reject startup')
            asyncio.run(lifecycle())
        runtime.start.assert_not_called()
        runtime.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
