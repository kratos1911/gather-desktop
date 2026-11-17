# Current Gather state

Updated for the hybrid/startup follow-up, based on checkpoint `ba077be` on
`codex/durable-ingestion-jobs`. This file is current state, not a session log. Repository context was audited/reorganized; see FILE_AUDIT.md.
See [tasks](../TASKS.md) for next acceptance and [topic index](PROJECT_HUB.md)
for contracts. [Previous state journal](history/2026-10-26/MEMORY-2026-10-26.md)
is historical and must not override this file.

## What is verified

- The installed private window is titled Gather. Signed-out screens show branding,
  sign-in and privacy only; Library controls appear after authentication and are
  removed on logout. Private-testing scope lives in account settings. See UNIFIED_LIBRARY.md.
  Windows builds now use the GUI subsystem in debug/release; the installed app
  was relaunched with no owned console process. See WINDOWS_INSTALL_QA.md.
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

The Windows candidate negotiates the live compact search route. Gather's active
Mumbai API uses Supabase connection reuse per search, fresh Auth and the existing
query cache. A small hosted comparison verified faster cache hits. Cold model
startup and both proposed p95 targets remain open. The latest local build adds
desktop timing. See [search latency](SEARCH_LATENCY.md).

Point 4 exercised the rebuilt Windows client against that deployment. Native
NLP preview/open, retry, deletion and quota restoration passed. An absent-topic
query returned an irrelevant note. The local correction uses shared content
terms or strong similarity for semantic candidates and passes the pinned-model
reproduction. Hosted retest is pending. See [native search acceptance](SEARCH_ACCEPTANCE.md).

Recruiter trial readiness takes priority over new formats. The durable model
quota mode is implemented locally with no hosted activation. Next verify
quota-aware import recovery and storage/parser limits for typical files, then
test with independent trial sessions. See TRIAL_MODEL_USAGE.md.

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
backport hash. No suppression or blanket security approval.

Current-PC install/uninstall/reinstall passed using the existing verified unsigned
installer and a separate D: test folder. The installed app launched with developer
tools removed from its PATH; real A/B sign-in, owned metadata and synthetic opening
were checked without model calls or cloud document changes. Exact binary identity
accounts for Tauri's three-byte NSIS marker patch. Seven verifier tests and the
frontend build passed. Clean-machine, upgrade, missing-WebView2, offline, signing
and broader release/quality acceptance remain unverified; see WINDOWS_INSTALL_QA.md.

The account's separate older job `caae0a28-c50c-4789-9eef-51e62c1fdd7b`
last reported processing, attempts 2/3, timeout, no publication. That is stored
state, not evidence of a live worker. Do not claim/retry/delete it implicitly.

DOCX is implemented and deployed through approved migration 15 and API revision
00007-x4t (approved standard-Word style-part compatibility correction). Native selection/review/Save reached ready on attempt 1; one real query
returned paragraph citations and exact saved opening passed. Exactly two successful
model requests were confirmed. Only the approved generated PDF fixture was cleaned;
personal PDF/A's sources were unchanged. That generated DOCX was subsequently
cleaned with explicit approval for the OCR test below. Frontend
74 checks, affected Linux checks, 13 SQL groups, final 23 parser-image checks and
native/installer builds pass. See DOCX_IMPORT.md for its scope and historical evidence.

Private PNG/JPEG English OCR is implemented and deployed in API revision
00008-t86, with migration16 and the approved CPU1/2GiB allocation. The updated
D: Windows app verified generated-image Save -> automatic ready -> semantic
search -> exact original/OCR-region opening, with two real embedding requests.
No explicit processing retry was needed. The image remains in pilot B's Library;
personal PDF and pilot A sources were not modified. See IMAGE_OCR.md for bounds,
selected evidence and unsuppressed dependency findings. Object/scene retrieval
is separate. SEARCH_RELEVANCE.md records the verified score-floor/near-best
filter, deployed with approval in API00009-mxp. One native/real-query check kept
the Cedar image and removed the resume. Known-set replay kept expected source/
context coverage; topic-adjacent false matches remain. CPU1/2GiB, scaling and
INR500 allowance unchanged.

Encrypted Upstash query caching was introduced in API00011-vn4 and verified
in the updated installed app: miss/store/repeat-hit, with fresh Auth/source reads.
Active TTL600s and approved Redis deadline1s; credentials stay backend-only. See
QUERY_EMBEDDING_CACHE.md for evidence and the initial timeout/fallback. Search
still has substantial Auth/DB latency. No1, single request-local authentication,
is now verified/deployed in API00012-x89; no identity reuse across requests.
SEARCH_AUTH_SCOPE.md owns its evidence. TASK-027 hybrid search/startup is now
verified in API00013-7zd, migration17 and the rebuilt installed app. The selected
cold Cedar and warm descriptive queries both return only the cited OCR note.
Startup precedes one15s embedding; two live embeddings total. HYBRID_SEARCH.md
owns limits/evidence. Connection reuse/batching remain future performance work.
Safe links/bookmarks remain the next format slice. No document/model changes.
Cold/larger-file
performance, general Office compatibility and clean-Windows/signing QA remain
separate acceptance. Both pilot B source slots are full; never raise quotas or
delete retained/personal sources implicitly.
Evidence/limits belong in TASKS.md and PRIVATE_DESKTOP_DELIVERY.md. General
signup/uploads, PPTX, photo object/scene retrieval and chat remain gated/deferred.

## Fixed scope and operating constraints

- Cloud CPU inference: private Gather Cloud Run in Mumbai, project
  `gather-development-511211`. Use explicit personal account/project flags from
  the existing helpers. Never use protected Intrixshield/work defaults.
- Supabase `fatolholcjxpwocnpzws`, Sydney session pooler. Seventeen migrations were
  applied manually; CLI migration history is not automatically populated.
- Qwen/Qwen3-Embedding-0.6B, pinned revision/dimensions in the serving contracts;
  512-dimensional query/document space. No end-user weight downloads.
- Private two-account TXT/Markdown/native-text PDF/DOCX/PNG/JPEG OCR pilot: input <=64 KiB, three processing
  passages/model attempts; no automatic inference retries. Existing deadlines,
  quotas and per-process counters are not billing meters.
- Normal min0/max1; the approved pilot budget is INR500 and alerts are not a
  hard spending cap. No new paid provisioning or always-warm changes without approval.
  Startup-only inference CPU boost is now explicitly approved/enabled; its benefit
  is unproven in the recorded sample. No permanent runtime CPU/memory increase.
- Library API: approved CPU1/2GiB, max1/min0; application admission1, platform
  concurrency4, three model attempts per API instance, two allowed users only.
  Up to three readiness GETs within one 60s budget were explicitly approved;
  embedding requests never retry automatically.
  Worker DB helpers remain capped at two, with separate heartbeat sockets and
  transaction reset/privilege checks; admission sessions remain fresh per user.
- Models/caches/temp/build evidence on D:. No protected API/container/project
  changes or app closures without specific authorization.
- One writer/agent by default. Keep commits local; never push without an
  explicit request. Preserve untracked/user-authored work and private data.
