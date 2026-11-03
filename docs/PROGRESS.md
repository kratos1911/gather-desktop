# Progress journal

Current state is in [MEMORY](MEMORY.md); current tasks are in [TASKS](../TASKS.md).
This journal records concise dated evidence once, not replicated status prefixes.

## 2–3 November 2026: bounded DOCX import and native/cloud acceptance

Implemented standard-library ZIP/XML main-body extraction with expansion/node/
depth limits, active/ambiguous-content rejection and paragraph provenance. PDF
and DOCX share the existing resource-bounded parser slot and staging validator;
jobs, hashes, leases, ownership, atomic publication and cleanup remain the same
pipeline. Added server capability gating and same-Library Word review/filter/
reader controls. No packages, models or larger limits were introduced.

Verification: affected Linux run 112 checks, refreshed DOCX subset, final exact
image 22 parser checks and 512 MiB/1 CPU tokenizer composition passed. Isolated
SQL 13 groups include DOCX and PDF compatibility. Frontend 74 tests, lint/typecheck/
build and native/installer builds passed. Groups overlap; do not sum as unique.
SQL fixture privilege/expiry setup, PowerShell framing/date-query and local edit
issues were corrected without weakening production guards or replaying inference.

After explicit approval, migration 15 committed and seven hosted permission checks
passed. Uploaded image 9fe1d130… and deployed only Gather API revision 00006-g5r,
retaining resources/scaling/speed flags, model service, identities and secrets.
User approved removal of the generated hosted PDF fixture; the app confirmed its
cleanup. Personal PDF/A's sources were unchanged. Native DOCX selection/review/
Save reached ready on attempt 1. One real query returned paragraphs 1/2; exact
saved reading passed. Cloud logs confirm two successful embeddings, document and
query, without replay. The generated DOCX remains available for inspection.

Promoted the verified native build, preserved prior artifacts and updated the
existing D: installation via NSIS /UPDATE with byte/marker verification and the
normal shortcut preserved. A standard-producer fixture then exposed a valid
style part above 256 KiB. The user approved a 512 KiB per-part cap with the
1 MiB total unchanged. Final image 95bb6106... passed 23 parser checks and the
bounded standard-producer/tokenizer check; deployed as 00007-x4t with no further
model calls or native rebuild. Evidence: output/docx-compatibility/.
Evidence and limits: DOCX_IMPORT.md and ignored
output/docx-pilot/. Clean-Windows, signing and broad Office compatibility remain
open; no GitHub push or protected workload change was made.

## 2 November 2026: current-PC Windows installer lifecycle

The user chose their existing Windows PC after no separate Sandbox/VM was found.
Installed the exact unsigned private installer in a separate D: test directory.
Verified executable identity, per-user registration and two shortcut targets.
Launched with only System32 on child PATH; real pilot A listing and synthetic
Markdown opening passed. Uninstall returned zero and removed the executable,
registration and shortcuts. Reinstall returned zero; launching its shortcut,
real pilot B listing and generated two-page PDF opening passed. Memory-only
sign-in reset as expected. No cloud document mutation, model calls, deployments,
protected workload changes or OS security bypass occurred.

Initial raw executable hash check stopped: exactly three bytes were Tauri's
documented UNK -> NSS bundle marker. All other bytes match the pinned source.
Added a bounded read-only verifier; seven synthetic checks and the required
frontend build pass. Receipts/install products are under output/windows-install-qa/.
Windows installation/runtime evidence is distinct from those synthetic checks.
Clean-machine, missing-WebView2, upgrade, offline/scaling and signing gates remain
open. Exact hashes/procedure: WINDOWS_INSTALL_QA.md.

## 1 November 2026: measured ingestion performance

Implemented content-free stage/DB timings, worker-only framed helper reuse with
transaction reset and two-helper eviction, and early bounded readiness preparation.
The exact image passed 112 checks. Twelve real restricted-driver cases, Linux
tokenizer/PDF and two-helper composition under 512 MiB/1 CPU pass. Frontend build passes;
native inputs stayed unchanged. Read-only hosted pooler compatibility passed.

User approved image 2c557d18… and two Gather-only API revisions: timing baseline
00004-9kb, optimized 00005-gkw. Four replacements of only the generated PDF used
four successful embeddings, all attempt 1 with exact opening. Paired warm worker
times 39–41s -> 18–19s; observed ready 61s -> 33–35s; in-job connections 12 -> 2.
No cold start was observed during those processing windows. Personal files,
model settings, quotas, other projects/containers and GitHub stayed untouched.

The local harness initially rejected the correct HTTP 202 import response after
the server had accepted it. Preserved that failure/request ID, added explicit 202
client handling and 18 HTTP/operator regressions, then recovered the same ack
without extra inference. Its client wall time is unavailable; server timing is
retained. Full evidence and caveats: PROCESSING_SPEED.md and ignored
output/processing-speed/. Cold/larger-file performance remains unproven.

## 1 November 2026: recovery controls and startup follow-up

Fixed active-job Resume visibility using owner-scoped SQL metadata wrappers and
refresh-on-refusal. Reconnect recovery restores bounded status watching. Kept the
same retry/inference limits and spaced readiness checks within60s. Sixty checks
pass in the exact API image, eight SQL groups and68 frontend checks pass; native
build/lint/format and rendered ready-state review pass. Approved migration14 and
API revision00003-dpb are live; startup-only boost is enabled on model00002-jpv.
One existing private PDF reached ready with two model calls; no content preview,
search, duplicate import or deletion. Earlier cold failure is retained. Startup
sample30.92s and overall recovery~68s do not prove a speedup; stage profiling is
next. Evidence/limits: PROCESSING_RECOVERY.md and ignored output/recovery-fix/.

## 31 October 2026: private native-text PDF flow

Extended the existing import/jobs/publication/search pipeline with pinned pypdf
extraction in a bounded Linux child, immutable original identity, separate text
hashes and numbered page provenance. Capability-gated selection and page reader
preserve the unified Library. Applied approved migration13 and API revision
00002-f55, image72ce93fd…, retaining service sizes, IAM, secrets and scale-to-zero.

Completed82 affected backend checks across scoped runs (one receipt test needed
its private tmpfs), six SQL acceptance groups,64 frontend checks, build/lint/format
and native build. Limited-parser/tokenizer composition passed under512MiB without
inference. The generated two-page PDF saved under pilot B; initial readiness429
left it queued, then explicit recovery reached ready. One actual query returned
Pages1,2 and exact saved-text opening passed. Exactly two successful embedding
POSTs are logged. Fixed stale recovery-card attempt metadata with a regression;
reused the existing status response without extra reads or automatic retries.

Preserved B's PDF and A's retained sources. No other project/container changed,
no GitHub push, no public-upload/OCR or broad quality/security claim. See
PDF_IMPORT.md and ignored output/pdf-pilot/ evidence. Clean Windows install/
uninstall and signing remain open; WINDOWS_INSTALL_QA.md defines that acceptance.

## 31 October 2026: unified connected Library

Connected the existing authenticated workspace to one main Library and explicit
semantic search. Removed the Operator pilot route; the old component remains an
isolated regression harness. Added local file review in a secondary panel,
same-grid status updates, exact-version reading and confirmed deletion/pending
cleanup. Session/ownership/citation/resource contracts stay intact.

Implemented the user's mymind-inspired minimal dark composition with existing
licensed fonts, original SVG controls and no new dependencies. Updated stale
private processing/deletion notices. All59 frontend tests, lint, formatting,
frontend build/typecheck and native rebuild pass; design detector returned no
findings. Desktop/640 CSS-pixel review passed without horizontal overflow. Native
sign-in restored two existing owned sources and exact saved-text opening passed.
No new inference, cloud deploy,
schema change, protected-workload change or push. Details: UNIFIED_LIBRARY.md.

Portable and unsigned installer refreshed. NSIS first failed with Windows
DLL-loading623 in the isolated shell, then the same cached bundler passed in the
normal host context. Scoped contrast pairs pass AA thresholds; no blanket
accessibility or clean-install claim. Screenshots/receipt: output/unified-library/.

## 31 October 2026: automatic ingestion, cleanup and native/cloud pilot

Implemented durable new-import intent/dispatch, exact-attempt recovery, bounded
startup, shared-slot contention handling, safe failure reasons and status updates.
Fixed startup failures incorrectly becoming invalid-input errors; mapped recovery
through the real SessionClient allowlist. Added owned cleanup and durable pending
metadata. Migrations10/11/12 were tested, explicitly approved and installed.

Deployed the approved library API and two restricted Secret Manager values in
Gather/Mumbai; native-origin preflight204 and unauthenticated POST401 verified.
Built the private native executable and unsigned installer. A fresh selected
133-byte Markdown file reached ready on attempt1 in the native app, then custom
semantic search/open succeeded with exact citation0..133. App cleanup of the prior
approved fixture completed without SQL. Native metadata reload worked with both
localhost helpers stopped. Older unfinished work remained untouched.

Focused backend/HTTP checks, 54 frontend tests, typecheck/lint/format, cleanup
SQL11 and final Linux37 checks passed. Existing unchanged publication/quality
evidence was reused; no model benchmark. Filelock was patched and rescanned;
scanner-open zlib retains its exact verified backport. The initial native bundle
hit a running-file lock; isolated-copy packaging succeeded. Details, IDs, failures,
artifacts and clean-install/signing limits: [delivery record](PRIVATE_DESKTOP_DELIVERY.md).

## 27 October 2026: consolidate the private-pilot delivery path

Changed TASKS/RULES to group work into complete flows and move cloud readiness
from a coding prerequisite to the relevant hosted acceptance check. MEMORY points
to the next implementation; DECISIONS records the rationale. No application or
cloud behavior changed; automatic processing remains planned. `git diff --check`
and `scripts/desktop.ps1 build` passed (exit 0); production asset names remained
unchanged. No model, database, Docker, deployment or native rebuild was needed.

## 26 October 2026: file audit and focused context

Audited all 418 initially tracked files for role, literal/static-import references,
Python syntax and local Markdown/Obsidian links. No source, migration, fixture,
locked build input or notice was identified as safe to delete solely from
absence of a text reference. Oversized working journals were preserved in
dated history and replaced with current context. Root diagnostic/stale cache
cleanup is recoverable under ignored output/file-audit/recovery.
Measured results and checks: [FILE_AUDIT](FILE_AUDIT.md).

## Prior work and evidence

- [Full journal through feature checkpoint 53cf9d8](history/2026-10-26/PROGRESS-2026-10-26.md)
- [Model availability](MODEL_AVAILABILITY.md): 123 backend/48 frontend scoped
  checks and delayed readiness observations; no fresh embedding verification
- [Selected-file lifecycle](PRIVATE_TEXT_FILES.md): hosted path through approved cleanup
- [Saved library](SAVED_LIBRARY.md), [empty search](EMPTY_LIBRARY_SEARCH.md)

Future entries: record the change, actual checks and material limitations.
Archive superseded journal sections when this file becomes unwieldy; do not
erase failed cases or historical evidence.
