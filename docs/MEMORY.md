# Current Gather state

Updated 2 November 2026. This performance milestone builds on checkpoint `4c76cd0` on
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
PDF_IMPORT.md for the original limits/evidence and PROCESSING_RECOVERY.md for the
subsequent status/eligibility changes and current checks.

Recovery follow-up: approved migration14/API revision00003-dpb are live. Owner
listing/status supply can_resume; active work no longer offers Resume and stale
rejections refresh metadata. Accepted reconnect recovery restores status watching.
One existing private PDF reached ready with two model calls; its contents were
not opened. Current checks:60 exact-image backend, eight SQL groups and68 frontend
checks plus builds/lint/format. See PROCESSING_RECOVERY.md. Model startup boost was
explicitly approved, retaining min0/max1 and runtime2CPU/5GiB. Observed startup
remained about 31s; that earlier recovery took about 68s. Later warm-path
measurements are recorded below; cold-start latency remains a limitation.

Performance follow-up is deployed in API revision 00005-gkw: content-free
stage timings, worker-only job-scoped DB reuse and early model readiness. Same
small PDF warm comparison: worker 39–41s -> 18–19s; observed ready 60.66s -> 33–35s;
in-job DB connections 12 -> 2. All four jobs reached ready on attempt 1 with four
successful model requests total. Personal files were untouched. First client
measurement had an HTTP 202 harness error; its original server timing was retained
and acknowledgement recovered idempotently. See PROCESSING_SPEED.md for limits.

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

Prior unified-interface checks/build/native review are in UNIFIED_LIBRARY.md.
The performance change is backend-only; the required frontend build passed and
no native rebuild was required. The exact server image passed 112 checks; twelve
real-driver cases and the 512 MiB/1 CPU tokenizer/PDF/two-helper composition passed.
Another 18 local operator HTTP/acknowledgement checks passed. These test groups
overlap and must not be summed as unique tests. Prior unchanged backend evidence:
11 owned-cleanup SQL cases and 37 Linux image cases passed. Filelock was fixed;
its targeted rescan is clear. Scanner-open zlib retains the identical verified
backport hash. No suppression or blanket security approval. Clean-machine install,
uninstall, signing and broader release/quality acceptance remain unverified.

The account's separate older job `caae0a28-c50c-4789-9eef-51e62c1fdd7b`
last reported processing, attempts 2/3, timeout, no publication. That is stored
state, not evidence of a live worker. Do not claim/retry/delete it implicitly.

Next: use captured timings for any further admission/selection/network latency
work; warm inference was not the main delay on this small fixture. Cold starts,
larger-file performance and clean-Windows installer QA remain separate acceptance.
See WINDOWS_INSTALL_QA.md.
Evidence/limits belong in TASKS.md and PRIVATE_DESKTOP_DELIVERY.md. General
signup/uploads, DOCX/PPTX/OCR and chat remain gated/deferred.

## Fixed scope and operating constraints

- Cloud CPU inference: private Gather Cloud Run in Mumbai, project
  `gather-development-511211`. Use explicit personal account/project flags from
  the existing helpers. Never use protected Intrixshield/work defaults.
- Supabase `fatolholcjxpwocnpzws`, Sydney session pooler. Fourteen migrations were
  applied manually; CLI migration history is not automatically populated.
- Qwen/Qwen3-Embedding-0.6B, pinned revision/dimensions in the serving contracts;
  512-dimensional query/document space. No end-user weight downloads.
- Private two-account TXT/Markdown/native-text PDF pilot: input <=64 KiB, three processing
  passages/model attempts; no automatic inference retries. Existing deadlines,
  quotas and per-process counters are not billing meters.
- Normal min0/max1; the approved pilot budget is INR500 and alerts are not a
  hard spending cap. No new paid provisioning or always-warm changes without approval.
  Startup-only inference CPU boost is now explicitly approved/enabled; its benefit
  is unproven in the recorded sample. No permanent runtime CPU/memory increase.
- Library API: approved CPU1/512MiB, max1/min0; application admission1, platform
  concurrency4, three model attempts per API instance, two allowed users only.
  Up to three readiness GETs within one 60s budget were explicitly approved;
  embedding requests never retry automatically.
  Worker DB helpers remain capped at two, with separate heartbeat sockets and
  transaction reset/privilege checks; admission sessions remain fresh per user.
- Models/caches/temp/build evidence on D:. No protected API/container/project
  changes or app closures without specific authorization.
- One writer/agent by default. Keep commits local; never push without an
  explicit request. Preserve untracked/user-authored work and private data.
