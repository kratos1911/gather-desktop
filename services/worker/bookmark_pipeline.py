"""Backend-only fetch-to-offline-parser connection. No persistence or embeddings."""
import base64
from datetime import datetime, timezone
import json
import re

from services.worker.bookmarks import normalize_url
from services.worker.extraction_adapters import _text
from services.worker.fetch_broker import FetchBroker, BrokerError
from services.worker.supervisor import DockerJobRunner


class BookmarkPipeline:
    def __init__(self, image):
        self.broker = FetchBroker()
        self.parser = DockerJobRunner(image)

    def process(self, source_id, url, *, notes='', cancel=None, fetch_timeout=15):
        # Validate before any request leaves the host. Source ID is not auth.
        if not isinstance(source_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', source_id):
            raise ValueError('INVALID_SOURCE_ID')
        url = normalize_url(url)
        notes = _text(notes, 8192)
        page = self.broker.fetch(url, timeout=fetch_timeout, cancel=cancel)
        if cancel is not None and cancel.is_set():
            raise BrokerError('FETCH_CANCELLED')
        job = {'backend': 'http-page', 'source_id': source_id, 'url': url, 'notes': notes,
               'backend_version': 'restricted-http-v1',
               'fetched_at': datetime.now(timezone.utc).isoformat(),
               'result': {'final_url': page.final_url, 'content_type': page.content_type,
                          'redirects': page.redirects,
                          'body_base64': base64.b64encode(page.body).decode('ascii')}}
        return self.parser.run(json.dumps(job).encode(), cancel=cancel)
