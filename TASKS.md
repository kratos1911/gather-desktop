# Delivery tasks

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
| TASK-005 | Cloud-oriented embedding evaluation | Partial: real host serving smoke passes | v1/v2 real benchmarks retained. Persistent CPU process has 14 synthetic boundary tests; real host smoke passed 13 October. Docker disk move to D: and HF login pending; Gemma terms accepted. No container or HTTP serving verified. See services/inference/README.md and docs/TEXT_V2_RESULTS.md. Independent review, Gemma/visual comparison, cloud latency/cost and production runtime remain pending |
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
