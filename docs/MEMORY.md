# Current project state

20 October: model-bearing release candidate built; see RELEASE_AND_PILOT.md and
deploy/cloud-run/pilot.json. Correct target is gather-development-511211 (Gather
Development), Mumbai; INR 500 total ceiling. Intrixshield is forbidden. Browser
verified Gather; local gcloud only has the work account and cannot access it.
Collected notices for 439 hashed crates plus separate parent-project components.
Fixed real Cloud Run hostname compatibility; 34 identity tests, 8 packaging/HTTP
checks, frontend build and 128 MiB baked-file integrity verification pass.
Real-model release smoke is blocked by 3.09 GiB free RAM (<4 GiB required).
Milestones 1/2 remain partial: personal CLI sign-in, real smoke and final resource/
security approval pending. No cloud mutation/upload/deployment. Model/caches on D:.

19 October latest: Docker available; cloud-startup candidate built. All 49 Linux
startup/auth/HTTP/artifact/SIGTERM checks pass, 512 MiB/one CPU, no model/network.
See CLOUD_STARTUP.md and cloud-startup-linux-20261019.json for evidence. Prior
unchanged frontend build retained. Two protected APIs showed restart-count changes;
no mutation commands issued and no cause inferred. Next: native attribution and
immutable model-bearing release packaging, then approved cloud pilot. Live IAM,
cold start, release findings and paid deployment remain unverified/unapproved.

19 October: guarded Cloud Run startup implemented and host-verified; see
CLOUD_STARTUP.md. Explicit module requires matching intended IAM policy, managed
Google auth and valid PORT; local startup remains loopback-only. 11 new cloud,
32 existing auth/startup/HTTP and 18 staging checks pass; frontend build passes.
Exact source staged, no models loaded. Linux image verification remains blocked:
Docker Linux engine pipe absent on preflight. Next: start Docker normally and
verify a separate cloud-startup candidate. No live IAM proof or deployment.

19 October: complete-input validation for zlib staging is verified. All four
inputs are read before output creation; hashes validate the bytes actually copied.
Missing installer/manifest fails without new or modified staging output. The CLI's
previous missing-patch regression is retained and included in this checkpoint.
18 focused tests and frontend build pass; no Docker/model run. Disk-write failures
are not transactionally rolled back. Next: guarded Cloud Run startup, with current
security/licence/IAM/spend release gates retained. Root CLI logs remain untouched.

Desktop/CLI collaboration rules ready: docs/CLI_WORKFLOW.md. One writer per
checkout, scoped handoff, reviewer-owned commit by default. No automatic session
connection. Python launcher now forwards piped text; focused checks/build pass.

Windows CLI runtime discovery fixed for lightweight checks: scripts/python.ps1
handles missing PATH, redirected LOCALAPPDATA and spaces; propagates failures.
AGENTS.md documents usage and bounded troubleshooting. Existing CLI test edit
and root log files remain uncommitted and untouched. No global PATH changes.

Final zlib scan: 28 findings (1 high, 1 medium, 26 low). Scout still flags
CVE-2026-85091 on +gather1; no suppression applied. The targeted defect is fixed
and regression-verified independently, not scanner-cleared. Evidence:
tests/inference/results/zlib-scan-20261018.json. Scanner exited zero; temporary
archive cleanup hit a file lock, so no forced deletion was attempted.

Current: zlib error-state bug fixed in the separate zlib-candidate image using
a pinned local backport, not an official Debian update. Original installed
library fails the regression (42); patched installed library passes (0).
Standard zlib tests, compression/PyTorch compatibility, 14 focused checks and
frontend build pass. See services/inference/zlib/README.md and retained evidence.
No model rerun or deployment. Other release gates remain; next is guarded cloud
startup implementation with the final scan result retained above.

Current: notice-packaged Linux candidate built and verified. Model card matches
the pinned artifact hash; official Apache licence retained. All required notices
are enforced by staging. 47 wheels, 177 embedded notices, five supplements;
87 OS copyright files present. Previous nine image layers identical. Ten focused
checks and frontend build pass. Evidence: notices-image-20261018.json.
Next independent development: explicit guarded Cloud Run entry point, keeping
loopback default. Deployment remains blocked by OS adjudication, full native
attribution review, actual IAM acceptance and spend approval. No model rerun.

Current: tokenizers upstream licence gap fixed in source; exact-version files
and provenance retained. Notice collection integrated into image staging and
Dockerfile. 47 wheels / 177 notices / 3 supplements staged; new image not built.
Focused checks and frontend build pass. OS zlib still unresolved in Debian's
tracker and bug report; no waiver. Next: model/native attribution review and
supported OS remediation evidence before release-image promotion.

Current checkpoint, 18 October: CLOUD_PILOT_PLAN.md records the bounded pilot
proposal and open gates. All 47 serving wheel hashes match the lock; tokenizers
has no detected bundled notice file. No licence clearance or OS waiver claimed.
Background key refresh requires revising the request-based CPU proposal;
instance-based billing is proposed, not authorized. Next: exact-version notices
and security adjudication, then explicit guarded cloud packaging. No deployment.

Latest, 18 October: live Google public-key compatibility passed inside Linux
startup-candidate: two keys, 0.505 s, unchanged freshness/resource bounds.
Evidence: RECEIVING_IDENTITY.md and tests/inference/results/live-google-keys-20261018.json.
Earlier 51 Linux checks and unchanged frontend build retained; no model rerun.
Next: remaining licence/OS security review and concrete cloud pilot configuration.
Actual identity-token/IAM/header validation, public bind and spend approval remain
gates. Successful public-key retrieval alone does not authorize deployment.

Current next-step status (17 October): real Qwen loopback HTTP smoke passed.
Startup 12.68 s, short requests 0.68-0.82 s, 512-token passage 4.69 s, peak 3.98 GiB
under the unchanged 5 GiB ceiling. Valid vectors, rejection/recovery and cleanup
pass. See services/inference/HTTP_SMOKE.md and its retained real-model evidence.
RAM guard passed at 6.05 GiB after specifically approved transient cache release.
No stop/restart commands or persistent Docker setting changes; API restart caveat
is recorded in PROGRESS.md. Next: cloud IAM/header integration plan and remaining
security gates before any authorized deployment. No cloud readiness claim.

Latest (17 October): receiving authentication and managed key refresh packaged in
an isolated 47-dependency Linux candidate. Actual SIGTERM verifies that a busy
synthetic inference child stops, HTTP returns 503 and the refresh thread joins.
Four host staging checks and required frontend build pass. Initial image passed
38 Linux checks plus the corrected signal test; patched image passes all 39
in one run. No real model or Google call.

Scan caught three high pyasn1 0.6.3 findings; upgraded only that added dependency
to 0.6.4. Final patched-image verification is recorded in
services/inference/SERVING_IMAGE.md. Final scan returns to 28 OS findings,
with none reported for Python; OS findings remain unresolved.
Public binding and deployment remain blocked. No protected workloads changed.

The real-model HTTP smoke above supersedes the previous RAM-blocked next step.
Actual Google/IAM/header handoff, release security review and cloud pilot approval
remain separate prerequisites. Desktop uses sample data; no live integration claim.
Historical implementation/test evidence is in PROGRESS.md and TASKS.md.

Latest UI checkpoint: expressive desktop preview redesign implemented. Five UI
tests, lint, frontend and native debug builds pass. Browser visual/contrast/reflow
checks recorded in DESIGN_REVIEW_20261015.md; native scaling/accessibility QA
remains open. Still fictional data; backend delivery milestone remains next.


Updated: 15 October 2026. Current forward plan: DELIVERY_PLAN.md. New architecture
choices there are proposed, not implemented. PROGRESS.md records history.

Current: bounded source context implemented and saved-vector replay completed;
see SEARCH_CONTEXT.md for policy, safety boundary and evidence. Nine focused tests
and frontend build pass. Known boundary coverage recovered with zero new model
calls; ranking/abstention and real-user quality remain unresolved. Next is
milestone 2 in TASKS.md: backend import/index/search/open/delete coordination with
trusted ownership/version reads. No Docker/app/process changes this checkpoint.

Prior evaluation checkpoint:

Latest: paired chunk-policy retrieval evaluation completed on 15 October. All
178 real requests passed. text-v2 candidate dense recall/evidence 1.0, MRR 0.9792;
predeclared gate passes. Boundary strict evidence stays 0.50, union coverage 0.875;
three split-condition questions and one multi-part passage miss need attention.
44 evaluation tests, 26 inference tests and frontend build pass. See
CHUNK_RETRIEVAL_RESULTS.md for all regressions and evidence. Next: bounded
same-source context assembly and multi-part coverage before ingestion integration.
Security/licence review remains open; no model/image promotion, deployment or push.
Docker recovered from a startup socket error through a user-approved close/reopen;
no reset or file deletion. Authorized background Teams/WhatsApp closure freed RAM;
Chrome and this session remained running. No individual API stop/update commands.

Earlier patched-image checkpoint:

Newest checkpoint: separate patched CPU image built; 25 focused tests and frontend
build passed on 14 October. Torch 2.14.1+cpu / Transformers 5.19.0 and exact Debian
OpenSSL/PCRE2 fixes reduced scan records from 56 (12 high) to 28 (1 high). Remaining
zlib high and tar medium findings have no fixes listed and remain open. New
512-token source-slice preparer preserves offsets/coverage but is not integrated
into desktop ingestion. Candidate real checks passed on 15 October: six vectors
match baseline tolerance, token counts/rankings unchanged; five 306–500-token
chunks took 3.053–5.883 s, peak 3.95 GiB. Approved transient Linux clean-cache
release cleared the unchanged 4 GiB host guard. No API stop, Docker restart,
candidate promotion or push. Next: retrieval-quality evaluation of new boundaries,
then ingestion integration; security/licence gates remain open. See
services/inference/UPGRADE.md for reproducible steps and evidence.

Latest extended checkpoint: all four real CPU profiles attempted and recorded.
512/1,024-token documents took 5.645/13.632 s; 2,048-token item and max batch
hit the 15 s deadline (no OOM, clean termination). Over-limit rejection/recovery
passed. Fifty short queries passed, median 0.710 s, p95 0.935 s, peak 3.64 GiB.
21 control/reporting tests pass on Windows/Linux; frontend build passes. Image
unchanged. Security scan: 56 records, including 12 high; image NOT deployment-ready.
See services/inference/PROFILE_RESULTS.md and IMAGE_SCAN_REVIEW.md. Next: OS/AI
dependency remediation with compatibility tests/rescan, then smaller-chunk policy
evaluation. No limits relaxed, no existing API changes or push. TASK-005 partial.

Latest TASK-005 checkpoint: isolated Linux CPU image built on D: with 25
hash-locked dependencies; 18 inference/protocol tests pass on Windows and inside
the container. The launcher verifies resource limits, non-root/read-only and
offline configuration and cleans only its uniquely named test container. The
frontend build passes. See services/inference/CONTAINER.md and recorded control
evidence. Real container inference passed on 14 October after 4.20 GiB host RAM
became available: 15.781 s startup, ten fictional requests at 0.593–0.742 s,
4,155,457,536-byte cgroup peak (3.87 GiB) within the 5 GiB ceiling. Model identity,
normalized 512-dimensional vectors and repeated-query consistency passed; the
test container exited successfully and was removed. Evidence:
tests/inference/results/qwen-container-20261014.json. Next: maximum-input/load
profiling and image security review. TASK-005 remains partial; no connected
desktop search or cloud deployment. Existing API containers unchanged. No push.

Latest setup result (13 October): Docker disk migration is complete and verified.
The failed UI move treated Robocopy success code 1 as failure. After stopping
Docker/WSL, the stale D: copy was refreshed from C: and matched its full SHA-256.
Settings were backed up and CustomWslDistroDir set to D:\DockerDesktop\DockerDesktopWSL.
Docker restarted with identical 9-container/64-image/1-volume inventory. D: disk
is in use; the old C: disk was detached/unlocked and then removed with approval.
C: had about 36.3 GiB free; D: about 32.74 GiB at migration completion. The image
build is now verified as recorded above; real container measurement is pending.

HF login is now saved in the ignored D:
benchmark HF home and authenticated successfully. The fine-grained token's account
still receives HTTP 403 for EmbeddingGemma; the response indicates account-level
model access is not approved. Check acceptance/access using the same account.
Docker startup socket failure recovered by closing the failed Desktop and
launching via Windows Explorer. Engine 29.7.2 responds. No factory reset, token
disclosure or model download performed during the migration.

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
chose Qwen first. On 12 October the user confirmed EmbeddingGemma terms accepted;
local Hugging Face authentication now works, but that account's Gemma access is denied. Commit
locally; push only on an explicit request to push.

Gather is a provisional name for a Windows desktop content library with semantic text/photo search and selected-source chat. Tauri/React/TypeScript and Supabase Free remain. User chose cloud AI on 27 September (ADR-009); later CPU/Cloud Run choices are in ADR-038. No end-user model downloads planned. Design avoid-list applies. No agentic file modification, payment feature or mobile app in MVP. Chat remains deferred until search works.

## Implemented

- 13 October real persistent Qwen host smoke passed using the verified D: model:
  14.239 s startup, three requests 0.505/0.669/0.709 s, two CPU threads, 512 dimensions.
  Same process reused and reaped after completion. RSS after requests 2.54 GiB
  (not peak memory). This supersedes the 12 October RAM blocker below; only three
  fictional inputs were used, not a load test. Docker disk is now verified on D:
  and HF login works, but Gemma account access is denied. Container build and
  Gemma remain pending. No new cloud work or GitHub push.

- TASK-005 persistent CPU process prerequisite added in services/inference.
  Fourteen synthetic tests verify bounds, readiness, process reuse, busy rejection,
  token preflight, deadline termination/reaping and explicit recovery. Full checks
  pass: 112 worker + 39 evaluation + 14 inference + 4 UI = 169 tests, lint/types/
  formatting/frontend build. Real Qwen host smoke stopped at the 4 GiB RAM guard.
  The later host smoke and D: Docker migration are now verified. Container build,
  limits and measurements remain unverified. No HTTP endpoint or cloud deployment.
  See ../services/inference/README.md. Next: implement and measure the bounded
  Linux serving container; resolve Gemma account access separately.

- TASK-005 fresh challenge: 40 new fictional documents, 64 chunks, 64 questions
  frozen before inference. Qwen 512 dense passes the declared development gate:
  100% document recall, 99.11% evidence recall, MRR 0.9613 on 56 answerable queries.
  All eight absent cases still return candidates. Five nonperfect dense queries
  reviewed; exact codes, temporal wording and multi-part passage coverage remain
  issues. Warm median/p95 0.329/0.403 s, OS peak 3.64 GiB, offline on D:. 39
  evaluation tests, frontend build, pip check and v1 regression pass. Previous
  worker/UI checks were not rerun for this evaluation-only change. See TEXT_V2_RESULTS.md.

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

- 10 October full quality checkpoint: 112 worker, 34 evaluation and four UI tests, ESLint,
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

TASK-005 fresh challenge verified on 12 October with settings unchanged from v1.
Next: measure a local serving container with explicit resource limits; verify
Docker image storage is on D: before large builds. The 512-dimensional candidate
advances only to this experiment, not final production selection. Independent
relevance review and the observed retrieval weaknesses remain open. EmbeddingGemma waits for license/access; visual
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
Provider connection remains pending. v1/v2 semantic benchmarks now exist; add
independently reviewed real-world and larger-scale cases before release claims. TASK-002
audience research and TASK-003 visual QA remain open.

## Inputs needed before later gates

Supabase project/public configuration; audience/regions; operator/contact and final policies; cloud provider, budget, model/license/runtime selection; signing and public distribution destination. Do not request secrets in chat. Current .env is private legacy configuration and is not copied into the new app.

## Obsidian workspace

Project hub: [[docs/PROJECT_HUB]]. Shared repository notes are the source of truth;
concepts, ideas, templates and the search-flow canvas supplement the canonical
documents. Local template/daily-note configuration saved; Obsidian UI not verified.
Latest evaluation checks: 39 tests and frontend build on 12 October; the full
source/UI checkpoint was 150 tests on 10 October. Locked-image
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
