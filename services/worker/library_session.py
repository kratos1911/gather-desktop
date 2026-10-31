"""Internal authenticated library boundary. No public listener or signup flow.

Trusted server composition supplies SessionClient, admission factory and inference.
The factory binds a restricted admission repository to the verified Auth user;
it must never be supplied by a desktop request. Hosted DB composition is separate.
"""
from uuid import UUID

from services.worker.ingestion import submit
from services.worker.search import search, SearchError
from services.worker.service_clients import SessionClient
from services.worker.service_transport import TransportError
from services.worker.source_listing import parameters, page
from services.worker.model_availability import MODEL_HTTP, status_reply
from services.worker.pdf_processing import enrich_published


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
        except TransportError as error:
            if str(error)=='busy': raise LibraryError('busy') from None
            raise LibraryError('session_unavailable') from None
        except Exception:
            raise LibraryError('session_unavailable') from None

    def _validate_import_scope(self, original, media, confirm_cloud_storage):
        # A browser acknowledgement cannot activate an operator-only feature.
        if confirm_cloud_storage is not False or media=='application/pdf':
            raise LibraryError('file_import_disabled')

    def import_text(self, *, request_id, title, original, media, source_id=None,
                    confirm_cloud_storage=False):
        owner = self._owner()
        document=self._validate_import_scope(original,media,confirm_cloud_storage)
        try:
            # No owner parameter exists on the user-facing method.
            return submit(self._admission(owner), request_id=request_id, title=title,
                          original=original, media=media, source_id=source_id,document=document)
        except Exception:
            raise LibraryError('import_failed') from None

    def search(self, query, *, limit=20, cancel=None):
        try:
            # Existing search verifies Auth before embedding; no cached identity.
            return search(query, api=self._api, provider=self._provider, limit=limit, cancel=cancel)
        except SearchError as error:
            if str(error) in MODEL_HTTP or str(error) in ('cancelled','invalid_query','session_unavailable',
                              'library_unavailable','search_failed'):
                raise LibraryError(str(error)) from None
            raise LibraryError('search_failed') from None
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
        return self._rpc('source_processing_status_with_recovery', {'p_source':source_id})

    def model_status(self, *, cancel=None):
        self._owner()  # User identity must be verified before any cloud probe.
        try:
            return status_reply(self._provider.check_ready(cancel=cancel))
        except Exception:
            if cancel is not None and cancel.is_set(): raise LibraryError('cancelled') from None
            raise LibraryError('model_unavailable') from None

    def list_sources(self, *, limit=20, cursor=None):
        self._owner()
        try:
            rows = self._api('POST','/rest/v1/rpc/list_library_sources_with_recovery',parameters(limit,cursor))
            return page(rows,limit,cursor)
        except Exception:
            raise LibraryError('library_unavailable') from None

    def open(self, source_id, version_id):
        documents=self._rpc('open_published_text', {'p_source':source_id,'p_version':version_id})
        try: return enrich_published(self._api,source_id,version_id,documents)
        except Exception: raise LibraryError('library_operation_failed') from None

    def delete(self, source_id):
        # Tombstone now; durable cleanup removes original/derivatives separately.
        return self._rpc('request_source_deletion', {'p_source_id':source_id})

    def cleanup(self, source_id):
        return self._rpc('complete_source_cleanup',{'p_source':source_id})

    def process(self, source_id, job_id, expected_attempts):
        self._owner()
        self._validate_process_scope()
        try:
            if type(expected_attempts) is not int or not 0<=expected_attempts<=2:
                raise ValueError()
            return self._api('POST','/rest/v1/rpc/request_automatic_processing',
                {'p_source':identifier(source_id),'p_job':identifier(job_id),'p_attempts':expected_attempts})
        except Exception:
            raise LibraryError('library_operation_failed') from None

    def _validate_process_scope(self):
        """Trusted composition may refuse work before changing durable intent."""
