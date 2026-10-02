import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.audit_extractor_packages import check


class ExtractorAuditTests(unittest.TestCase):
    def test_successful_empty_advisory_feed(self):
        with patch('scripts.audit_extractor_packages.urlopen',
                   return_value=io.BytesIO(b'{"vulnerabilities": []}')):
            result = check({'name': 'example', 'version': '1.0'})
        self.assertEqual(result['vulnerabilities'], [])
        self.assertNotIn('error', result)

    def test_missing_field_is_not_clean(self):
        for payload in (b'{}', b'{"vulnerabilities": null}'):
            with patch('scripts.audit_extractor_packages.urlopen',
                       return_value=io.BytesIO(payload)):
                result = check({'name': 'example', 'version': '1.0'})
            self.assertIn('error', result)
            self.assertNotIn('vulnerabilities', result)

    def test_network_failure_is_not_clean(self):
        with patch('scripts.audit_extractor_packages.urlopen', side_effect=TimeoutError):
            result = check({'name': 'example', 'version': '1.0'})
        self.assertEqual(result['error'], 'TimeoutError')

    def test_committed_lock_matches_inventory(self):
        root = Path(__file__).resolve().parents[2] / 'services/worker'
        packages = json.loads((root / 'extraction-packages.json').read_text())['packages']
        expected = {f"{p['name']}=={p['version']} --hash=sha256:{p['sha256']}" for p in packages}
        actual = {line for line in (root / 'requirements-extraction.lock').read_text().splitlines()
                  if line and not line.startswith('#')}
        self.assertEqual(actual, expected)
