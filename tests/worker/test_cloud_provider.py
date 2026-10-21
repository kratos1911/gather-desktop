"""Composition/control checks, synthetic tokens and responses, no network."""
import threading
import unittest
from unittest.mock import patch, Mock

from scripts.check_cloud_ingestion import PilotToken, BoundedProvider, IDENTITY
from services.worker.cloud_provider import cloud_provider, pinned_token_counter
from services.worker.service_clients import CloudInferenceClient
from services.worker.service_transport import TransportError
from tests.worker.test_cloud_identity import token, NOW


class CloudProviderTests(unittest.TestCase):
    def test_metadata_is_still_default(self):
        with patch('services.worker.cloud_identity.MetadataTokenProvider') as metadata:
            CloudInferenceClient(IDENTITY, lambda text: 1)
            metadata.assert_called_once_with(IDENTITY)

    def test_composition_reuses_verified_tokenizer_and_explicit_identity(self):
        provider = Mock(config=IDENTITY)
        with patch('services.worker.cloud_provider.pinned_token_counter', return_value=len):
            client = cloud_provider(IDENTITY, 'fixture', token_provider=provider)
        self.assertIs(client._identity, provider)
        self.assertEqual(client.count_tokens('hello'), 5)

    def test_foreign_or_missing_provider_contract_rejected(self):
        for provider in [object(), Mock(config=None)]:
            with self.assertRaises(TransportError):
                CloudInferenceClient(IDENTITY, len, token_provider=provider)

    def test_bad_tokenizer_fails_before_loading_or_network(self):
        with self.assertRaises(ValueError):
            pinned_token_counter('relative-path')

    def test_pilot_token_cancel_expiry_and_invalidation(self):
        with patch('scripts.check_cloud_ingestion.time.time', return_value=NOW), patch(
                'scripts.check_cloud_ingestion.time.monotonic', return_value=100):
            # Synthetic claim checks only, not cryptographic authentication.
            value = token(aud=IDENTITY.audience, email=IDENTITY.caller_email)
            provider = PilotToken(value)
            self.assertEqual(provider.get(), value)
            cancel = threading.Event()
            cancel.set()
            with self.assertRaisesRegex(TransportError, 'cancelled'):
                provider.get(cancel=cancel)
            provider.invalidate()
            with self.assertRaisesRegex(TransportError, 'identity_unavailable'):
                provider.get()

    def test_pilot_wrong_audience_rejected(self):
        with patch('scripts.check_cloud_ingestion.time.time', return_value=NOW):
            with self.assertRaises(TransportError):
                PilotToken(token())

    def test_pilot_monotonic_expiry_blocks_wall_clock_rollback(self):
        with patch('scripts.check_cloud_ingestion.time.time', return_value=NOW), patch(
                'scripts.check_cloud_ingestion.time.monotonic', return_value=100):
            provider = PilotToken(token(aud=IDENTITY.audience, email=IDENTITY.caller_email))
        with patch('scripts.check_cloud_ingestion.time.time', return_value=NOW-100), patch(
                'scripts.check_cloud_ingestion.time.monotonic', return_value=4000):
            with self.assertRaises(TransportError):
                provider.get()

    def test_failed_requests_consume_budget_without_retry(self):
        wrapped = Mock()
        wrapped.infer.side_effect = RuntimeError('synthetic failure')
        provider = BoundedProvider(wrapped)
        for _ in range(4):
            with self.assertRaises(RuntimeError):
                provider.infer({}, cancel=None)
        self.assertEqual(provider.calls, 3)
        self.assertEqual(wrapped.infer.call_count, 3)


if __name__ == '__main__':
    unittest.main()
