import unittest

from services.worker.extraction_adapters import crawl4ai_passages, ytdlp_passages

CONFIG = {"backend_version": "fixture-v1", "fetched_at": "2026-09-30T12:00:00Z"}


class ExtractionAdapterTests(unittest.TestCase):
    def page(self, **overrides):
        return {"success": True, "url": "https://example.com/final", "status_code": 200,
                "markdown": {"raw_markdown": "# Guide\nA **waterproof** jacket."}, **overrides}

    def test_markdown_is_preserved_and_redirect_recorded(self):
        doc = crawl4ai_passages("a", "https://example.com", self.page(status_code=302, redirected_status_code=200), **CONFIG)
        self.assertEqual(doc["fields"]["page_text"], "# Guide\nA **waterproof** jacket.")
        self.assertEqual(doc["provenance"]["final_url"], "https://example.com/final")
        self.assertFalse(doc["semantic_ready"])

    def test_failure_preserves_notes_without_leaking_error(self):
        doc = crawl4ai_passages("a", "https://example.com", {"success": False, "error_message": "private-token"}, notes="Reminder", **CONFIG)
        self.assertEqual(doc["extraction_reason"], "EXTRACTION_FAILED")
        self.assertEqual(doc["fields"]["notes"], "Reminder")
        self.assertNotIn("private-token", str(doc))

    def test_http_error_is_not_indexed(self):
        doc = crawl4ai_passages("a", "https://example.com", self.page(status_code=403), **CONFIG)
        self.assertEqual(doc["fields"]["page_text"], "")
        self.assertEqual(doc["extraction_reason"], "HTTP_UNAVAILABLE")

    def test_subtitle_timestamps_and_language(self):
        cues = [{"start": 1.5, "end": 3.0, "text": "Camping"}, {"start": 4, "end": 8, "text": "Rain jacket"}]
        doc = ytdlp_passages("a", "https://example.com/video", {"title": "Guide"}, cues=cues, language="en", automatic=True, **CONFIG)
        chunk = next(c for c in doc["chunks"] if c["evidence_type"] == "subtitle")
        self.assertEqual(chunk["cue_spans"][1]["start_seconds"], 4)
        self.assertEqual(chunk["language"], "en")
        self.assertTrue(chunk["automatic"])
        self.assertEqual(chunk["text"], "Camping\nRain jacket")

    def test_subtitle_url_is_not_a_transcript(self):
        doc = ytdlp_passages("a", "https://example.com/video", {"title": "Guide", "subtitles": {"en": [{"url": "https://example.com/subs"}]}}, **CONFIG)
        self.assertEqual(doc["extraction_status"], "metadata-only")
        self.assertFalse(any(c["evidence_type"] == "subtitle" for c in doc["chunks"]))

    def test_invalid_subtitles_and_playlists_rejected(self):
        for time in [float("nan"), -1, True]:
            with self.subTest(time=time), self.assertRaises(ValueError):
                ytdlp_passages("a", "https://example.com", {}, cues=[{"start": time, "end": 3, "text": "x"}], language="en", **CONFIG)
        with self.assertRaisesRegex(ValueError, "INVALID_VIDEO_RESULT"):
            ytdlp_passages("a", "https://example.com", {"_type": "playlist"}, **CONFIG)

    def test_bounds_and_provenance_validation(self):
        with self.assertRaises(ValueError):
            crawl4ai_passages("a", "https://example.com", self.page(markdown="x" * 65537), **CONFIG)
        with self.assertRaisesRegex(ValueError, "INVALID_FETCH_TIME"):
            crawl4ai_passages("a", "https://example.com", self.page(), backend_version="v1", fetched_at="yesterday")
        with self.assertRaises(ValueError):
            crawl4ai_passages("a", "https://example.com", self.page(url="http://127.0.0.1"), **CONFIG)

    def test_versions_and_timestamps_change_revision(self):
        a = crawl4ai_passages("a", "https://example.com", self.page(), **CONFIG)
        self.assertEqual(a, crawl4ai_passages("a", "https://example.com", self.page(), **CONFIG))
        b = crawl4ai_passages("a", "https://example.com", self.page(), **{**CONFIG, "backend_version": "v2"})
        self.assertNotEqual(a["revision"], b["revision"])


if __name__ == "__main__":
    unittest.main()
