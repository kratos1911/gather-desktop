import base64
import hashlib
import json
from pathlib import Path
import unittest

from services.worker.text_processing import (
    CHUNK_CHARACTERS, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, MAX_SOURCE_BYTES,
    OVERLAP_CHARACTERS, process_request, serialize_response,
)


def request(raw: bytes, **changes) -> bytes:
    value = {"version": 1, "request_id": "test-004", "format": "txt",
             "content_base64": base64.b64encode(raw).decode("ascii")}
    value.update(changes)
    return json.dumps(value).encode("utf-8")


class TextProcessingTests(unittest.TestCase):
    def assert_coverage(self, text, result):
        self.assertEqual(result["status"], "processed")
        doc = result["document"]
        self.assertEqual(doc["source_sha256"], hashlib.sha256(text.encode("utf-8")).hexdigest())
        chunks = doc["chunks"]
        self.assertEqual(chunks[0]["start"], 0)
        self.assertEqual(chunks[-1]["end"], len(text))
        rebuilt = chunks[0]["text"]
        for index, chunk in enumerate(chunks):
            self.assertEqual(chunk["text"], text[chunk["start"]:chunk["end"]])
            self.assertLessEqual(len(chunk["text"]), CHUNK_CHARACTERS)
            if index:
                previous = chunks[index - 1]
                self.assertEqual(previous["end"] - chunk["start"], OVERLAP_CHARACTERS)
                self.assertGreater(chunk["start"], previous["start"])
                rebuilt += chunk["text"][OVERLAP_CHARACTERS:]
        self.assertEqual(rebuilt, text)
        self.assertEqual(len({chunk["id"] for chunk in chunks}), len(chunks))
        self.assertLessEqual(len(serialize_response(result)), MAX_RESPONSE_BYTES)

    def test_synthetic_fixtures(self):
        for path in (Path(__file__).parents[1] / "fixtures/text").iterdir():
            with self.subTest(format=path.suffix):
                raw = path.read_bytes()
                self.assert_coverage(raw.decode("utf-8"), process_request(request(raw, format=path.suffix[1:])))

    def test_unicode_bom_crlf_and_markdown_are_preserved(self):
        text = "\ufeff# Café 😀\r\nनमस्ते\r\n\r\n[link](https://example.invalid)\tfin\n" * 120
        self.assert_coverage(text, process_request(request(text.encode("utf-8"), format="md")))

    def test_boundary_lengths_and_unbroken_text(self):
        for length in (1, 1023, 1024, 1025, 1920, 1921, MAX_SOURCE_BYTES):
            with self.subTest(length=length):
                self.assert_coverage("a" * length, process_request(request(b"a" * length)))

    def test_prefers_paragraph_boundary(self):
        text = "a" * 600 + "\n\n" + "b" * 900
        result = process_request(request(text.encode()))
        self.assertEqual(result["document"]["chunks"][0]["end"], 602)
        self.assert_coverage(text, result)

    def test_retry_and_request_id_do_not_change_document_identity(self):
        payload = request(b"same content")
        first = process_request(payload)
        self.assertEqual(first, process_request(payload))
        self.assertEqual(first["document"], process_request(request(b"same content", request_id="retry"))["document"])
        for changed in (request(b"changed"), request(b"same content", format="md")):
            self.assertNotEqual(first["document"]["chunks"][0]["id"], process_request(changed)["document"]["chunks"][0]["id"])

    def test_empty_content(self):
        for raw in (b"", b" \t\r\n", "\ufeff  ".encode()):
            self.assertEqual(process_request(request(raw))["code"], "EMPTY_CONTENT")

    def test_encoding_and_binary_rejection(self):
        for raw, code in ((b"\xff", "UNSUPPORTED_ENCODING"), (b"abc\x00", "BINARY_CONTENT"),
                          ("abc\x85".encode(), "BINARY_CONTENT")):
            self.assertEqual(process_request(request(raw))["code"], code)

    def test_strict_request_schema(self):
        cases = [b"not-json", b"[]", b"null", b"\xff", b"[" * 2000,
                 request(b"x", version=True), request(b"x", version=2),
                 request(b"x", request_id="../private"), request(b"x", path="private.txt"),
                 b'{"version":1,"version":1}']
        for payload in cases:
            with self.subTest(payload=payload[:30]):
                self.assertEqual(process_request(payload)["code"], "INVALID_REQUEST")

    def test_format_and_base64_rejection(self):
        self.assertEqual(process_request(request(b"x", format="pdf"))["code"], "UNSUPPORTED_FORMAT")
        for encoded in (None, 123, "!!!!", "é", "eA==\n"):
            self.assertEqual(process_request(request(b"x", content_base64=encoded))["code"], "INVALID_BASE64")

    def test_size_limits(self):
        self.assertEqual(process_request(b"x" * (MAX_REQUEST_BYTES + 1))["code"], "REQUEST_TOO_LARGE")
        self.assertEqual(process_request(request(b"x" * (MAX_SOURCE_BYTES + 1)))["code"], "SOURCE_TOO_LARGE")

    def test_response_bound_with_escaping(self):
        text = ('"\\\t' * (MAX_SOURCE_BYTES // 3))
        self.assert_coverage(text, process_request(request(text.encode())))

    def test_errors_do_not_echo_content_and_next_request_recovers(self):
        result = process_request(request(b"private-content\x00"))
        self.assertNotIn("private-content", serialize_response(result).decode())
        self.assertFalse(result["retryable"])
        self.assertEqual(process_request(request(b"valid"))["status"], "processed")


if __name__ == "__main__":
    unittest.main()
