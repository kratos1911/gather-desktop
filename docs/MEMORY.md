# Current project state

Updated: 10 October 2026. Current forward plan: DELIVERY_PLAN.md. New architecture
choices there are proposed, not implemented. PROGRESS.md records history.

Extractor checkpoint: TASK-019A hash-locked image rebuilt after Docker recovery.
Exact installed versions, pip consistency, bad-hash rejection, offline restrictions
and prompt timeout cleanup pass. TASK-023 patched OpenSSL/PCRE2 and removed
runtime pip/ensurepip on 3 October. The 8 October code-image rescan reports
29 records (2 high, 1 medium, 26 low); no dependency versions changed this turn.
Two GCC records disappeared from the refreshed feed, not through a code fix. Remaining
unpatched/applicability and build-tool review stay open; live execution is gated.
See services/worker/IMAGE_SCAN_REVIEW.md. OKF remains a later optional export layer.

## Product and constraints

Latest steering: self-hosted CPU AI on Google Cloud Run, R2 originals and Supabase
Free Auth/Postgres/pgvector. User has created the Google Cloud account. Application
deployment remains unverified; do not provision paid resources from benchmark
permission. On 10 October the user authorized D:-only local model tests, and
chose Qwen first while EmbeddingGemma license acceptance is pending. Commit
locally; push only on an explicit request to push.

Gather is a provisional name for a Windows desktop content library with semantic text/photo search and selected-source chat. Tauri/React/TypeScript and Supabase Free remain. User chose cloud AI on 27 September (ADR-009); later CPU/Cloud Run choices are in ADR-038. No end-user model downloads planned. Design avoid-list applies. No agentic file modification, payment feature or mobile app in MVP. Chat remains deferred until search works.

## Implemented

- TASK-005 real local CPU benchmark: pinned Qwen3-Embedding-0.6B downloaded to
  D: and evaluated at 256/512/1,024 dimensions with two/four CPU threads. All
  dimensions have 100% document/evidence Recall@5 on 35 answerable development
  queries; 512-dimensional MRR is 0.9857. All five absent queries still return
  neighbors. Four-thread median/p95 query time: 0.324/0.376 seconds; sampled peak
  RAM about 3.58 GiB. This is isolated evaluation, not connected app search or
  cloud performance. 150 source/UI tests and frontend build pass. See CPU_BENCHMARK.md.

- Real core Supabase API harness: 31 checks pass on disposable Auth/PostgREST/
  Storage + PostgreSQL. Actual JWT login, private reads, denied client writes,
  tombstone visibility and Storage API deletion before SQL finalization verified.
  Explicit loopback gateway; no DB host port; synthetic data/containers removed.
  No desktop integration or background cleanup worker. See ../supabase/LOCAL_INTEGRATION.md.

- TASK-021 database lifecycle: 45 SQL assertions and four concurrent scenarios
  pass for ownership, atomic source-slot quota/idempotent saves, tombstones,
  database cleanup rollback and late-write protection. This fast suite still uses
  Auth/Storage metadata shims; the separate API suite uses real local services.
  No real user account, hosted RPC or desktop connection.
  See ../supabase/README.md for remaining quota/retention/external cleanup gates.

- FetchBroker bounds the entire fetch process, including hanging DNS/connect/TLS,
  kills/reaps cancelled or timed-out children and validates bounded responses.
  BookmarkPipeline passes fetched bytes to the offline Docker parser, preserving
  URL/time/hash/notes and passage provenance. Only controlled loopback integration
  is verified; no API, desktop ingestion, persistence or semantic results.

- Backend-only restricted HTTP transport: approved numeric address dialing,
  redirect revalidation, TLS identity checks and bounded page bodies. Tested only
  against controlled local peers; resolver/connector injection is trusted code.
- Host-side offline DockerJobRunner: fixed entrypoint/digest, bounded input/output,
  concurrency, execution timeout, cancellation and cleanup. Actual container
  resource/egress tests pass. Not an API, durable queue or live fetch broker.

- Local quality checks: 112 worker, 34 evaluation and four UI tests, ESLint,
  TypeScript, Prettier and frontend build pass. Native development build passes.
  Manual GitHub workflow authored; remote execution unverified.
- Links/bookmarks added to product scope and delivery plan in BOOKMARKS.md.
  Offline extraction implemented with ten synthetic tests. No bookmark UI, storage or fetcher.

- Server/developer-only embedding request client with batching, full-job token
  preflight, bounded HTTPS, index reordering and safe errors. Eight mocked tests
  pass; no real tokenizer/provider/export integration or cost measurement yet.

- Saved-vector evaluation adapter with exact normalized cosine ranking and equal-weight RRF (k=60) comparison to TF-IDF. Export metadata checks model/revision/templates/tokenizer/dimensions, corpus/index hashes and truncation. Initially synthetic math tests only; now complemented by the real CPU export above. The corpus remains fictional, while the generated vectors are actual model outputs.

- Offline TF-IDF keyword baseline and strict scoring harness with corpus/index fingerprints, per-category and per-query metrics. Twenty-one evaluation tests pass. Baseline text-v1 document/evidence Recall@5 is 0.9714 and MRR@5 is 0.8667; 4/5 absent queries return candidates. This is a tiny development comparator, not semantic search or an answerability system.

- Retrieval development corpus text-v1: 14 synthetic documents and 40 queries (35 answerable, 5 absent), with exact evidence mapped to 16 real processing chunks. Seven integrity tests pass. Export tool separates index/query inputs from relevance labels. See tests/evaluation/README.md and CPU_BENCHMARK.md for the first real model results.

- Transport-independent Python text processor: bounded typed request/results, strict UTF-8 TXT/Markdown, original source offsets, deterministic hashes/versioned passage IDs, structured safe errors. Twelve synthetic tests pass. No filesystem/network/model calls or new dependencies in this module.

- Desktop shell with fixture library, filters, reader, model lineup and preview policy screens.
- Motion selection feedback, optional reader Lenis, paused Thinking Orbs sample, local fonts/artwork/license notices.
- Four passing component tests, passing frontend and native development builds at the last implementation checkpoint.
- Legacy privacy fixes, documented audit and release follow-ups.
- Official Rust toolchain installed; C++ tools found; compatible Node available through scripts/desktop.ps1. Global npm shim remains broken; helper avoids it without changing global PATH.

## Not implemented / unverified

No real desktop import, connected worker/cloud endpoint, production embeddings, Supabase project connection, auth, durable search index, chat or signed installer. Processing and Qwen inference are tested in isolation. The frozen corpus fits the actual tokenizer; arbitrary/long passages still require token-aware production limits. No native/visual/E2E verification. Previous browser opening was declined; that limitation was not bypassed. Canvas is stubbed in component tests, so passing tests do not verify the orb renderer.

Frontend lint and format checks are configured; remote CI and native E2E remain unverified. The full initial baseline diff also reports pre-existing trailing-whitespace issues in legacy files; those are not hidden or counted as a clean full-diff check. Git repository: https://github.com/kratos1911/gather-desktop (private). origin is configured; main tracks origin/main. Baseline commit b89ceec was pushed and its remote hash verified. The TASK-001 baseline contains the existing implementation and workflow documents.

## Current task

TASK-005 D:-only Qwen CPU slice verified on 10 October. Next: broaden the text
evaluation before locking dimensions/fusion, then measure the serving container
under explicit resource limits. EmbeddingGemma waits for license/access; visual
models need an image/OCR corpus; chat stays deferred. These remain unfinished.

TASK-021 core API slice verified locally on 9 October. Next: upload fencing and
external-object reconciliation, then processing job leases. Exact hosted parity,
desktop sessions and connected persistence remain pending. The CLI binding issue
was replaced with a disposable Compose harness using explicit loopback ports.

TASK-022 documents the system/security delivery plan. TASK-019A added dependency
locking/review; current source checks total 150 tests. The new recipe built and
passed offline smoke checks. TASK-023 records open scan findings; TASK-019B
has a tested offline Docker supervisor and plain-HTTP restricted transport.
Whole-broker DNS/process deadlines and controlled HTTP-to-parser integration
now pass. Browser/tool egress and production broker confinement remain open.
TASK-005 hosted deployment remains pending; local CPU evidence is now available.
No GitHub push authorized. Offline bookmark processing passes; live bookmark search remains pending. Chat deferred by user on 28 September.

## Next implementation

30 September final choice: Crawl4AI for public webpages and yt-dlp for supported
video metadata/available subtitles. Agent Reach is optional. See
docs/knowledge/EXTRACTION_STACK.md. Tools installed in the offline container only. Transcription,
visual video understanding and chat remain deferred. TASK-019 follows TASK-018.

TASK-018 completed: offline bookmark passages with source/field references and
TF-IDF retrieval tests. TASK-019 adapters/offline runner pass; next is TASK-023
remaining security review. TASK-019B controlled HTTP transport and offline Docker supervision now pass
local tests. FetchBroker and BookmarkPipeline now pass controlled end-to-end
HTTP/process/Docker parsing tests. Next: production confinement and browser/tool
egress; live invocation (019C) stays gated. No persistence or semantic indexing.
TASK-021 plans local Supabase schema/job/isolation tests. TASK-017 connects the flow.
Provider connection and semantic benchmarks remain pending. Add harder long-document
and independently reviewed unseen questions before release claims. TASK-002
audience research and TASK-003 visual QA remain open.

## Inputs needed before later gates

Supabase project/public configuration; audience/regions; operator/contact and final policies; cloud provider, budget, model/license/runtime selection; signing and public distribution destination. Do not request secrets in chat. Current .env is private legacy configuration and is not copied into the new app.

## Obsidian workspace

Project hub: [[docs/PROJECT_HUB]]. Shared repository notes are the source of truth;
concepts, ideas, templates and the search-flow canvas supplement the canonical
documents. Local template/daily-note configuration saved; Obsidian UI not verified.
Latest source checks: 145 tests and frontend build on 8 October. Locked-image
smoke passes, including actual timeout cleanup; no smoke containers remain.

## Earlier checkpoints (superseded by the 1 October status below)

Six root prototype files moved unchanged to legacy/; three unused starter logos
removed. Original data, secrets, environments and user notes preserved. See
docs/REPOSITORY_AUDIT.md for all 109 original tracked-file dispositions.

Bookmark passage adapter implemented in services/worker/bookmark_passages.py.
Seven new synthetic tests; no desktop search, storage or actual embeddings.

TASK-019 partial: eight synthetic output-adapter tests pass. Markdown preserved,
subtitle cue timing/language tracked. No installed extractors or live requests.
Next: isolated runner and network enforcement.

## Subtitle parsing checkpoint

services/worker/subtitles.py now parses a bounded UTF-8 SRT/WebVTT subset into
normalized cues. Eight tests include byte-to-passage timestamp preservation.
TASK-019 remains partial; installed/pinned runners and live network checks remain.

## Network preflight checkpoint

TASK-019 partial: direct extractor pins recorded; eight synthetic destination
policy tests pass. No packages installed or real DNS performed. Connection/egress
isolation, transitive dependency lock and executable runner remain unfinished.

## Runner checkpoint (30 September history)

Bounded offline JSON runner and network-disabled Docker configuration added.
Docker CLI validates Compose, but Linux engine is unavailable after startup
attempt. Image build, package installation and runtime isolation are unverified.
Runner only consumes supplied extraction outputs; live URL extraction and enforced
public-only egress remain unfinished. TASK-019 remains partial.

## Historical checkpoint: 1 October

Docker Linux engine is ready. Extractor image built; installed Crawl4AI 0.9.4 and
yt-dlp 2026.8.19 verified inside it; pip check passes. Repeatable container smoke
checks pass for synthetic jobs, non-root UID, application write rejection, an
unreachable external route and absent checked personal paths. All 98 tests and
frontend quality/build checks pass. Earlier package/engine limitations above are
historical. TASK-019 remains partial: no live tool invocation or browser installed.
Next: dependency/image locking and enforced public-only egress before live fetching.
No paid resources or GitHub push.
