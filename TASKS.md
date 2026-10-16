# Delivery tasks

## 16 October authenticated published search and reader

TASK-021 read API slice complete locally: exact cosine search restricted to the
owner's current publications and matching model space; version-bound reader with
exact text/hash/offsets. Real Auth/PostgREST tests cover token tampering, anonymous
access, owner isolation, drafts, replacement, deletion and invalid query vectors.
64 API checks pass (31 retained lifecycle/storage checks + 33 new read checks).
Frontend build passes. Evidence: output/database-checks/published-api-20261016.log
and published-api-frontend-20261016.log. Synthetic vectors prove ordering and API
boundaries, not natural-language retrieval quality. No model or native rebuild.

Fixed the disposable harness's missing private-network database access rule;
startup failures now retain bounded, redacted diagnostics before cleanup.
Contract: docs/PUBLISHED_SEARCH.md. Next: query-text embedding/context integration
and privileged ingestion transport verification. Desktop and cloud deployment
remain separate milestones. Earlier database/model evidence was not rerun.

## 16 October internal ingestion coordinator

TASK-021 coordinator slice complete locally: trusted-context submission commits
source/job/original together; the worker claims, parses, chunks, embeds missing
passages, stages and publishes through existing contracts. Heartbeats cancel
active work after lease loss; recovered attempts reuse committed vectors.
196 database checks pass (169 retained + 27 coordinator checks), plus 10 focused
coordinator unit tests, 27 inference-control tests and the required frontend build.
Evidence: output/database-checks/coordinator-20261016.log,
coordinator-unit-20261016.log, coordinator-runtime-20261016.log and
coordinator-frontend-20261016.log. All embeddings in these runs are synthetic.
No model loaded; native inputs unchanged, so no native rebuild required.

Contract/limits: docs/INGESTION_COORDINATOR.md. Database integration uses a psql
test transport; the DB-API adapter has unit checks, not live-driver/network proof.
Real JWT/API, cloud inference and desktop integration remain incomplete. Next:
verify server identity/transport and connect published search/open adapters.
TASK-021 overall remains partial; no production readiness or deployment claimed.

## 15 October verified text publication

TASK-021 publication slice complete locally: actual-byte validation, immutable
private passage/vector staging, complete-coverage/count checks, atomic ready
transition, prior-version visibility and stale/deleted-worker fencing. See
docs/TEXT_PUBLICATION.md for contracts and limits. 169 database checks pass:
105 existing lifecycle/scheduling checks plus 64 publication checks. Frontend
build passes; Supabase test-role/pgvector bootstrap smoke and Compose validation
pass. Local logs: output/database-checks/publication-20261015.log and
publication-frontend-20261015.log. Synthetic unit vectors, no inference evidence.
No native rebuild required: frontend/native inputs unchanged. Full real API stack
was not rerun. Next: trusted coordinator and published search/context adapter;
whole TASK-021 and desktop import/search flow remain partial.

## 15 October durable ingestion scheduling

TASK-021 scheduling prerequisite complete locally: owner/request idempotency,
atomic version/job creation for an existing source, exclusive leases, crash
recovery, bounded retries, immutable provenance, deletion/replacement fencing,
private worker functions and owner-only status. 96 SQL assertions (51 new) plus
9 concurrent scenarios (5 new) pass; frontend build passes. Evidence/scope:
docs/INGESTION_JOBS.md and output/database-checks/ingestion-jobs-20261015.log.
Historical scheduling-only result; the publication slice above supersedes its
former next step. Whole backend import/search flow remains partial.

## 15 October desktop redesign

TASK-003 visual slice implemented: forest/citron/coral theme, local OFL Manrope,
responsive library/reader/setup/policies, focus restoration and reduced-motion
controls. Five UI tests, lint, frontend and native debug builds pass. Browser
inspection/contrast/reflow evidence: docs/DESIGN_REVIEW_20261015.md. Overall task
remains partial for native/accessibility QA. No push; backend plan unchanged.


## Current three-milestone path (15 October)

| Order | Outcome | Prerequisites | Completion criteria / status |
| --- | --- | --- | --- |
| 1 | Bounded source context and multi-part coverage | Verified saved vectors and source offsets | **Local component complete:** nine focused tests and frontend build pass; saved-vector replay recovers all known evidence in both sets without new inference. See docs/SEARCH_CONTEXT.md. API/desktop integration remains pending. |
| 2 | Backend TXT/MD import → index → search → open → delete | Existing schema/worker; trusted owner/version repository, durable jobs, idempotency, quotas, upload fencing and storage cleanup; relevant privacy/security gates | Test the full backend flow with isolated identities, restart/retry, stale versions and deletion visibility. No hosted provisioning is implied. |
| 3 | Desktop end-to-end flow | Milestone 2, session/credential handling and release prerequisites | Native import, truthful processing states, search/context citations, reader and delete survive restart; verify errors, keyboard access and isolation. |

Later optional work: chat, additional format adapters, ranking refinements and
visual polish. Security/licence fixes remain prerequisites to production, not
optional improvements. TASK-005/007 overall remain partial. Continue milestone 2
with one bounded backend slice; do not rerun model experiments without a relevant
input/configuration change or new evaluation question.

## 15 October paired chunk retrieval evaluation

TASK-005 evaluation slice complete: frozen text-v2 plus six-source/ten-query
boundary stress set, both policies on the same patched Qwen512 image. All 178
requests passed, 0.637–6.972 s each, about 4.00 GiB peak under unchanged limits.
Main dense gate passes: document recall 1.0, MRR 0.9792, strict evidence recall
1.0 versus legacy 1.0/0.9613/0.9911. Stress dense strict recall remains 0.50;
union coverage improves to 0.875. Split conditions and a multi-part passage miss
remain unresolved; no default fusion or production chunking change.

44 evaluation tests, 26 inference tests and frontend build pass. Failure reports
now survive outer timeout; test verifies only owned-container cleanup. Evidence:
tests/evaluation/results/chunk-retrieval-20261015.json and
docs/CHUNK_RETRIEVAL_RESULTS.md. Next: bounded same-source context assembly and
multi-part passage coverage, then ingestion integration; security/licence gates
remain. TASK-005 overall partial. No push or cloud deployment.

## 15 October patched-image checkpoint

Built separate cpu-patched image with Torch 2.14.1+cpu, Transformers 5.19.0,
34 hash-locked wheels and exact OpenSSL/PCRE2 fixes. Rescan completed on 14 October:
28 records (1 high/1 medium/26 low), down from 56/12 high. Remaining zlib/tar
findings are open. Added a 512-token/8-KiB source-slice preparer preserving Unicode
offsets, overlap and stable IDs; existing parser/index and runtime budgets unchanged.
Not yet wired into desktop ingestion. 25 focused tests passed on Windows/candidate
Linux and frontend build passed on 14 October. Baseline six-case export captured.

15 October real checks now pass: six candidate vectors match the baseline within
tolerance, token counts and three tested rankings unchanged. Five chunks (306–500
tokens) return valid embeddings in 3.053–5.883 s, under the unchanged 15 s deadline;
peak 3.95 GiB under the 5 GiB ceiling. Evidence: tests/inference/results/
patched-{compatibility,comparison,chunks}-20261015.json. Memory was freed through
approved transient Linux clean-cache release; no API stop or Docker restart.
Next: retrieval-quality evaluation with new boundaries before ingestion integration,
plus remaining security/licence review. No deployment or push. TASK-005 partial.

## 14 October extended CPU profiles and security review

TASK-005 measured: 512 tokens 5.645 s, 1,024 tokens 13.632 s; 2,048-token item
and 4,096-token batch failed the unchanged 15 s deadline with clean termination,
no OOM. Over-limit rejection plus valid-request recovery passed. Fifty sequential
short queries passed: median 0.710 s, p95 0.935 s, cgroup peak 3.64 GiB.
Evidence: tests/inference/results/qwen-{long,batch,limits,sustained}-20261014.json.
No failures discarded. 21 control/reporting tests pass on Windows and Linux;
frontend build passes. Runtime image unchanged. TASK-005 remains partial.

Scout reviewed that exact image: 56 records (12 high, 7 medium, 37 low), no
suppression. See services/inference/IMAGE_SCAN_REVIEW.md and PROFILE_RESULTS.md.
Next: patch OS packages, compatibility-test a maintained CPU AI stack, rescan,
and evaluate smaller chunks/batches before API integration. No deployment,
existing API changes, Docker restart or GitHub push.

## 14 October real Linux Qwen smoke passed

TASK-005 container smoke slice verified: 2 CPUs, 5 GiB RAM ceiling, no extra swap,
network disabled, non-root and read-only configuration assertions passed. Startup
15.781 s; ten short fictional requests 0.593–0.742 s; cgroup peak 3.87 GiB.
Pinned identity, 512-dimensional normalized vectors and repeated-query consistency
passed. Container exited zero and was removed. Evidence:
tests/inference/results/qwen-container-20261014.json. This supersedes the RAM
blocker below. No runtime code changed; previous 18 control tests/frontend build
were not rerun for this evidence-only update. Next: maximum-input/load profiling
and image security/licence review. Whole TASK-005 remains partial. No API changes,
cloud deployment or GitHub push.

## 13 October isolated inference container checkpoint

TASK-005 remains partial. Built gather-inference:cpu-local on D: from a pinned
Python base and 25 hash-locked Linux CPU wheels. Private bounded JSONL adapter,
verified model export and isolated test launcher implemented. Eighteen synthetic
tests pass both on Windows and inside the Linux container, including malformed
frames, oversized-frame closure, deadlines, child cleanup and explicit recovery.
Actual Docker configuration assertions pass for CPU/RAM/swap/PID limits, non-root,
read-only mounts/root and disabled network. Frontend production build passes.
Evidence: tests/inference/results/container-controls-20261013.json.

Real Qwen container smoke stopped before creating a container at the 4 GiB host
RAM guard; measured free memory then about 2.4 GiB. No real container latency or
peak-memory result yet. Next: rerun the prepared real smoke after memory is free,
then maximum-input profiling and image vulnerability/licence review before API
integration. Existing API containers/settings untouched. No cloud deploy or push.

## 13 October Docker migration verified

Storage prerequisite complete: D:\DockerDesktop\DockerDesktopWSL\disk\docker_data.vhdx
is active after a stopped-source refresh and full SHA-256 verification. Before/
after inventory identical: 9 containers, 64 images, 1 volume. All nine containers
restarted; unrelated application behavior was not tested. Old C: data disk removed
with approval after verification; C: free space about 36.3 GiB. Settings backup and
private inventory/hash evidence live in ignored output/docker-migration.
Next TASK-005: build/measure bounded Linux CPU serving image. Gemma account-level
access remains denied despite valid local login. No model/container build this turn.

## Earlier 13 October setup follow-up (disk blocker superseded above)

HF login saved on D: and API authentication verified; EmbeddingGemma still returns
403 with account-level model-access denial. Same-account access approval needs
checking. Docker engine recovered from startup socket error and responds as
29.7.2. Two settings-based disk moves reverted to C:; D:\DockerDesktop exists but
contains no migrated VHDX. Container builds remain paused. No reset/data deletion.

## 13 October real serving smoke

TASK-005: pinned Qwen persistent host process passed with three fictional inputs,
two CPU threads and 512-dimensional vectors. Startup 14.239 s; requests
0.505/0.669/0.709 s; process reuse and cleanup verified. Post-request RSS 2.54 GiB,
not peak. Evidence: tests/inference/results/qwen-host-20261013.json.
Docker data disk remains on C:; HF login unavailable at checked locations.
Container limits/performance and Gemma comparison remain pending. No runtime
code changed; prior 169-test checkpoint retained, not rerun for documentation.

## 12 October fresh text challenge

TASK-005 second local slice complete: 40 new fictional documents, 64 passages,
64 questions (56 answerable), corpus/labels frozen before inference. Unchanged
Qwen/prompt/chunker/cosine/RRF evaluated at 256/512/1,024 dimensions. The primary
512 candidate passes declared >=0.90 gates: document recall 1.0, evidence recall
0.9911, MRR 0.9613. Five nonperfect dense queries reviewed; all eight absent
questions still return candidates. Do not claim blind or real-world evaluation.
39 evaluation tests, frontend build, pip consistency and v1 regression pass;
twelve v1 raw artifacts still match recorded hashes. See docs/TEXT_V2_RESULTS.md.

Next TASK-005 slice: local serving-container measurement with explicit CPU/RAM/
concurrency/request limits and D: image storage verified first. 512 dimensions is
an experimental candidate, not a final production selection. Exact identifiers,
temporal distinctions and multi-part passage coverage remain quality follow-ups.
No cloud deployment or GitHub push is authorized by this checkpoint.

## 10 October CPU benchmark checkpoint

TASK-005 local slice complete: real Qwen3-Embedding-0.6B export with immutable
revision and safetensors hashes; D:-only environment/cache/temp/output; token
preflight; 256/512/1,024-dimensional dense and RRF evaluation; two/four CPU-thread
memory/latency measurements. 112 worker + 34 evaluation + 4 UI tests, lint,
typecheck, formatting, frontend build and pip check pass. See docs/CPU_BENCHMARK.md
and tests/evaluation/results/qwen-cpu-20261010.json for detailed evidence.

TASK-005 overall stays partial. Historical next acceptance (now measured above): larger frozen unseen text set
and failure review before selecting model/dimensions/fusion, then a bounded CPU
serving-container test. EmbeddingGemma requires user license acceptance; visual
models need image/OCR fixtures. Cloud measurement, production runtime/security,
inference quotas and connected desktop-to-pgvector search remain unverified.
Local model tests do not authorize paid deployment. No GitHub push.

## 2 October planning checkpoint

TASK-022: delivery/security plan documented in docs/DELIVERY_PLAN.md. Planning
only; runtime gates remain open. Ordered next work:

| Task | Status | Acceptance |
| --- | --- | --- |
| TASK-019A | Build and audit verified, 3 October | Base digest + 96 wheel hashes + bootstrap pip lock and declared license inventory. No-cache build, dependency consistency, smoke and actual hash-rejection checks pass. Full image scan completed with open findings; remediation tracked in TASK-023. See services/worker/DEPENDENCY_REVIEW.md |
| TASK-023 | Partial: available patches verified | Patched OpenSSL/PCRE2; removed runtime pip/ensurepip; rebuilt and rescanned: 31 records (4 high, 2 medium, 25 low), down from 51. 21 previous records gone; one newly reported GCC advisory. Remaining unpatched/applicability review and build-tool exposure stay open. Smoke verifies fixes and prompt timeout cleanup. 8 October code-image scan: 29 records (2 high, 1 medium, 26 low), with unchanged package versions; feed differences are not new fixes. See services/worker/IMAGE_SCAN_REVIEW.md |
| TASK-019B | Partial: whole-fetch deadline and page pipeline verified, 8 October | Nine broker subprocess tests and six adapter/pipeline tests added; stuck DNS/connect/TLS, cancellation, output limits, cleanup and controlled HTTP-to-Docker-parser flow pass. Browser/tool egress, production broker confinement and public compatibility remain open. Live use gated by 023. See services/worker/SUPERVISION.md |
| TASK-019C | After 019B | Actual Crawl4AI/yt-dlp invocation on approved public tests, bounded output and truthful fallback |
| TASK-021 | Partial: core Supabase APIs verified, 9 October | 49 database checks plus 31 real Auth/PostgREST/Storage checks pass: owner JWT/RPC, private originals, tombstone visibility, API byte removal before SQL finalization and interruption/retry. Disposable core stack, not complete hosted parity. Upload fencing, background cleanup, byte/rate quotas, processing leases and desktop connection remain pending. See supabase/LOCAL_INTEGRATION.md |

TASK-021 can advance if live-site checks are blocked. No paid AI account needed
for local schema work. TASK-005 remains provider-gated. Follow vertical slices
in DELIVERY_PLAN.md. No runtime work is claimed by this planning checkpoint.

Current checkpoint: local quality checks pass; remote CI execution pending. Links/bookmarks accepted on 28 September. Next: TASK-019B production broker confinement/browser egress, or TASK-021 local persistence while live-use security gates remain open. Chat deferred. Provider/account/live tests remain deferred; no pushes without an explicit request.

| ID | Task | Status | Acceptance / evidence |
| --- | --- | --- | --- |
| TASK-001 | Establish docs, current state and local Git baseline | Done | Canonical documents and links reviewed; 74 baseline paths scanned with no private/generated inclusions; four tests and frontend build pass; local baseline commit contains this record; no remote publish |
| TASK-002 | Validate audience and comparable products | Ready | Record user interviews/feedback or explicitly unvalidated hypotheses; compare primary-source alternatives; decide initial audience/regions |
| TASK-003 | Desktop shell and design verification | Partial | Frontend/native build and four component tests pass; actual visual, keyboard, zoom and motion checks still pending after browser permission denial |
| TASK-004 | Transport-independent text processing contract | Done | 12 standard-library tests pass; strict JSON/base64/UTF-8 and 64 KiB source limit; source offsets, hashes/versioned IDs, overlap and retry determinism verified; no personal imports or cloud writes; see services/worker/README.md |
| TASK-005 | Cloud-oriented embedding evaluation | Partial: paired chunk retrieval measured | 44 evaluation/26 inference tests and frontend build pass. 178 real requests; text-v2 candidate dense gate passes, boundary strict/union evidence 0.50/0.875 exposes context and multi-part misses. No connected HTTP/desktop ingestion. Remaining context/coverage, security/licence, Gemma/visual and cloud measurement gates stay open. See docs/CHUNK_RETRIEVAL_RESULTS.md |
| TASK-006 | Supabase identity and private schema | Needs project configuration | Versioned migrations; supported signup/session/logout flow; enforce audience decision; RLS and two-user isolation tests; secure session storage; quota policy |
| TASK-007 | Text import-to-search vertical slice | Depends on 005/006 | Import TXT/MD -> durable processing -> all passages -> real search -> reader -> deletion; retry/restart/dedup/isolation tests; user-readable errors |
| TASK-008 | Native document formats | Depends on 007 | PDF/DOCX/PPTX parsers; preserved page/slide/section references; long-document and malformed-file cases; scanned pages correctly identified |
| TASK-009 | Photo and OCR retrieval slice | Depends on 007 | JPEG/PNG and scanned text ingestion; SigLIP plus OCR; separate vector spaces and rank fusion; actual source results; category-specific evaluation |
| TASK-010 | Selected-source chat slice | Deferred by user, 28 September | Pin Qwen runtime/quantization; scoped retrieval, streaming, cancellation, citations, missing-evidence and injection tests; measured resource limits |
| TASK-011 | Automated quality checks | Partial | 12 October: 112 worker + 39 evaluation + 14 inference + 4 UI = 169 tests, lint/types/format/build pass. Inference suite added to local check script. Manual CI workflow authored, not pushed/executed remotely. No native E2E claim |
| TASK-012 | Security and code review | Continuous / release gate | Threat model, input limits, access isolation, deletion reconciliation, license/secret scan, reviewed changes; close privacy audit owner inputs |
| TASK-013 | Preview installer and QA | Depends on core slices | Clean Windows install/update/uninstall; cloud setup; network/low-disk/offline/quota scenarios; no developer tools or model downloads required |
| TASK-014 | Production distribution | Depends on 012/013 | Approved destination, signing decision, final policies, backup/restore and rollback; verified release artifacts; no public upload before ready |
| TASK-015 | Monitoring and iteration | After release | Privacy-preserving failures/performance/quota metrics; opt-in telemetry only; issue triage and tested patch releases |
| TASK-016 | Bookmark processing contract | Done | Ten synthetic tests pass; bounded offline HTML extraction and URL validation. No live fetch. |
| TASK-018 | Bookmark passage-to-search adapter | Done | Seven synthetic tests pass: field provenance, deterministic/versioned IDs, failed-page notes, late-passage TF-IDF retrieval. Map extracted text, metadata and notes to versioned passages; verify keyword retrieval and provenance using synthetic bookmarks. No cloud account required. |
| TASK-017 | Bookmark save-to-search flow | Depends on 006/007/016 | Private save/edit/delete, restricted fetching/enrichment, search, retry/refresh, SSRF and two-user tests; video content separately scoped |

## Planned task TASK-019

Partial TASK-019 (output adapters, offline runner and container smoke checks pass; live checks pending): Crawl4AI webpage and yt-dlp metadata/subtitle adapters.
Depends on TASK-018 and fetch/privacy review. Acceptance: versioned backend,
normalized output/provenance, mocked success/unavailable/limit/error checks,
documented external recipients and safe invocation. No desktop-cookie Instagram
integration or real semantic results claimed. See docs/knowledge/EXTRACTION_STACK.md.

## Cleanup checkpoint

TASK-020: repository organization complete; 109 tracked-file dispositions recorded,
six legacy files archived, three unused logos removed. 63 tests and frontend
quality/build checks pass. See docs/REPOSITORY_AUDIT.md.

## Completed task brief: TASK-004

**Context:** Read canonical docs and preserve the existing UI. The next risk is consistent document representation, not another decorative screen.

**Task:** Implement the transport-independent processing contract and synthetic text extraction/chunking module, exercised locally before future cloud integration.

**Files:** Introduce services/worker and tests/fixtures only as needed; add typed interface definitions in the desktop app when actually used.

**Constraints:** No Supabase schema writes, new hosted service, model download, personal document parsing or UI pretending real ingestion exists. Preserve native command least privilege. Token limits remain aligned with the later selected embedding tokenizer.

**Acceptance:** Stable source references; deterministic content hashes/chunk identifiers; bounded inputs; useful structured errors; explicit parser/chunker versions; recovery behavior documented.

**Testing:** Synthetic UTF-8, empty input, long text, boundaries/overlap, unsupported encoding, invalid request and size limits. Review the data contract before wiring UI/IPC.

**Report:** What changed, why, checks and evidence, review findings/fixes, remaining issues, commit and updated state.

## TASK-019 container evidence, 1 October

Image build succeeded after Docker became available. Direct package versions and
pip dependency consistency verified. `scripts/check_extractor_container.py` passes
synthetic success/error jobs and selected runtime restrictions. Full local checks:
65 worker + 29 evaluation + 4 UI = 98 tests, lint/types/format/frontend build pass.
Still open: transitive/base-image locking, enforced public-only egress, actual tool
invocation, browser dependencies and live compatibility tests. No semantic results
or end-to-end desktop ingestion claimed.
