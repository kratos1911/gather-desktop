# Current Gather state

Updated 27 October 2026. Feature checkpoint: `53cf9d8` on
`codex/durable-ingestion-jobs`. This file is current state, not a session log. Repository context was audited/reorganized; see FILE_AUDIT.md.
See [tasks](../TASKS.md) for next acceptance and [topic index](PROJECT_HUB.md)
for contracts. [Previous state journal](history/2026-10-26/MEMORY-2026-10-26.md)
is historical and must not override this file.

## What is verified

- React/TypeScript/Tauri sample interface remains separate from the
  development-only private browser operator panel.
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
  Latest scoped checks: 123 backend and 48 frontend, build/lint/format pass.
  No new embedding was made for availability verification; native production
  assets were unchanged. See [MODEL_AVAILABILITY](MODEL_AVAILABILITY.md).

## Current limitations and next work

The last live app check timed out. A matching Cloud Run readiness GET later
logged HTTP200 after ~31 seconds, beyond the 15-second outbound allowance.
An isolated caller-token mint passed within five seconds. The earlier generic
model failure is not conclusively diagnosed. A successful later in-app readiness
check and fresh post-idle embedding remain unverified.

The account's separate older job `caae0a28-c50c-4789-9eef-51e62c1fdd7b`
last reported processing, attempts 2/3, timeout, no publication. That is stored
state, not evidence of a live worker. Do not claim/retry/delete it implicitly.

Next implementation: automatic processing of new private text imports, with
startup/readiness verification inside its final integration check. Live readiness
does not block independent local implementation. The ordered outcomes and acceptance
are in TASKS.md. Worker execution and physical cleanup are still operator actions;
the plan is not implemented. General signup/uploads, native connected mode, other
formats and chat remain gated/deferred.

## Fixed scope and operating constraints

- Cloud CPU inference: private Gather Cloud Run in Mumbai, project
  `gather-development-511211`. Use explicit personal account/project flags from
  the existing helpers. Never use protected Intrixshield/work defaults.
- Supabase `fatolholcjxpwocnpzws`, Sydney session pooler. Nine migrations were
  applied manually; CLI migration history is not automatically populated.
- Qwen/Qwen3-Embedding-0.6B, pinned revision/dimensions in the serving contracts;
  512-dimensional query/document space. No end-user weight downloads.
- Private two-account TXT/Markdown pilot: UTF-8 <=64 KiB, three processing
  passages/model attempts; no automatic inference retries. Existing deadlines,
  quotas and per-process counters are not billing meters.
- Normal min0/max1; the approved pilot budget is INR500 and alerts are not a
  hard spending cap. No new paid provisioning or always-warm changes without approval.
- Models/caches/temp/build evidence on D:. No protected API/container/project
  changes or app closures without specific authorization.
- One writer/agent by default. Keep commits local; never push without an
  explicit request. Preserve untracked/user-authored work and private data.
