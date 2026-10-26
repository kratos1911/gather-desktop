# Current architecture

Current behavior and boundaries, updated 26 October 2026.
[Prior architecture journal](history/2026-10-26/ARCHITECTURE-2026-10-26.md)
preserves earlier proposals/evidence. Status belongs in [MEMORY](MEMORY.md);
next implementation belongs in [TASKS](../TASKS.md).

## Components and trust boundaries

| Component | Role | Contract |
| --- | --- | --- |
| React/TypeScript in apps/desktop | Sample native UI; development-only private operator panel, memory-only user bearer | [Desktop guide](../apps/desktop/README.md), [file pilot](PRIVATE_TEXT_FILES.md) |
| Loopback ASGI application API | Fixed JSON routes, user Auth before privileged work, Host/Origin guards, bounded single-flight lifecycle | [LIBRARY_API](LIBRARY_API.md), [LIBRARY_SESSION](LIBRARY_SESSION.md) |
| Restricted DB transport | Separate admission/worker identities, bounded Psycopg helpers and trusted owner context | [DATABASE_TRANSPORT](DATABASE_TRANSPORT.md) |
| Supabase Sydney | Auth, owned sources/versions, private originals/jobs/staging, publication and vector reads | [Hosted setup](HOSTED_SUPABASE_SETUP.md), [published reads](PUBLISHED_SEARCH.md) |
| Separate explicit worker | Exact-job claim, leases/retries/cancellation, pinned processing/model identity, atomic publication | [Coordinator](INGESTION_COORDINATOR.md), [exact claim](EXACT_JOB_CLAIM.md) |
| Private Cloud Run CPU service, Mumbai | Pinned Qwen embeddings, backend Google identity, bounded runtime and readiness | [Inference HTTP](INFERENCE_HTTP.md), [availability](MODEL_AVAILABILITY.md) |

The frontend never receives DB worker credentials or Google caller tokens.
User Supabase identity and backend Google service identity are separate.
RLS/SQL ownership and version guards remain authoritative; cursors/checkboxes
do not grant access.

## Current data flows

1. Import: select/review locally -> explicit confirmation -> Auth -> bounded
   actual-byte/parser/tokenizer validation -> idempotent source/version/job +
   immutable original. Saving does not launch a worker or mean ready.
2. Process: explicit exact-job worker -> lease -> parse/chunk preserving bytes,
   hashes/offsets -> pinned cloud embedding -> private staging/validation ->
   one atomic publication. Deleted, stale or superseded workers cannot publish.
3. Search: Auth -> owned publication metadata -> empty if a complete page proves
   no publication; otherwise query embedding in the matching model space ->
   published vector ranking -> exact-version reads -> bounded source context.
4. Open: requested source/version must still be owned, published and unchanged;
   never redirect an old citation silently to a replacement.
5. Delete: tombstone immediately hides content; explicit privileged cleanup
   removes active originals/derivatives/jobs after guards pass. A minimal
   duplicate-request receipt prevents resurrection by replay.
6. Readiness: explicit authenticated check -> local attempt budget -> fresh
   backend caller identity -> fixed GET /ready. It submits no embedding and
   never automatically resends search. Ready is not proof of embedding success.

## Deployment and limits

The existing private pilot uses CPU2/5GiB, concurrency1, max1/min0. Model
operation budget is 15 seconds, requested identity step five seconds; the
operator worker uses its separately approved startup guard. The private pilot
allows two existing test accounts and three model attempts per process.
No limits were raised to pass checks. See individual contracts for exact bounds.

The packaged native app is still sample-only. Public signup/general upload,
distribution, broader quality/security and operational automation remain gates.
R2 originals, additional document/image/OCR formats and bookmark enrichment
are planned work, not active integrations. Chat remains deferred.

## Read only when relevant

- [Current flow map](knowledge/Search%20flow.canvas)
- [Source publication](TEXT_PUBLICATION.md) and [job ownership](INGESTION_JOBS.md)
- [Context/citations](SEARCH_CONTEXT.md), [query coordinator](QUERY_SEARCH.md)
- [Security](SECURITY.md), [privacy/release gates](PRIVACY_RELEASE_AUDIT.md)
- [Decisions](DECISIONS.md): inspect the matching ADR, not the whole log
- [Delivery plan](DELIVERY_PLAN.md): supporting design/history, not current status
