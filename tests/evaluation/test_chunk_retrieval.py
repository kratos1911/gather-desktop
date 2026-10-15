import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.evaluate_chunk_retrieval import prepare_layout, coverage_report, span_covered, boundary_corpus
from scripts.prepare_text_evaluation import load_corpus, prepare, corpus_hash
from scripts.score_text_evaluation import index_hash


class ChunkEvaluationTests(unittest.TestCase):
    def test_frozen_boundary_source_query_and_label_changes_are_rejected(self):
        corpus = boundary_corpus()
        directory = Path(__file__).resolve().parents[2] / 'output/evaluation-tests'
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as tmp:
            path = Path(tmp) / 'boundary.json'
            path.with_suffix('.freeze.json').write_text(json.dumps({'corpus_sha256': corpus_hash(corpus)}))
            for collection, field in (('documents', 'text'), ('queries', 'text'), ('queries', 'expected')):
                changed = copy.deepcopy(corpus)
                if field == 'expected':
                    changed[collection][0][field][0]['quote'] += ' changed'
                else:
                    changed[collection][0][field] += ' changed'
                path.write_text(json.dumps(changed), encoding='utf-8')
                with patch('scripts.evaluate_chunk_retrieval.FIXTURE', path):
                    with self.assertRaisesRegex(ValueError, 'Boundary corpus changed'):
                        boundary_corpus()

    def test_legacy_reproduces_frozen_v2_index_and_labels(self):
        corpus = load_corpus('text-v2')
        original = prepare(corpus)
        paired = prepare_layout(corpus, 'legacy', len)
        self.assertEqual(original['index'], paired['index'])
        self.assertEqual(original['labels'], paired['labels'])
        self.assertEqual(original['queries'], paired['queries'])

    def test_split_evidence_is_not_relabelled_or_dropped(self):
        text = 'a' * 480 + 'Unique relevant span ' * 9 + 'z' * 500
        quote = text[400:680]
        corpus = {'version': 'test', 'documents': [{'id': 'd', 'text': text, 'format': 'txt'}],
                  'queries': [{'id': 'q', 'text': 'find relevant span', 'category': 'paraphrase',
                               'expected': [{'document_id': 'd', 'quote': quote}]}]}
        prepared = prepare_layout(corpus, 'token512', len)
        evidence = prepared['labels']['queries'][0]['evidence'][0]
        self.assertEqual(evidence['quote'], quote)
        self.assertEqual((evidence['start'], evidence['end']), (400, 680))
        self.assertEqual(evidence['acceptable_chunk_ids'], [])
        index = prepared['index']
        run = {'schema_version': 1, 'corpus_version': 'test', 'corpus_sha256': index['corpus_sha256'],
               'index_sha256': index_hash(index), 'retriever': 'test', 'results': [{'id': 'q',
               'hits': [{'document_id': 'd', 'chunk_id': c['id']} for c in index['documents'][0]['chunks']]}]}
        report = coverage_report(prepared, run)
        self.assertEqual(report['summary']['evidence_recall_at_5'], 0)
        self.assertEqual(report['summary']['union_evidence_recall_at_5'], 1)
        self.assertEqual(len(report['structurally_uncontained']), 1)

    def test_union_requires_continuous_same_source_coverage(self):
        evidence = {'document_id': 'd', 'start': 10, 'end': 40}
        chunks = {('d', 'a'): {'start': 0, 'end': 20}, ('d', 'b'): {'start': 21, 'end': 45},
                  ('other', 'c'): {'start': 0, 'end': 50}}
        hits = [{'document_id': d, 'chunk_id': c} for d, c in chunks]
        self.assertFalse(span_covered(evidence, hits, chunks))
        chunks[('d', 'b')]['start'] = 20
        self.assertTrue(span_covered(evidence, hits, chunks))
        self.assertFalse(span_covered(evidence, hits[:1] * 2, chunks))

    def test_layouts_preserve_evidence_offsets_and_reject_unknown_policy(self):
        corpus = load_corpus('text-v2')
        original = copy.deepcopy(corpus)
        legacy = prepare_layout(corpus, 'legacy', lambda t: max(1, len(t)//6))
        candidate = prepare_layout(corpus, 'token512', lambda t: max(1, len(t)//6))
        for a, b in zip(legacy['labels']['queries'], candidate['labels']['queries']):
            for x, y in zip(a['evidence'], b['evidence']):
                for key in ('document_id', 'quote', 'start', 'end'):
                    self.assertEqual(x[key], y[key])
        self.assertEqual(corpus, original)
        with self.assertRaises(ValueError):
            prepare_layout(corpus, 'unknown', len)


if __name__ == '__main__':
    unittest.main()
