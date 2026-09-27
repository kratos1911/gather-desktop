import copy
import math
import unittest

from scripts.evaluate_vectors import fuse_runs, vector_run
from scripts.score_text_evaluation import index_hash


class VectorTests(unittest.TestCase):
    def setUp(self):
        self.index = {"corpus_version": "test", "corpus_sha256": "fixture", "documents": [
            {"id": "a", "chunks": [{"id": "a0", "text": "one"}]},
            {"id": "b", "chunks": [{"id": "b0", "text": "two"}]},
            {"id": "c", "chunks": [{"id": "c0", "text": "three"}]}]}
        self.queries = {"corpus_version": "test", "corpus_sha256": "fixture", "queries": [{"id": "q", "text": "question"}]}
        self.config = {"provider": "test-only", "model": "hand-authored-vectors", "revision": "1",
                       "dimensions": 2, "query_template": "identity", "document_template": "identity",
                       "tokenizer_revision": "not-applicable-test"}
        self.artifact = {"schema_version": 1, "corpus_version": "test", "corpus_sha256": "fixture",
                         "index_sha256": index_hash(self.index), "embedding_space": self.config,
                         "provenance": "synthetic_test",
                         "documents": [{"document_id": letter, "chunk_id": letter + "0",
                                        "vector": vector, "embedding_space": copy.deepcopy(self.config), "truncated": False}
                                       for letter, vector in (("a", [3, 0]), ("b", [0, 4]), ("c", [-2, 0]))],
                         "queries": [{"id": "q", "vector": [10, 0], "embedding_space": copy.deepcopy(self.config), "truncated": False}]}

    def run_vectors(self):
        return vector_run(self.index, self.queries, self.artifact)

    def test_exact_cosine_keeps_negative_scores_and_normalizes(self):
        run = self.run_vectors()
        self.assertEqual([h["score"] for h in run["results"][0]["hits"]], [1, 0, -1])
        self.assertEqual(run["provenance"], "synthetic_test")

    def test_extreme_finite_values_do_not_overflow(self):
        self.artifact["queries"][0]["vector"] = [1e308, 0]
        self.artifact["documents"][0]["vector"] = [1e-308, 0]
        self.assertEqual(self.run_vectors()["results"][0]["hits"][0]["score"], 1)

    def test_zero_invalid_and_wrong_dimension_vectors_rejected(self):
        for vector in ([0, 0], [1], [1, 2, 3], [True, 0], [math.nan, 0], [math.inf, 0], ["1", 0]):
            with self.subTest(vector=vector):
                self.artifact["queries"][0]["vector"] = vector
                with self.assertRaises(ValueError):
                    self.run_vectors()

    def test_mixed_spaces_rejected_even_when_dimensions_match(self):
        self.artifact["documents"][0]["embedding_space"]["revision"] = "different"
        with self.assertRaises(ValueError):
            self.run_vectors()

    def test_missing_duplicate_unknown_and_truncated_vectors_rejected(self):
        for mutation in ("missing", "duplicate", "unknown", "truncated"):
            bad = copy.deepcopy(self.artifact)
            if mutation == "missing":
                bad["documents"].pop()
            elif mutation == "duplicate":
                bad["queries"].append(copy.deepcopy(bad["queries"][0]))
            elif mutation == "unknown":
                bad["queries"][0]["id"] = "unknown"
            else:
                bad["documents"][0]["truncated"] = True
            with self.assertRaises(ValueError):
                vector_run(self.index, self.queries, bad)

    def test_stale_export_and_malformed_configuration_rejected(self):
        for field in ("corpus_sha256", "index_sha256", "provenance"):
            bad = copy.deepcopy(self.artifact)
            bad[field] = "invalid"
            with self.assertRaises(ValueError):
                vector_run(self.index, self.queries, bad)
        self.artifact["embedding_space"]["dimensions"] = True
        with self.assertRaises(ValueError):
            self.run_vectors()

    def test_ties_are_deterministic(self):
        self.artifact["documents"][1]["vector"] = [1, 0]
        hits = self.run_vectors()["results"][0]["hits"]
        self.assertEqual([h["document_id"] for h in hits], ["a", "b", "c"])

    def test_rrf_uses_ranks_not_score_scales(self):
        dense = self.run_vectors()
        lexical = copy.deepcopy(dense)
        lexical["retriever"] = "test-lexical"
        lexical["results"][0]["hits"] = [lexical["results"][0]["hits"][1]]
        lexical["results"][0]["hits"][0]["score"] = 1000000
        labels = {"corpus_version": "test", "corpus_sha256": "fixture",
                  "queries": [{"id": "q", "category": "absent", "evidence": []}]}
        fused = fuse_runs(self.index, labels, lexical, dense)
        first = fused["results"][0]["hits"][0]
        self.assertEqual(first["document_id"], "b")
        self.assertAlmostEqual(first["score"], 1 / 61 + 1 / 62)
        lexical["results"][0]["hits"][0]["score"] = 0.00001
        self.assertEqual(fused, fuse_runs(self.index, labels, lexical, dense))


if __name__ == "__main__":
    unittest.main()
