"""Internal authenticated library boundary. No public listener or signup flow.

Trusted server composition supplies SessionClient, admission factory and inference.
The factory binds a restricted admission repository to the verified Auth user;
it must never be supplied by a desktop request. Hosted DB composition is separate.
"""
from uuid import UUID

from services.worker.ingestion import submit
from services.worker.search import search
from services.worker.service_clients import SessionClient


class LibraryError(Exception):
    """Safe fixed errors; no session token, source bytes or database exception."""


def identifier(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError('invalid_identifier')
    return value


class LibrarySession:
    def __init__(self, api, admission_factory, provider):
        if not isinstance(api, SessionClient) or not callable(admission_factory):
            raise ValueError('invalid_library_configuration')
        self._api, self._admission, self._provider = api, admission_factory, provider

    def _owner(self):
        try:
            # This HTTPS Auth request verifies the bearer; decoding JWT is insufficient.
            return identifier(self._api('GET', '/auth/v1/user')['id'])
        except Exception:
            raise LibraryError('session_unavailable') from None

    def import_text(self, *, request_id, title, original, media, source_id=None):
        owner = self._owner()
        try:
            # No owner parameter exists on the user-facing method.
            return submit(self._admission(owner), request_id=request_id, title=title,
                          original=original, media=media, source_id=source_id)
        except Exception:
            raise LibraryError('import_failed') from None

    def search(self, query, *, limit=20, cancel=None):
        try:
            # Existing search verifies Auth before embedding; no cached identity.
            return search(query, api=self._api, provider=self._provider, limit=limit, cancel=cancel)
        except Exception:
            raise LibraryError('search_failed') from None

    def _rpc(self, name, payload):
        self._owner()
        try:
            for value in payload.values():
                identifier(value)
            # Preserve the original user bearer: PostgREST enforces ownership too.
            return self._api('POST', '/rest/v1/rpc/'+name, payload)
        except Exception:
            raise LibraryError('library_operation_failed') from None

    def status(self, source_id):
        return self._rpc('source_processing_status', {'p_source':source_id})

    def open(self, source_id, version_id):
        return self._rpc('open_published_text', {'p_source':source_id,'p_version':version_id})

    def delete(self, source_id):
        # Tombstone now; durable cleanup removes original/derivatives separately.
        return self._rpc('request_source_deletion', {'p_source_id':source_id})
