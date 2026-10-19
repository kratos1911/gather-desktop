"""Lifecycle-owned Google key refresh; inbound requests never initiate fetching."""
import asyncio
import threading
import time

from services.inference.service_auth import GoogleServiceAuth
from services.worker.cloud_identity import receiver_identity
from services.worker.service_transport import request_google_certificates


class ManagedGoogleServiceAuth:
    def __init__(self, identity, caller_subject=None):
        self._identity = receiver_identity(identity, caller_subject)
        self._snapshot = None
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._next_attempt = 0
        self._delay = 30
        self._started = False

    @property
    def identity(self):
        return self._identity

    @property
    def ready(self):
        snapshot = self._snapshot
        return not self._stop.is_set() and snapshot is not None and snapshot.ready

    def __call__(self, headers):
        snapshot = self._snapshot
        return bool(self.ready and snapshot(headers) and not self._stop.is_set())

    def _refresh(self):
        if not self._lock.acquire(blocking=False):
            return False
        try:
            started, wall = time.monotonic(), time.time()
            if self._stop.is_set() or started < self._next_attempt:
                return False
            self._next_attempt = started+30
            self._delay = 30
            result = request_google_certificates(cancel=self._stop)
            ttl = result['ttl']
            if type(ttl) not in (int,float) or not 0 < ttl <= 300:
                return False
            remaining = ttl-(time.monotonic()-started)
            if remaining <= 0 or self._stop.is_set():
                return False
            candidate = GoogleServiceAuth(self._identity,None,
                                          result['certificates'],key_ttl=remaining)
            candidate._deadline = min(candidate._deadline,started+ttl)
            candidate._expires = min(candidate._expires,wall+ttl)
            if self._stop.is_set() or not candidate.ready:
                return False
            self._snapshot = candidate  # Publish only the complete validated snapshot.
            self._delay = max(30, min(240, remaining*.8))
            return True
        except Exception:
            # Keep the old snapshot only within its original freshness; never extend it.
            return False
        finally:
            self._lock.release()

    def _loop(self):
        while not self._stop.wait(self._delay):
            self._refresh()

    async def start(self, *, cancel):
        if self._started:
            raise ValueError('auth_lifecycle_already_started')
        self._started = True
        self._stop = cancel
        if not await asyncio.to_thread(self._refresh):
            raise ValueError('trusted_keys_unavailable')
        if self._stop.is_set():
            raise ValueError('trusted_keys_unavailable')
        self._thread = threading.Thread(target=self._loop,daemon=True,name='gather-key-refresh')
        self._thread.start()

    async def close(self):
        self._stop.set()
        if self._thread is not None:
            await asyncio.to_thread(self._thread.join,8)
            if self._thread.is_alive():
                raise RuntimeError('auth_cleanup_failed')
        self._snapshot = None
