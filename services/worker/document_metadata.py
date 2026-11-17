"""Exact published-version metadata; each reader retains its format validation."""
import base64
from hashlib import sha256

from services.worker.pdf_processing import enrich_published as pdf_metadata
from services.worker.docx_processing import MEDIA as DOCX_MEDIA, enrich_published as docx_metadata
from services.worker.image_processing import MEDIA as IMAGE_MEDIA, enrich_published as image_metadata

ORIGINAL_MEDIA = frozenset(('text/plain', 'text/markdown', 'application/pdf', DOCX_MEDIA, *IMAGE_MEDIA))


def enrich_published(api, source_id, version_id, documents):
    return image_metadata(api, source_id, version_id, docx_metadata(api, source_id, version_id,
                         pdf_metadata(api, source_id, version_id, documents)))


def checked_original(source_id, version_id, value):
    if value is None:
        return None
    if (type(value) is not dict or set(value) != {
            'source_id', 'version_id', 'title', 'media_type', 'source_sha256', 'content_base64'}
            or (value['source_id'], value['version_id']) != (source_id, version_id)
            or type(value['title']) is not str or not 1 <= len(value['title'].strip()) <= 500
            or value['media_type'] not in ORIGINAL_MEDIA):
        raise ValueError('invalid_original')
    encoded = value['content_base64']
    if type(encoded) is not str or not 4 <= len(encoded) <= 87384:
        raise ValueError('invalid_original')
    raw = base64.b64decode(encoded, validate=True)
    if not 1 <= len(raw) <= 65536 or sha256(raw).hexdigest() != value['source_sha256']:
        raise ValueError('invalid_original')
    return value
