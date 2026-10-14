"""Ensure failed and incomplete benchmarks cannot be reported as passing."""
import unittest

from scripts.check_inference_container import profile_requests, review_rows


class ProfileTests(unittest.TestCase):
    def test_expected_limit_rejection_is_not_model_success(self):
        requests, expected = profile_requests('limits')
        outcomes, passed = review_rows([{'error': 'token_limit'}] * 3, requests, expected)
        self.assertFalse(passed)
        self.assertTrue(outcomes[0]['passed'])
        self.assertFalse(outcomes[-1]['passed'])

    def test_timeout_and_missing_requests_are_failures(self):
        requests, expected = profile_requests('long')
        outcomes, passed = review_rows([{'error': 'deadline_exceeded'}], requests, expected)
        self.assertFalse(passed)
        self.assertEqual(outcomes[1]['error'], 'not_executed')

    def test_extra_responses_fail(self):
        _, passed = review_rows([{'error': 'token_limit'}] * 2,
                                [{'role': 'document', 'texts': ['x']}], ['token_limit'])
        self.assertFalse(passed)
