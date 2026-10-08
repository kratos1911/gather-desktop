"""Offline adapter for a fetched, bounded page; never makes network calls."""
import base64
import hashlib

from services.worker.bookmarks import extract_bookmark, normalize_url
from services.worker.bookmark_passages import prepare_extracted
from services.worker.extraction_adapters import _base, _text
from services.worker.restricted_fetch import MAX_BODY, MAX_REDIRECTS, CONTENT_TYPES


def http_page_passages(source_id, url, result, *, backend_version, fetched_at, notes=''):
    if not isinstance(result, dict) or set(result) != {
            'body_base64', 'content_type', 'final_url', 'redirects'}:
        raise ValueError('INVALID_HTTP_PAGE')
    if (result['content_type'] not in CONTENT_TYPES or type(result['redirects']) is not int
            or not 0 <= result['redirects'] <= MAX_REDIRECTS):
        raise ValueError('INVALID_HTTP_PAGE')
    body = base64.b64decode(result['body_base64'], validate=True)
    if len(body) > MAX_BODY:
        raise ValueError('HTTP_PAGE_TOO_LARGE')
    bookmark = _base(url, notes, 'http-page', backend_version, fetched_at)
    if result['content_type'] == 'text/plain':
        text = _text(body.decode('utf-8-sig'))
        bookmark.update(text=text, status='extracted' if text.strip() else 'extraction-unavailable',
                        reason=None if text.strip() else 'NO_READABLE_TEXT',
                        source_sha256=hashlib.sha256(body).hexdigest(),
                        parser_version='http-plain-v1', extraction_method='plain_text')
    else:
        # XHTML is treated as bounded HTML text, never as an XML/DTD document.
        bookmark.update(extract_bookmark(url, body, notes=notes, content_type='text/html'))
    bookmark.update(final_url=normalize_url(result['final_url']),
                    content_type=result['content_type'], redirects=result['redirects'])
    document = prepare_extracted(source_id, bookmark)
    document['fetch'] = {'original_url': bookmark['original_url'],
                         'final_url': bookmark['final_url'], 'fetched_at': bookmark['fetched_at'],
                         'backend': 'restricted-http-v1', 'content_type': result['content_type'],
                         'redirects': result['redirects'],
                         'body_sha256': hashlib.sha256(body).hexdigest()}
    return document
