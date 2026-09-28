# Delivery tasks

Current checkpoint: local quality checks pass; remote CI execution pending. Links/bookmarks accepted on 28 September. Next independent task: TASK-016 synthetic bookmark processing. Provider/account/live tests remain deferred; no pushes without an explicit request.

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
| TASK-010 | Selected-source chat slice | Depends on 007 | Pin Qwen runtime/quantization; scoped retrieval, streaming, cancellation, citations, missing-evidence and injection tests; measured resource limits |
| TASK-011 | Automated quality checks | Partial | Local runner passes 20 worker + 29 evaluation + 4 UI tests, ESLint, TypeScript, Prettier and frontend build. Manual CI workflow authored, not pushed/executed remotely. No native E2E claim |
| TASK-012 | Security and code review | Continuous / release gate | Threat model, input limits, access isolation, deletion reconciliation, license/secret scan, reviewed changes; close privacy audit owner inputs |
| TASK-013 | Preview installer and QA | Depends on core slices | Clean Windows install/update/uninstall; cloud setup; network/low-disk/offline/quota scenarios; no developer tools or model downloads required |
| TASK-014 | Production distribution | Depends on 012/013 | Approved destination, signing decision, final policies, backup/restore and rollback; verified release artifacts; no public upload before ready |
| TASK-015 | Monitoring and iteration | After release | Privacy-preserving failures/performance/quota metrics; opt-in telemetry only; issue triage and tested patch releases |
| TASK-016 | Bookmark processing contract | Ready | Synthetic URL validation and safe metadata/article extraction, provenance and unavailable fallback; no live fetch/account; see docs/BOOKMARKS.md |
| TASK-017 | Bookmark save-to-search flow | Depends on 006/007/016 | Private save/edit/delete, restricted fetching/enrichment, search/chat, retry/refresh, SSRF and two-user tests; video content separately scoped |

## Completed task brief: TASK-004

**Context:** Read canonical docs and preserve the existing UI. The next risk is consistent document representation, not another decorative screen.

**Task:** Implement the transport-independent processing contract and synthetic text extraction/chunking module, exercised locally before future cloud integration.

**Files:** Introduce services/worker and tests/fixtures only as needed; add typed interface definitions in the desktop app when actually used.

**Constraints:** No Supabase schema writes, new hosted service, model download, personal document parsing or UI pretending real ingestion exists. Preserve native command least privilege. Token limits remain aligned with the later selected embedding tokenizer.

**Acceptance:** Stable source references; deterministic content hashes/chunk identifiers; bounded inputs; useful structured errors; explicit parser/chunker versions; recovery behavior documented.

**Testing:** Synthetic UTF-8, empty input, long text, boundaries/overlap, unsupported encoding, invalid request and size limits. Review the data contract before wiring UI/IPC.

**Report:** What changed, why, checks and evidence, review findings/fixes, remaining issues, commit and updated state.
