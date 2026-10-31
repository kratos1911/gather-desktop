# Current Gather state

Updated 31 October 2026. Current work builds on checkpoint `3f23632` on
`codex/durable-ingestion-jobs`. This file is current state, not a session log. Repository context was audited/reorganized; see FILE_AUDIT.md.
See [tasks](../TASKS.md) for next acceptance and [topic index](PROJECT_HUB.md)
for contracts. [Previous state journal](history/2026-10-26/MEMORY-2026-10-26.md)
is historical and must not override this file.

## What is verified

- The private/dev interface uses one authenticated Library and semantic search.
  Owned imports appear in its grid; import review and diagnostics are secondary
  panels. A separate sample-only build remains fictional. See UNIFIED_LIBRARY.md.
- One selected synthetic 170-byte Markdown file passed hosted Auth/admission,
  durable processing, one real worker embedding, atomic publication, custom
  search, exact saved text opening, tombstoning and explicitly approved cleanup.
  Content/jobs are gone; the minimal replay guard remains. The local file is
  preserved. IDs/receipts: [PRIVATE_TEXT_FILES](PRIVATE_TEXT_FILES.md).
- Owned paginated listing/restoration works in the pilot. Empty complete
  publication metadata skips query inference; unknown/incomplete metadata is
  not silently treated as empty. See [SAVED_LIBRARY](SAVED_LIBRARY.md) and
  [EMPTY_LIBRARY_SEARCH](EMPTY_LIBRARY_SEARCH.md).
- Fixed availability reasons and manual readiness control are implemented.
  Retained availability evidence: 123 backend and 48 frontend checks at its
  earlier checkpoint, with build/lint/format passing.
  No new embedding was made for availability verification; native production
  assets were unchanged. See [MODEL_AVAILABILITY](MODEL_AVAILABILITY.md).

## Current limitations and next work

Native-text PDF support is implemented and deployed in the existing private API,
with migration13 explicitly approved and applied. The Windows PDF build passes
focused checks. Pilot B's generated two-page hosted-pilot.pdf reached ready after
explicit recovery; real search returned a cited passage and exact saved page
opening passed. Exactly two successful embedding requests were used. Keep this
source for inspection; do not resubmit, retry or delete it implicitly. See
PDF_IMPORT.md for limits, image and evidence. The status-sync fix keeps recovery
cards on the observed attempt;64 frontend checks/build/lint/format pass.

Automatic dispatch, exact-attempt recovery and owner-scoped cleanup are implemented.
Migrations 10/11/12 were explicitly approved and applied to Gather. The library API
and two restricted Secret Manager credentials were deployed with explicit approval.
The native app verified hosted sign-in -> fresh file Save -> automatic ready ->
custom semantic search -> exact saved text. See PRIVATE_DESKTOP_DELIVERY.md.

Recovery source `f092452e-6a08-47a3-92eb-d75153bd4d00` reached ready, passed
search/open and was physically cleaned through the app after explicit approval.
New native source `88da1cf6-3708-4f07-9631-6493601a3f3a` remains published for
inspection; do not rerun its job or delete it implicitly. Its 133-byte file is
synthetic/nonsensitive. Prior failed results remain historical evidence.

Current frontend checks: 59 tests, typecheck/build/lint/format, native rebuild
and rendered desktop/minimum-width review. Live native sign-in/listing/opening
passed against existing published text; no new inference was submitted.
Prior unchanged backend evidence: focused backend/HTTP,
11 owned-cleanup SQL cases and 37 Linux image cases passed. Filelock was fixed;
its targeted rescan is clear. Scanner-open zlib retains the identical verified
backport hash. No suppression or blanket security approval. Clean-machine install,
uninstall, signing and broader release/quality acceptance remain unverified.

The account's separate older job `caae0a28-c50c-4789-9eef-51e62c1fdd7b`
last reported processing, attempts 2/3, timeout, no publication. That is stored
state, not evidence of a live worker. Do not claim/retry/delete it implicitly.

Next: clean-Windows installer QA using WINDOWS_INSTALL_QA.md.
Evidence/limits belong in TASKS.md and PRIVATE_DESKTOP_DELIVERY.md. General
signup/uploads, DOCX/PPTX/OCR and chat remain gated/deferred.

## Fixed scope and operating constraints

- Cloud CPU inference: private Gather Cloud Run in Mumbai, project
  `gather-development-511211`. Use explicit personal account/project flags from
  the existing helpers. Never use protected Intrixshield/work defaults.
- Supabase `fatolholcjxpwocnpzws`, Sydney session pooler. Thirteen migrations were
  applied manually; CLI migration history is not automatically populated.
- Qwen/Qwen3-Embedding-0.6B, pinned revision/dimensions in the serving contracts;
  512-dimensional query/document space. No end-user weight downloads.
- Private two-account TXT/Markdown/native-text PDF pilot: input <=64 KiB, three processing
  passages/model attempts; no automatic inference retries. Existing deadlines,
  quotas and per-process counters are not billing meters.
- Normal min0/max1; the approved pilot budget is INR500 and alerts are not a
  hard spending cap. No new paid provisioning or always-warm changes without approval.
- Library API: approved CPU1/512MiB, max1/min0; application admission1, platform
  concurrency4, three model attempts per API instance, two allowed users only.
  Up to three readiness GETs within one 60s budget were explicitly approved;
  embedding requests never retry automatically.
- Models/caches/temp/build evidence on D:. No protected API/container/project
  changes or app closures without specific authorization.
- One writer/agent by default. Keep commits local; never push without an
  explicit request. Preserve untracked/user-authored work and private data.
