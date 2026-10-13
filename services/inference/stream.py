"""Private bounded JSONL adapter. No network, credentials or client authentication."""

import json
import sys
import time
from pathlib import Path

from services.inference.qwen import QwenEngine
from services.inference.runtime import InferenceError, Runtime

MAX_LINE = 65536


def emit(output, value):
    output.write(json.dumps(value, allow_nan=False) + "\n")
    output.flush()


def serve(runtime, source, output):
    """Malformed frames recover; oversized frames and fatal model errors end session."""
    try:
        started = time.perf_counter()
        runtime.start()
        emit(output, {"status": "ready", "startup_seconds": time.perf_counter() - started})
        while line := source.readline(MAX_LINE + 1):
            if len(line) > MAX_LINE:
                emit(output, {"error": "frame_too_large"})
                return 2
            try:
                request = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeError, RecursionError):
                emit(output, {"error": "invalid_json"})
                continue
            try:
                started = time.perf_counter()
                result = runtime.infer(request)
                emit(output, {"result": result, "seconds": time.perf_counter() - started})
            except InferenceError as error:
                emit(output, {"error": str(error)})
                if not runtime.ready:
                    return 2
        return 0
    except InferenceError as error:
        emit(output, {"error": str(error)})
        return 2
    finally:
        runtime.close()


def main():
    result = serve(Runtime(QwenEngine, "/model"), sys.stdin.buffer, sys.stdout)
    # Linux cgroup peak includes the whole container, not just Python RSS.
    peak = Path("/sys/fs/cgroup/memory.peak")
    if peak.is_file():
        emit(sys.stdout, {"container_peak_bytes": int(peak.read_text().strip())})
    return result


if __name__ == "__main__":
    raise SystemExit(main())
