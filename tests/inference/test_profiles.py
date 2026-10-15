"""Ensure failed and incomplete benchmarks cannot be reported as passing."""
import unittest
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

from scripts.check_inference_container import main, profile_requests, review_rows


class ProfileTests(unittest.TestCase):
    def test_outer_timeout_retains_failure_and_removes_only_owned_container(self):
        directory = Path(__file__).resolve().parents[2] / 'output/inference-tests'
        directory.mkdir(parents=True, exist_ok=True)
        config = {'Image': 'test-image', 'Config': {'User': '65532:65532'}, 'Mounts': [],
                  'HostConfig': {'Memory': 512 * 1024**2, 'MemorySwap': 512 * 1024**2,
                    'NanoCpus': 2000000000, 'PidsLimit': 128, 'NetworkMode': 'none',
                    'ReadonlyRootfs': True, 'CapDrop': ['ALL'], 'SecurityOpt': ['no-new-privileges']}}
        calls = []
        def command(*args):
            calls.append(args)
            if args[0] == 'create':
                return 'owned-test-id'
            if args[0] == 'inspect':
                if len([c for c in calls if c[0] == 'inspect']) == 1:
                    return json.dumps([config])
                return json.dumps([{'State': {'ExitCode': 137, 'OOMKilled': False}}])
            return ''
        process = MagicMock()
        process.returncode = 1
        process.communicate.side_effect = [subprocess.TimeoutExpired('docker', 300), ('', '')]
        with tempfile.TemporaryDirectory(dir=directory) as tmp:
            with patch('scripts.check_inference_container.ROOT', Path(tmp)), \
                 patch('scripts.check_inference_container.command', side_effect=command), \
                 patch('scripts.check_inference_container.subprocess.Popen', return_value=process), \
                 patch('sys.argv', ['check', '--candidate', '--controls']), patch('builtins.print'):
                with self.assertRaises(SystemExit):
                    main()
            report = json.loads((Path(tmp) / 'output/inference-results/patched/controls.json').read_text())
            self.assertFalse(report['passed'])
            self.assertTrue(report['outer_timeout'])
        self.assertIn(('kill', 'owned-test-id'), calls)
        self.assertEqual(calls[-1], ('rm', '-f', 'owned-test-id'))

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
