# Text processing contract v1

This dependency-free Python module is a processing prerequisite, not a running
server or a connected desktop worker. Cloud deployment is deferred. It performs
no file access, network requests, model execution, logging or persistence.

Run from the repository root with Python 3.11 or newer:

```powershell
python -m unittest discover -s tests/worker -v
```

`process_request(payload: bytes)` accepts one UTF-8 JSON object with exactly:

```json
{"version":1,"request_id":"job-004","format":"txt","content_base64":"SGVsbG8="}
```

Request IDs contain 1–64 ASCII letters, digits, underscores or hyphens. Formats
are `txt` or `md`. The transport envelope is at most 96 KiB and decoded source at
most 64 KiB. These are conservative contract limits for this slice, not the
eventual upload limit. A future HTTP/IPC adapter must reject oversized streams
before buffering them and authenticate/authorize before invoking this module.

Success has status `processed` (never `ready` or `indexed`) and a document with
the original-byte SHA-256, parser/chunker versions, format, character count and
chunks. Each chunk has an ID, text and a half-open `[start, end)` source range.
Offsets count Unicode code points in strict UTF-8 decoded source, including BOM,
CRLF and Markdown syntax. They are neither byte offsets nor JavaScript UTF-16
indices. The future viewer must convert offsets or use code-point-aware slicing.
Markdown is plain source text here; links/images are never fetched or rendered.

Chunks contain at most 1,024 characters and overlap by 128. Paragraph, newline
and space boundaries in the latter half of a window are preferred, with a hard
split for unbroken text. This is a deterministic pre-tokenizer representation,
not a guarantee of an embedding model's token limit. TASK-005 must measure the
selected tokenizer and version any rechunking needed before inference.

Chunk IDs include source hash, format, parser/chunker versions and offsets.
Identical retries produce identical documents even when request IDs differ.
Hashes are content identity, not authorization or globally public document IDs;
future database keys/deduplication must also be scoped by authenticated owner.
There is no filename/path field and no filesystem resolution.

Errors have status `error`, a stable code, fixed message, safe request ID or null,
and `retryable: false`. Fix invalid input rather than automatically retrying it.
Use `serialize_response` for canonical UTF-8 JSON; output is capped at 512 KiB
and 256 chunks. Failed calls leave no state; the next request works normally.
Process crashes, durable jobs, timeouts, cancellation and restart orchestration
belong to the later service integration; none is claimed implemented here.
