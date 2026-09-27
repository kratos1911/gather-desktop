import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from services.worker.embedding_client import EmbeddingError, Limits, embed_texts, https_transport


class EmbeddingClientTests(unittest.TestCase):
    def setUp(self):
        self.limits = Limits(2, 10, 30, batch_size=2)
        self.send = Mock(side_effect=lambda body: {"model": "test", "data": [
            {"index": i, "embedding": [i + 1, 1]} for i in reversed(range(len(body["input"])))],
            "usage": {"total_tokens": len(body["input"])}})

    def embed(self, texts):
        return embed_texts(texts, model="test", limits=self.limits, count_tokens=lambda text: len(text.split()), send=self.send)

    def test_batching_reorders_provider_results_and_tracks_usage(self):
        result = self.embed(["a", "b", "c"])
        self.assertEqual(result["vectors"], [[1, 1], [2, 1], [1, 1]])
        self.assertEqual(result["requests"], 2)
        self.assertEqual(result["reported_tokens"], 3)
        self.assertEqual(result["preflight_tokens"], 3)

    def test_all_inputs_checked_before_any_request(self):
        with self.assertRaises(EmbeddingError):
            self.embed(["valid", "valid", "word " * 11])
        self.send.assert_not_called()

    def test_token_budget_and_request_budget(self):
        for limits in (Limits(2, 10, 1), Limits(2, 10, 100, batch_size=1, max_requests=1)):
            self.limits = limits
            with self.assertRaises(EmbeddingError):
                self.embed(["a", "b"])
        self.send.assert_not_called()

    def test_malformed_duplicate_wrong_model_and_zero_vectors(self):
        responses = [None, {"model": "other", "data": []},
                     {"model": "test", "data": [{"index": 0, "embedding": [0, 0]}]},
                     {"model": "test", "data": [{"index": 0, "embedding": [1]}]}]
        for response in responses:
            self.send = Mock(return_value=response)
            with self.assertRaises(EmbeddingError):
                self.embed(["a"])

    def test_unknown_usage_is_not_zero(self):
        self.send = Mock(return_value={"model": "test", "data": [{"index": 0, "embedding": [1, 2]}]})
        self.assertIsNone(self.embed(["a"])["reported_tokens"])

    def test_transport_failure_has_no_sensitive_body_or_retry(self):
        self.send = Mock(side_effect=RuntimeError("private text and secret"))
        with self.assertRaises(EmbeddingError) as caught:
            self.embed(["a"])
        self.assertNotIn("private", str(caught.exception))
        self.assertEqual(self.send.call_count, 1)

    def test_https_transport_auth_error_is_sanitized(self):
        opener = Mock()
        opener.open.side_effect = HTTPError("https://example.invalid", 401, "secret", {}, None)
        with patch("services.worker.embedding_client.build_opener", return_value=opener):
            send = https_transport("https://example.invalid/v1/embeddings", "test-token")
            with self.assertRaisesRegex(EmbeddingError, "authentication failed"):
                send({"model": "test", "input": ["fictional"]})
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)

    def test_insecure_endpoint_rejected(self):
        for url in ("http://example.invalid", "https://user:pass@example.invalid", "https://example.invalid?key=x"):
            with self.assertRaises(EmbeddingError):
                https_transport(url, "test-token")


if __name__ == "__main__":
    unittest.main()
