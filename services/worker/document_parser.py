"""Shared disposable-process limits for trusted PDF/DOCX parser entry points."""
import json
import os
import subprocess
import sys
import threading
import time

SLOT = threading.BoundedSemaphore(1)
MAX_REPLY_BYTES = 524288
WALL_SECONDS = 5


def limits():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (192 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))


def extract(raw, *, script, validate, error, prefix, child_errors, cancel=None):
    if sys.platform != 'linux':
        raise error(prefix + '_parser_unavailable')
    if not SLOT.acquire(blocking=False):
        raise error(prefix + '_busy')
    process = None
    try:
        if cancel is not None and cancel.is_set():
            raise error(prefix + '_cancelled')
        process = subprocess.Popen([sys.executable, '-I', '-B', str(script), '--child'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env={'PATH': os.defpath, 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'},
            start_new_session=True)
        deadline, first = time.monotonic() + WALL_SECONDS, True
        while True:
            if cancel is not None and cancel.is_set():
                raise error(prefix + '_cancelled')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise error(prefix + '_timeout')
            try:
                output, _ = process.communicate(input=raw if first else None, timeout=min(.1, remaining))
                break
            except subprocess.TimeoutExpired:
                first = False
        if len(output) > MAX_REPLY_BYTES:
            raise error(prefix + '_invalid_output')
        try:
            result = json.loads(output)
        except (ValueError, UnicodeError):
            raise error(prefix + '_invalid') from None
        if process.returncode:
            code = result.get('error') if type(result) is dict else None
            raise error(code if code in child_errors else prefix + '_invalid')
        return validate(result, raw)
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=2)
        SLOT.release()
