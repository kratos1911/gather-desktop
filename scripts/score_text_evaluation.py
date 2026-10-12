"""Offline lexical baseline and strict retrieval scorer. No AI or network calls."""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

from scripts.prepare_text_evaluation import CORPORA, load_corpus, prepare


def index_hash(index: dict) -> str:
    encoded = json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    # Keep hyphenated identifiers intact; no stemming, synonyms or stopword tuning.
    return re.findall(r"[^\W_]+(?:-[^\W_]+)*", text.casefold(), flags=re.UNICODE)


def lexical_run(index: dict, queries: dict) -> dict:
    """Receives index and question text only, never relevance labels."""
    for field in ("corpus_version", "corpus_sha256"):
        if queries[field] != index[field]:
            raise ValueError("Query/index corpus mismatch")
    chunks = [(doc["id"], chunk["id"], Counter(tokenize(chunk["text"])))
              for doc in index["documents"] for chunk in doc["chunks"]]
    frequency = Counter(term for _, _, counts in chunks for term in counts)
    idf = {term: math.log((1 + len(chunks)) / (1 + count)) + 1
           for term, count in frequency.items()}

    def vector(counts):
        weights = {term: (1 + math.log(count)) * idf[term]
                   for term, count in counts.items() if term in idf}
        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        return {term: weight / norm for term, weight in weights.items()} if norm else {}

    vectors = [(doc_id, chunk_id, vector(counts)) for doc_id, chunk_id, counts in chunks]
    results = []
    for query in queries["queries"]:
        query_vector = vector(Counter(tokenize(query["text"])))
        hits = []
        for doc_id, chunk_id, weights in vectors:
            similarity = sum(weight * weights.get(term, 0) for term, weight in query_vector.items())
            if similarity > 0:
                hits.append({"document_id": doc_id, "chunk_id": chunk_id, "score": similarity})
        hits.sort(key=lambda hit: (-hit["score"], hit["document_id"], hit["chunk_id"]))
        results.append({"id": query["id"], "hits": hits})
    return {"schema_version": 1, "corpus_version": index["corpus_version"],
            "corpus_sha256": index["corpus_sha256"], "index_sha256": index_hash(index),
            "retriever": "tfidf-cosine-v1", "results": results}


def score_run(index: dict, labels: dict, run: dict) -> dict:
    """Validate the entire ranking, then score; malformed runs never get partial credit."""
    try:
        return _score_run(index, labels, run)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Malformed evaluation run or prepared inputs") from exc


def _score_run(index, labels, run):
    if type(run["schema_version"]) is not int or run["schema_version"] != 1:
        raise ValueError("Unsupported run schema")
    for field in ("corpus_version", "corpus_sha256"):
        if not (run[field] == index[field] == labels[field]):
            raise ValueError("Corpus mismatch")
    if run["index_sha256"] != index_hash(index):
        raise ValueError("Index mismatch; regenerate results after processing changes")
    if not isinstance(run["retriever"], str) or not run["retriever"].strip():
        raise ValueError("Retriever identifier required")
    valid_pairs = {(doc["id"], chunk["id"]) for doc in index["documents"] for chunk in doc["chunks"]}
    expected = {query["id"]: query for query in labels["queries"]}
    if not isinstance(run["results"], list):
        raise ValueError("Results must be a list")
    ranked = {}
    for row in run["results"]:
        query_id = row["id"]
        if query_id not in expected or query_id in ranked:
            raise ValueError("Unknown or duplicate query ID")
        if not isinstance(row["hits"], list):
            raise ValueError("Hits must be a list")
        seen = set()
        for hit in row["hits"]:
            pair = (hit["document_id"], hit["chunk_id"])
            if pair not in valid_pairs or pair in seen:
                raise ValueError("Unknown, mismatched or duplicate document/chunk pair")
            seen.add(pair)
            if "score" in hit and (type(hit["score"]) not in (int, float)
                                   or not math.isfinite(hit["score"])):
                raise ValueError("Optional ranking score must be finite and numeric")
        ranked[query_id] = row["hits"]
    if set(ranked) != set(expected):
        raise ValueError("Every query needs a result; use empty hits for a genuine no-result response")

    rows = []
    for query_id, label in expected.items():
        hits = ranked[query_id]
        documents = list(dict.fromkeys(hit["document_id"] for hit in hits))[:5]
        top_chunks = {(hit["document_id"], hit["chunk_id"]) for hit in hits[:5]}
        evidence = label["evidence"]
        row = {"id": query_id, "category": label["category"], "returned_candidates": bool(hits),
               "document_recall_at_5": None, "document_mrr_at_5": None,
               "evidence_recall_at_5": None, "missing_evidence": []}
        if evidence:
            relevant = {item["document_id"] for item in evidence}
            row["document_recall_at_5"] = len(relevant.intersection(documents)) / len(relevant)
            row["document_mrr_at_5"] = next((1 / rank for rank, doc_id in enumerate(documents, 1)
                                              if doc_id in relevant), 0.0)
            found = 0
            for item in evidence:
                if any((item["document_id"], chunk_id) in top_chunks for chunk_id in item["acceptable_chunk_ids"]):
                    found += 1
                else:
                    row["missing_evidence"].append({key: item[key] for key in ("document_id", "start", "end")})
            row["evidence_recall_at_5"] = found / len(evidence)
        rows.append(row)

    def summarize(group):
        answerable = [row for row in group if row["document_recall_at_5"] is not None]
        absent = [row for row in group if row["document_recall_at_5"] is None]
        result = {"queries": len(group), "answerable": len(answerable), "absent": len(absent)}
        for metric in ("document_recall_at_5", "document_mrr_at_5", "evidence_recall_at_5"):
            result[metric] = sum(row[metric] for row in answerable) / len(answerable) if answerable else None
        result["absent_queries_returning_candidates"] = sum(row["returned_candidates"] for row in absent)
        # A ranked candidate is not an assertion that its contents answer the question.
        result["unsupported_answer_rate"] = None
        return result

    return {"scorer_version": "retrieval-at5-v1", "corpus_version": run["corpus_version"],
            "corpus_sha256": run["corpus_sha256"], "index_sha256": run["index_sha256"],
            "retriever": run["retriever"], "summary": summarize(rows),
            "categories": {category: summarize([row for row in rows if row["category"] == category])
                           for category in sorted({row["category"] for row in rows})},
            "queries": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=CORPORA, default="text-v1")
    parser.add_argument("--run", type=Path, help="Score existing rankings instead of running the lexical baseline")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    prepared = prepare(load_corpus(args.corpus))
    args.output = args.output or Path("output/evaluation") / args.corpus / "baseline"
    run = (json.loads(args.run.read_text(encoding="utf-8")) if args.run else
           lexical_run(prepared["index"], prepared["queries"]))
    report = score_run(prepared["index"], prepared["labels"], run)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (("run", run), ("report", report)):
        (args.output / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"retriever": report["retriever"], **report["summary"]}, indent=2))


if __name__ == "__main__":
    main()
