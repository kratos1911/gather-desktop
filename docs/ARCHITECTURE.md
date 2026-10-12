# Architecture: how the product works

Current forward plan: [DELIVERY_PLAN.md](DELIVERY_PLAN.md), dated 2 October.
It defines proposed API/worker boundaries, job leases, version publication,
security checks and delivery gates. Proposed mechanisms are not implemented yet.

## Current implementation

12 October: services/inference adds a private persistent CPU process boundary.
Requests are single-flight, validated and token-budgeted; deadlines stop/reap the
child. A local Qwen adapter and hash-verifying host smoke launcher are prepared.
Synthetic control tests pass; real serving smoke is RAM-blocked. No serving
container, HTTP endpoint or desktop connection is verified. See its README.

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
