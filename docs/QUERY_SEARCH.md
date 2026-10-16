# Query-to-context coordinator

16 October 2026. `services/worker/search.py` connects existing query inference,
published RPCs and `source-neighbors-v1`. This is an internal callable, not a new
HTTP route or deployed service. Completion evidence lives in TASKS.md.

## Flow

Query -> validate -> verify session through Auth -> one query embedding ->
owner-scoped published vector search -> exact-version reads -> bounded citations.

`search(query, api=..., provider=..., limit=20, cancel=...)` requires explicit
server-created dependencies. The API callable takes method/path/JSON payload,
is permanently bound to one user's bearer token, and returns decoded JSON only
on successful responses. It must enforce bounded responses, timeouts, no redirects
and content-free errors/logging. Never use a service-role key or accept a transport,
provider or owner from a client payload. SERVICE_CLIENTS.md implements this adapter
with locally verified Auth/REST integration; hosted TLS verification remains pending.

The provider contract is the existing ingestion infer/count_tokens interface.
Count the exact pinned Qwen query template; pass raw query text with role=query
to inference, which applies the template once. Maximum input is 8 KiB and 2,048
templated tokens, preserving runtime limits. Validate exact model/revision/512
dimensions, numeric finite output and unit norm. No inference retry, model startup,
automatic normalization of bad outputs or synthetic production fallback.

One call performs Auth verification, one inference request, one search RPC and
at most five reader RPCs. Up to 100 candidates are validated before source
selection; no more than five snapshots are fetched. The existing assembler caps
each excerpt at 8 KiB and total excerpt text at 32 KiB. Return source/version/hash,
Unicode offsets, original seed rank, title, similarity and omission reasons.
Scores are ranking signals, not proof that the query is answerable.

If deletion/replacement occurs between ranking and opening, the exact-version
reader returns nothing; report `no_longer_available`, without retrying against a
new version or returning cached passage text. Malformed/mismatched snapshots fail
the request. Cancellation suppresses results and reaches inference; transports
must bound in-flight I/O themselves. A later deletion cannot revoke bytes already
read; multiple RPCs do not provide a cross-request database snapshot.

## Verification boundary

Unit tests inject synthetic vectors and session responses. The existing local
Supabase harness now includes three additional coordinator checks using real JWT
requests with explicitly synthetic vectors labelled with the pinned identity.
All 67 local Auth/REST/Storage checks now pass, including those three coordinator
cases: exact context, second-user isolation and replacement between rank/open.
Evidence: output/database-checks/query-api-20261016.log. Synthetic vectors verify
orchestration and boundaries, not live model quality or production transport.

No real model loaded, prompt/chunk/vector benchmark changed, or deployment made.
SERVICE_CLIENTS.md now provides bounded session and prepared inference clients.
Next: authenticated inference HTTP handler and remote integration; verify private
ingestion identity/driver integration and connect the desktop under release gates.
