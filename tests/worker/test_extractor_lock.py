"""The lock generator must fail closed when resolution drifts or omits hashes."""
import copy
import unittest

from scripts.lock_extractor import lock_from_report


class ExtractorLockTests(unittest.TestCase):
    def setUp(self):
        self.report = {'install': [{
            'metadata': {'name': 'Example_Package', 'version': '1.0',
                         'license_expression': 'MIT'},
            'download_info': {'url': 'https://files.pythonhosted.org/example.whl',
                              'archive_info': {'hashes': {'sha256': 'a' * 64}}},
        }]}
        self.expected = {'example-package': '1.0'}

    def test_normalized_exact_version_and_artifact(self):
        rows, inventory = lock_from_report(self.report, self.expected)
        self.assertEqual(rows, ['example-package==1.0 --hash=sha256:' + 'a' * 64])
        self.assertEqual(inventory[0]['license_expression'], 'MIT')

    def test_resolution_drift_and_omission_rejected(self):
        for expected in ({'example-package': '2.0'},
                         {'example-package': '1.0', 'missing': '1.0'}):
            with self.assertRaises(ValueError):
                lock_from_report(self.report, expected)

    def test_duplicate_and_invalid_hash_rejected(self):
        duplicate = copy.deepcopy(self.report)
        duplicate['install'] *= 2
        with self.assertRaises(ValueError):
            lock_from_report(duplicate, self.expected)
        self.report['install'][0]['download_info']['archive_info']['hashes']['sha256'] = 'invalid'
        with self.assertRaises(ValueError):
            lock_from_report(self.report, self.expected)

    def test_source_builds_and_unexpected_hosts_rejected(self):
        for url in ('https://files.pythonhosted.org/example.tar.gz',
                    'https://untrusted.invalid/example.whl'):
            self.report['install'][0]['download_info']['url'] = url
            with self.assertRaises(ValueError):
                lock_from_report(self.report, self.expected)
