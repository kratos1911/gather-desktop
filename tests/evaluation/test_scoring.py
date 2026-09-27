import copy
import json
import math
import unittest

from scripts.prepare_text_evaluation import CORPUS, prepare
from scripts.score_text_evaluation import index_hash, lexical_run, score_run, tokenize


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.index = {"corpus_version": "test", "corpus_sha256": "fixture",
                      "documents": [{"id": "a", "chunks": [{"id": f"a{i}", "text": "alpha"} for i in range(6)]},
                                    {"id": "b", "chunks": [{"id": "b0", "text": "beta"}]}]}
        self.labels = {"corpus_version": "test", "corpus_sha256": "fixture", "queries": [
            {"id": "q1", "category": "multiple_sources", "evidence": [
                {"document_id": "a", "start": 0, "end": 2, "acceptable_chunk_ids": ["a1", "a2"]},
                {"document_id": "b", "start": 0, "end": 2, "acceptable_chunk_ids": ["b0"]}]},
            {"id": "q2", "category": "absent", "evidence": []}]}
        self.run = {"schema_version": 1, "corpus_version": "test", "corpus_sha256": "fixture",
                    "index_sha256": index_hash(self.index), "retriever": "hand-calculated-test",
                    "results": [{"id": "q1", "hits": []}, {"id": "q2", "hits": []}]}

    def hits(self, *chunk_ids):
        return [{"document_id": c[0], "chunk_id": c} for c in chunk_ids]

    def score(self):
        return score_run(self.index, self.labels, self.run)

    def test_partial_recall_and_absent_excluded_from_denominator(self):
        self.run["results"][0]["hits"] = self.hits("a1")
        summary = self.score()["summary"]
        self.assertEqual(summary["document_recall_at_5"], 0.5)
        self.assertEqual(summary["evidence_recall_at_5"], 0.5)
        self.assertEqual(summary["document_mrr_at_5"], 1)
        self.assertEqual(summary["answerable"], 1)
        self.assertEqual(summary["absent"], 1)

    def test_document_dedup_before_top_five_and_chunk_cutoff(self):
        self.run["results"][0]["hits"] = self.hits("a0", "a1", "a2", "a3", "a4", "a5", "b0")
        summary = self.score()["summary"]
        self.assertEqual(summary["document_recall_at_5"], 1)
        self.assertEqual(summary["evidence_recall_at_5"], 0.5)

    def test_wrong_passage_is_not_evidence(self):
        self.run["results"][0]["hits"] = self.hits("a0")
        row = self.score()["queries"][0]
        self.assertEqual(row["document_recall_at_5"], 0.5)
        self.assertEqual(row["evidence_recall_at_5"], 0)
        self.assertEqual(len(row["missing_evidence"]), 2)

    def test_sixth_unique_document_receives_no_top_five_credit(self):
        for letter in ("c", "d", "e", "f"):
            self.index["documents"].append({"id": letter, "chunks": [{"id": letter + "0", "text": "noise"}]})
        self.run["index_sha256"] = index_hash(self.index)
        self.labels["queries"][0]["evidence"] = self.labels["queries"][0]["evidence"][:1]
        self.run["results"][0]["hits"] = self.hits("b0", "c0", "d0", "e0", "f0", "a1")
        summary = self.score()["summary"]
        self.assertEqual(summary["document_recall_at_5"], 0)
        self.assertEqual(summary["document_mrr_at_5"], 0)
        self.assertEqual(summary["evidence_recall_at_5"], 0)

    def test_overlap_does_not_double_count_and_mrr_uses_rank(self):
        self.labels["queries"][0]["evidence"] = self.labels["queries"][0]["evidence"][:1]
        self.run["results"][0]["hits"] = self.hits("b0", "a1", "a2")
        summary = self.score()["summary"]
        self.assertEqual(summary["document_mrr_at_5"], 0.5)
        self.assertEqual(summary["evidence_recall_at_5"], 1)

    def test_absent_candidates_are_not_answer_claims(self):
        self.run["results"][1]["hits"] = self.hits("b0")
        absent = self.score()["categories"]["absent"]
        self.assertEqual(absent["absent_queries_returning_candidates"], 1)
        self.assertIsNone(absent["document_recall_at_5"])
        self.assertIsNone(absent["unsupported_answer_rate"])

    def test_empty_complete_run_is_valid_zero_recall(self):
        self.assertEqual(self.score()["summary"]["document_recall_at_5"], 0)

    def test_missing_duplicate_and_unknown_queries_rejected(self):
        for rows in (self.run["results"][:1], self.run["results"] * 2,
                     self.run["results"] + [{"id": "unknown", "hits": []}]):
            bad = copy.deepcopy(self.run)
            bad["results"] = rows
            with self.assertRaises(ValueError):
                score_run(self.index, self.labels, bad)

    def test_unknown_mismatched_and_duplicate_chunks_rejected(self):
        cases = [self.hits("a1", "a1"), self.hits("z0"),
                 [{"document_id": "b", "chunk_id": "a1"}], self.hits("a999")]
        for hits in cases:
            self.run["results"][0]["hits"] = hits
            with self.assertRaises(ValueError):
                self.score()

    def test_stale_corpus_and_processing_results_rejected(self):
        for field in ("corpus_version", "corpus_sha256", "index_sha256"):
            bad = copy.deepcopy(self.run)
            bad[field] = "stale"
            with self.assertRaises(ValueError):
                score_run(self.index, self.labels, bad)

    def test_invalid_scores_and_schema_rejected(self):
        for value in (math.nan, math.inf, True, "1"):
            self.run["results"][0]["hits"] = [{"document_id": "a", "chunk_id": "a0", "score": value}]
            with self.assertRaises(ValueError):
                self.score()
        for bad in ({}, {**self.run, "schema_version": True}, {**self.run, "results": None}):
            with self.assertRaises(ValueError):
                score_run(self.index, self.labels, bad)

    def test_identifier_tokenization_and_case(self):
        self.assertEqual(tokenize("LAMP-450, lamp-450; café!"), ["lamp-450", "lamp-450", "café"])

    def test_lexical_ranking_without_labels_and_oov_query(self):
        index = {"corpus_version": "test", "corpus_sha256": "fixture", "documents": [
            {"id": "a", "chunks": [{"id": "a0", "text": "desk lamp lamp"}]},
            {"id": "b", "chunks": [{"id": "b0", "text": "laptop computer"}]}]}
        queries = {"corpus_version": "test", "corpus_sha256": "fixture", "queries": [
            {"id": "q1", "text": "LAMP"}, {"id": "q2", "text": "unseenword"}]}
        result = lexical_run(index, queries)
        self.assertEqual(result["results"][0]["hits"][0]["document_id"], "a")
        self.assertEqual(result["results"][1]["hits"], [])
        self.assertEqual(result, lexical_run(index, queries))

    def test_real_corpus_run_is_complete_and_deterministic(self):
        data = prepare(json.loads(CORPUS.read_text(encoding="utf-8")))
        run = lexical_run(data["index"], data["queries"])
        report = score_run(data["index"], data["labels"], run)
        self.assertEqual(report["summary"]["queries"], 40)
        self.assertEqual(report["summary"]["answerable"], 35)
        self.assertEqual(run, lexical_run(data["index"], data["queries"]))


if __name__ == "__main__":
    unittest.main()
