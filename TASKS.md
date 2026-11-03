# Current delivery tasks

Updated 3 November 2026. Current state: [MEMORY](docs/MEMORY.md).
Work/evidence: [progress](docs/PROGRESS.md) and task-specific contracts.
The [full previous task journal](docs/history/2026-10-26/TASKS-2026-10-26.md)
preserves all earlier acceptance text and checkpoints.

## Next sequence

The main Library now uses owned saved files and one semantic search, with a
minimal dark interface. Native sign-in/listing/opening passed; new UI import,
search and deletion paths passed synthetic HTTP integration checks. See
[unified interface](docs/UNIFIED_LIBRARY.md). Current-PC installer QA passed;
clean-machine acceptance remains open. The selected DOCX slice is implemented
and its approved hosted/native acceptance passed; exact scope and evidence are
in [DOCX_IMPORT](docs/DOCX_IMPORT.md). PDF live acceptance is in [PDF_IMPORT](docs/PDF_IMPORT.md).
Do not confuse the separate sample build
with the connected application.

Deliver complete user flows; supporting fixes/checks belong inside their milestone.
These three milestones target a usable private text pilot, not the whole multi-format
MVP or public release. Implementation is present; acceptance remains per item below.

Current delivery: milestones 1/2 are implemented and verified in the private
hosted flow. Milestone 3 has a deployed API, native executable/installer and real
Windows sign-in/import/automatic-ready/search/open evidence. Clean-machine
install/uninstall and release signing remain open acceptance. See
[delivery evidence and artifacts](docs/PRIVATE_DESKTOP_DELIVERY.md).

| Milestone | Outcome and completion criteria | Dependencies / gates |
| --- | --- | --- |
| 1. Automatic private text processing (verified private flow) | A newly saved, owned TXT/Markdown import progresses to searchable/openable text without a terminal worker command. Truthful progress/failure states, bounded restart recovery, duplicate prevention and deletion/account isolation pass focused checks plus one bounded hosted flow. | Reuse admission, durable jobs, exact-target claims, leases and atomic publication. Startup handling and readiness verification are part of final integration, not prerequisites for offline implementation. Preserve existing request budgets/deadlines, explicit retry rules and the older unfinished job. |
| 2. Complete recovery and deletion | Reconnect shows durable state and actionable failures; deletion hides immediately and reports confirmed physical cleanup or a truthful pending/failure state. No manual SQL for the supported flow; late work cannot restore deleted content. | Reuse listing, tombstones, cleanup guards and replay receipts; integrate trusted cleanup execution without exposing privileges. Test restart/race cases. Hosted changes need approval. |
| 3. Connected Windows private pilot | The packaged app completes sign-in -> import -> search -> open -> delete on a clean Windows test environment without developer tools. No DB/Google operator credentials are bundled. | Choose and verify trusted backend/session packaging, close the relevant privacy/security/native gates, then test the installable artifact. Any new hosted service/deployment needs separate approval. |

Startup permits the approved maximum of three readiness GETs within one 60-second
budget; inference retains its 15-second deadline with no automatic replay.
The selected native pipeline already passed. Clean-install/signing QA remains.

For each milestone: one brief interview checkpoint; implement the connected slice;
run changed-behavior checks and required builds once after edits stabilize; finish
with a combined acceptance check and concise evidence. User sign-in or an actual
authorization is a handoff; routine coding/testing is not. A blocked hosted check
does not block independent local work, but hosted acceptance stays unverified.

Additional formats/bookmarks/OCR, broad quality benchmarks and general distribution
remain in the register. They are outside the immediate text-pilot path, not removed
from the product scope. No new dependencies/services for speed alone, no automatic
model retries, no larger limits and no broad automation authorization from this plan.

## Task register

| ID | Current scope/status | Remaining acceptance or evidence |
| --- | --- | --- |
| TASK-001 | Done: context/Git baseline | Keep current docs accurate; local commits only |
| TASK-002 | Ready: audience/product research | Interviews or explicitly unvalidated hypotheses; audience/regions decisions |
| TASK-003 | Unified private Library implemented | One owned grid/search with dark minimal UI; 59 frontend checks including five new synthetic integrations, plus native listing/opening. See [UNIFIED_LIBRARY](docs/UNIFIED_LIBRARY.md); clean-install/accessibility QA remains |
| TASK-004 | Done: bounded TXT/Markdown contract | Exact bytes/offsets/hashes and deterministic processing; [worker contract](services/worker/README.md) |
| TASK-005 | Partial: embedding/quality | Qwen CPU serving and selected hosted flow pass. Broader recall, split/multi-part coverage, visual/Gemma and security/licence work remain; [retrieval evidence](docs/CHUNK_RETRIEVAL_RESULTS.md) |
| TASK-006 | Partial: identity/private schema | Hosted private pilot; fifteen approved migrations applied. PDF/DOCX/recovery ownership permissions checked; general signup/audience policy remain gated; [hosted setup](docs/HOSTED_SUPABASE_SETUP.md) |
| TASK-007 | Private pilot verified; general app partial | Selected synthetic Markdown passed import -> publish -> search/open -> deletion/cleanup. Automatic processing/owned cleanup verified; release gates remain; [file pilot](docs/PRIVATE_TEXT_FILES.md) |
| TASK-008 | PDF and bounded DOCX private flows verified | DOCX native import reached ready on attempt 1; real search/cited opening passed with two model requests. Approved migration 15/API/native installed update are live; general Office compatibility, PPTX and public release remain open. [DOCX contract](docs/DOCX_IMPORT.md), [PDF contract](docs/PDF_IMPORT.md) |
| TASK-009 | Planned: photo/OCR retrieval | JPEG/PNG/scanned text, distinct model spaces and separately measured quality |
| TASK-010 | Deferred by user: chat | Selected-source isolation/citations; do not start before search priorities |
| TASK-011 | Partial: automated quality | Focused local checks/builds pass; remote manual CI/native E2E not claimed |
| TASK-012 | Continuous release gate | Ownership, limits, cleanup, dependencies/licences/secrets and [privacy gates](docs/PRIVACY_RELEASE_AUDIT.md) |
| TASK-013 | Current-PC installer lifecycle verified; clean environment pending | D: install, tool-free child PATH launch, real A/B sign-in/listing, synthetic opening, uninstall and reinstall passed. Missing-WebView2, upgrade, offline and clean-machine acceptance remain; [WINDOWS_INSTALL_QA](docs/WINDOWS_INSTALL_QA.md) |
| TASK-014 | Gated: production distribution | Signing, final policies, approved destination, backup/restore/rollback and verified artifacts |
| TASK-015 | After release: monitoring | Privacy-preserving diagnostics; telemetry requires separate review/consent |
| TASK-016 | Done: offline bookmark contract | Bounded synthetic HTML/URL extraction; not live fetching |
| TASK-017 | Partial/planned: bookmark user flow | Private save/search/delete plus safe enrichment, SSRF and isolation gates |
| TASK-018 | Done: bookmark passage baseline | Versioned field provenance + TF-IDF baseline, not semantic production evidence |
| TASK-019 | Partial: extraction integration | Offline adapters/runner verified; real tools/network/security gates tracked in 019A/B/C |
| TASK-019A | Verified build inputs; ongoing review | Extraction image locks/provenance and [dependency review](services/worker/DEPENDENCY_REVIEW.md) |
| TASK-019B | Partial: restricted extraction pipeline | Offline/parser and broker supervision checks pass; browser egress/production confinement remain |
| TASK-019C | Gated: real extraction tools | Approved Crawl4AI/yt-dlp tests after security/network/privacy gates |
| TASK-020 | Current audit done; ongoing hygiene | [FILE_AUDIT](docs/FILE_AUDIT.md) records roles, retention and checks |
| TASK-021 | Developer persistence slice verified; production partial | Owned originals/jobs/private staging/atomic publication/search/deletion verified in scoped local/hosted evidence. Automation/distribution/release gates remain |
| TASK-022 | Supporting plan recorded | [Delivery plan](docs/DELIVERY_PLAN.md) is planning/history, not current completion status |
| TASK-023 | Partial: dependency/image risk | Keep open findings and applicability review; [worker scan](services/worker/IMAGE_SCAN_REVIEW.md), [inference risk](services/inference/OS_RISK_REVIEW.md) |
| TASK-024 | Private ingestion performance implemented/verified | Profiled stages, bounded worker reuse and early readiness are deployed. Same small-PDF warm comparison: worker 39–41s -> 18–19s, observed ready 61s -> 33–35s. Cold/larger-file/p95 behavior is not established; [PROCESSING_SPEED](docs/PROCESSING_SPEED.md) |

## Latest verification

DOCX: 74 frontend checks, affected Linux run 112 checks, final corrective-image 23
parser checks and 13 SQL groups pass, with builds/lint/native bundling. Approved
migration/API update and native real import -> first-attempt ready -> cited
search/open passed with exactly two successful embeddings. Installed update
identity/shortcut checks pass. Counts overlap; [DOCX_IMPORT](docs/DOCX_IMPORT.md)
owns detailed evidence and limits.

Performance: 112 exact-image checks, twelve real-driver cases and 512 MiB/1 CPU
composition pass. Four approved generated-PDF imports used four real embeddings;
all reached ready on attempt 1 and reopened exactly. The 18 local operator HTTP/ack
checks and required frontend build pass. These check groups overlap. API 00005-gkw
is optimized, with unchanged resources/model/quotas. The first harness HTTP 202
failure is retained, with idempotent ack
recovery and no extra inference. Detailed paired timings: PROCESSING_SPEED.md.

Recovery follow-up:60 exact-image backend checks, eight SQL groups and68 frontend
checks/builds pass. Migration14/API update/startup boost were explicitly approved
and applied. One retained private PDF reached ready with two model calls, contents
unopened. Erroneous active Resume/stale-state controls are fixed; roughly68s
processing and 31s cold startup were observed in that earlier test. Later
profiling/connection improvements are covered by TASK-024 above.
See [PROCESSING_RECOVERY](docs/PROCESSING_RECOVERY.md).

PDF:82 affected backend checks, six SQL acceptance groups and64 frontend checks
completed; lint/format/typecheck/build pass. Approved migration13 and API update
are live. One bounded native PDF flow passed with two actual model requests;
cold-start failure and explicit recovery remain recorded. PDF_IMPORT.md owns
the detailed evidence. Clean-install QA remains separate and unverified.

Unified Library: 59 frontend checks, lint/format/typecheck/build and native build
pass. Rendered desktop/narrow review and live hosted sign-in/listing/opening pass;
no fresh embedding was submitted. Current artifacts/evidence: UNIFIED_LIBRARY.md.

Feature checkpoint `53cf9d8`: 123 affected backend checks and 48 frontend checks,
frontend build/lint/format passed. Live readiness exercised identity/deadline
paths with no embedding; a matching readiness GET logged HTTP200 after the client
deadline. See [MODEL_AVAILABILITY](docs/MODEL_AVAILABILITY.md) for boundaries.
Do not rerun benchmarks or recreate cleaned fixtures to refresh documentation.

Update this register and current acceptance here. Record a concise dated result
once in PROGRESS; archive detailed superseded journals instead of prepending
the same status into every document.
