import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.prepare_text_evaluation import CORPORA, corpus_run_root, load_corpus, prepare
from scripts.score_text_evaluation import lexical_run, score_run
from scripts.evaluate_vectors import vector_run


class ChallengeCorpusTests(unittest.TestCase):
    def test_frozen_inventory_and_late_evidence(self):
        prepared = prepare(load_corpus("text-v2"))
        self.assertEqual(prepared["summary"]["corpus_sha256"],
                         "d23f63392759b5db751f1a024468908d8d6b3832652ddbdb7234264c8eb4d25b")
        self.assertEqual((prepared["summary"]["documents"], prepared["summary"]["chunks"],
                          prepared["summary"]["queries"]), (40, 64, 64))
        self.assertEqual(prepared["summary"]["categories"],
                         {"absent": 8, "confusable": 16, "exact": 8,
                          "late_document": 8, "multiple_sources": 8, "paraphrase": 16})
        for query in prepared["labels"]["queries"]:
            if query["category"] == "late_document":
                self.assertTrue(all(e["start"] > 2300 for e in query["evidence"]))

    def test_new_sources_questions_and_label_separation(self):
        old, new = load_corpus("text-v1"), load_corpus("text-v2")
        for collection, field in (("documents", "text"), ("queries", "text")):
            self.assertFalse({row[field] for row in old[collection]} & {row[field] for row in new[collection]})
        prepared = prepare(new)
        self.assertTrue(all(set(row) == {"id", "text"} for row in prepared["queries"]["queries"]))
        for row in prepared["index"]["documents"]:
            self.assertNotIn("expected", row)
            self.assertNotIn("category", row)

    def test_frozen_query_source_and_label_edits_are_rejected(self):
        original = load_corpus("text-v2")
        freeze = CORPORA["text-v2"].with_suffix(".freeze.json").read_text(encoding="utf-8")
        # Temp files only under ignored repository output, including on Windows D:.
        directory = Path(__file__).resolve().parents[2] / "output/evaluation-tests"
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as tmp:
            path = Path(tmp) / "challenge.json"
            path.with_suffix(".freeze.json").write_text(freeze, encoding="utf-8")
            for kind in ("source", "query", "label"):
                changed = copy.deepcopy(original)
                if kind == "source":
                    changed["documents"][0]["text"] += " changed"
                elif kind == "query":
                    changed["queries"][0]["text"] += " changed"
                else:
                    changed["queries"][0]["expected"][0]["quote"] = "changed"
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(kind=kind), patch.dict(CORPORA, {"text-v2": path}):
                    with self.assertRaisesRegex(ValueError, "Frozen"):
                        load_corpus("text-v2")

    def test_runs_cannot_overwrite_other_corpus_by_selection(self):
        root = Path("output/model-benchmark")
        self.assertEqual(corpus_run_root(root, "text-v1"), root)
        self.assertEqual(corpus_run_root(root, "text-v2"), root / "text-v2")
        with self.assertRaises(ValueError):
            corpus_run_root(root, "../../elsewhere")
        with self.assertRaises(ValueError):
            load_corpus("unknown")

    def test_scorer_and_vector_adapter_reject_cross_corpus_results(self):
        first, second = [prepare(load_corpus(name)) for name in ("text-v1", "text-v2")]
        run = lexical_run(first["index"], first["queries"])
        with self.assertRaisesRegex(ValueError, "Corpus mismatch"):
            score_run(second["index"], second["labels"], run)
        artifact = {"schema_version": 1, "corpus_version": first["index"]["corpus_version"],
                    "corpus_sha256": first["index"]["corpus_sha256"]}
        with self.assertRaisesRegex(ValueError, "Corpus mismatch"):
            vector_run(second["index"], second["queries"], artifact)


if __name__ == "__main__":
    unittest.main()
