"""Evaluate exported model vectors without contacting a provider."""

import argparse
import json
import math
from pathlib import Path

from scripts.prepare_text_evaluation import CORPUS, prepare
from scripts.score_text_evaluation import index_hash, lexical_run, score_run


def _normalize(vector, dimensions):
    if not isinstance(vector, list) or len(vector) != dimensions:
        raise ValueError("Vector dimension mismatch")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
        raise ValueError("Vectors require finite numeric values")
    # Scale first to avoid overflow/underflow for otherwise valid nonzero vectors.
    scale = max(abs(x) for x in vector)
    if not scale:
        raise ValueError("Zero vectors cannot be compared by cosine similarity")
    scaled = [x / scale for x in vector]
    norm = math.sqrt(sum(x * x for x in scaled))
    return [x / norm for x in scaled]


def vector_run(index, queries, artifact):
    """Saved-vector adapter. Labels are deliberately absent from this interface."""
    try:
        return _vector_run(index, queries, artifact)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("Malformed embedding export") from exc


def _vector_run(index, queries, artifact):
    if type(artifact["schema_version"]) is not int or artifact["schema_version"] != 1:
        raise ValueError("Unsupported embedding export schema")
    for field in ("corpus_version", "corpus_sha256"):
        if not (artifact[field] == index[field] == queries[field]):
            raise ValueError("Corpus mismatch")
    if artifact["index_sha256"] != index_hash(index):
        raise ValueError("Processing/index mismatch")
    config = artifact["embedding_space"]
    dimensions = config["dimensions"]
    if type(dimensions) is not int or not 1 <= dimensions <= 4096:
        raise ValueError("Embedding dimensions must be in 1..4096")
    for field in ("provider", "model", "revision", "query_template", "document_template", "tokenizer_revision"):
        if not isinstance(config[field], str) or not config[field].strip():
            raise ValueError("Embedding configuration must identify every transformation")
    if artifact["provenance"] not in ("model_export", "synthetic_test"):
        raise ValueError("Declare model_export or synthetic_test provenance")
    chunks = [(doc["id"], chunk["id"]) for doc in index["documents"] for chunk in doc["chunks"]]
    query_ids = [query["id"] for query in queries["queries"]]

    def collect(rows, expected, keys):
        if not isinstance(rows, list):
            raise ValueError("Embedding rows must be a list")
        vectors = {}
        for row in rows:
            identity = tuple(row[key] for key in keys)
            if identity not in expected or identity in vectors:
                raise ValueError("Unknown or duplicate embedding identity")
            if row["embedding_space"] != config:
                raise ValueError("Mixed embedding spaces; equal dimensions do not imply compatibility")
            if row["truncated"] is not False:
                raise ValueError("Truncated or unverified input cannot enter this benchmark")
            vectors[identity] = _normalize(row["vector"], dimensions)
        if set(vectors) != set(expected):
            raise ValueError("Incomplete embeddings; failed requests cannot become empty results")
        return vectors

    document_vectors = collect(artifact["documents"], set(chunks), ("document_id", "chunk_id"))
    query_vectors = collect(artifact["queries"], {(q,) for q in query_ids}, ("id",))
    results = []
    for query_id in query_ids:
        vector = query_vectors[(query_id,)]
        hits = [{"document_id": doc_id, "chunk_id": chunk_id,
                 "score": max(-1.0, min(1.0, sum(a * b for a, b in zip(vector, document_vectors[(doc_id, chunk_id)]))))}
                for doc_id, chunk_id in chunks]
        hits.sort(key=lambda hit: (-hit["score"], hit["document_id"], hit["chunk_id"]))
        results.append({"id": query_id, "hits": hits})
    return {"schema_version": 1, "corpus_version": index["corpus_version"],
            "corpus_sha256": index["corpus_sha256"], "index_sha256": index_hash(index),
            "retriever": "exact-cosine-v1", "embedding_space": config,
            "provenance": artifact["provenance"], "results": results}


def fuse_runs(index, labels, lexical, dense):
    """Equal-weight reciprocal rank fusion, fixed k=60; never blend raw scores."""
    # Fail on incomplete/stale rankings before performing fusion.
    score_run(index, labels, lexical)
    score_run(index, labels, dense)
    by_query = {row["id"]: row["hits"] for row in dense["results"]}
    results = []
    for row in lexical["results"]:
        totals = {}
        for ranking in (row["hits"], by_query[row["id"]]):
            for rank, hit in enumerate(ranking, 1):
                key = (hit["document_id"], hit["chunk_id"])
                totals[key] = totals.get(key, 0.0) + 1 / (60 + rank)
        hits = [{"document_id": key[0], "chunk_id": key[1], "score": value}
                for key, value in totals.items()]
        hits.sort(key=lambda hit: (-hit["score"], hit["document_id"], hit["chunk_id"]))
        results.append({"id": row["id"], "hits": hits})
    return {**dense, "retriever": "rrf-k60-tfidf-dense-v1", "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vectors", type=Path, required=True, help="Provider-exported JSON; never reads credentials")
    parser.add_argument("--output", type=Path, default=Path("output/evaluation/text-v1/vectors"))
    args = parser.parse_args()
    if args.vectors.stat().st_size > 32 * 1024 * 1024:
        parser.error("Embedding export exceeds 32 MiB")
    artifact = json.loads(args.vectors.read_text(encoding="utf-8"))
    prepared = prepare(json.loads(CORPUS.read_text(encoding="utf-8")))
    dense = vector_run(prepared["index"], prepared["queries"], artifact)
    lexical = lexical_run(prepared["index"], prepared["queries"])
    hybrid = fuse_runs(prepared["index"], prepared["labels"], lexical, dense)
    reports = {}
    for name, run in (("lexical", lexical), ("dense", dense), ("hybrid", hybrid)):
        reports[name] = score_run(prepared["index"], prepared["labels"], run)
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"provenance": artifact["provenance"], "embedding_space": artifact["embedding_space"],
              "runs": {"lexical": lexical, "dense": dense, "hybrid": hybrid}, "reports": reports}
    (args.output / "comparison.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"provenance": artifact["provenance"],
                      "summaries": {name: report["summary"] for name, report in reports.items()}}, indent=2))


if __name__ == "__main__":
    main()
