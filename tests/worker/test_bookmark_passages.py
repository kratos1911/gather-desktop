import unittest

from services.worker.bookmark_passages import prepare_bookmark
from scripts.score_text_evaluation import lexical_run


class BookmarkPassageTests(unittest.TestCase):
    def test_field_offsets_and_evidence(self):
        doc = prepare_bookmark("a", "https://example.com", b'<title>Trip</title><main><p>Rain jacket</p></main>', notes="Bring boots")
        for chunk in doc["chunks"]:
            self.assertEqual(chunk["text"], doc["fields"][chunk["field"]][chunk["start"]:chunk["end"]])
        self.assertEqual({c["evidence_type"] for c in doc["chunks"]}, {"url", "notes", "page_text", "metadata"})
        self.assertFalse(doc["semantic_ready"])

    def test_stable_retry_and_changed_revision(self):
        args = ("a", "https://example.com", b'<p>Rain jacket</p>')
        original = prepare_bookmark(*args)
        self.assertEqual(original, prepare_bookmark(*args))
        changed = prepare_bookmark(*args, notes="Updated")
        self.assertNotEqual(original["revision"], changed["revision"])
        self.assertFalse({c["id"] for c in original["chunks"]} & {c["id"] for c in changed["chunks"]})

    def test_source_identity_prevents_collisions(self):
        a = prepare_bookmark("a", "https://example.com", notes="same")
        b = prepare_bookmark("b", "https://example.com", notes="same")
        self.assertFalse({c["id"] for c in a["chunks"]} & {c["id"] for c in b["chunks"]})

    def test_failed_extraction_keeps_searchable_notes(self):
        doc = prepare_bookmark("a", "https://example.com", b'\xff', notes="Tournament schedule")
        self.assertEqual(doc["extraction_reason"], "UNSUPPORTED_ENCODING")
        self.assertEqual({c["field"] for c in doc["chunks"]}, {"url", "notes"})

    def test_metadata_only_is_not_video_understanding(self):
        doc = prepare_bookmark("a", "https://example.com/video", b'<meta property="og:title" content="Surfing">')
        self.assertEqual(doc["extraction_status"], "metadata-only")
        self.assertNotIn("page_text", {c["field"] for c in doc["chunks"]})

    def test_late_passage_and_keyword_result_provenance(self):
        a = prepare_bookmark("hiking", "https://example.com/trip", ('<main>' + 'Ordinary travel advice. ' * 150 + '<p>waterproof jacket</p></main>').encode())
        b = prepare_bookmark("gaming", "https://example.com/game", b'<p>Tournament schedule</p>')
        index = {"corpus_version": "bookmark-test", "corpus_sha256": "synthetic", "documents": [a, b]}
        queries = {"corpus_version": "bookmark-test", "corpus_sha256": "synthetic", "queries": [{"id": "q", "text": "waterproof jacket"}]}
        hits = lexical_run(index, queries)["results"][0]["hits"]
        self.assertEqual(hits[0]["document_id"], "hiking")
        chunk = next(c for c in a["chunks"] if c["id"] == hits[0]["chunk_id"])
        self.assertEqual(chunk["field"], "page_text")
        self.assertGreater(chunk["start"], 1024)
        self.assertIn("waterproof jacket", chunk["text"])
        self.assertEqual(chunk["url"], "https://example.com/trip")

    def test_reject_invalid_id_and_control_text(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_ID"):
            prepare_bookmark("../bad", "https://example.com")
        with self.assertRaisesRegex(ValueError, "BINARY_CONTENT"):
            prepare_bookmark("a", "https://example.com", notes="bad\x00note")


if __name__ == "__main__":
    unittest.main()
