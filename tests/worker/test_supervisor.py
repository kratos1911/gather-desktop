import threading
import unittest
from unittest.mock import patch

from services.worker.supervisor import DockerJobRunner, WorkerError, _SLOT

IMAGE = 'sha256:' + 'a' * 64


class SupervisorTests(unittest.TestCase):
    def test_image_must_be_operator_selected_digest(self):
        for image in ['latest', 'gather-extraction-extractor', 'sha256:bad', None]:
            with self.subTest(image=image), self.assertRaises(ValueError):
                DockerJobRunner(image)

    def test_oversized_or_nonbyte_input_cannot_start_docker(self):
        with patch('services.worker.supervisor.subprocess.run') as run:
            for payload in ['{}', b'x' * (256 * 1024 + 1)]:
                with self.assertRaisesRegex(WorkerError, 'INPUT_DENIED'):
                    DockerJobRunner(IMAGE).run(payload)
            run.assert_not_called()

    def test_cancelled_job_never_starts(self):
        cancelled = threading.Event()
        cancelled.set()
        with patch('services.worker.supervisor.subprocess.run') as run:
            with self.assertRaisesRegex(WorkerError, 'CANCELLED'):
                DockerJobRunner(IMAGE).run(b'{}', cancel=cancelled)
            run.assert_not_called()

    def test_busy_supervisor_has_no_unbounded_wait_queue(self):
        _SLOT.acquire()
        try:
            with patch('services.worker.supervisor.subprocess.run') as run:
                with self.assertRaisesRegex(WorkerError, 'BUSY'):
                    DockerJobRunner(IMAGE).run(b'{}')
                run.assert_not_called()
        finally:
            _SLOT.release()

    def test_invalid_time_budgets_rejected_before_launch(self):
        for timeout in [0, -1, 61, True, float('nan'), float('inf'), '30']:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                DockerJobRunner(IMAGE).run(b'{}', timeout=timeout)
