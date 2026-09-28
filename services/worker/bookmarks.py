"""Offline bookmark extraction. Never fetches URLs or renders HTML.

URL validation is input hygiene, NOT a network SSRF boundary. A future fetcher
must enforce DNS, redirects, connection addresses, quotas and response limits.
"""

import hashlib
import ipaddress
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit

MAX_HTML_BYTES = 64 * 1024
PARSER_VERSION = "bookmark-html-v1"


def normalize_url(url: str) -> str:
    if not isinstance(url, str) or not url or len(url) > 4096:
        raise ValueError("INVALID_URL")
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url) or "\\" in url:
        raise ValueError("INVALID_URL")
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
        if parts.scheme.lower() not in {"http", "https"} or not host or parts.username is not None or parts.password is not None:
            raise ValueError()
        host = host.encode("idna").decode("ascii").lower().rstrip(".")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if "." not in host or host.endswith((".localhost", ".local", ".internal")):
                raise ValueError()
            if len(host) > 253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")):
                raise ValueError()
        else:
            if not address.is_global:
                raise ValueError()
            host = f"[{host}]" if address.version == 6 else host
        netloc = host
        if port is not None and port != (443 if parts.scheme.lower() == "https" else 80):
            netloc += f":{port}"
        return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, parts.fragment))
    except (ValueError, UnicodeError):
        raise ValueError("INVALID_URL") from None


class _Page(HTMLParser):
    SKIP = {"script", "style", "template", "noscript", "nav", "footer", "aside", "iframe", "svg"}
    BLOCK = {"p", "div", "section", "article", "main", "h1", "h2", "h3", "li", "br", "tr"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.title = []
        self.metadata = {}
        self.body = []
        self.focus = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = tag in self.SKIP or "hidden" in attrs or attrs.get("aria-hidden") == "true"
        suppressed = hidden or any(entry[1] for entry in self.stack)
        if tag == "meta" and not suppressed:
            key = attrs.get("property") or attrs.get("name")
            if key in {"og:title", "og:description", "description", "author", "og:site_name"}:
                value = " ".join((attrs.get("content") or "").split())
                if value:
                    self.metadata.setdefault(key, value)
        if tag in self.BLOCK and not suppressed:
            self._append("\n")
        if tag not in self.VOID:
            if len(self.stack) >= 256:
                raise ValueError("HTML_TOO_DEEP")
            self.stack.append((tag, suppressed))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.handle_data("\n")
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def _append(self, text):
        self.body.append(text)
        if any(tag in {"main", "article"} for tag, _ in self.stack):
            self.focus.append(text)

    def handle_data(self, data):
        if any(hidden for _, hidden in self.stack):
            return
        tags = {tag for tag, _ in self.stack}
        if "title" in tags:
            self.title.append(data)
        elif "head" not in tags:
            self._append(data)


def extract_bookmark(url: str, html: bytes | None = None, *, notes: str = "",
                     content_type: str = "text/html") -> dict:
    """Return text/provenance or an honest fallback from caller-supplied bytes.

    Offsets refer to normalized extracted text, never raw HTML. UTF-8 only in v1.
    Fetch time/redirect provenance belong to the future trusted fetcher.
    """
    normalized = normalize_url(url)
    if not isinstance(notes, str) or len(notes) > 8192:
        raise ValueError("INVALID_NOTES")
    result = {"original_url": url, "normalized_url": normalized, "notes": notes,
              "parser_version": PARSER_VERSION, "status": "extraction-unavailable",
              "reason": "NO_CONTENT", "metadata": {}, "text": "", "passages": []}
    if html is None:
        return result
    if not isinstance(html, bytes):
        raise ValueError("INVALID_CONTENT")
    if len(html) > MAX_HTML_BYTES:
        result["reason"] = "CONTENT_TOO_LARGE"
        return result
    if content_type.split(";", 1)[0].strip().lower() != "text/html":
        result["reason"] = "UNSUPPORTED_CONTENT_TYPE"
        return result
    try:
        source = html.decode("utf-8-sig", errors="strict")
    except UnicodeError:
        result["reason"] = "UNSUPPORTED_ENCODING"
        return result
    if any(ord(c) < 32 and c not in "\t\r\n" for c in source):
        result["reason"] = "INVALID_TEXT"
        return result
    page = _Page()
    try:
        page.feed(source)
        page.close()
    except ValueError:
        result["reason"] = "HTML_TOO_DEEP"
        return result
    metadata = page.metadata
    title = " ".join("".join(page.title).split())
    if title:
        metadata.setdefault("title", title)
    focused = "".join(page.focus).strip()
    lines = [" ".join(line.split()) for line in (focused or "".join(page.body)).splitlines()]
    text = "\n".join(line for line in lines if line)
    result.update(metadata=metadata, text=text, source_sha256=hashlib.sha256(html).hexdigest(),
                  evidence_type="page_text" if text else "metadata",
                  extraction_method="main_article" if focused else "body_fallback")
    result["status"] = "extracted" if text else "metadata-only" if metadata else "extraction-unavailable"
    result["reason"] = None if text or metadata else "NO_READABLE_TEXT"
    start = 0
    for i, paragraph in enumerate(text.splitlines()):
        result["passages"].append({"paragraph": i + 1, "start": start, "end": start + len(paragraph)})
        start += len(paragraph) + 1
    return result
