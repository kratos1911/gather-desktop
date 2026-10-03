"""Trusted host-side supervisor for one offline Docker extraction job.

No daemon socket is exposed to the worker. This is not an authenticated API or
durable queue. Only the operator supplies an already-built image digest.
"""
import json
import re
import subprocess
import threading
import time
import uuid

from services.worker.extractor_runner import MAX_INPUT, MAX_OUTPUT

_SLOT = threading.BoundedSemaphore(1)


class WorkerError(RuntimeError):
    """Stable code without job content or Docker diagnostics."""


class DockerJobRunner:
    # A fixed trusted command, never supplied by job data.
    _COMMAND = ('python', '-m', 'services.worker.extractor_runner')

    def __init__(self, image):
        if not isinstance(image, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
            raise ValueError('WORKER_IMAGE_DIGEST_REQUIRED')
        self.image = image

    def run(self, payload, *, cancel=None, timeout=30):
        if not isinstance(payload, bytes) or len(payload) > MAX_INPUT:
            raise WorkerError('WORKER_INPUT_DENIED')
        if type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('WORKER_TIMEOUT_INVALID')
        if cancel is not None and cancel.is_set():
            raise WorkerError('WORKER_CANCELLED')
        if not _SLOT.acquire(blocking=False):
            raise WorkerError('WORKER_BUSY')
        name = 'gather-job-' + uuid.uuid4().hex
        process = None
        threads = []
        try:
            created = subprocess.run([
                'docker', 'create', '--pull', 'never', '--name', name, '-i',
                '--network', 'none', '--read-only', '--user', '65532:65532',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                '--memory', '1g', '--memory-swap', '1g', '--cpus', '1',
                '--pids-limit', '64', '--log-driver', 'none',
                '--tmpfs', '/tmp:size=67108864,mode=1777',
                '--entrypoint', self._COMMAND[0], self.image, *self._COMMAND[1:],
            ], capture_output=True, timeout=15)
            if created.returncode:
                raise WorkerError('WORKER_START_FAILED')
            if cancel is not None and cancel.is_set():
                raise WorkerError('WORKER_CANCELLED')
            process = subprocess.Popen(['docker', 'start', '--attach', '--interactive', name],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            overflow = threading.Event()
            io_error = threading.Event()
            output = bytearray()

            def drain(stream, limit, retain=False):
                count = 0
                try:
                    while chunk := stream.read1(8192):
                        count += len(chunk)
                        if count > limit:
                            overflow.set()
                        elif retain:
                            output.extend(chunk)
                except (OSError, ValueError):
                    io_error.set()

            def send():
                try:
                    process.stdin.write(payload)
                    process.stdin.close()
                except (OSError, ValueError):
                    io_error.set()

            threads = [threading.Thread(target=drain, args=(process.stdout, MAX_OUTPUT + 1, True)),
                       threading.Thread(target=drain, args=(process.stderr, 8192)),
                       threading.Thread(target=send)]
            for thread in threads:
                thread.daemon = True
                thread.start()
            deadline = time.monotonic() + timeout
            while process.poll() is None:
                if overflow.is_set():
                    raise WorkerError('WORKER_OUTPUT_LIMIT')
                if cancel is not None and cancel.is_set():
                    raise WorkerError('WORKER_CANCELLED')
                if time.monotonic() >= deadline:
                    raise WorkerError('WORKER_TIMEOUT')
                overflow.wait(min(0.02, max(0, deadline - time.monotonic())))
            for thread in threads:
                thread.join(timeout=2)
            if any(thread.is_alive() for thread in threads):
                raise WorkerError('WORKER_IO_FAILED')
            if overflow.is_set():
                raise WorkerError('WORKER_OUTPUT_LIMIT')
            if io_error.is_set() or process.returncode:
                raise WorkerError('WORKER_FAILED')
            try:
                response = json.loads(output)
            except (ValueError, UnicodeError, RecursionError):
                raise WorkerError('WORKER_INVALID_RESULT') from None
            if not isinstance(response, dict) or response.get('status') not in ('processed', 'error'):
                raise WorkerError('WORKER_INVALID_RESULT')
            return response
        except (OSError, subprocess.SubprocessError):
            raise WorkerError('WORKER_UNAVAILABLE') from None
        finally:
            try:
                if process is not None and process.poll() is None:
                    process.kill()
                # Remove before closing pipes: Windows child handles can outlive
                # the Docker client. This targets only this job's random name.
                removed = subprocess.run(['docker', 'rm', '--force', name],
                                         capture_output=True, timeout=15)
                if removed.returncode and b'No such container' not in removed.stderr:
                    raise WorkerError('WORKER_CLEANUP_FAILED')
            except (OSError, subprocess.SubprocessError):
                raise WorkerError('WORKER_CLEANUP_FAILED') from None
            finally:
                if process is not None:
                    try:
                        process.wait(timeout=5)
                        for thread in threads:
                            thread.join(timeout=2)
                        if any(thread.is_alive() for thread in threads):
                            raise WorkerError('WORKER_CLEANUP_FAILED')
                        for stream in (process.stdin, process.stdout, process.stderr):
                            stream.close()
                    except (OSError, subprocess.SubprocessError):
                        raise WorkerError('WORKER_CLEANUP_FAILED') from None
                    finally:
                        _SLOT.release()
                else:
                    _SLOT.release()
