"""Offline, synthetic-input smoke of the real persistent Qwen CPU runtime."""

import json
import time
from pathlib import Path

from scripts.benchmark_cpu import ROOT, configure_storage, sha256, write_json
from services.inference.qwen import QwenEngine
from services.inference.runtime import MODEL, REVISION, Runtime


def main():
    root = configure_storage(ROOT)
    import psutil
    if psutil.virtual_memory().available < 4 * 1024**3:
        raise SystemExit("Real-model check paused: at least 4 GiB available RAM required.")
    manifest = json.loads((root / "qwen-download.json").read_text(encoding="utf-8"))
    if (manifest.get("model"), manifest.get("revision"), manifest.get("status")) != (MODEL, REVISION, "verified"):
        raise SystemExit("Verified pinned model manifest required.")
    snapshot = Path(manifest["snapshot"]).resolve()
    if not snapshot.is_relative_to(root):
        raise SystemExit("Model must remain inside D: benchmark directory.")
    for artifact in manifest["artifacts"]:
        path = (snapshot / artifact["file"]).resolve()
        if not path.is_relative_to(root) or sha256(path) != artifact["sha256"]:
            raise SystemExit("Model artifact verification failed.")
    runtime = Runtime(QwenEngine, str(snapshot))
    report = {"scope": "Windows host smoke; not container or retrieval evaluation",
              "model": MODEL, "revision": REVISION, "threads": 2, "dimensions": 512}
    try:
        started = time.perf_counter()
        runtime.start()
        report["startup_seconds"] = time.perf_counter() - started
        pid = runtime.pid
        timings = []
        for role, text in (("document", "The fictional museum opens at nine on Tuesday."),
                           ("query", "When does the museum open?"),
                           ("query", "When does the museum open?")):
            started = time.perf_counter()
            result = runtime.infer({"role": role, "texts": [text]})
            timings.append(time.perf_counter() - started)
            assert result["dimensions"] == 512 and len(result["data"][0]["embedding"]) == 512
            assert runtime.pid == pid
        report["request_seconds"] = timings
        report["process_reused"] = True
        report["rss_after_requests_bytes"] = psutil.Process(pid).memory_info().rss
    finally:
        runtime.close()
    report["process_reaped"] = runtime.pid is None
    write_json(root / "serving/host-smoke.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
