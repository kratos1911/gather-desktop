# Current delivery tasks

Updated 27 October 2026. Current state: [MEMORY](docs/MEMORY.md).
Work/evidence: [progress](docs/PROGRESS.md) and task-specific contracts.
The [full previous task journal](docs/history/2026-10-26/TASKS-2026-10-26.md)
preserves all earlier acceptance text and checkpoints.

## Next sequence

Deliver complete user flows; supporting fixes/checks belong inside their milestone.
These three milestones target a usable private text pilot, not the whole multi-format
MVP or public release. Implementation remains pending.

| Milestone | Outcome and completion criteria | Dependencies / gates |
| --- | --- | --- |
| 1. Automatic private text processing (next) | A newly saved, owned TXT/Markdown import progresses to searchable/openable text without a terminal worker command. Truthful progress/failure states, bounded restart recovery, duplicate prevention and deletion/account isolation pass focused checks plus one bounded hosted flow. | Reuse admission, durable jobs, exact-target claims, leases and atomic publication. Startup handling and readiness verification are part of final integration, not prerequisites for offline implementation. Preserve existing request budgets/deadlines, explicit retry rules and the older unfinished job. |
| 2. Complete recovery and deletion | Reconnect shows durable state and actionable failures; deletion hides immediately and reports confirmed physical cleanup or a truthful pending/failure state. No manual SQL for the supported flow; late work cannot restore deleted content. | Reuse listing, tombstones, cleanup guards and replay receipts; integrate trusted cleanup execution without exposing privileges. Test restart/race cases. Hosted changes need approval. |
| 3. Connected Windows private pilot | The packaged app completes sign-in -> import -> search -> open -> delete on a clean Windows test environment without developer tools. No DB/Google operator credentials are bundled. | Choose and verify trusted backend/session packaging, close the relevant privacy/security/native gates, then test the installable artifact. Any new hosted service/deployment needs separate approval. |

Cold-start evidence remains unresolved: the last app check timed out, and a matching
Cloud Run readiness GET later logged HTTP200/~31 s. Diagnose that integration gap
within milestone 1; never silently raise limits, keep an instance warm or replay
inference. See [availability](docs/MODEL_AVAILABILITY.md).

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
| TASK-003 | Partial: desktop design | Sample UI + private browser operator panel verified in scoped checks; native accessibility/zoom/motion QA remains |
| TASK-004 | Done: bounded TXT/Markdown contract | Exact bytes/offsets/hashes and deterministic processing; [worker contract](services/worker/README.md) |
| TASK-005 | Partial: embedding/quality | Qwen CPU serving and selected hosted flow pass. Broader recall, split/multi-part coverage, visual/Gemma and security/licence work remain; [retrieval evidence](docs/CHUNK_RETRIEVAL_RESULTS.md) |
| TASK-006 | Partial: identity/private schema | Hosted private pilot and nine migrations verified. General signup/session packaging/audience policy remain gated; [hosted setup](docs/HOSTED_SUPABASE_SETUP.md) |
| TASK-007 | Private pilot verified; general app partial | Selected synthetic Markdown passed import -> publish -> search/open -> deletion/cleanup. Manual worker/admin cleanup remain; [file pilot](docs/PRIVATE_TEXT_FILES.md) |
| TASK-008 | Planned: native document formats | PDF/DOCX/PPTX with exact page/slide/section provenance and malformed-input cases |
| TASK-009 | Planned: photo/OCR retrieval | JPEG/PNG/scanned text, distinct model spaces and separately measured quality |
| TASK-010 | Deferred by user: chat | Selected-source isolation/citations; do not start before search priorities |
| TASK-011 | Partial: automated quality | Focused local checks/builds pass; remote manual CI/native E2E not claimed |
| TASK-012 | Continuous release gate | Ownership, limits, cleanup, dependencies/licences/secrets and [privacy gates](docs/PRIVACY_RELEASE_AUDIT.md) |
| TASK-013 | Planned: installer QA | Clean Windows install/update/uninstall and network/offline/quota cases without developer tools |
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

## Latest verification

Feature checkpoint `53cf9d8`: 123 affected backend checks and 48 frontend checks,
frontend build/lint/format passed. Live readiness exercised identity/deadline
paths with no embedding; a matching readiness GET logged HTTP200 after the client
deadline. See [MODEL_AVAILABILITY](docs/MODEL_AVAILABILITY.md) for boundaries.
Do not rerun benchmarks or recreate cleaned fixtures to refresh documentation.

Update this register and current acceptance here. Record a concise dated result
once in PROGRESS; archive detailed superseded journals instead of prepending
the same status into every document.
