"""Pure adapters for supplied extraction outputs, never fetch or execute tools."""

import math
import re
from datetime import datetime

from services.worker.bookmarks import extract_bookmark, normalize_url
from services.worker.bookmark_passages import prepare_extracted


def _text(value, limit=65536):
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("INVALID_EXTRACTED_TEXT")
    try:
        if len(value.encode("utf-8")) > limit:
            raise ValueError("EXTRACTED_TEXT_TOO_LARGE")
    except UnicodeError:
        raise ValueError("INVALID_EXTRACTED_TEXT") from None
    if any((ord(c) < 32 and c not in "\t\r\n") or 127 <= ord(c) <= 159 for c in value):
        raise ValueError("INVALID_EXTRACTED_TEXT")
    return value


def _base(url, notes, backend, version, fetched_at):
    if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9._+-]{1,64}", version):
        raise ValueError("INVALID_BACKEND_VERSION")
    try:
        timestamp = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        if timestamp.utcoffset() is None:
            raise ValueError()
    except (ValueError, AttributeError, TypeError):
        raise ValueError("INVALID_FETCH_TIME") from None
    bookmark = extract_bookmark(url, notes=_text(notes, 8192))
    bookmark.update(parser_version=f"{backend}-output-v1", backend=backend,
                    backend_version=version, fetched_at=timestamp.isoformat())
    return bookmark


def crawl4ai_passages(source_id, url, result, *, backend_version, fetched_at, notes=""):
    """Accept a CrawlResult.model_dump() dictionary, not executable objects."""
    bookmark = _base(url, notes, "crawl4ai", backend_version, fetched_at)
    if not isinstance(result, dict) or type(result.get("success")) is not bool:
        raise ValueError("INVALID_CRAWL_RESULT")
    if not result["success"]:
        bookmark["reason"] = "EXTRACTION_FAILED"
    else:
        code = result.get("redirected_status_code") or result.get("status_code")
        if type(code) is not int or not 200 <= code < 300:
            bookmark["reason"] = "HTTP_UNAVAILABLE"
        else:
            bookmark["final_url"] = normalize_url(result.get("url"))
            markdown = result.get("markdown")
            if isinstance(markdown, dict):
                markdown = markdown.get("raw_markdown")
            bookmark["text"] = _text(markdown)
            metadata = result.get("metadata") or {}
            if not isinstance(metadata, dict):
                raise ValueError("INVALID_METADATA")
            bookmark["metadata"] = {key: _text(metadata[key], 4096) for key in
                                    ("title", "description", "author") if metadata.get(key)}
            bookmark["status"] = "extracted" if bookmark["text"].strip() else "metadata-only" if bookmark["metadata"] else "extraction-unavailable"
            bookmark["reason"] = None if bookmark["status"] != "extraction-unavailable" else "NO_READABLE_TEXT"
    document = prepare_extracted(source_id, bookmark)
    document["provenance"] = {key: bookmark[key] for key in
                              ("backend", "backend_version", "fetched_at", "final_url") if key in bookmark}
    document["content_format"] = "markdown"
    return document


def ytdlp_passages(source_id, url, info, *, backend_version, fetched_at, notes="",
                   cues=None, language=None, automatic=False):
    """Single-video info plus supplied normalized cues; never follows subtitle URLs.

    Cues: {start: seconds, end: seconds, text: string}. Parsing downloaded VTT/SRT
    and determining the actual language/automatic flag belong to a future runner.
    """
    bookmark = _base(url, notes, "yt-dlp", backend_version, fetched_at)
    if not isinstance(info, dict) or info.get("_type", "video") != "video":
        raise ValueError("INVALID_VIDEO_RESULT")
    bookmark["metadata"] = {key: _text(info[key], 8192) for key in
                            ("title", "description", "uploader") if info.get(key)}
    if info.get("webpage_url"):
        bookmark["final_url"] = normalize_url(info["webpage_url"])
    if cues is None:
        cues = []
    if not isinstance(cues, list) or len(cues) > 1000 or type(automatic) is not bool:
        raise ValueError("INVALID_SUBTITLES")
    if cues and (not isinstance(language, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,32}", language)):
        raise ValueError("INVALID_SUBTITLE_LANGUAGE")
    spans = []
    texts = []
    offset = 0
    previous = -1
    for cue in cues:
        if not isinstance(cue, dict) or set(cue) != {"start", "end", "text"}:
            raise ValueError("INVALID_SUBTITLE_CUE")
        start, end = cue["start"], cue["end"]
        if any(type(t) not in (int, float) or not math.isfinite(t) for t in (start, end)) or start < 0 or end <= start or start < previous:
            raise ValueError("INVALID_SUBTITLE_TIME")
        text = _text(cue["text"], 8192)
        if not text.strip():
            raise ValueError("EMPTY_SUBTITLE_CUE")
        spans.append({"start": offset, "end": offset + len(text), "start_seconds": start, "end_seconds": end})
        texts.append(text)
        offset += len(text) + 1
        if offset > 65537:
            raise ValueError("EXTRACTED_TEXT_TOO_LARGE")
        previous = start
    bookmark["text"] = _text("\n".join(texts))
    bookmark.update(subtitle_spans=spans, language=language, automatic=automatic)
    bookmark["status"] = "extracted" if spans else "metadata-only" if bookmark["metadata"] else "extraction-unavailable"
    bookmark["reason"] = None if spans else "NO_SUBTITLES"
    document = prepare_extracted(source_id, bookmark)
    document["provenance"] = {key: bookmark[key] for key in
                              ("backend", "backend_version", "fetched_at", "final_url") if key in bookmark}
    for chunk in document["chunks"]:
        if chunk["field"] == "page_text":
            chunk["evidence_type"] = "subtitle"
            chunk["language"] = language
            chunk["automatic"] = automatic
            chunk["cue_spans"] = [s.copy() for s in spans if s["start"] < chunk["end"] and s["end"] > chunk["start"]]
    return document
