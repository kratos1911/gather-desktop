import subprocess
import unittest
from unittest.mock import patch

from scripts.check_extractor_container import execute


class ContainerCleanupTests(unittest.TestCase):
    def test_timeout_removes_container_before_closing_pipes(self):
        events = []
        with patch('scripts.check_extractor_container.subprocess.Popen') as popen, \
                patch('scripts.check_extractor_container.subprocess.run') as run:
            process = popen.return_value
            process.communicate.side_effect = subprocess.TimeoutExpired('docker', 1)
            process.poll.return_value = None
            process.kill.side_effect = lambda: events.append('kill')
            process.stdout.close.side_effect = lambda: events.append('close')
            def cleanup(*args, **kwargs):
                events.append('remove')
                return subprocess.CompletedProcess([], 0, b'', b'')
            run.side_effect = cleanup
            with self.assertRaises(subprocess.TimeoutExpired):
                execute(['extractor'], timeout=1)
            command = popen.call_args.args[0]
            name = command[command.index('--name') + 1]
            self.assertTrue(name.startswith('gather-smoke-'))
            self.assertEqual(run.call_args.args[0], ['docker', 'rm', '-f', name])
            self.assertEqual(events, ['kill', 'remove', 'close'])
            process.wait.assert_called_once_with(timeout=10)

    def test_auto_removed_container_is_success(self):
        with patch('scripts.check_extractor_container.subprocess.Popen') as popen, \
                patch('scripts.check_extractor_container.subprocess.run') as run:
            process = popen.return_value
            process.communicate.return_value = (b'result', b'')
            process.poll.return_value = 0
            process.returncode = 0
            run.return_value = subprocess.CompletedProcess([], 1, b'', b'No such container')
            self.assertEqual(execute(['extractor']), b'result')
            process.kill.assert_not_called()

    def test_cleanup_failure_is_not_hidden(self):
        with patch('scripts.check_extractor_container.subprocess.Popen') as popen, \
                patch('scripts.check_extractor_container.subprocess.run') as run:
            process = popen.return_value
            process.communicate.return_value = (b'result', b'')
            process.poll.return_value = 0
            run.return_value = subprocess.CompletedProcess([], 1, b'', b'daemon unavailable')
            with self.assertRaisesRegex(RuntimeError, 'cleanup failed'):
                execute(['extractor'])
            process.stdout.close.assert_called_once()
