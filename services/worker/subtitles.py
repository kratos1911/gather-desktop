"""Bounded UTF-8 SRT/WebVTT subset for retrieval, not a subtitle renderer."""

import html
import re

MAX_BYTES = 128 * 1024
PARSER_VERSION = "subtitle-text-v1"


def _time(value, format):
    pattern = r"(?:(\d{2,6}):)?([0-5]\d):([0-5]\d)\.([0-9]{3})" if format == "vtt" else r"(\d{2,6}):([0-5]\d):([0-5]\d),([0-9]{3})"
    match = re.fullmatch(pattern, value)
    if not match:
        raise ValueError("INVALID_SUBTITLE_TIME")
    hours, minutes, seconds, millis = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def parse_subtitles(payload: bytes, format: str) -> list[dict]:
    """Reject malformed cue blocks atomically; retain overlaps and repetitions."""
    if format not in ("srt", "vtt"):
        raise ValueError("UNSUPPORTED_SUBTITLE_FORMAT")
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise ValueError("SUBTITLE_INPUT_LIMIT")
    try:
        text = payload.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError:
        raise ValueError("SUBTITLE_ENCODING") from None
    if any((ord(c) < 32 and c not in "\t\n") or 127 <= ord(c) <= 159 for c in text):
        raise ValueError("INVALID_SUBTITLE_TEXT")
    blocks = re.split(r"\n[ \t]*\n", text.strip())
    if format == "vtt":
        if not blocks or not re.fullmatch(r"WEBVTT(?:[ \t][^\n]*)?", blocks[0].split("\n")[0]):
            raise ValueError("INVALID_VTT_HEADER")
        if "-->" in blocks[0]:
            raise ValueError("INVALID_VTT_HEADER")
        blocks = blocks[1:]
    cues = []
    total = 0
    previous = -1
    for block in blocks:
        if not block.strip():
            continue
        lines = block.splitlines()
        if format == "vtt" and (re.match(r"NOTE(?:[ \t]|$)", lines[0]) or lines[0] in ("STYLE", "REGION")):
            continue
        if "-->" not in lines[0]:
            if format == "srt" and not lines[0].isdigit():
                raise ValueError("INVALID_SUBTITLE_CUE")
            lines = lines[1:]
        if len(lines) < 2:
            raise ValueError("INVALID_SUBTITLE_CUE")
        timing = re.fullmatch(r"(\S+)[ \t]+-->[ \t]+(\S+)(?:[ \t]+(.*))?", lines[0])
        if not timing or (format == "srt" and timing.group(3)):
            raise ValueError("INVALID_SUBTITLE_CUE")
        start, end = (_time(timing.group(i), format) for i in (1, 2))
        if start < previous or end <= start:
            raise ValueError("INVALID_SUBTITLE_TIME")
        body = "\n".join(lines[1:])
        if "-->" in body:
            raise ValueError("INVALID_SUBTITLE_CUE")
        # Strip cue markup before decoding entities, preserving escaped literal tags.
        body = html.unescape(re.sub(r"<[^>\n]*>", "", body)).strip()
        if not body or any((ord(c) < 32 and c not in "\t\n") or 127 <= ord(c) <= 159 for c in body):
            raise ValueError("INVALID_SUBTITLE_TEXT")
        size = len(body.encode("utf-8"))
        total += size + (1 if cues else 0)
        if size > 8192 or total > 65536 or len(cues) >= 1000:
            raise ValueError("SUBTITLE_OUTPUT_LIMIT")
        cues.append({"start": start, "end": end, "text": body})
        previous = start
    return cues
