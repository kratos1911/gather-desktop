"""Validate and prepare synthetic retrieval inputs; never call a model/provider."""

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path

from services.worker.text_processing import process_request

CORPUS = Path(__file__).resolve().parents[1] / "tests/evaluation/text-v1.json"
CATEGORIES = {"paraphrase", "exact", "confusable", "late_document", "multiple_sources", "absent"}


def _unique_ids(items, name):
    ids = [item["id"] for item in items]
    if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"Invalid or duplicate {name} IDs")


def prepare(corpus: dict) -> dict:
    """Trusted repository fixture input, not a public request validation boundary."""
    if corpus["version"] != "gather-text-v1":
        raise ValueError("Unsupported corpus version")
    _unique_ids(corpus["documents"], "document")
    _unique_ids(corpus["queries"], "query")
    canonical = json.dumps(corpus, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    documents = {}
    for source in corpus["documents"]:
        payload = {"version": 1, "request_id": "evaluation", "format": source["format"],
                   "content_base64": base64.b64encode(source["text"].encode("utf-8")).decode("ascii")}
        result = process_request(json.dumps(payload).encode("utf-8"))
        if result["status"] != "processed":
            raise ValueError(f"Fixture {source['id']} rejected: {result['code']}")
        documents[source["id"]] = {"id": source["id"], **result["document"]}

    labels = []
    sources = {source["id"]: source["text"] for source in corpus["documents"]}
    seen_queries = set()
    for query in corpus["queries"]:
        category = query["category"]
        if category not in CATEGORIES or not query["text"].strip():
            raise ValueError("Invalid query category or text")
        normalized = query["text"].strip().casefold()
        if normalized in seen_queries:
            raise ValueError("Duplicate query text")
        seen_queries.add(normalized)
        if (category == "absent") != (len(query["expected"]) == 0):
            raise ValueError("Only absent queries may have no evidence")
        if category == "absent" and not query.get("reason", "").strip():
            raise ValueError("Absent query needs a reviewed rationale")
        evidence = []
        for expected in query["expected"]:
            document_id, quote = expected["document_id"], expected["quote"]
            if document_id not in sources or not quote or sources[document_id].count(quote) != 1:
                raise ValueError("Evidence must occur exactly once in a known document")
            start = sources[document_id].index(quote)
            end = start + len(quote)
            if category == "late_document" and start < 1024:
                raise ValueError("Late evidence must be beyond the first 1024 characters")
            matching = [chunk["id"] for chunk in documents[document_id]["chunks"]
                        if chunk["start"] <= start and chunk["end"] >= end]
            if not matching:
                raise ValueError("Evidence is not fully contained in any processing chunk")
            evidence.append({"document_id": document_id, "quote": quote,
                             "start": start, "end": end, "acceptable_chunk_ids": matching})
        if category == "multiple_sources" and len({item["document_id"] for item in evidence}) < 2:
            raise ValueError("Multiple-source query requires distinct relevant documents")
        labels.append({"id": query["id"], "category": category, "evidence": evidence,
                       "absent_reason": query.get("reason")})

    metadata = {"corpus_version": corpus["version"], "corpus_sha256": fingerprint}
    return {
        "index": {**metadata, "documents": list(documents.values())},
        "queries": {**metadata, "queries": [{"id": q["id"], "text": q["text"]} for q in corpus["queries"]]},
        "labels": {**metadata, "queries": labels},
        "summary": {**metadata, "documents": len(documents), "queries": len(labels),
                    "chunks": sum(len(doc["chunks"]) for doc in documents.values()),
                    "categories": dict(sorted(Counter(q["category"] for q in labels).items())),
                    "model_evaluated": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional directory for generated inputs and separate labels")
    args = parser.parse_args()
    prepared = prepare(json.loads(CORPUS.read_text(encoding="utf-8")))
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        for name in ("index", "queries", "labels"):
            (args.output / f"{name}.json").write_text(
                json.dumps(prepared[name], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(prepared["summary"], indent=2))


if __name__ == "__main__":
    main()
