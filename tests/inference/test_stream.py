"""Protocol tests use a synthetic engine, never claimed as semantic evidence."""

import io
import json
import unittest

from services.inference.runtime import Runtime
from services.inference.stream import MAX_LINE, serve
from test_runtime import FakeEngine


class StreamTests(unittest.TestCase):
    def run_stream(self, data, mode=None, **kwargs):
        output = io.StringIO()
        runtime = Runtime(FakeEngine, mode, **kwargs)
        code = serve(runtime, io.BytesIO(data), output)
        self.assertIsNone(runtime.pid)
        return code, [json.loads(line) for line in output.getvalue().splitlines()]

    def test_invalid_frames_recover_and_eof_reaps(self):
        code, rows = self.run_stream(b'bad\n\xff\n{"role":"query","texts":["hello"]}\n')
        self.assertEqual(code, 0)
        self.assertEqual(rows[0]["status"], "ready")
        self.assertEqual([r["error"] for r in rows[1:3]], ["invalid_json"] * 2)
        self.assertEqual(rows[3]["result"]["dimensions"], 512)

    def test_oversized_frame_ends_session_without_reading_rest(self):
        code, rows = self.run_stream(b'x' * (MAX_LINE + 5) + b'\n{}\n')
        self.assertEqual(code, 2)
        self.assertEqual(rows[-1], {"error": "frame_too_large"})
        self.assertEqual(len(rows), 2)

    def test_model_timeout_ends_session(self):
        code, rows = self.run_stream(b'{"role":"query","texts":["hello"]}\n',
                                     "hang", request_timeout=0.1)
        self.assertEqual(code, 2)
        self.assertEqual(rows[-1], {"error": "deadline_exceeded"})

    def test_startup_failure_is_redacted(self):
        code, rows = self.run_stream(b'', "startup_failure")
        self.assertEqual(code, 2)
        self.assertEqual(rows, [{"error": "model_failed"}])
