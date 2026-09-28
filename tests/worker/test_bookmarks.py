import unittest

from services.worker.bookmarks import extract_bookmark, normalize_url, MAX_HTML_BYTES


class BookmarkTests(unittest.TestCase):
    def test_normalization_preserves_query_fragment(self):
        self.assertEqual(normalize_url("HTTPS://Example.COM:443/read?a=1#part"),
                         "https://example.com/read?a=1#part")

    def test_invalid_urls(self):
        for url in ["javascript:alert(1)", "file:///x", "https://u:p@example.com",
                    "http://127.0.0.1", "http://[::1]", "http://169.254.169.254",
                    "https://localhost", "https://box.local", "https://a\nb.com",
                    "https://example.com:bad", "https://example.com\\@evil.com", ""]:
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "INVALID_URL"):
                normalize_url(url)

    def test_article_and_metadata(self):
        html = b'<head><title>Guide &amp; tips</title><meta name="author" content="Ada"></head><nav>Menu</nav><main><h1>Camping</h1><p>Pack a <b>waterproof</b> jacket.</p></main><footer>Legal</footer>'
        result = extract_bookmark("https://example.com", html)
        self.assertEqual(result["text"], "Camping\nPack a waterproof jacket.")
        self.assertEqual(result["metadata"], {"title": "Guide & tips", "author": "Ada"})
        self.assertEqual(result["status"], "extracted")
        self.assertEqual(result["extraction_method"], "main_article")
        self.assertEqual([result["text"][p["start"]:p["end"]] for p in result["passages"]],
                         ["Camping", "Pack a waterproof jacket."])

    def test_untrusted_html_is_plain_text(self):
        result = extract_bookmark("https://example.com", b'<main><script>steal()</script><style>x</style><p hidden>secret</p><iframe>bad</iframe><p>&lt;script&gt;literal&lt;/script&gt;</p></main>')
        self.assertEqual(result["text"], "<script>literal</script>")
        # Consumers must render as text, not innerHTML, even after extraction.

    def test_metadata_only_video(self):
        result = extract_bookmark("https://www.instagram.com/reel/test/", b'<meta property="og:title" content="Game clip"><script>player()</script>')
        self.assertEqual(result["status"], "metadata-only")
        self.assertEqual(result["text"], "")

    def test_missing_content_preserves_notes(self):
        result = extract_bookmark("https://example.com/private", notes="My reminder")
        self.assertEqual(result["notes"], "My reminder")
        self.assertEqual(result["reason"], "NO_CONTENT")

    def test_bounded_and_unsupported_content(self):
        for html, kind, reason in [(b'x' * (MAX_HTML_BYTES + 1), "text/html", "CONTENT_TOO_LARGE"),
                                  (b'pdf', "application/pdf", "UNSUPPORTED_CONTENT_TYPE"),
                                  (b'\xff', "text/html", "UNSUPPORTED_ENCODING"),
                                  (b'\x00', "text/html", "INVALID_TEXT"),
                                  (b'<div>' * 257, "text/html", "HTML_TOO_DEEP")]:
            with self.subTest(reason=reason):
                result = extract_bookmark("https://example.com", html, content_type=kind)
                self.assertEqual(result["reason"], reason)
                self.assertEqual(result["text"], "")

    def test_malformed_html_and_stability(self):
        html = '<main><p>Café & tea<p>Next'.encode()
        first = extract_bookmark("https://example.com", html)
        self.assertEqual(first, extract_bookmark("https://example.com", html))
        self.assertEqual(first["text"], "Café & tea\nNext")

    def test_body_fallback_and_no_guessed_fields(self):
        result = extract_bookmark("https://example.com", b'<div>Game release notes</div>')
        self.assertEqual(result["metadata"], {})
        self.assertEqual(result["extraction_method"], "body_fallback")
        self.assertEqual(result["text"], "Game release notes")

    def test_empty_page(self):
        self.assertEqual(extract_bookmark("https://example.com", b' ')["reason"], "NO_READABLE_TEXT")


if __name__ == "__main__":
    unittest.main()
