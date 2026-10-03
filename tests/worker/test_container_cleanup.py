import subprocess
import unittest
from unittest.mock import patch

from scripts.check_extractor_container import execute


class ContainerCleanupTests(unittest.TestCase):
    def test_timeout_removes_exact_named_container(self):
        with patch('scripts.check_extractor_container.subprocess.run') as run:
            run.side_effect = [subprocess.TimeoutExpired('docker', 1),
                               subprocess.CompletedProcess([], 0, b'', b'')]
            with self.assertRaises(subprocess.TimeoutExpired):
                execute(['extractor'], timeout=1)
            command = run.call_args_list[0].args[0]
            name = command[command.index('--name') + 1]
            self.assertTrue(name.startswith('gather-smoke-'))
            self.assertEqual(run.call_args_list[1].args[0], ['docker', 'rm', '-f', name])

    def test_auto_removed_container_is_success(self):
        with patch('scripts.check_extractor_container.subprocess.run') as run:
            run.side_effect = [subprocess.CompletedProcess([], 0, b'result', b''),
                               subprocess.CompletedProcess([], 1, b'', b'No such container')]
            self.assertEqual(execute(['extractor']), b'result')

    def test_cleanup_failure_is_not_hidden(self):
        with patch('scripts.check_extractor_container.subprocess.run') as run:
            run.side_effect = [subprocess.CompletedProcess([], 0, b'result', b''),
                               subprocess.CompletedProcess([], 1, b'', b'daemon unavailable')]
            with self.assertRaisesRegex(RuntimeError, 'cleanup failed'):
                execute(['extractor'])
