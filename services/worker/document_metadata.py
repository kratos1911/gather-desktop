"""Exact published-version metadata; each reader retains its format validation."""
from services.worker.pdf_processing import enrich_published as pdf_metadata
from services.worker.docx_processing import enrich_published as docx_metadata
from services.worker.image_processing import enrich_published as image_metadata


def enrich_published(api, source_id, version_id, documents):
    return image_metadata(api, source_id, version_id, docx_metadata(api, source_id, version_id,
                         pdf_metadata(api, source_id, version_id, documents)))
