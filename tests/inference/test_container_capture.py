"""Real subprocess pipe checks only; no Docker or model invocation."""
import json
import sys
import unittest

from scripts.check_inference_container import captured_process


class ContainerCaptureTests(unittest.TestCase):
    def test_non_ascii_and_invalid_diagnostics_preserved(self):
        code = "import sys;sys.stdout.buffer.write(b'{\"passed\":true}');sys.stderr.buffer.write(bytes([0xe2,0x96,0x8f,0xff]))"
        process = captured_process([sys.executable, '-c', code])
        stdout, stderr = process.communicate(b'', timeout=10)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(json.loads(stdout), {'passed': True})
        self.assertEqual(stderr, bytes([0xe2,0x96,0x8f,0xff]))

    def test_utf8_input_and_failure_exit_preserved(self):
        code = 'import sys;sys.stdout.buffer.write(sys.stdin.buffer.read());sys.exit(7)'
        process = captured_process([sys.executable, '-c', code])
        value = 'fictional café'.encode('utf-8')
        stdout, stderr = process.communicate(value, timeout=10)
        self.assertEqual(stdout, value)
        self.assertEqual(stderr, b'')
        self.assertEqual(process.returncode, 7)
