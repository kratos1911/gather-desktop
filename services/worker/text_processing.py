"""Bounded, deterministic UTF-8 processing. No filesystem, network or model calls."""

import base64
import binascii
import hashlib
import json
import re
from typing import Literal, TypedDict

MAX_SOURCE_BYTES = 64 * 1024
MAX_REQUEST_BYTES = 96 * 1024
MAX_RESPONSE_BYTES = 512 * 1024
MAX_CHUNKS = 256
CHUNK_CHARACTERS = 1024
OVERLAP_CHARACTERS = 128
PARSER_VERSION = "utf8-plain-v1"
CHUNKER_VERSION = "boundary-1024-overlap128-v1"


class Request(TypedDict):
    version: Literal[1]
    request_id: str
    format: Literal["txt", "md"]
    content_base64: str


class Chunk(TypedDict):
    id: str
    start: int
    end: int
    text: str


class Document(TypedDict):
    source_sha256: str
    format: str
    parser_version: str
    chunker_version: str
    offset_unit: Literal["unicode_code_point"]
    character_count: int
    chunks: list[Chunk]


class Success(TypedDict):
    version: Literal[1]
    request_id: str
    status: Literal["processed"]
    document: Document


class Failure(TypedDict):
    version: Literal[1]
    request_id: str | None
    status: Literal["error"]
    code: str
    message: str
    retryable: Literal[False]


MESSAGES = {
    "INVALID_REQUEST": "Provide a version 1 text-processing request with the required fields.",
    "REQUEST_TOO_LARGE": "The request exceeds the 96 KiB processing limit.",
    "UNSUPPORTED_FORMAT": "Only TXT and Markdown are supported by this processor.",
    "INVALID_BASE64": "The document payload is not valid base64.",
    "SOURCE_TOO_LARGE": "The document exceeds the 64 KiB processing limit.",
    "UNSUPPORTED_ENCODING": "Save the document as UTF-8 before processing it.",
    "BINARY_CONTENT": "The document contains unsupported control characters.",
    "EMPTY_CONTENT": "The document contains no searchable text.",
    "RESULT_TOO_LARGE": "The extracted result exceeds the processing limit.",
}


def _error(code: str, request_id: str | None = None) -> Failure:
    return {"version": 1, "request_id": request_id, "status": "error",
            "code": code, "message": MESSAGES[code], "retryable": False}


def _chunks(text: str, source_hash: str, source_format: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARACTERS, len(text))
        if end < len(text):
            # Prefer a paragraph/line/word boundary in the latter half of a window.
            lower = start + CHUNK_CHARACTERS // 2
            for separator in ("\n\n", "\n", " "):
                boundary = text.rfind(separator, lower, end)
                if boundary != -1:
                    end = boundary + len(separator)
                    break
        identity = f"{source_hash}:{source_format}:{PARSER_VERSION}:{CHUNKER_VERSION}:{start}:{end}"
        chunks.append({"id": hashlib.sha256(identity.encode("ascii")).hexdigest(),
                       "start": start, "end": end, "text": text[start:end]})
        if end == len(text):
            break
        start = end - OVERLAP_CHARACTERS
    return chunks


def process_request(payload: bytes) -> Success | Failure:
    """Process one bounded JSON request. Caller must bound transport reads too."""
    if not isinstance(payload, bytes):
        return _error("INVALID_REQUEST")
    if len(payload) > MAX_REQUEST_BYTES:
        return _error("REQUEST_TOO_LARGE")
    try:
        request = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return _error("INVALID_REQUEST")
    if not isinstance(request, dict):
        return _error("INVALID_REQUEST")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request_id):
        return _error("INVALID_REQUEST")
    if (set(request) != {"version", "request_id", "format", "content_base64"}
            or type(request.get("version")) is not int or request["version"] != 1):
        return _error("INVALID_REQUEST", request_id)
    if request["format"] not in ("txt", "md"):
        return _error("UNSUPPORTED_FORMAT", request_id)
    encoded = request["content_base64"]
    if not isinstance(encoded, str):
        return _error("INVALID_BASE64", request_id)
    if len(encoded) > 4 * ((MAX_SOURCE_BYTES + 2) // 3):
        return _error("SOURCE_TOO_LARGE", request_id)
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return _error("INVALID_BASE64", request_id)
    if len(raw) > MAX_SOURCE_BYTES:
        return _error("SOURCE_TOO_LARGE", request_id)
    try:
        # Keep BOM, line endings, whitespace and Markdown syntax for exact offsets.
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _error("UNSUPPORTED_ENCODING", request_id)
    if any((ord(c) < 32 and c not in "\t\n\r") or 127 <= ord(c) <= 159 for c in text):
        return _error("BINARY_CONTENT", request_id)
    if not text.lstrip("\ufeff").strip():
        return _error("EMPTY_CONTENT", request_id)
    source_hash = hashlib.sha256(raw).hexdigest()
    chunks = _chunks(text, source_hash, request["format"])
    result: Success = {
        "version": 1, "request_id": request_id, "status": "processed",
        "document": {"source_sha256": source_hash, "format": request["format"],
                     "parser_version": PARSER_VERSION, "chunker_version": CHUNKER_VERSION,
                     "offset_unit": "unicode_code_point", "character_count": len(text),
                     "chunks": chunks},
    }
    if len(chunks) > MAX_CHUNKS or len(serialize_response(result)) > MAX_RESPONSE_BYTES:
        return _error("RESULT_TOO_LARGE", request_id)
    return result


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


def serialize_response(response: Success | Failure) -> bytes:
    """Canonical UTF-8 response encoding, including the response-size check's format."""
    return json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
