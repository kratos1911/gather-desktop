# Architecture: how the product works

## Current implementation

28 September: chat is deferred until search works. The offline bookmark parser
in services/worker/bookmarks.py extracts supplied HTML without network access.
It is not yet connected to desktop persistence, passages or search.

apps/desktop contains a React/TypeScript interface, synthetic fixtures, component tests and a Tauri Windows shell. services/worker contains a transport-independent TXT/Markdown processing module with synthetic tests. No auth, processing endpoint, database client, inference runtime or upload pipeline is connected. See MEMORY.md for verification.

## Target boundaries

Selected bookmark extraction: self-hosted Crawl4AI for webpages and yt-dlp for
supported video metadata/available subtitles, behind explicit worker adapters.
See [[docs/knowledge/EXTRACTION_STACK]]. Not installed or connected yet; no
generic agent shell in the ingestion path. Agent Reach is optional, not core.

```text
React UI -> typed application services -> authenticated cloud API (planned)
Tauri -> narrowly scoped native file selection (planned)
Cloud API -> bounded ingestion jobs -> Python processing worker
Worker -> parsers / cloud OCR / embedding / chat adapters
Cloud service -> ownership-enforced Supabase Postgres + pgvector
              -> private Storage objects
```

ADR-009 supersedes local AI deployment. Supabase Auth supplies user sessions; OS-backed credential storage is to be selected and tested. Cloud provider, API framework, durable queue and inference runtime are deferred decisions. No server or paid resource is provisioned. The current pure processing module can be tested locally and reused in the cloud. No required end-user models or local inference server.

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
untrusted HTML inside Tauri. See BOOKMARKS.md; no fetcher is implemented yet.

Existing: apps/desktop/src/components, fixtures.ts, App.tsx, src-tauri, scripts/desktop.ps1, docs.

Create as needed, not as empty scaffolding: apps/desktop/src/features, services, types; services/worker; supabase/migrations; tests/fixtures; tests/evaluation. Keep fixture mode explicit until each service is real. Old root Python files now live in legacy for reference; do not run them against personal documents during checks.

## Release path

Local checks -> development executable -> staging/test installer -> clean-machine QA -> release review -> signed/public installer -> monitoring and iteration. A browser preview is useful UI testing but not proof of native integration. No automatic production publish or remote push is implied by an individual implementation task.

Detailed ingestion design remains in PROJECT_BLUEPRINT.md. This file is the architecture entry point; DECISIONS.md records changes.
