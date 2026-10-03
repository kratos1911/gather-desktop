# Delivery tasks

## 2 October planning checkpoint

TASK-022: delivery/security plan documented in docs/DELIVERY_PLAN.md. Planning
only; runtime gates remain open. Ordered next work:

| Task | Status | Acceptance |
| --- | --- | --- |
| TASK-019A | Build and audit verified, 3 October | Base digest + 96 wheel hashes + bootstrap pip lock and declared license inventory. No-cache build, dependency consistency, smoke and actual hash-rejection checks pass. Full image scan completed with open findings; remediation tracked in TASK-023. See services/worker/DEPENDENCY_REVIEW.md |
| TASK-023 | Partial: available patches verified | Patched OpenSSL/PCRE2; removed runtime pip/ensurepip; rebuilt and rescanned: 31 records (4 high, 2 medium, 25 low), down from 51. 21 previous records gone; one newly reported GCC advisory. Remaining unpatched/applicability review and build-tool exposure stay open. Smoke verifies fixes and prompt timeout cleanup. See services/worker/IMAGE_SCAN_REVIEW.md |
| TASK-019B | Ready for local isolation tests; live use gated by 023 | Enforced public-only egress and supervisor; DNS/redirect/subresource/bypass and timeout cleanup tests |
| TASK-019C | After 019B | Actual Crawl4AI/yt-dlp invocation on approved public tests, bounded output and truthful fallback |
| TASK-021 | Planned | Local Supabase migrations, two-user RLS/Storage/RPC tests and retry/delete/quota races |

TASK-021 can advance if live-site checks are blocked. No paid AI account needed
for local schema work. TASK-005 remains provider-gated. Follow vertical slices
in DELIVERY_PLAN.md. No runtime work is claimed by this planning checkpoint.

Current checkpoint: local quality checks pass; remote CI execution pending. Links/bookmarks accepted on 28 September. Next independent task: TASK-019 extraction adapters. Chat deferred. Provider/account/live tests remain deferred; no pushes without an explicit request.

| ID | Task | Status | Acceptance / evidence |
| --- | --- | --- | --- |
| TASK-001 | Establish docs, current state and local Git baseline | Done | Canonical documents and links reviewed; 74 baseline paths scanned with no private/generated inclusions; four tests and frontend build pass; local baseline commit contains this record; no remote publish |
| TASK-002 | Validate audience and comparable products | Ready | Record user interviews/feedback or explicitly unvalidated hypotheses; compare primary-source alternatives; decide initial audience/regions |
| TASK-003 | Desktop shell and design verification | Partial | Frontend/native build and four component tests pass; actual visual, keyboard, zoom and motion checks still pending after browser permission denial |
| TASK-004 | Transport-independent text processing contract | Done | 12 standard-library tests pass; strict JSON/base64/UTF-8 and 64 KiB source limit; source offsets, hashes/versioned IDs, overlap and retry determinism verified; no personal imports or cloud writes; see services/worker/README.md |
| TASK-005 | Cloud-oriented embedding evaluation | Partial | Corpus, TF-IDF, scorer, saved-vector adapter, exact cosine and RRF comparison implemented; 29 evaluation tests and frontend build pass. Vector tests use hand-authored numbers only, no semantic accuracy claim. TF-IDF baseline unchanged (BASELINE.md). Real export producer/provider/tokenizer/dimension/latency/cost benchmarks pending |
| TASK-006 | Supabase identity and private schema | Needs project configuration | Versioned migrations; supported signup/session/logout flow; enforce audience decision; RLS and two-user isolation tests; secure session storage; quota policy |
| TASK-007 | Text import-to-search vertical slice | Depends on 005/006 | Import TXT/MD -> durable processing -> all passages -> real search -> reader -> deletion; retry/restart/dedup/isolation tests; user-readable errors |
| TASK-008 | Native document formats | Depends on 007 | PDF/DOCX/PPTX parsers; preserved page/slide/section references; long-document and malformed-file cases; scanned pages correctly identified |
| TASK-009 | Photo and OCR retrieval slice | Depends on 007 | JPEG/PNG and scanned text ingestion; SigLIP plus OCR; separate vector spaces and rank fusion; actual source results; category-specific evaluation |
| TASK-010 | Selected-source chat slice | Deferred by user, 28 September | Pin Qwen runtime/quantization; scoped retrieval, streaming, cancellation, citations, missing-evidence and injection tests; measured resource limits |
| TASK-011 | Automated quality checks | Partial | Local runner passes 76 worker + 29 evaluation + 4 UI tests, ESLint, TypeScript, Prettier and frontend build. Manual CI workflow authored, not pushed/executed remotely. No native E2E claim |
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
