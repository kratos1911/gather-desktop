import copy
import json
import unittest

from scripts.prepare_text_evaluation import CORPUS, prepare


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))

    def test_inventory_and_every_evidence_span(self):
        result = prepare(self.corpus)
        self.assertEqual(result["summary"]["documents"], 14)
        self.assertEqual(result["summary"]["queries"], 40)
        self.assertEqual(result["summary"]["categories"]["absent"], 5)
        self.assertFalse(result["summary"]["model_evaluated"])
        docs = {d["id"]: d for d in result["index"]["documents"]}
        sources = {d["id"]: d["text"] for d in self.corpus["documents"]}
        for query in result["labels"]["queries"]:
            for evidence in query["evidence"]:
                doc_id = evidence["document_id"]
                self.assertEqual(sources[doc_id][evidence["start"]:evidence["end"]], evidence["quote"])
                for chunk_id in evidence["acceptable_chunk_ids"]:
                    chunk = next(c for c in docs[doc_id]["chunks"] if c["id"] == chunk_id)
                    self.assertIn(evidence["quote"], chunk["text"])

    def test_deterministic_metadata_and_separate_labels(self):
        first = prepare(self.corpus)
        self.assertEqual(first, prepare(copy.deepcopy(self.corpus)))
        for query in first["queries"]["queries"]:
            self.assertEqual(set(query), {"id", "text"})
        for doc in first["index"]["documents"]:
            self.assertNotIn("expected", doc)
        self.corpus["queries"][0]["text"] += " Please."
        self.assertNotEqual(first["summary"]["corpus_sha256"], prepare(self.corpus)["summary"]["corpus_sha256"])

    def test_missing_or_ambiguous_evidence_rejected(self):
        for bad_quote in ("not present", "", " "):
            with self.subTest(quote=bad_quote):
                bad = copy.deepcopy(self.corpus)
                bad["queries"][0]["expected"][0]["quote"] = bad_quote
                with self.assertRaises(ValueError):
                    prepare(bad)

    def test_duplicate_ids_or_query_text_rejected(self):
        for key in ("documents", "queries"):
            bad = copy.deepcopy(self.corpus)
            bad[key].append(copy.deepcopy(bad[key][0]))
            with self.assertRaises(ValueError):
                prepare(bad)
        self.corpus["queries"][1]["text"] = self.corpus["queries"][0]["text"]
        with self.assertRaises(ValueError):
            prepare(self.corpus)

    def test_absent_requires_no_evidence_and_rationale(self):
        absent = self.corpus["queries"][-1]
        absent["reason"] = ""
        with self.assertRaises(ValueError):
            prepare(self.corpus)
        absent["reason"] = "Fictional missing evidence"
        absent["expected"] = self.corpus["queries"][0]["expected"]
        with self.assertRaises(ValueError):
            prepare(self.corpus)

    def test_false_late_and_multiple_source_labels_rejected(self):
        for category in ("late_document", "multiple_sources"):
            bad = copy.deepcopy(self.corpus)
            bad["queries"][0]["category"] = category
            with self.assertRaises(ValueError):
                prepare(bad)

    def test_broken_source_rejected_before_export(self):
        self.corpus["documents"][0]["text"] = "\x00"
        with self.assertRaises(ValueError):
            prepare(self.corpus)


if __name__ == "__main__":
    unittest.main()
