# Published search and reader API

16 October 2026. This slice adds authenticated read operations to the existing
Supabase/PostgREST boundary. It does not deploy a cloud service or connect the
desktop. Test evidence and current completion status are recorded in TASKS.md.

## Operations

| Operation | Input | Result |
| --- | --- | --- |
| `POST /rest/v1/rpc/search_published_text` | `p_query` numeric vector, `p_model`, `p_revision`, `p_dimensions`, optional `p_limit` | Ranked published passages with source/version IDs, title, hash, offsets, body, model identity and cosine similarity |
| `POST /rest/v1/rpc/open_published_text` | `p_source`, `p_version` | One exact published text snapshot and its ordered passage manifest, or an empty array |

Both calls use the user's authenticated bearer session. PostgREST validates the
JWT; the SQL functions derive ownership from `auth.uid()`. No owner parameter or
worker/service credential belongs in a desktop payload. Only the authenticated
role receives function grants. Private staging and ingestion functions remain
outside the exposed REST schema.

Search selects only the live owner's published pointer and exact model/revision/
dimension space, then computes **exact cosine distance** with pgvector. Materializing
the eligible rows prevents incompatible vector dimensions from entering comparison.
Ties sort by source ID then passage order. Results are passage candidates, not yet
source-grouped context. The existing bounded context assembler remains the next
adapter integration; this endpoint does not duplicate that algorithm.

Inputs require 256/512/1024 dimensions, finite numeric values, unit norm within
0.001, at most 64 KiB JSON, model/revision identifiers of 1–200 characters and
1–100 results (default 20). Invalid inputs fail with a safe query error or pgvector
numeric validation error. No raw document data is placed in error messages.
No approximate index, minimum-score threshold or relevance guarantee is introduced.
Initial exact search must be profiled before claiming large-library latency;
production rate limits, request deadlines and concurrent-query limits remain gates.

Opening requires the version returned by search. A replacement draft leaves the
previous publication available; activating the replacement makes old citations
unavailable instead of silently redirecting them to different text. Tombstones
hide both search and reader results on subsequent requests. Missing, foreign,
draft, replaced or deleted reader targets all return an empty array. Already-read
transaction snapshots cannot be retroactively erased.

The reader returns exact UTF-8 text (including BOM, CRLF and Unicode), source hash,
parser/chunker/model identity and passage IDs with Unicode codepoint offsets.
Render the body as document text; it is untrusted content, not executable HTML.
Original file downloads from R2 remain a separate adapter.

## Evidence and next boundary

`scripts/check_published_api.py` extends the existing disposable Supabase test
stack. It uses real Auth sessions and PostgREST, plus synthetic document/unit-vector
fixtures staged through existing worker functions. It checks cosine ordering,
identity-space filters, citation alignment, ownership, hidden drafts, replacement,
deletion, malformed vectors, anonymous requests and tampered JWT signatures.
Synthetic vectors establish API/storage behavior, not natural-language retrieval.

Run `python scripts/supabase_test_stack.py` with cached images and sufficient memory.
The loopback-only gateway and private test database are temporary; cleanup targets
only generated fixtures and the dedicated test stack. Public signup stays disabled.
The established lifecycle/storage checks also run because these endpoints share
the same authentication and deletion boundary.

Next connect server-side query-text embedding and bounded context assembly to
these authenticated reads, then the desktop. The private ingestion coordinator's
real connection factory/authentication boundary still needs verification. Neither
new RPC accepts files nor exposes privileged ingestion credentials.
