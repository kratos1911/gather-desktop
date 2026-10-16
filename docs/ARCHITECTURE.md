# Architecture: how the product works

Current forward plan: [DELIVERY_PLAN.md](DELIVERY_PLAN.md), dated 2 October.
It defines proposed API/worker boundaries, job leases, version publication,
security checks and delivery gates. Implementation status is distinguished below.

## Current implementation

15 October scheduling prerequisite: private PostgreSQL jobs and processing-target
versions, idempotent enqueue, bounded leases/retries, narrowly granted worker
functions, owner-derived status and deletion/replacement fencing are verified.
See INGESTION_JOBS.md. TEXT_PUBLICATION.md adds verified-byte admission, private
pgvector staging, a separate published pointer and atomic ready activation.
INGESTION_COORDINATOR.md adds internal submission, durable original handoff,
lease-aware worker orchestration and reuse of completed vectors. PUBLISHED_SEARCH.md
adds published-vector search and version-bound text reads through locally verified
Supabase JWT/PostgREST. QUERY_SEARCH.md adds internal query embedding/context
coordination with injected dependencies; live coordinator API checks and production
transport, plus privileged ingestion transport integration, remain pending.

Bounded context now exists as a pure worker component after ranking. It groups
sources, expands at most one contiguous neighbor per side and returns exact
versioned text citations within byte limits. Saved-vector replay is verified;
trusted repository/API/desktop wiring is pending. See SEARCH_CONTEXT.md.

15 October paired retrieval: host evaluation tooling compares legacy and token512
layouts using identical patched-model vectors for shared inputs. Frozen source
quotes remain unchanged; strict and continuous union evidence coverage are scored
separately. text-v2 gate passes; boundary stress exposes split context and missed
multi-part passages. Context assembly/coverage remains the next prerequisite,
not implemented ingestion behavior. See CHUNK_RETRIEVAL_RESULTS.md.

15 October: separate patched CPU image built and scanned (28 findings/1 high).
Added token-aware <=512-token source preparation, preserving offsets and overlap.
Existing index/parser versions and request budgets unchanged. Candidate real-model
compatibility passes on six cases; five 306–500-token chunks complete in
3.053–5.883 s. Helper not yet connected to ingestion; retrieval quality with the
new boundaries is measured with limitations above. See services/inference/UPGRADE.md.
Deployment/promotion remains gated.

14 October extended profiles: 50 short sequential queries passed; 2,048-token
single and max-batch requests exceed the 15 s deadline on this shared machine.
No runtime limits changed. Image scan has 56 open records, including 12 high.
Remediation/rescan and smaller-chunk evaluation precede API integration. See
services/inference/PROFILE_RESULTS.md and IMAGE_SCAN_REVIEW.md.

12 October: services/inference adds a private persistent CPU process boundary.
Requests are single-flight, validated and token-budgeted; deadlines stop/reap the
child. A local Qwen adapter and hash-verifying host smoke launcher are prepared.
Synthetic control tests pass; real host serving smoke passed on 13 October.
The Linux CPU container now builds with 25 hash-locked dependencies and passes
18 synthetic tests with offline/non-root/read-only resource restrictions. Real
container inference passed on 14 October: ten short fictional inputs, 15.781 s
startup, 0.593–0.742 s requests and 3.87 GiB cgroup peak. No HTTP endpoint or desktop
connection is verified. See its README and CONTAINER.md.

8 October: `supabase/migrations` now defines sources and source_versions with
ownership RLS, metadata-only client updates and composite ownership references.
Nineteen PostgreSQL checks pass using a test-only Auth contract shim. This is
schema groundwork, not connected persistence, Auth, Storage or search. Client
direct creation/deletion remains disabled. The 9 October migration adds SQL
save/delete functions with slot quotas, durable idempotency receipts, atomic
tombstone/cleanup requests and private database-only cleanup. Parent locks guard
late version writes. 45 SQL assertions and four concurrency scenarios pass.
The next migration adds private original reads and a Storage-presence cleanup
guard. A disposable core-service harness passes 31 actual Auth/PostgREST/Storage
checks, including API removal before finalization. Worker leases, concurrent
upload fencing, background reconciliation and hosted/desktop integration remain pending.

28 September: chat is deferred until search works. The offline bookmark parser
in services/worker/bookmarks.py extracts supplied HTML without network access.
Offline bookmark passages now reuse text chunking and are tested with TF-IDF.
Desktop persistence, live extraction and semantic search remain disconnected.
A backend-only plain-HTTP transport and offline Docker supervisor now pass local
controlled tests. FetchBroker now covers whole-fetch deadlines including DNS;
BookmarkPipeline connects it to offline parsing. Production broker confinement
and browser/tool egress remain open;
see services/worker/SUPERVISION.md.

apps/desktop contains a React/TypeScript interface, synthetic fixtures, component tests and a Tauri Windows shell. services/worker contains a transport-independent TXT/Markdown processing module with synthetic tests. No auth, processing endpoint, database client, inference runtime or upload pipeline is connected. See MEMORY.md for verification.

## Target boundaries

Selected bookmark extraction: self-hosted Crawl4AI for webpages and yt-dlp for
supported video metadata/available subtitles, behind explicit worker adapters.
See [[docs/knowledge/EXTRACTION_STACK]]. Installed in the tested offline container only; not connected to live fetching; no
generic agent shell in the ingestion path. Agent Reach is optional, not core.

```text
React UI -> typed application services -> authenticated cloud API (planned)
Tauri -> narrowly scoped native file selection (planned)
Cloud API -> bounded ingestion jobs -> Python processing worker
Worker -> parsers / cloud OCR / embedding / chat adapters
Cloud service -> ownership-enforced Supabase Postgres + pgvector
              -> private Cloudflare R2 objects (selected target; adapter pending)
```

ADR-009 supersedes local AI deployment. Supabase Auth supplies user sessions; OS-backed credential storage is to be selected and tested. The user selected Google Cloud Run with self-hosted CPU inference and R2 for original files; Supabase Free remains Auth/Postgres/pgvector. API framework, durable queue and production inference runtime remain open. The user has set up a Google Cloud account, but no application deployment is verified here. Do not provision paid resources from local benchmark authorization. R2 byte/request limits need application enforcement; the existing local Storage harness does not verify R2. No required end-user models or local inference server.

10 October: TASK-005 adds a developer-only Qwen CPU benchmark on D:. Downloads,
environment, caches and reports are under ignored output/model-benchmark. This
is a measurement tool, not the cloud serving endpoint or a desktop integration.
It checks exact prompted token lengths, embeds offline with pinned safetensors,
exports versioned vectors and evaluates cosine/RRF against the frozen TF-IDF baseline.
See [CPU benchmark](CPU_BENCHMARK.md) for evidence and limits.

12 October: evaluation accepts a fixed corpus selection, validates a frozen
text-v2 fingerprint and separates corpus outputs. The 512-dimensional candidate
passes the fresh challenge gate with known retrieval weaknesses. The next runtime
step is a local container experiment, not a deployed API. See TEXT_V2_RESULTS.md.

## Architecture rules

- UI components contain no SQL, model execution, filesystem traversal or provider credentials.
- Application services own workflow/state transitions; adapters own external/storage/runtime calls.
- Validate requests, file size/type/content and paths at native/API/worker boundaries. Authenticate requests and enforce owner/quota checks server-side; never trust owner IDs supplied by the desktop.
- Enforce ownership, quota and resource relationships in Supabase policies/functions. Never distribute a service-role key or database password.
- Text and visual vectors occupy different model-versioned spaces. Fuse result ranks, never raw scores from incompatible models.
- Commit all indexed passages before ready state. Use idempotent writes and bounded durable retries.
- Storage and Postgres operations need reconciliation because they are not one transaction.
- Selected-source retrieval constrains chat; source text is evidence, not executable instructions.
- Run heavy processing in cloud workers with bounded memory/concurrency. Provider secrets stay on the server. Define request quotas, timeouts and spend controls before hosted inference.

## Layout

Planned bookmark boundary: persist an owner-scoped source before asynchronous
enrichment; a restricted cloud fetcher and metadata/article adapters produce safe
text with URL/fetch-time/provenance. Reuse the existing chunk/embedding pipeline.
Failed fetching retains the bookmark. No arbitrary page-script execution or
untrusted HTML inside Tauri. See BOOKMARKS.md; the backend page pipeline is
verified with controlled local fixtures and is not connected to desktop bookmarks.

Existing: apps/desktop/src/components, fixtures.ts, App.tsx, src-tauri, scripts/desktop.ps1, docs.

Create as needed, not as empty scaffolding: apps/desktop/src/features, services, types; services/worker; supabase/migrations; tests/fixtures; tests/evaluation. Keep fixture mode explicit until each service is real. Old root Python files now live in legacy for reference; do not run them against personal documents during checks.

## Release path

Local checks -> development executable -> staging/test installer -> clean-machine QA -> release review -> signed/public installer -> monitoring and iteration. A browser preview is useful UI testing but not proof of native integration. No automatic production publish or remote push is implied by an individual implementation task.

Detailed ingestion design remains in PROJECT_BLUEPRINT.md. This file is the architecture entry point; DECISIONS.md records changes.
