# Current architecture

Current behavior and boundaries, updated 3 November 2026.
[Prior architecture journal](history/2026-10-26/ARCHITECTURE-2026-10-26.md)
preserves earlier proposals/evidence. Status belongs in [MEMORY](MEMORY.md);
next implementation belongs in [TASKS](../TASKS.md).

## Components and trust boundaries

| Component | Role | Contract |
| --- | --- | --- |
| React/TypeScript in apps/desktop | One connected Library in private/dev builds; separate sample-only build, memory-only bearer, HTTPS API | [Unified Library](UNIFIED_LIBRARY.md), [private delivery](PRIVATE_DESKTOP_DELIVERY.md) |
| ASGI library API | Loopback operator mode or explicit Cloud Run startup; fixed Host/Origins, Auth before privileged work, bounded single-flight HTTP | [LIBRARY_API](LIBRARY_API.md), [Private delivery](PRIVATE_DESKTOP_DELIVERY.md) |
| Restricted DB transport | Fresh verified-user admission; bounded worker-only job-scoped helpers, transaction reset and separate heartbeat | [DATABASE_TRANSPORT](DATABASE_TRANSPORT.md), [performance](PROCESSING_SPEED.md) |
| Supabase Sydney | Auth, owned sources/versions, private originals/jobs/staging, publication and vector reads | [Hosted setup](HOSTED_SUPABASE_SETUP.md), [published reads](PUBLISHED_SEARCH.md) |
| Worker / optional private dispatcher | New-import intent, exact-job claim, leases/cancellation, pinned model and atomic publication; explicit attempt-bound recovery | [Automatic processing](AUTOMATIC_PROCESSING.md), [coordinator](INGESTION_COORDINATOR.md), [exact claim](EXACT_JOB_CLAIM.md) |
| Native-text PDF / DOCX extractors | Shared bounded Linux extraction slot; separate original/text hashes, PDF pages or extracted DOCX paragraphs. Restricted hosted pilot | [PDF contract](PDF_IMPORT.md), [DOCX contract](DOCX_IMPORT.md) |
| Private Cloud Run CPU service, Mumbai | Pinned Qwen embeddings, backend Google identity, bounded runtime and readiness | [Inference HTTP](INFERENCE_HTTP.md), [availability](MODEL_AVAILABILITY.md) |

The frontend never receives DB worker credentials or Google caller tokens.
User Supabase identity and backend Google service identity are separate.
RLS/SQL ownership and version guards remain authoritative; cursors/checkboxes
do not grant access.

## Current data flows

1. Import: select/review locally -> explicit confirmation -> Auth -> bounded
   actual-byte/parser/tokenizer validation -> idempotent source/version/job +
   immutable original. Opt-in automatic mode also commits a private dispatch
   intent and wakes a separate worker. Saving never means ready.
2. Process: explicit or opted-in exact-job worker -> lease -> parse/chunk preserving bytes,
   hashes/offsets -> pinned cloud embedding -> private staging/validation ->
   one atomic publication. Deleted, stale or superseded workers cannot publish.
   Automatic workers perform one bounded startup check under lease renewal;
   failures require explicit recovery bound to the observed job and attempt.
   In the optimized private API, bounded readiness starts after the trusted
   claim/manifest/lease and overlaps reading/parsing/staging. Inference remains
   sequential and waits for readiness. Worker connections close at job end;
   idle helpers can be evicted while retaining the global two-helper cap.
3. Search: Auth -> owned publication metadata -> empty if a complete page proves
   no publication; otherwise query embedding in the matching model space ->
   published vector ranking -> exact-version reads -> bounded source context.
4. Open: requested source/version must still be owned, published and unchanged;
   never redirect an old citation silently to a replacement.
5. Delete: tombstone immediately hides content; an authenticated owner-scoped
   cleanup wrapper removes originals/derivatives/jobs after guards pass and
   returns confirmed completion. Pending cleanup restores on reconnect. A minimal
   duplicate-request receipt prevents resurrection by replay.
6. Readiness: explicit authenticated check -> local attempt budget -> fresh
   backend caller identity -> fixed GET /ready. It submits no embedding and
   never automatically resends search. Ready is not proof of embedding success.

Owned listing/status wrappers also return a recovery-eligibility hint derived
from current targets, leases, backoff and attempt caps. UI hints never authorize
work; recovery rechecks under the existing transaction. See
[recovery and measured startup limits](PROCESSING_RECOVERY.md).

## Deployment and limits

Inference uses CPU2/5GiB, concurrency1, max1/min0. The approved library API uses
CPU1/512MiB, platform concurrency4, single-flight app admission, max1/min0.
Model operations retain 15 seconds and request identity five seconds. Automatic
startup permits the explicitly approved three readiness GETs inside one shared
60-second deadline; embeddings never retry automatically. Two existing accounts
and three model attempts per API instance remain private-pilot limits.

The separate private Windows build uses the approved hosted API. The default build
retains sample behavior. Public signup/general upload, distribution, broader
quality/security, signing and clean-install validation remain gates.
The approved PDF extension reuses this flow. Original PDF bytes remain immutable;
search offsets address extracted Unicode text, with its own hash and numbered page
ranges. Admission and worker parsing have separate resource-bounded runs. Exact
owned-version reads validate page metadata before displaying citations. See
[PDF limits and evidence](PDF_IMPORT.md); this is not a full OS parser sandbox.

DOCX shares extracted-document staging validation while keeping typed PDF/DOCX
wrappers and private format metadata. It is explicitly enabled in the hosted
private API. R2 originals, PPTX/image/OCR formats and bookmark enrichment remain
planned work. Chat remains deferred.

## Read only when relevant

- [Current flow map](knowledge/Search%20flow.canvas)
- [Source publication](TEXT_PUBLICATION.md) and [job ownership](INGESTION_JOBS.md)
- [Context/citations](SEARCH_CONTEXT.md), [query coordinator](QUERY_SEARCH.md)
- [Security](SECURITY.md), [privacy/release gates](PRIVACY_RELEASE_AUDIT.md)
- [Decisions](DECISIONS.md): inspect the matching ADR, not the whole log
- [Delivery plan](DELIVERY_PLAN.md): supporting design/history, not current status
