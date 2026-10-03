# Current project state

Updated: 3 October 2026. Current forward plan: DELIVERY_PLAN.md. New architecture
choices there are proposed, not implemented. PROGRESS.md records history.

Latest checkpoint: TASK-019A hash-locked image rebuilt after Docker recovery.
Exact installed versions, pip consistency, bad-hash rejection, offline restrictions
and prompt timeout cleanup pass. TASK-023 patched OpenSSL/PCRE2 and removed
runtime pip/ensurepip. Rescan: 31 open records (4 high, 2 medium, 25 low), down
from 51; 21 old records gone and one newly reported GCC advisory. Remaining
unpatched/applicability and build-tool review stay open; live execution is gated.
See services/worker/IMAGE_SCAN_REVIEW.md. OKF remains a later optional export layer.

## Product and constraints

27 September steering: user has no provider account yet and explicitly deferred
it. Continue independent work without paid/live calls. Commit locally; push only
on an explicit request to push.

Gather is a provisional name for a Windows desktop content library with semantic text/photo search and selected-source chat. Tauri/React/TypeScript and Supabase Free remain. User chose cloud AI on 27 September (ADR-009); provider, budget and deployment are deferred. No paid resources authorized/provisioned. No end-user model downloads planned. Design avoid-list applies. No agentic file modification, payment feature or mobile app in MVP.

## Implemented

- Backend-only restricted HTTP transport: approved numeric address dialing,
  redirect revalidation, TLS identity checks and bounded page bodies. Tested only
  against controlled local peers; resolver/connector injection is trusted code.
- Host-side offline DockerJobRunner: fixed entrypoint/digest, bounded input/output,
  concurrency, execution timeout, cancellation and cleanup. Actual container
  resource/egress tests pass. Not an API, durable queue or live fetch broker.

- Local quality runner: 97 worker, 29 evaluation and four UI tests, ESLint,
  TypeScript, Prettier and frontend build pass. Native development build passes.
  Manual GitHub workflow authored; remote execution unverified.
- Links/bookmarks added to product scope and delivery plan in BOOKMARKS.md.
  Offline extraction implemented with ten synthetic tests. No bookmark UI, storage or fetcher.

- Server/developer-only embedding request client with batching, full-job token
  preflight, bounded HTTPS, index reordering and safe errors. Eight mocked tests
  pass; no real tokenizer/provider/export integration or cost measurement yet.

- Saved-vector evaluation adapter with exact normalized cosine ranking and equal-weight RRF (k=60) comparison to TF-IDF. Export metadata checks model/revision/templates/tokenizer/dimensions, corpus/index hashes and truncation. Twenty-nine evaluation tests pass; vector evidence is synthetic math tests only. No actual embedding model has run.

- Offline TF-IDF keyword baseline and strict scoring harness with corpus/index fingerprints, per-category and per-query metrics. Twenty-one evaluation tests pass. Baseline text-v1 document/evidence Recall@5 is 0.9714 and MRR@5 is 0.8667; 4/5 absent queries return candidates. This is a tiny development comparator, not semantic search or an answerability system.

- Retrieval development corpus text-v1: 14 synthetic documents and 40 queries (35 answerable, 5 absent), with exact evidence mapped to 16 real processing chunks. Seven integrity tests pass. Export tool separates index/query inputs from relevance labels; no model results yet. See tests/evaluation/README.md.

- Transport-independent Python text processor: bounded typed request/results, strict UTF-8 TXT/Markdown, original source offsets, deterministic hashes/versioned passage IDs, structured safe errors. Twelve synthetic tests pass. No filesystem/network/model calls or new dependencies in this module.

- Desktop shell with fixture library, filters, reader, model lineup and preview policy screens.
- Motion selection feedback, optional reader Lenis, paused Thinking Orbs sample, local fonts/artwork/license notices.
- Four passing component tests, passing frontend and native development builds at the last implementation checkpoint.
- Legacy privacy fixes, documented audit and release follow-ups.
- Official Rust toolchain installed; C++ tools found; compatible Node available through scripts/desktop.ps1. Global npm shim remains broken; helper avoids it without changing global PATH.

## Not implemented / unverified

No real desktop import, connected worker/cloud endpoint, embeddings, Supabase project connection, auth, durable search index, chat or signed installer. Processing is tested in isolation, with character-based passages pending tokenizer validation. No native/visual/E2E verification. Previous browser opening was declined; that limitation was not bypassed. Canvas is stubbed in component tests, so passing tests do not verify the orb renderer.

Frontend lint and format checks are configured; remote CI and native E2E remain unverified. The full initial baseline diff also reports pre-existing trailing-whitespace issues in legacy files; those are not hidden or counted as a clean full-diff check. Git repository: https://github.com/kratos1911/gather-desktop (private). origin is configured; main tracks origin/main. Baseline commit b89ceec was pushed and its remote hash verified. The TASK-001 baseline contains the existing implementation and workflow documents.

## Current task

TASK-022 documents the system/security delivery plan. TASK-019A added dependency
locking/review; current source checks total 130 tests. The new recipe built and
passed offline smoke checks. TASK-023 records open scan findings; TASK-019B
has a tested offline Docker supervisor and plain-HTTP restricted transport.
Whole-broker DNS/process deadlines, browser/tool egress and integration remain open.
Provider-dependent TASK-005 work remains deferred by user.
No GitHub push authorized. Offline bookmark processing passes; live bookmark search remains pending. Chat deferred by user on 28 September.

## Next implementation

30 September final choice: Crawl4AI for public webpages and yt-dlp for supported
video metadata/available subtitles. Agent Reach is optional. See
docs/knowledge/EXTRACTION_STACK.md. Tools installed in the offline container only. Transcription,
visual video understanding and chat remain deferred. TASK-019 follows TASK-018.

TASK-018 completed: offline bookmark passages with source/field references and
TF-IDF retrieval tests. TASK-019 adapters/offline runner pass; next is TASK-023
remaining security review. TASK-019B controlled HTTP transport and offline Docker supervision now pass
local tests. Next: isolate the fetch broker with a hard deadline covering DNS,
then connect it to parsing and implement browser/tool egress. Live invocation
(019C) stays gated.
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
Latest source checks: 130 tests and frontend build on 3 October. Locked-image
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
