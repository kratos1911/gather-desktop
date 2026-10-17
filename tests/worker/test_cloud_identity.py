"""Synthetic claims and mocked metadata only; no Google signature/IAM evidence."""
import base64
import json
import threading
import unittest
from unittest.mock import MagicMock, patch

from services.inference.runtime import InferenceError
from services.worker.cloud_identity import IdentityConfig, MetadataTokenProvider
from services.worker.service_clients import CloudInferenceClient
from services.worker.service_transport import TransportError, _metadata_response, request_identity_token

AUD = 'https://gather-model-example.run.app'
EMAIL = 'gather-api@sample-project.iam.gserviceaccount.com'
MEMBERS = ('serviceAccount:'+EMAIL,)
NOW = 1800000000


def token(**changes):
    claims = dict(iss='https://accounts.google.com', aud=AUD, email=EMAIL,
                  email_verified=True, sub='123456789', iat=NOW, exp=NOW+3600)
    claims.update(changes)
    def encode(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip('=')
    return encode(dict(alg='RS256', kid='synthetic'))+'.'+encode(claims)+'.fake'


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.config = IdentityConfig(AUD, EMAIL, MEMBERS)
        self.clock = patch('services.worker.cloud_identity.time.time', return_value=NOW).start()
        self.mono = patch('services.worker.cloud_identity.time.monotonic', return_value=100).start()
        self.fetch = patch('services.worker.cloud_identity.request_identity_token', return_value=token()).start()
        self.addCleanup(patch.stopall)

    def test_configuration_rejects_unsafe_policy(self):
        for fields in [dict(audience='http://x.run.app'), dict(audience=AUD+'/embed'),
                       dict(audience='https://example.com'), dict(caller_email='person@gmail.com'),
                       dict(invoker_members=('allUsers',)), dict(invoker_members=([],)),
                       dict(invoker_members=()), dict(invoker_members=MEMBERS*2),
                       dict(invoker_check_required=False)]:
            with self.subTest(fields=fields), self.assertRaises(TransportError):
                IdentityConfig(**(dict(audience=AUD, caller_email=EMAIL, invoker_members=MEMBERS)|fields))

    def test_cache_and_explicit_invalidation(self):
        provider = MetadataTokenProvider(self.config)
        self.assertEqual(provider.get(), token())
        self.assertEqual(provider.get(), token())
        self.assertEqual(self.fetch.call_count, 1)
        provider.invalidate()
        provider.get()
        self.assertEqual(self.fetch.call_count, 2)
        with self.assertRaises(AttributeError):
            provider.config = self.config

    def test_bad_claims_are_never_cached(self):
        for changes in [dict(aud=AUD+'x'), dict(email='other@sample-project.iam.gserviceaccount.com'),
                        dict(iss='attacker'), dict(email_verified=False), dict(sub=12),
                        dict(exp=NOW+60), dict(exp=NOW-1), dict(exp=NOW+4000),
                        dict(iat=NOW+61), dict(exp=True), dict(iat=NOW-100)]:
            with self.subTest(changes=changes):
                provider = MetadataTokenProvider(self.config)
                self.fetch.return_value = token(**changes)
                with self.assertRaisesRegex(TransportError, '^invalid_identity_token$'):
                    provider.get()
                self.assertIsNone(provider._token)
        for invalid in ['not-a-jwt', 'a.b.c', token().replace('fake','!'), 'x'*8193]:
            self.fetch.return_value = invalid
            with self.assertRaises(TransportError):
                MetadataTokenProvider(self.config).get()

    def test_refresh_failure_does_not_fall_back(self):
        provider = MetadataTokenProvider(self.config)
        provider.get()
        self.clock.return_value = NOW+3540
        self.fetch.side_effect = TransportError('service_unavailable')
        with self.assertRaises(TransportError):
            provider.get()
        self.assertIsNone(provider._token)

    def test_monotonic_expiry_survives_clock_rollback(self):
        provider = MetadataTokenProvider(self.config)
        provider.get()
        self.clock.return_value = NOW-500
        self.mono.return_value = 3641
        self.fetch.side_effect = TransportError('service_unavailable')
        with self.assertRaises(TransportError):
            provider.get()
        self.assertEqual(self.fetch.call_count, 2)

    def test_busy_and_cancelled_do_not_fetch(self):
        provider = MetadataTokenProvider(self.config)
        with provider._lock, self.assertRaisesRegex(TransportError, '^busy$'):
            provider.get()
        cancel = threading.Event()
        cancel.set()
        with self.assertRaisesRegex(TransportError, '^cancelled$'):
            provider.get(cancel=cancel)
        self.fetch.assert_not_called()
        cancel.clear()
        def fetch(*args, **kwargs):
            cancel.set()
            return token()
        self.fetch.side_effect = fetch
        with self.assertRaisesRegex(TransportError, '^cancelled$'):
            provider.get(cancel=cancel)
        self.assertIsNone(provider._token)

    def test_separate_audiences_do_not_share_tokens(self):
        MetadataTokenProvider(self.config).get()
        other = IdentityConfig('https://other-model.run.app', EMAIL, MEMBERS)
        with self.assertRaisesRegex(TransportError, '^invalid_identity_token$'):
            MetadataTokenProvider(other).get()
        self.assertEqual(self.fetch.call_count, 2)

    def test_metadata_fixed_destination_and_bounds(self):
        response = MagicMock(status=200)
        response.headers = {'Metadata-Flavor':'Google'}
        response.read.return_value = token().encode()
        with patch('services.worker.service_transport.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value = response
            self.assertTrue(_metadata_response(AUD).startswith(b'OK\n'))
            request = opener.return_value.open.call_args.args[0]
            self.assertTrue(request.full_url.startswith('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?'))
            self.assertIn('audience=https%3A%2F%2Fgather-model-example.run.app', request.full_url)
            self.assertEqual(request.get_header('Metadata-flavor'), 'Google')
            response.read.assert_called_with(8193)
            self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'], 5)
            response.headers = {}
            self.assertEqual(_metadata_response(AUD), b'ERR\ninvalid_response')
            response.headers = {'Metadata-Flavor':'Google'}
            response.read.return_value = b'x'*8193
            self.assertEqual(_metadata_response(AUD), b'ERR\nresponse_too_large')

    def test_metadata_parent_caps_deadline_without_network(self):
        with patch('services.worker.service_transport._exchange', return_value='synthetic') as exchange:
            request_identity_token(AUD, timeout=10)
            self.assertEqual(exchange.call_args.kwargs['timeout'], 5)
            for invalid in [None, '5', True, 0, float('nan')]:
                with self.assertRaises(TransportError):
                    request_identity_token(AUD, timeout=invalid)
            self.assertEqual(exchange.call_count, 1)

    def test_cloud_client_budget_and_authorization(self):
        client = CloudInferenceClient(self.config, lambda text: 1)
        with patch.object(client._identity, 'get', return_value=token()), patch(
                'services.worker.service_clients.time.monotonic', side_effect=[100,103]), patch(
                'services.worker.service_clients.request_json', return_value={'fixture':True}) as send:
            self.assertEqual(client.infer(dict(role='query', texts=['hello']), cancel=None), {'fixture':True})
            self.assertEqual(send.call_args.args[:3], (AUD, '/embed', {
                'Authorization':'Bearer '+token(), 'X-Serverless-Authorization':'Bearer '+token()}))
            self.assertEqual(send.call_args.kwargs['timeout'], 12)

    def test_dual_header_size_bound_rejects_before_send(self):
        client = CloudInferenceClient(self.config, lambda text: 1)
        with patch.object(client._identity, 'get', return_value='x'*7169), patch(
                'services.worker.service_clients.request_json') as send:
            with self.assertRaisesRegex(InferenceError, 'service_unavailable'):
                client.infer(dict(role='query', texts=['hello']), cancel=None)
            send.assert_not_called()

    def test_cloud_client_rejects_before_io_and_no_fallback(self):
        client = CloudInferenceClient(self.config, lambda text: 2049)
        with self.assertRaisesRegex(InferenceError, 'token_limit'):
            client.infer(dict(role='query', texts=['hello']), cancel=None)
        self.fetch.assert_not_called()
        client.count_tokens = lambda text: 1
        self.fetch.side_effect = TransportError('timeout')
        with patch('services.worker.service_clients.request_json') as send:
            with self.assertRaisesRegex(InferenceError, 'deadline_exceeded'):
                client.infer(dict(role='query', texts=['hello']), cancel=None)
            send.assert_not_called()

    def test_rejected_service_token_invalidated_without_retry(self):
        client = CloudInferenceClient(self.config, lambda text: 1)
        with patch('services.worker.service_clients.request_json', side_effect=TransportError('authentication_failed')) as send:
            with self.assertRaisesRegex(InferenceError, 'service_unavailable'):
                client.infer(dict(role='query', texts=['hello']), cancel=None)
            self.assertEqual(send.call_count, 1)
            self.assertIsNone(client._identity._token)


if __name__ == '__main__':
    unittest.main()
