from dataclasses import replace
import hashlib
import unittest

from services.worker.search_context import assemble_context, Snapshot, Passage, Hit


def snapshot(source='s', text='abcdefghijkl', ranges=((0, 5), (3, 9), (7, 12))):
    return Snapshot('owner', source, 'v1', hashlib.sha256(text.encode()).hexdigest(), text,
                    tuple(Passage(str(i), start, end) for i, (start, end) in enumerate(ranges)))


def hit(source='s', passage='1'):
    return Hit('owner', source, 'v1', passage)


class ContextTests(unittest.TestCase):
    def test_overlap_merged_once_with_exact_citation(self):
        source = snapshot()
        result = assemble_context('owner', [hit()], [source])
        window = result['windows'][0]
        self.assertEqual(window['text'], source.text)
        self.assertEqual((window['start'], window['end'], window['utf8_bytes']), (0, 12, 12))
        self.assertEqual(window['version_id'], 'v1')
        self.assertEqual(window['seed_passage_id'], '1')

    def test_source_diversity_preserves_first_hit_order(self):
        sources = [snapshot(str(i)) for i in range(6)]
        hits = [hit('0'), hit('0', '2')] + [hit(str(i)) for i in range(1, 6)]
        result = assemble_context('owner', hits, sources)
        self.assertEqual([w['source_id'] for w in result['windows']], list('01234'))
        self.assertEqual(result['omitted_sources'], [{'source_id': '5', 'reason': 'source_limit'}])

    def test_does_not_bridge_gap_or_expand_two_hops(self):
        source = snapshot(ranges=((0, 2), (3, 5), (5, 8), (8, 12)))
        window = assemble_context('owner', [hit()], [source])['windows'][0]
        self.assertEqual((window['start'], window['end']), (3, 8))
        self.assertEqual(window['skipped_neighbors'], [{'passage_id': '0', 'reason': 'gap'}])

    def test_unicode_byte_limit_omits_whole_neighbor(self):
        source = snapshot(text='🙂' * 2400, ranges=((0, 1200), (1100, 2400)))
        result = assemble_context('owner', [hit(passage='0')], [source])
        window = result['windows'][0]
        self.assertEqual(window['text'], source.text[:1200])
        self.assertEqual(window['utf8_bytes'], 4800)
        self.assertEqual(window['skipped_neighbors'][0]['reason'], 'window_byte_limit')

    def test_reserves_seed_budgets_and_reports_omission(self):
        sources = [snapshot(str(i), 'x' * 8000, ((0, 8000),)) for i in range(5)]
        result = assemble_context('owner', [hit(str(i), '0') for i in range(5)], sources)
        self.assertEqual(result['utf8_bytes'], 32000)
        self.assertEqual(len(result['windows']), 4)
        self.assertEqual(result['omitted_sources'][0]['reason'], 'total_byte_limit')

    def test_expansion_cannot_spend_reserved_seed_budget(self):
        first = snapshot('0', 'x' * 8100, ((0, 7000), (6900, 8100)))
        sources = [first] + [snapshot(str(i), 'x' * 6400, ((0, 6400),)) for i in range(1, 5)]
        result = assemble_context('owner', [hit(str(i), '0') for i in range(5)], sources)
        self.assertEqual(len(result['windows']), 5)
        self.assertEqual(result['utf8_bytes'], 32600)
        self.assertEqual(result['windows'][0]['skipped_neighbors'][0]['reason'], 'total_byte_limit')

    def test_rejects_owner_version_deletion_and_integrity_mismatch(self):
        source = snapshot()
        bad_sources = [replace(source, owner_id='other'), replace(source, version_id='v2'),
                       replace(source, deleted=True), replace(source, published=False),
                       replace(source, text='tampered')]
        for bad in bad_sources:
            with self.subTest(source=bad), self.assertRaises(ValueError):
                assemble_context('owner', [hit()], [bad])
        for bad in (replace(hit(), owner_id='other'), replace(hit(), passage_id='unknown')):
            with self.assertRaises(ValueError):
                assemble_context('owner', [bad], [source])
        with self.assertRaises(ValueError):
            assemble_context('owner', [hit()], [source, replace(source, version_id='v2')])

    def test_validates_all_candidates_before_returning(self):
        sources = [snapshot(str(i)) for i in range(6)]
        hits = [hit(str(i)) for i in range(6)]
        hits[-1] = replace(hits[-1], version_id='stale')
        with self.assertRaises(ValueError):
            assemble_context('owner', hits, sources)
        with self.assertRaises(ValueError):
            assemble_context('owner', [hit()] * 101, [snapshot()])

    def test_invalid_ranges_and_empty_results(self):
        source = snapshot()
        for passages in ((Passage('x', True, 5),), (Passage('x', 0, 99),),
                         (Passage('x', 4, 8), Passage('y', 0, 5))):
            with self.assertRaises(ValueError):
                assemble_context('owner', [], [replace(source, passages=passages)])
        self.assertEqual(assemble_context('owner', [], [])['windows'], [])
        with self.assertRaisesRegex(ValueError, '^invalid_source_text$'):
            assemble_context('owner', [], [replace(source, text='\ud800')])


if __name__ == '__main__':
    unittest.main()
