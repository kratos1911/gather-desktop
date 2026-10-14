import unittest

from services.inference.chunking import chunk_document


class ChunkingTests(unittest.TestCase):
    def test_unicode_coverage_offsets_and_budgets(self):
        text = ('Museum notes. नमस्ते 🙂\n\n' * 120) + 'last evidence'
        count = lambda s: len(s.encode('utf-8')) + 1
        chunks = chunk_document(text, count)
        covered = 0
        for chunk in chunks:
            self.assertLessEqual(chunk['start'], covered)
            self.assertGreater(chunk['end'], covered)
            self.assertEqual(chunk['text'], text[chunk['start']:chunk['end']])
            self.assertLessEqual(count(chunk['text']), 512)
            covered = chunk['end']
        self.assertEqual(covered, len(text))
        self.assertEqual(chunks, chunk_document(text, count))

    def test_byte_limit_even_when_token_count_is_small(self):
        chunks = chunk_document('🙂' * 3000, lambda _: 2)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c['text'].encode('utf-8')) <= 8192 for c in chunks))

    def test_rejects_invalid_count_or_oversized_source(self):
        for counter in (lambda _: 0, lambda _: True, lambda _: 513):
            with self.assertRaises(ValueError):
                chunk_document('hello', counter)
        with self.assertRaises(ValueError):
            chunk_document('x' * 65537, len)

    def test_long_blank_prefix_is_explicitly_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsearchable_whitespace_chunk'):
            chunk_document(' ' * 10000 + 'evidence', lambda _: 2)
