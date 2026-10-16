"""Single-flight, persistent CPU inference with process-level deadlines.

This is a serving prerequisite, not an authenticated or deployed API. Callers
must explicitly start it again after a timeout or model failure.
"""

import math
import multiprocessing
import threading
import time

MODEL = "Qwen/Qwen3-Embedding-0.6B"
REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
QUERY_TEMPLATE = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:{text}"
DIMENSIONS = 512


class InferenceError(Exception):
    """Content-free error safe for callers to report."""


def validate_request(request):
    if (not isinstance(request, dict) or set(request) != {"role", "texts"}
            or request["role"] not in ("query", "document")):
        raise InferenceError("invalid_request")
    texts = request["texts"]
    if not isinstance(texts, list) or not 1 <= len(texts) <= 4:
        raise InferenceError("invalid_batch")
    try:
        if any(not isinstance(text, str) or not text.strip()
               or len(text.encode("utf-8")) > 8192 for text in texts):
            raise InferenceError("invalid_text")
        if sum(len(text.encode("utf-8")) for text in texts) > 16384:
            raise InferenceError("request_too_large")
    except UnicodeError:
        raise InferenceError("invalid_text") from None
    return [QUERY_TEMPLATE.format(text=text) if request["role"] == "query" else text
            for text in texts]


def normalize(vector):
    if len(vector) < DIMENSIONS:
        raise InferenceError("invalid_model_output")
    values = vector[:DIMENSIONS]
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        raise InferenceError("invalid_model_output")
    norm = math.hypot(*values)
    if not norm or not math.isfinite(norm):
        raise InferenceError("invalid_model_output")
    return [value / norm for value in values]


def _child(connection, factory, configuration):
    try:
        engine = factory(configuration)
        connection.send({"status": "ready"})
        while True:
            texts = connection.recv()
            counts = [engine.count_tokens(text) for text in texts]
            if any(type(count) is not int or not 0 < count <= 2048 for count in counts) or sum(counts) > 4096:
                connection.send({"error": "token_limit"})
                continue
            vectors = [normalize(engine.embed(text)) for text in texts]
            connection.send({"model": MODEL, "revision": REVISION,
                             "dimensions": DIMENSIONS, "prompt_tokens": sum(counts),
                             "data": [{"index": index, "embedding": vector}
                                      for index, vector in enumerate(vectors)]})
    except (EOFError, BrokenPipeError):
        pass
    except Exception:
        try:
            connection.send({"error": "model_failed"})
        except (OSError, EOFError):
            pass
    finally:
        connection.close()


class Runtime:
    def __init__(self, factory, configuration=None, *, startup_timeout=90, request_timeout=15):
        for value in (startup_timeout, request_timeout):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 120:
                raise ValueError("Timeout must be positive and at most 120 seconds")
        self.factory, self.configuration = factory, configuration
        self.startup_timeout, self.request_timeout = startup_timeout, request_timeout
        self._lock = threading.Lock()
        self._process = self._connection = None
        self.ready = False

    @property
    def pid(self):
        return self._process.pid if self._process else None

    def _stop(self):
        self.ready = False
        if self._process:
            if self._process.is_alive():
                self._process.terminate()
            self._process.join(2)
            if self._process.is_alive():
                self._process.kill()
                self._process.join(2)
            if self._process.is_alive():
                raise InferenceError("cleanup_failed")
            self._process.close()
            self._process = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def _receive(self, timeout, cancel=None):
        try:
            deadline = time.monotonic() + timeout
            while True:
                if cancel is not None and cancel.is_set():
                    self._stop()
                    raise InferenceError("cancelled")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._stop()
                    raise InferenceError("deadline_exceeded")
                if self._connection.poll(min(remaining, 0.05)):
                    break
            result = self._connection.recv()
        except (EOFError, OSError):
            self._stop()
            raise InferenceError("model_failed") from None
        if result.get("error"):
            if result["error"] != "token_limit":
                self._stop()
            raise InferenceError(result["error"])
        return result

    def start(self, *, cancel=None):
        with self._lock:
            self._stop()
            context = multiprocessing.get_context("spawn")
            self._connection, child = context.Pipe()
            self._process = context.Process(target=_child, args=(child, self.factory, self.configuration), daemon=True)
            try:
                self._process.start()
            except Exception:
                self._process = None
                self._connection.close()
                self._connection = None
                raise InferenceError("startup_failed") from None
            finally:
                child.close()
            result = self._receive(self.startup_timeout, cancel)
            self.ready = result == {"status": "ready"}
            if not self.ready:
                self._stop()
                raise InferenceError("startup_failed")

    def infer(self, request, *, cancel=None):
        if not self._lock.acquire(blocking=False):
            raise InferenceError("busy")
        try:
            texts = validate_request(request)
            if not self.ready or not self._process.is_alive():
                self._stop()
                raise InferenceError("not_ready")
            try:
                self._connection.send(texts)
            except (OSError, EOFError):
                self._stop()
                raise InferenceError("model_failed") from None
            return self._receive(self.request_timeout, cancel)
        finally:
            self._lock.release()

    def close(self):
        with self._lock:
            self._stop()
