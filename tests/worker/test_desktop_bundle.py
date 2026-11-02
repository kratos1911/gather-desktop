"""Synthetic byte-identity checks; not Windows installation evidence."""
import hashlib
import unittest

from scripts.verify_desktop_bundle import MARKER, NSIS_MARKER, verify_bytes


class DesktopBundleTests(unittest.TestCase):
    def setUp(self):
        self.source = b"MZ" + bytes(range(128)) + MARKER + b"\0fixture executable"
        self.packaged = self.source.replace(MARKER, NSIS_MARKER)
        self.expected = hashlib.sha256(self.source).hexdigest()

    def test_exact_nsis_marker_patch(self):
        result = verify_bytes(self.source, self.packaged, self.expected.upper())
        self.assertTrue(result["verified"])
        self.assertEqual(result["installed_sha256"], hashlib.sha256(self.packaged).hexdigest())
        self.assertFalse(result["signing_or_clean_machine_acceptance"])

    def test_modified_code_rejected(self):
        changed = self.packaged[:8] + b"X" + self.packaged[9:]
        with self.assertRaisesRegex(ValueError, "installed_executable_mismatch"):
            verify_bytes(self.source, changed, self.expected)

    def test_source_must_match_recorded_candidate(self):
        with self.assertRaisesRegex(ValueError, "source_differs_from_verified_candidate"):
            verify_bytes(self.source + b"changed", self.packaged, self.expected)

    def test_raw_unbundled_executable_is_not_nsis_proof(self):
        with self.assertRaisesRegex(ValueError, "installed_executable_mismatch"):
            verify_bytes(self.source, self.source, self.expected)

    def test_ambiguous_marker_rejected(self):
        source = self.source + MARKER
        with self.assertRaisesRegex(ValueError, "unexpected_tauri_bundle_marker"):
            verify_bytes(source, source.replace(MARKER, NSIS_MARKER), hashlib.sha256(source).hexdigest())

    def test_missing_marker_or_invalid_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_verified_source_hash"):
            verify_bytes(self.source, self.packaged, "not a hash")
        source = b"MZwithout a packaging marker"
        with self.assertRaisesRegex(ValueError, "unexpected_tauri_bundle_marker"):
            verify_bytes(source, source, hashlib.sha256(source).hexdigest())

    def test_non_windows_or_truncated_payload_rejected(self):
        source = b"NO" + self.source[2:]
        with self.assertRaisesRegex(ValueError, "unexpected_tauri_bundle_marker"):
            verify_bytes(source, source.replace(MARKER, NSIS_MARKER), hashlib.sha256(source).hexdigest())
        with self.assertRaisesRegex(ValueError, "installed_executable_mismatch"):
            verify_bytes(self.source, self.packaged[:-1], self.expected)


if __name__ == "__main__":
    unittest.main()
