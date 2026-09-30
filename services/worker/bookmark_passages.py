"""Offline HTML bookmark -> provenance-labelled passages. No persistence/network."""

import base64
import hashlib
import json
import re

from services.worker.bookmarks import extract_bookmark
from services.worker.text_processing import process_request, CHUNKER_VERSION

ADAPTER_VERSION = "bookmark-passages-v1"


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def prepare_bookmark(source_id: str, url: str, html: bytes | None = None,
                     *, notes: str = "", content_type: str = "text/html") -> dict:
    """Caller supplies a stable source ID, not an authorization credential.

    Each chunk points into its exact field text (Unicode code points). A source
    revision covers URL, extraction outcome, metadata and notes. No partial
    passage set is returned if an individual field fails processing.
    """
    if not isinstance(source_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", source_id):
        raise ValueError("INVALID_SOURCE_ID")
    bookmark = extract_bookmark(url, html, notes=notes, content_type=content_type)
    fields = {"url": bookmark["original_url"], "notes": bookmark["notes"],
              "page_text": bookmark["text"]}
    fields.update({f"metadata.{key}": value for key, value in sorted(bookmark["metadata"].items())})
    revision = _hash({"adapter": ADAPTER_VERSION, "chunker": CHUNKER_VERSION,
                      "bookmark": bookmark})
    chunks = []
    for field, text in fields.items():
        if not text.strip():
            continue
        try:
            raw = text.encode("utf-8")
        except UnicodeError:
            raise ValueError("INVALID_TEXT") from None
        request = {"version": 1, "request_id": source_id, "format": "txt",
                   "content_base64": base64.b64encode(raw).decode("ascii")}
        processed = process_request(json.dumps(request).encode())
        if processed["status"] != "processed":
            raise ValueError(processed["code"])
        for chunk in processed["document"]["chunks"]:
            chunks.append({**chunk, "id": _hash([source_id, revision, field, chunk["id"]]),
                           "source_id": source_id, "revision": revision, "field": field,
                           "evidence_type": "metadata" if field.startswith("metadata.") else field,
                           "url": bookmark["original_url"],
                           "offset_unit": "unicode_code_point"})
    return {"id": source_id, "revision": revision, "adapter_version": ADAPTER_VERSION,
            "parser_version": bookmark["parser_version"], "chunker_version": CHUNKER_VERSION,
            "extraction_status": bookmark["status"], "extraction_reason": bookmark["reason"],
            "status": "passages_prepared", "semantic_ready": False,
            "fields": fields, "chunks": chunks}
