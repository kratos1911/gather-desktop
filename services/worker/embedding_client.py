"""Developer/server-only embeddings client. No automatic credentials or calls."""

from dataclasses import dataclass
import json
import math
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class EmbeddingError(Exception):
    """Fixed errors never include provider bodies, input text or credentials."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def https_transport(endpoint: str, api_key: str) -> Callable[[dict], dict]:
    """Create transport for an operator-reviewed endpoint, never a user's URL."""
    url = urlsplit(endpoint)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.query or url.fragment or not api_key.strip() or "\n" in api_key or "\r" in api_key):
        raise EmbeddingError("Invalid endpoint or credential configuration")
    opener = build_opener(_NoRedirect())

    def send(body: dict) -> dict:
        request = Request(endpoint, data=json.dumps(body).encode("utf-8"), method="POST",
                          headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
        try:
            with opener.open(request, timeout=30) as response:
                data = response.read(4 * 1024 * 1024 + 1)
            if len(data) > 4 * 1024 * 1024:
                raise EmbeddingError("Embedding response exceeds size limit")
            return json.loads(data)
        except HTTPError as error:
            code = error.code
            error.close()
            if code in (401, 403):
                raise EmbeddingError("Provider authentication failed") from None
            if code == 429:
                raise EmbeddingError("Provider rate limit reached; automatic retry disabled") from None
            raise EmbeddingError("Provider HTTP request failed") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise EmbeddingError("Provider connection or response failed") from None

    return send


@dataclass(frozen=True)
class Limits:
    dimensions: int
    per_input_tokens: int
    total_tokens: int
    batch_size: int = 8
    max_requests: int = 16


def embed_texts(texts: list[str], *, model: str, limits: Limits,
                count_tokens: Callable[[str], int], send: Callable[[dict], dict]) -> dict:
    """Embed already-templated texts; caller supplies the pinned model tokenizer."""
    values = (limits.dimensions, limits.per_input_tokens, limits.total_tokens,
              limits.batch_size, limits.max_requests)
    if any(type(value) is not int or value <= 0 for value in values):
        raise EmbeddingError("Positive integer limits required")
    if limits.dimensions > 4096 or limits.batch_size > 32 or limits.max_requests > 64:
        raise EmbeddingError("Configured limits exceed client bounds")
    if not isinstance(model, str) or not model.strip():
        raise EmbeddingError("Model identifier required")
    if not isinstance(texts, list) or not texts or len(texts) > limits.batch_size * limits.max_requests:
        raise EmbeddingError("Input count exceeds request budget or is empty")
    # Validate the entire job before the first possible billable request.
    counts = []
    for text in texts:
        if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 65536:
            raise EmbeddingError("Invalid or oversized embedding input")
        try:
            count = count_tokens(text)
        except Exception:
            raise EmbeddingError("Configured tokenizer failed") from None
        if type(count) is not int or not 0 < count <= limits.per_input_tokens:
            raise EmbeddingError("Input exceeds token limit or token count is invalid")
        counts.append(count)
    if sum(counts) > limits.total_tokens:
        raise EmbeddingError("Job exceeds configured token budget")

    vectors, usage, request_count = [], [], 0
    for offset in range(0, len(texts), limits.batch_size):
        batch = texts[offset:offset + limits.batch_size]
        try:
            result = send({"model": model, "input": batch})
        except EmbeddingError:
            raise
        except Exception:
            raise EmbeddingError("Embedding transport failed; no automatic retry") from None
        request_count += 1
        try:
            if result["model"] != model or len(result["data"]) != len(batch):
                raise ValueError()
            ordered = {}
            for row in result["data"]:
                index, vector = row["index"], row["embedding"]
                if type(index) is not int or not 0 <= index < len(batch) or index in ordered:
                    raise ValueError()
                if not isinstance(vector, list) or len(vector) != limits.dimensions:
                    raise ValueError()
                if any(type(x) not in (int, float) or not math.isfinite(x) for x in vector) or not any(vector):
                    raise ValueError()
                ordered[index] = vector
            vectors.extend(ordered[i] for i in range(len(batch)))
            reported = result.get("usage", {}).get("total_tokens")
            if reported is not None and (type(reported) is not int or reported < 0):
                raise ValueError()
            usage.append(reported)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
            raise EmbeddingError("Provider returned invalid embeddings or usage") from None
    return {"vectors": vectors, "requests": request_count, "preflight_tokens": sum(counts),
            "reported_tokens": sum(usage) if all(x is not None for x in usage) else None}
