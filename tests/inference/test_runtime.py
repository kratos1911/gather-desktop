"""Synthetic engines exercise process isolation; these are not model results."""

import math
import multiprocessing
import os
import threading
import time
import unittest

from services.inference.runtime import InferenceError, Runtime, normalize, validate_request


class FakeEngine:
    def __init__(self, mode):
        self.mode = mode
        if mode == "startup_failure":
            raise ValueError("sensitive detail")
        if mode == "startup_hang":
            time.sleep(20)

    def count_tokens(self, text):
        if "aggregate" in text:
            return 1500
        return 3000 if "oversized" in text else 10

    def embed(self, text):
        if self.mode == "hang":
            time.sleep(20)
        if self.mode == "crash":
            os._exit(7)
        if self.mode == "invalid":
            return [float("nan")] * 512
        return [1.0] * 512


class RuntimeTests(unittest.TestCase):
    def runtime(self, mode=None, **kwargs):
        runtime = Runtime(FakeEngine, mode, **kwargs)
        self.addCleanup(runtime.close)
        return runtime

    def test_prompt_roles(self):
        self.assertEqual(validate_request({"role": "document", "texts": ["hello"]}), ["hello"])
        self.assertTrue(validate_request({"role": "query", "texts": ["hello"]})[0].endswith("Query:hello"))

    def test_invalid_requests(self):
        for request in (None, {}, {"role": "tool", "texts": ["x"]},
                        {"role": "query", "texts": "x"}, {"role": "query", "texts": []},
                        {"role": "query", "texts": ["x"] * 5},
                        {"role": "query", "texts": [" "]},
                        {"role": "query", "texts": ["\ud800"]},
                        {"role": "query", "texts": ["x"], "model": "other"}):
            with self.subTest(request=request), self.assertRaises(InferenceError):
                validate_request(request)

    def test_byte_limits(self):
        for texts in (["é" * 4097], ["a" * 6000] * 3):
            with self.assertRaises(InferenceError):
                validate_request({"role": "document", "texts": texts})

    def test_normalization_and_invalid_vectors(self):
        self.assertAlmostEqual(math.hypot(*normalize([1.0] * 1024)), 1)
        for vector in ([1.] * 511, [0.] * 512, [float("inf")] * 512, [True] * 512):
            with self.assertRaises(InferenceError):
                normalize(vector)

    def test_not_ready(self):
        with self.assertRaisesRegex(InferenceError, "not_ready"):
            self.runtime().infer({"role": "query", "texts": ["x"]})

    def test_reuses_loaded_process(self):
        runtime = self.runtime()
        runtime.start()
        pid = runtime.pid
        for _ in range(2):
            result = runtime.infer({"role": "document", "texts": ["a", "b"]})
            self.assertEqual(len(result["data"]), 2)
            self.assertEqual(result["prompt_tokens"], 20)
            self.assertEqual(len(result["data"][0]["embedding"]), 512)
            self.assertEqual(runtime.pid, pid)

    def test_token_rejection_keeps_ready(self):
        runtime = self.runtime()
        runtime.start()
        with self.assertRaisesRegex(InferenceError, "token_limit"):
            runtime.infer({"role": "document", "texts": ["oversized"]})
        self.assertTrue(runtime.ready)
        runtime.infer({"role": "query", "texts": ["valid"]})

    def test_aggregate_token_budget_is_atomic(self):
        # The invalid-output engine proves embedding is never called when the
        # whole batch exceeds the token budget, even if each item fits.
        runtime = self.runtime("invalid")
        runtime.start()
        with self.assertRaisesRegex(InferenceError, "token_limit"):
            runtime.infer({"role": "document", "texts": ["aggregate"] * 3})
        self.assertTrue(runtime.ready)

    def test_failure_is_redacted(self):
        runtime = self.runtime("startup_failure")
        with self.assertRaisesRegex(InferenceError, "^model_failed$"):
            runtime.start()
        self.assertFalse(runtime.ready)
        self.assertIsNone(runtime.pid)

    def test_startup_deadline(self):
        runtime = self.runtime("startup_hang", startup_timeout=.3)
        with self.assertRaisesRegex(InferenceError, "deadline_exceeded"):
            runtime.start()
        self.assertIsNone(runtime.pid)

    def test_timeout_reaps_then_explicit_restart(self):
        runtime = self.runtime("hang", request_timeout=.3)
        runtime.start()
        old_pid = runtime.pid
        before = time.monotonic()
        with self.assertRaisesRegex(InferenceError, "deadline_exceeded"):
            runtime.infer({"role": "query", "texts": ["x"]})
        self.assertLess(time.monotonic() - before, 5)
        self.assertNotIn(old_pid, [child.pid for child in multiprocessing.active_children()])
        self.assertFalse(runtime.ready)
        runtime.configuration = None
        runtime.start()
        runtime.infer({"role": "query", "texts": ["x"]})

    def test_crash_and_invalid_model_output(self):
        for mode in ("crash", "invalid"):
            runtime = self.runtime(mode)
            runtime.start()
            with self.assertRaisesRegex(InferenceError, "model_failed"):
                runtime.infer({"role": "query", "texts": ["x"]})
            self.assertFalse(runtime.ready)

    def test_concurrent_call_is_rejected_without_queue(self):
        runtime = self.runtime("hang", request_timeout=.5)
        runtime.start()
        errors = []

        def request():
            try:
                runtime.infer({"role": "query", "texts": ["x"]})
            except InferenceError as error:
                errors.append(str(error))

        thread = threading.Thread(target=request)
        thread.start()
        deadline = time.monotonic() + 2
        while not runtime._lock.locked() and time.monotonic() < deadline:
            time.sleep(.005)
        with self.assertRaisesRegex(InferenceError, "busy"):
            runtime.infer({"role": "query", "texts": ["x"]})
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ["deadline_exceeded"])

    def test_timeout_configuration(self):
        for value in (0, -1, float("nan"), float("inf"), True, 121):
            with self.assertRaises(ValueError):
                Runtime(FakeEngine, request_timeout=value)


if __name__ == "__main__":
    unittest.main()
