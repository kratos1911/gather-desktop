"""Developer-only Qwen embedding benchmark; downloads require --download.

Inputs are the frozen fictional corpus, never personal files. Inference is offline.
All writable caches, temporary files and reports live under the D: benchmark root.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import threading
import time

from scripts.score_text_evaluation import index_hash
from scripts.prepare_text_evaluation import CORPORA, corpus_run_root

MODEL = "Qwen/Qwen3-Embedding-0.6B"
REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
QUERY_TEMPLATE = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:{text}"
ROOT = Path(__file__).resolve().parents[1] / "output/model-benchmark"
TOKEN_LIMIT = 2048  # Explicit app benchmark cap, not the model's maximum context.


def configure_storage(root):
    root = Path(root).resolve()
    if os.name != "nt" or root.drive.upper() != "D:":
        raise ValueError("This local benchmark requires an absolute D: output directory")
    paths = {
        "HF_HOME": root / "hf", "HF_HUB_CACHE": root / "hf/hub",
        "HF_XET_CACHE": root / "hf/xet", "TORCH_HOME": root / "torch",
        "PIP_CACHE_DIR": root / "pip-cache", "XDG_CACHE_HOME": root / "cache",
        "TEMP": root / "tmp", "TMP": root / "tmp",
    }
    for key, path in paths.items():
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError("Cache/temp links must not redirect outside the D: benchmark directory")
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
                      HF_HUB_DISABLE_XET="1", TOKENIZERS_PARALLELISM="false")
    # Python may already have resolved its temp directory before this entrypoint.
    import tempfile
    tempfile.tempdir = str(paths["TEMP"])
    return root


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(root):
    from huggingface_hub import HfApi, snapshot_download
    manifest_path = root / "qwen-download.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        revision = manifest["revision"]
    else:
        revision = REVISION
    if revision != REVISION or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected immutable model commit")
    info = HfApi(token=False).model_info(MODEL, revision=revision, files_metadata=True)
    files = [f for f in info.siblings if "/" not in f.rfilename and (
        f.rfilename.endswith((".json", ".txt", ".safetensors", ".model"))
        or f.rfilename in ("LICENSE", "README.md"))]
    if not files or any(f.size is None for f in files):
        raise ValueError("Missing upstream artifact sizes")
    total = sum(f.size for f in files)
    if total > 4 * 1024**3 or shutil.disk_usage(root).free < total * 2 + 2 * 1024**3:
        raise ValueError("Download exceeds budget or D: lacks working headroom")
    write_json(manifest_path, {"model": MODEL, "revision": revision, "expected_bytes": total,
                              "license": "Apache-2.0", "status": "downloading"})
    print(json.dumps({"model": MODEL, "revision": revision, "download_bytes": total}), flush=True)
    snapshot = Path(snapshot_download(MODEL, revision=revision, token=False,
                                     allow_patterns=[f.rfilename for f in files], max_workers=2))
    artifacts = [{"file": f.rfilename, "bytes": (snapshot / f.rfilename).stat().st_size,
                  "sha256": sha256(snapshot / f.rfilename)} for f in files]
    for item, upstream in zip(artifacts, files):
        if item["bytes"] != upstream.size:
            raise ValueError("Artifact size mismatch")
        if upstream.lfs and item["sha256"] != upstream.lfs.sha256:
            raise ValueError("LFS artifact hash mismatch")
    write_json(manifest_path, {"model": MODEL, "revision": revision, "expected_bytes": total,
                              "license": "Apache-2.0", "status": "verified",
                              "snapshot": str(snapshot), "artifacts": artifacts})
    print("Model snapshot downloaded and hashed on D:.", flush=True)


def preflight(tokenizer, texts, limit):
    """Count exact prompted inputs including special tokens; never silently truncate."""
    lengths = [len(tokenizer(text, truncation=False, add_special_tokens=True)["input_ids"])
               for text in texts]
    if not lengths or min(lengths) <= 0 or max(lengths) > limit:
        raise ValueError("Empty or oversized tokenized input; revise chunking before inference")
    return lengths


def reduce_vector(vector, dimensions):
    if dimensions <= 0 or dimensions > len(vector):
        raise ValueError("Invalid Matryoshka dimensions")
    values = vector[:dimensions]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Non-finite model vector")
    norm = math.sqrt(sum(value * value for value in values))
    if not norm:
        raise ValueError("Zero model vector")
    return [value / norm for value in values]


@contextmanager
def memory_peak(process):
    peak = {"sampled_peak_rss_bytes": process.memory_info().rss}
    done = threading.Event()

    def sample():
        while not done.wait(0.02):
            peak["sampled_peak_rss_bytes"] = max(peak["sampled_peak_rss_bytes"], process.memory_info().rss)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    try:
        yield peak
    finally:
        done.set()
        thread.join()
        peak["sampled_peak_rss_bytes"] = max(peak["sampled_peak_rss_bytes"], process.memory_info().rss)


def run(root, threads, corpus="text-v1"):
    # These flags precede third-party imports; network is unnecessary after download.
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import psutil
    import torch
    from transformers import AutoModel, AutoTokenizer

    manifest = json.loads((root / "qwen-download.json").read_text(encoding="utf-8"))
    if (manifest.get("status") != "verified" or manifest.get("model") != MODEL
            or manifest.get("revision") != REVISION):
        raise ValueError("Run --download to finish a verified Qwen snapshot first")
    snapshot = Path(manifest["snapshot"]).resolve()
    if not snapshot.is_relative_to(root):
        raise ValueError("Model snapshot must remain inside the D: benchmark directory")
    for artifact in manifest["artifacts"]:
        path = snapshot / artifact["file"]
        if sha256(path) != artifact["sha256"]:
            raise ValueError("Model snapshot changed after download")
    if psutil.virtual_memory().available < 4 * 1024**3:
        raise ValueError("At least 4 GiB of available RAM is required before loading Qwen")
    run_root = corpus_run_root(root, corpus)
    index = json.loads((run_root / "inputs/index.json").read_text(encoding="utf-8"))
    queries = json.loads((run_root / "inputs/queries.json").read_text(encoding="utf-8"))
    if index["corpus_version"] != f"gather-{corpus}":
        raise ValueError("Prepared inputs do not match selected corpus")
    for field in ("corpus_version", "corpus_sha256"):
        if index[field] != queries[field]:
            raise ValueError("Input fingerprints differ")
    chunks = [(doc["id"], chunk["id"], chunk["text"])
              for doc in index["documents"] for chunk in doc["chunks"]]
    document_texts = [chunk[2] for chunk in chunks]
    query_texts = [QUERY_TEMPLATE.format(text=q["text"]) for q in queries["queries"]]
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    process = psutil.Process()
    report = {"measured_at_utc": datetime.now(timezone.utc).isoformat(), "model": MODEL,
              "corpus_version": index["corpus_version"], "corpus_sha256": index["corpus_sha256"],
              "index_sha256": index_hash(index),
              "revision": manifest["revision"], "device": "cpu", "dtype": "float32",
              "threads": threads, "batch_size": 1, "token_limit": TOKEN_LIMIT,
              "platform": platform.platform(), "cpu": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
              "ram_bytes": psutil.virtual_memory().total, "model_bytes": manifest["expected_bytes"],
              "packages": {name: importlib.metadata.version(name) for name in
                           ("torch", "transformers", "huggingface-hub", "tokenizers", "safetensors", "psutil")}}
    with memory_peak(process) as memory:
        start = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False,
                                                  padding_side="left")
        report["document_tokens"] = preflight(tokenizer, document_texts, TOKEN_LIMIT)
        report["query_tokens"] = preflight(tokenizer, query_texts, TOKEN_LIMIT)
        model = AutoModel.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False,
                                         use_safetensors=True, dtype=torch.float32,
                                         attn_implementation="sdpa").to("cpu").eval()
        report["load_seconds"] = time.perf_counter() - start

        def encode(text):
            tokens = tokenizer(text, return_tensors="pt", truncation=False, add_special_tokens=True)
            if tokens["input_ids"].shape[1] > TOKEN_LIMIT:
                raise ValueError("Tokenizer changed after preflight")
            with torch.inference_mode():
                output = model(**tokens, use_cache=False).last_hidden_state[0, -1].float()
                return output.tolist()

        start = time.perf_counter()
        encode(query_texts[0])
        report["first_inference_seconds"] = time.perf_counter() - start
        start = time.perf_counter()
        document_vectors = []
        for number, text in enumerate(document_texts, 1):
            document_vectors.append(encode(text))
            if number % 20 == 0:
                print(f"Embedded {number}/{len(document_texts)} passages", flush=True)
        report["document_index_seconds"] = time.perf_counter() - start
        vectors, latencies = [], []
        for number, text in enumerate(query_texts, 1):
            start = time.perf_counter()
            vectors.append(encode(text))
            latencies.append(time.perf_counter() - start)
            if number % 10 == 0:
                print(f"Embedded {number}/{len(query_texts)} queries", flush=True)
        report["query_seconds"] = latencies
        report["query_p50_seconds"] = statistics.median(latencies)
        report["query_p95_seconds"] = sorted(latencies)[math.ceil(0.95 * len(latencies)) - 1]
    report.update(memory)
    if hasattr(process.memory_info(), "peak_wset"):
        report["process_peak_working_set_bytes"] = process.memory_info().peak_wset
    destination = run_root / f"qwen-{threads}threads"
    for dimensions in (256, 512, 1024):
        space = {"provider": "self-hosted-cpu", "model": MODEL, "revision": manifest["revision"],
                 "dimensions": dimensions, "query_template": QUERY_TEMPLATE,
                 "document_template": "{text}", "tokenizer_revision": manifest["revision"]}
        artifact = {"schema_version": 1, "provenance": "model_export", "embedding_space": space,
                    "corpus_version": index["corpus_version"], "corpus_sha256": index["corpus_sha256"],
                    "index_sha256": index_hash(index),
                    "documents": [{"document_id": doc_id, "chunk_id": chunk_id,
                                   "vector": reduce_vector(vector, dimensions), "embedding_space": space,
                                   "truncated": False}
                                  for (doc_id, chunk_id, _), vector in zip(chunks, document_vectors)],
                    "queries": [{"id": query["id"], "vector": reduce_vector(vector, dimensions),
                                 "embedding_space": space, "truncated": False}
                                for query, vector in zip(queries["queries"], vectors)]}
        write_json(destination / f"vectors-{dimensions}.json", artifact)
    write_json(destination / "measurement.json", report)
    print(json.dumps({key: report[key] for key in ("load_seconds", "document_index_seconds",
          "query_p50_seconds", "query_p95_seconds", "sampled_peak_rss_bytes")}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Explicitly permit downloading only the Qwen snapshot")
    parser.add_argument("--threads", type=int, choices=(2, 4, 8), default=2)
    parser.add_argument("--corpus", choices=CORPORA, default="text-v1")
    args = parser.parse_args()
    root = configure_storage(ROOT)
    if args.download:
        download(root)
    else:
        run(root, args.threads, args.corpus)


if __name__ == "__main__":
    main()
