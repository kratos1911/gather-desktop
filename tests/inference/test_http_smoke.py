"""Harness checks only: synthetic embeddings do not establish model performance."""
import unittest
from unittest.mock import patch

from scripts.check_inference_http import run
from scripts.check_inference_container import main
from services.inference.runtime import Runtime


class Engine:
    def __init__(self, invalid):
        self.invalid = invalid

    def count_tokens(self, text):
        return len(text.split()) + 1 if text.startswith('x') else 10

    def embed(self, text):
        return [float('nan') if self.invalid else 1.] * 512


class HTTPSmokeTests(unittest.TestCase):
    def test_complete_http_path_and_cleanup(self):
        report = run(Runtime(Engine, False, startup_timeout=5))
        self.assertTrue(report['passed'], report)
        self.assertEqual(len(report['outcomes']), 4)
        self.assertTrue(report['checks']['token_limit'])
        self.assertTrue(report['process_reaped'])

    def test_invalid_vectors_cannot_pass_and_cleanup_remains_required(self):
        report = run(Runtime(Engine, True, startup_timeout=5))
        self.assertFalse(report['passed'])
        self.assertTrue(report['process_reaped'])
        self.assertTrue(report['server_stopped'])

    def test_cli_rejects_wrong_candidate_before_any_docker_operation(self):
        with patch('sys.argv', ['check', '--profile', 'http']), \
                patch('scripts.check_inference_container.command') as docker:
            with self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
            docker.assert_not_called()


if __name__ == '__main__':
    unittest.main()
