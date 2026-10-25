25 October CURRENT: user screenshot confirms hosted Operator UI semantic search returned the saved text and Open displayed the exact saved source. Worker receipt already confirms ready; no repeat import/worker needed. Delete and physical cleanup are remaining flow steps. Earlier generic search errors were resolved after fetch binding, targeted job claims, readiness-before-claim, per-request operator token refresh and error categories; prior root errors were not independently attributed.

25 October CURRENT: safe search-stage diagnostics implemented; operator API now mints Google invoker token for each model request (pinned account/project/caller/audience, uncached), and Ctrl+C exits cleanly. 45 focused backend,25 frontend tests pass; frontend/native builds, lint and formatting pass. Prior search database-category error is not explained by current logs; one search after API restart is needed for fresh diagnostics. No model request by agent.

25 October CURRENT: search errors now identify session (401), model (502) or library (503) failures; original database-category incident remains unconfirmed because no matching Cloud Run error log was present. Long-running operator API refreshes a pinned Google caller token for each model request, without caching or retries. 45 focused backend tests, 25 frontend tests, lint/format/frontend/native builds pass. Restart current API to load this code, then one user-directed search can report a current category. No new model query by agent.

25 October CURRENT: search failure classifier implemented. Search now distinguishes session 401, model 502 and library 503 without exception/body leakage; restarted operator API needed to load changed Python. 34 focused search/session/API tests and frontend build pass. Last hosted attempt root cause unconfirmed (no matching recent inference logs); no new hosted search/model request by agent. Next: restart API once then one UI search to capture accurate category. See OPERATOR_LIBRARY_PILOT.md.

25 October CURRENT: saved operator receipt confirms requested job efea703e-22e5-4663-b4e3-c9280c650a88 ready, version5842b025-e9f5-4c79-bb0a-05a0d417f719, one real model request; operator output reports min0 restored. UI search/open still pending. Frontend launch failed in ordinary PowerShell because PATH only exposed Node22.7; desktop.ps1 now checks existing bundled Node24 and supports GATHER_NODE override. Build passed with PATH restricted to old Node; unsupported override rejected. No installation/model/cloud changes.

25 October CURRENT: requested job reached embed_passage but requeued after one real request. Gather Cloud Run log at 2026-10-25T09:41:41.966998Z reports HTTP429/no available instance. Operator worker now reuses approved warm_instance and bounded readiness before any job claim, restores min0 on exit. 19 focused tests/build pass; no agent processing/scaling retry. Next: one explicit run of the same acknowledged job. See OPERATOR_LIBRARY_PILOT.md.

25 October CURRENT: migration8 exact-job claiming applied to Gather after explicit user approval. Hosted metadata verifies installed/worker allowed=true and client/anonymous/admission/private-core access=false. Local repair checkpoint3e44b48 verified previously. No job/model retry performed; next is one explicit worker run for efea703e-22e5-4663-b4e3-c9280c650a88. See EXACT_JOB_CLAIM.md.

25 October CURRENT: exact-job selection fix implemented and verified locally; hosted migration awaits action-time approval. Older expired job was selected by FIFO while requested efea703e-22e5-4663-b4e3-c9280c650a88 stayed queued/attempts0. 41 focused tests, real isolated SQL suite and frontend build pass. Safe receipts/nonzero failure exits added; no job/model retry. Do not run updated worker before migration8 is applied. See EXACT_JOB_CLAIM.md.

24 October CURRENT: user reached signed-in operator UI; import failed before networking due to native fetch called with a LibraryClient receiver. Corrected to a plain function invocation and verified in real Chrome with an invalid synthetic bearer reaching the local API. 25 frontend tests, build, lint/format pass. Production assets are hash-identical, so prior native build is reused. API process unchanged; refresh/sign-in and live import remain next. See OPERATOR_LIBRARY_PILOT.md.

24 October CURRENT: restricted operator-library milestone implemented and locally verified. Loopback API, cancellable worker, typed desktop client/state and development-only synthetic pilot UI are connected in code. 49 Python/24 frontend tests, lint/format/frontend build and native debug build pass. Signed-out screen visually checked; live new-UI hosted sign-in/flow remains unverified. No cloud changes/calls or model/Docker runs. Stop here per user; see OPERATOR_LIBRARY_PILOT.md for runbook and precise limits.

22 October CURRENT: hosted pilot passed import/publication/search/open/delete with real Auth and two real cloud model calls. Operator confirmed final physical cleanup=true; runner reported min0 restored. Internal application ASGI adapter now implements five fixed library routes; synthetic checks pass. No listener, worker scheduler, desktop wiring or public upload release. See LIBRARY_API.md for limits and remaining gates.

# Current project state

22 October CURRENT: old cancelled fixture cleaned=true per operator. New run stopped
in warm scaling before new receipt/import; original evidence intact. API audit timing
fits local 45s synchronous update wait. Warm command now async, followed by target/
generation-ready observation and one HTTP probe sharing the existing startup60s.
Live scoped warm/readiness/restore verification passes, actual min0/max1 confirmed.
61 focused checks/build pass. Next: operator --run --new-after-cleanup once; no new
fixture needs cleanup yet and no complete hosted workflow claim. See HOSTED_FLOW_PILOT.

22 October CURRENT: Gather minimum restored to 0/max1 after warm setting remained
active through ~4h44 operator gap. New full-run capacity guard restores min0 in
finally; no permanent timer/hard cap claimed. Supavisor handshake closures fit
inner connect=3 cutoff; pilot now connect=10 within approved total15, defaults
unchanged. Read-only hosted profile check, 56 tests, preview/build pass. Cancelled
source 5a4c1c59-9313-4982-a1b4-c8dd73dd30c1 needs dashboard finish_source_cleanup.
After cleaned=true, guarded --new-after-cleanup creates new request and archives
old evidence. No new import/inference yet. See HOSTED_FLOW_PILOT.md.

22 October latest: import acknowledged, processing failed before staging/inference.
Receipt queued/temporarily_unavailable, then failure cleanup tombstoned source.
Operator confirms job cancelled/deleted, attempts=1, no staged text/passages.
Do not resume this source; original bytes still need admin physical cleanup.
Added safe worker-step/reason diagnostics; 30 tests/build pass. Need existing
Postgres error/warning log around 07:15–07:30 UTC for old root cause. Offline pinned-
tokenizer/fixture replay passes but does not prove hosted behavior. Warm min=1
still active; no agent inference or hosted retry. See HOSTED_FLOW_PILOT.md.

22 October CURRENT CLOUD OBLIGATION: user approved min=1/max=1 for Gather's active
pilot; applied and authenticated readiness passes. Image/resources unchanged;
actual invoker policy still only pilot caller. Idle billing active. Restore min=0
after pilot completion or operator stop; NOT done yet. Original import receipt
unchanged; guarded resume next. 16 runner checks and frontend build pass.

22 October latest: resumed run again failed at readiness, before receipt/history
change. Cloud logs confirm another 429/no-instance followed by startup; original
import receipt remains unchanged with zero model calls. Proposed temporary min=1
to avoid repeated cold handoffs; user decision pending, no scaling change made.
Safe readiness IO error categories added; 16 runner checks and frontend build pass.
Do not request another full run before addressing capacity. See HOSTED_FLOW_PILOT.md.

22 October latest: failed import has no hosted save receipt per operator check.
Measured TLS/login 7.56 s; connection+role setup 9.05 s, beyond five-second adapter
bound. User approved explicit 15-second DB allowance for operator pilot only;
production/SQL/model defaults unchanged. Guarded --resume-import preserves history
and request ID. 40 focused checks, real non-mutating hosted lookup and frontend
build pass. Operator resumed run next; no hosted-flow completion claim. See
HOSTED_FLOW_PILOT.md for evidence, semantics and remaining cleanup requirement.

22 October latest: both hosted user logins passed operator --check-auth. Full
run then hit platform 429 "no available instance" on /ready during cold startup,
before import. Logs showed startup completed afterward; one agent readiness-only
probe now passes. Added --check-startup and safe HTTP status reporting, 11 runner
tests pass. Next: operator full run once against ready service. Cold-start UX
remains open; no deployed settings changed. See HOSTED_FLOW_PILOT.md.

22 October latest: first hosted run stopped at A sign-in before imports/inference.
Both emails confirmed; read-only settings show email/password enabled and public
signup disabled. Added safe Auth error codes and --check-auth to isolate the cause
without DB/model work. 25 focused checks and frontend build pass. Operator auth-only
run is next; hosted workflow remains unverified. See HOSTED_FLOW_PILOT.md.

22 October latest: user created both hosted Auth pilot accounts and confirmed two
slots each, unused. One-source hosted flow runner now prepared: real sessions,
bounded DB/cloud provider, query-vector replay for isolation/deletion, safe receipt
and failure tombstones. 13 focused checks, preview and frontend build pass. Operator
must run with hidden user passwords; no hosted-flow success claim. Physical cleanup
needs dashboard admin after tombstoning. See HOSTED_FLOW_PILOT.md.

22 October latest: stored encrypted credentials decrypt under owning Windows user;
both hosted restricted-role TLS logins now verified by agent. Read-only probe uses
no source/job functions. 14 focused checks and frontend build pass; earlier approval
block resolved. Public API configuration/hosted Auth users remain unavailable via
current CLI login; operator dashboard input needed before a real-session hosted
flow. See HOSTED_SUPABASE_SETUP.md. No new model calls or public deployment.

22 October latest: user reports both hosted restricted passwords committed and
logins verified. Local Windows-user DPAPI loading/helper prepared; 12 checks and
real synthetic memory roundtrip pass. Operator must run store helper before the
backend can load credentials. No hosted flow rerun. Exposed-password rotation
explicitly deferred by user. Build pending from prior approval-review usage limit;
changes uncommitted. See HOSTED_SUPABASE_SETUP.md; older failure notes are history.

Password helper follow-up: generic failure reported after hidden prompts; cause
and hosted outcome unconfirmed. Added safe per-role validation messages and
--check-input (no network). Eight tests pass. Operator input-only check next;
required build still blocked/unrun, changes remain uncommitted.

22 October: hosted Sydney project fatolholcjxpwocnpzws retained by user. Seven
migrations and restricted-login creation reported successful; CA inspected.
Password helper prepared with hidden local prompts; six checks and preview pass.
No hosted password update/login performed. Required build blocked by automatic
approval-review usage limit; changes uncommitted. See HOSTED_SUPABASE_SETUP.md.

21 October latest: bounded DatabaseRepository now uses real Psycopg connections
and reuses PostgresRepository. Restricted login/role, verified-owner transaction
context, five-second whole-operation deadline and forced helper cleanup verified.
24 focused checks, disposable real-driver integration and frontend build pass.
See DATABASE_TRANSPORT.md. Hosted Supabase project not linked locally; browser
inventory unavailable. Hosted TLS/driver packaging remains unverified. Next:
application HTTP admission around LibrarySession, then hosted setup and desktop.

21 October latest: authenticated LibrarySession boundary verified with two real
local Supabase Auth sessions. Import owner comes from Auth; fixed session RPCs
provide status/open/delete and existing search verifies Auth before inference.
17 new local integration assertions pass within the existing stack; 41 distinct
focused unit/transport tests and frontend build pass. Synthetic vectors and test
psql admission only; no cloud inference rerun. See LIBRARY_SESSION.md. Next:
bounded production DB composition and application HTTP admission, then desktop.

21 October latest: developer backend cloud integration passes: TXT submission ->
real cloud embedding -> atomic publication -> real query -> source open -> delete.
Two model requests, disposable local SQL with test-only Auth shim. See
CLOUD_INGESTION_PILOT.md for exact evidence and the initial cold-start failure.
Production metadata remains default; pilot token is explicit/in-memory only.
Next: authenticated application/session boundary and production DB composition,
then desktop wiring. Hosted ownership and cold-start UX remain open. The following
upload/deployment-pending entries are historical: the user completed both and IAM.

Manual upload helper ready: scripts/upload-pilot-image.ps1. Preview checked;
live upload remains user action via explicit -Account and -Upload. No image sent.

21 October: personal-account CLI access now verified for Gather caller and
Mumbai Docker repository. Caller numeric subject confirmed; identity/policy files
validated and baked into pilot-configured image. Non-root/read-only config check
and frontend build pass. Release/model layers unchanged; no new model run. Next:
explicitly approved private image upload, then Cloud Run deployment/IAM pilot.
No agent upload, IAM grant or deployment has occurred.

21 October: real baked-model release smoke passed. Startup 18.55 s; four requests
0.86–7.76 s, peak 4.09 GiB under 5 GiB; valid vectors, rejection/recovery and cleanup.
Evidence: qwen-release-http-20261021.json. Host stderr locale failure corrected to
binary capture; six focused harness checks and frontend build pass, no model rerun.
Technical local release verification complete; no cloud-readiness claim. Next:
personal Gather account CLI sign-in, verify gather-development-511211 access,
then final pilot/security approval within INR 500/Mumbai. Intrixshield excluded.

20 October: model-bearing release candidate built; see RELEASE_AND_PILOT.md and
deploy/cloud-run/pilot.json. Correct target is gather-development-511211 (Gather
Development), Mumbai; INR 500 total ceiling. Intrixshield is forbidden. Browser
verified Gather; local gcloud only has the work account and cannot access it.
Collected notices for 439 hashed crates plus separate parent-project components.
Fixed real Cloud Run hostname compatibility; 34 identity tests, 8 packaging/HTTP
checks, frontend build and 128 MiB baked-file integrity verification pass.
Real-model release smoke is blocked by 3.09 GiB free RAM (<4 GiB required).
Milestones 1/2 remain partial: personal CLI sign-in, real smoke and final resource/
security approval pending. No cloud mutation/upload/deployment. Model/caches on D:.

19 October latest: Docker available; cloud-startup candidate built. All 49 Linux
startup/auth/HTTP/artifact/SIGTERM checks pass, 512 MiB/one CPU, no model/network.
See CLOUD_STARTUP.md and cloud-startup-linux-20261019.json for evidence. Prior
unchanged frontend build retained. Two protected APIs showed restart-count changes;
no mutation commands issued and no cause inferred. Next: native attribution and
immutable model-bearing release packaging, then approved cloud pilot. Live IAM,
cold start, release findings and paid deployment remain unverified/unapproved.

19 October: guarded Cloud Run startup implemented and host-verified; see
CLOUD_STARTUP.md. Explicit module requires matching intended IAM policy, managed
Google auth and valid PORT; local startup remains loopback-only. 11 new cloud,
32 existing auth/startup/HTTP and 18 staging checks pass; frontend build passes.
Exact source staged, no models loaded. Linux image verification remains blocked:
Docker Linux engine pipe absent on preflight. Next: start Docker normally and
verify a separate cloud-startup candidate. No live IAM proof or deployment.

19 October: complete-input validation for zlib staging is verified. All four
inputs are read before output creation; hashes validate the bytes actually copied.
Missing installer/manifest fails without new or modified staging output. The CLI's
previous missing-patch regression is retained and included in this checkpoint.
18 focused tests and frontend build pass; no Docker/model run. Disk-write failures
are not transactionally rolled back. Next: guarded Cloud Run startup, with current
security/licence/IAM/spend release gates retained. Root CLI logs remain untouched.

Desktop/CLI collaboration rules ready: docs/CLI_WORKFLOW.md. One writer per
checkout, scoped handoff, reviewer-owned commit by default. No automatic session
connection. Python launcher now forwards piped text; focused checks/build pass.

Windows CLI runtime discovery fixed for lightweight checks: scripts/python.ps1
handles missing PATH, redirected LOCALAPPDATA and spaces; propagates failures.
AGENTS.md documents usage and bounded troubleshooting. Existing CLI test edit
and root log files remain uncommitted and untouched. No global PATH changes.

Final zlib scan: 28 findings (1 high, 1 medium, 26 low). Scout still flags
CVE-2026-85091 on +gather1; no suppression applied. The targeted defect is fixed
and regression-verified independently, not scanner-cleared. Evidence:
tests/inference/results/zlib-scan-20261018.json. Scanner exited zero; temporary
archive cleanup hit a file lock, so no forced deletion was attempted.

Current: zlib error-state bug fixed in the separate zlib-candidate image using
a pinned local backport, not an official Debian update. Original installed
library fails the regression (42); patched installed library passes (0).
Standard zlib tests, compression/PyTorch compatibility, 14 focused checks and
frontend build pass. See services/inference/zlib/README.md and retained evidence.
No model rerun or deployment. Other release gates remain; next is guarded cloud
startup implementation with the final scan result retained above.

Current: notice-packaged Linux candidate built and verified. Model card matches
the pinned artifact hash; official Apache licence retained. All required notices
are enforced by staging. 47 wheels, 177 embedded notices, five supplements;
87 OS copyright files present. Previous nine image layers identical. Ten focused
checks and frontend build pass. Evidence: notices-image-20261018.json.
Next independent development: explicit guarded Cloud Run entry point, keeping
loopback default. Deployment remains blocked by OS adjudication, full native
attribution review, actual IAM acceptance and spend approval. No model rerun.

Current: tokenizers upstream licence gap fixed in source; exact-version files
and provenance retained. Notice collection integrated into image staging and
Dockerfile. 47 wheels / 177 notices / 3 supplements staged; new image not built.
Focused checks and frontend build pass. OS zlib still unresolved in Debian's
tracker and bug report; no waiver. Next: model/native attribution review and
supported OS remediation evidence before release-image promotion.

Current checkpoint, 18 October: CLOUD_PILOT_PLAN.md records the bounded pilot
proposal and open gates. All 47 serving wheel hashes match the lock; tokenizers
has no detected bundled notice file. No licence clearance or OS waiver claimed.
Background key refresh requires revising the request-based CPU proposal;
instance-based billing is proposed, not authorized. Next: exact-version notices
and security adjudication, then explicit guarded cloud packaging. No deployment.

Latest, 18 October: live Google public-key compatibility passed inside Linux
startup-candidate: two keys, 0.505 s, unchanged freshness/resource bounds.
Evidence: RECEIVING_IDENTITY.md and tests/inference/results/live-google-keys-20261018.json.
Earlier 51 Linux checks and unchanged frontend build retained; no model rerun.
Next: remaining licence/OS security review and concrete cloud pilot configuration.
Actual identity-token/IAM/header validation, public bind and spend approval remain
gates. Successful public-key retrieval alone does not authorize deployment.

Current next-step status (17 October): real Qwen loopback HTTP smoke passed.
Startup 12.68 s, short requests 0.68-0.82 s, 512-token passage 4.69 s, peak 3.98 GiB
under the unchanged 5 GiB ceiling. Valid vectors, rejection/recovery and cleanup
pass. See services/inference/HTTP_SMOKE.md and its retained real-model evidence.
RAM guard passed at 6.05 GiB after specifically approved transient cache release.
No stop/restart commands or persistent Docker setting changes; API restart caveat
is recorded in PROGRESS.md. Next: cloud IAM/header integration plan and remaining
security gates before any authorized deployment. No cloud readiness claim.

Latest (17 October): receiving authentication and managed key refresh packaged in
an isolated 47-dependency Linux candidate. Actual SIGTERM verifies that a busy
synthetic inference child stops, HTTP returns 503 and the refresh thread joins.
Four host staging checks and required frontend build pass. Initial image passed
38 Linux checks plus the corrected signal test; patched image passes all 39
in one run. No real model or Google call.

Scan caught three high pyasn1 0.6.3 findings; upgraded only that added dependency
to 0.6.4. Final patched-image verification is recorded in
services/inference/SERVING_IMAGE.md. Final scan returns to 28 OS findings,
with none reported for Python; OS findings remain unresolved.
Public binding and deployment remain blocked. No protected workloads changed.

The real-model HTTP smoke above supersedes the previous RAM-blocked next step.
Actual Google/IAM/header handoff, release security review and cloud pilot approval
remain separate prerequisites. Desktop uses sample data; no live integration claim.
Historical implementation/test evidence is in PROGRESS.md and TASKS.md.

Latest UI checkpoint: expressive desktop preview redesign implemented. Five UI
tests, lint, frontend and native debug builds pass. Browser visual/contrast/reflow
checks recorded in DESIGN_REVIEW_20261015.md; native scaling/accessibility QA
remains open. Still fictional data; backend delivery milestone remains next.


Updated: 15 October 2026. Current forward plan: DELIVERY_PLAN.md. New architecture
choices there are proposed, not implemented. PROGRESS.md records history.

Current: bounded source context implemented and saved-vector replay completed;
see SEARCH_CONTEXT.md for policy, safety boundary and evidence. Nine focused tests
and frontend build pass. Known boundary coverage recovered with zero new model
calls; ranking/abstention and real-user quality remain unresolved. Next is
milestone 2 in TASKS.md: backend import/index/search/open/delete coordination with
trusted ownership/version reads. No Docker/app/process changes this checkpoint.

Prior evaluation checkpoint:

Latest: paired chunk-policy retrieval evaluation completed on 15 October. All
178 real requests passed. text-v2 candidate dense recall/evidence 1.0, MRR 0.9792;
predeclared gate passes. Boundary strict evidence stays 0.50, union coverage 0.875;
three split-condition questions and one multi-part passage miss need attention.
44 evaluation tests, 26 inference tests and frontend build pass. See
CHUNK_RETRIEVAL_RESULTS.md for all regressions and evidence. Next: bounded
same-source context assembly and multi-part coverage before ingestion integration.
Security/licence review remains open; no model/image promotion, deployment or push.
Docker recovered from a startup socket error through a user-approved close/reopen;
no reset or file deletion. Authorized background Teams/WhatsApp closure freed RAM;
Chrome and this session remained running. No individual API stop/update commands.

Earlier patched-image checkpoint:

Newest checkpoint: separate patched CPU image built; 25 focused tests and frontend
build passed on 14 October. Torch 2.14.1+cpu / Transformers 5.19.0 and exact Debian
OpenSSL/PCRE2 fixes reduced scan records from 56 (12 high) to 28 (1 high). Remaining
zlib high and tar medium findings have no fixes listed and remain open. New
512-token source-slice preparer preserves offsets/coverage but is not integrated
into desktop ingestion. Candidate real checks passed on 15 October: six vectors
match baseline tolerance, token counts/rankings unchanged; five 306–500-token
chunks took 3.053–5.883 s, peak 3.95 GiB. Approved transient Linux clean-cache
release cleared the unchanged 4 GiB host guard. No API stop, Docker restart,
candidate promotion or push. Next: retrieval-quality evaluation of new boundaries,
then ingestion integration; security/licence gates remain open. See
services/inference/UPGRADE.md for reproducible steps and evidence.

Latest extended checkpoint: all four real CPU profiles attempted and recorded.
512/1,024-token documents took 5.645/13.632 s; 2,048-token item and max batch
hit the 15 s deadline (no OOM, clean termination). Over-limit rejection/recovery
passed. Fifty short queries passed, median 0.710 s, p95 0.935 s, peak 3.64 GiB.
21 control/reporting tests pass on Windows/Linux; frontend build passes. Image
unchanged. Security scan: 56 records, including 12 high; image NOT deployment-ready.
See services/inference/PROFILE_RESULTS.md and IMAGE_SCAN_REVIEW.md. Next: OS/AI
dependency remediation with compatibility tests/rescan, then smaller-chunk policy
evaluation. No limits relaxed, no existing API changes or push. TASK-005 partial.

Latest TASK-005 checkpoint: isolated Linux CPU image built on D: with 25
hash-locked dependencies; 18 inference/protocol tests pass on Windows and inside
the container. The launcher verifies resource limits, non-root/read-only and
offline configuration and cleans only its uniquely named test container. The
frontend build passes. See services/inference/CONTAINER.md and recorded control
evidence. Real container inference passed on 14 October after 4.20 GiB host RAM
became available: 15.781 s startup, ten fictional requests at 0.593–0.742 s,
4,155,457,536-byte cgroup peak (3.87 GiB) within the 5 GiB ceiling. Model identity,
normalized 512-dimensional vectors and repeated-query consistency passed; the
test container exited successfully and was removed. Evidence:
tests/inference/results/qwen-container-20261014.json. Next: maximum-input/load
profiling and image security review. TASK-005 remains partial; no connected
desktop search or cloud deployment. Existing API containers unchanged. No push.

Latest setup result (13 October): Docker disk migration is complete and verified.
The failed UI move treated Robocopy success code 1 as failure. After stopping
Docker/WSL, the stale D: copy was refreshed from C: and matched its full SHA-256.
Settings were backed up and CustomWslDistroDir set to D:\DockerDesktop\DockerDesktopWSL.
Docker restarted with identical 9-container/64-image/1-volume inventory. D: disk
is in use; the old C: disk was detached/unlocked and then removed with approval.
C: had about 36.3 GiB free; D: about 32.74 GiB at migration completion. The image
build is now verified as recorded above; real container measurement is pending.

HF login is now saved in the ignored D:
benchmark HF home and authenticated successfully. The fine-grained token's account
still receives HTTP 403 for EmbeddingGemma; the response indicates account-level
model access is not approved. Check acceptance/access using the same account.
Docker startup socket failure recovered by closing the failed Desktop and
launching via Windows Explorer. Engine 29.7.2 responds. No factory reset, token
disclosure or model download performed during the migration.

Extractor checkpoint: TASK-019A hash-locked image rebuilt after Docker recovery.
Exact installed versions, pip consistency, bad-hash rejection, offline restrictions
and prompt timeout cleanup pass. TASK-023 patched OpenSSL/PCRE2 and removed
runtime pip/ensurepip on 3 October. The 8 October code-image rescan reports
29 records (2 high, 1 medium, 26 low); no dependency versions changed this turn.
Two GCC records disappeared from the refreshed feed, not through a code fix. Remaining
unpatched/applicability and build-tool review stay open; live execution is gated.
See services/worker/IMAGE_SCAN_REVIEW.md. OKF remains a later optional export layer.

## Product and constraints

Latest steering: self-hosted CPU AI on Google Cloud Run, R2 originals and Supabase
Free Auth/Postgres/pgvector. User has created the Google Cloud account. Application
deployment remains unverified; do not provision paid resources from benchmark
permission. On 10 October the user authorized D:-only local model tests, and
chose Qwen first. On 12 October the user confirmed EmbeddingGemma terms accepted;
local Hugging Face authentication now works, but that account's Gemma access is denied. Commit
locally; push only on an explicit request to push.

Gather is a provisional name for a Windows desktop content library with semantic text/photo search and selected-source chat. Tauri/React/TypeScript and Supabase Free remain. User chose cloud AI on 27 September (ADR-009); later CPU/Cloud Run choices are in ADR-038. No end-user model downloads planned. Design avoid-list applies. No agentic file modification, payment feature or mobile app in MVP. Chat remains deferred until search works.

## Implemented

- 13 October real persistent Qwen host smoke passed using the verified D: model:
  14.239 s startup, three requests 0.505/0.669/0.709 s, two CPU threads, 512 dimensions.
  Same process reused and reaped after completion. RSS after requests 2.54 GiB
  (not peak memory). This supersedes the 12 October RAM blocker below; only three
  fictional inputs were used, not a load test. Docker disk is now verified on D:
  and HF login works, but Gemma account access is denied. Container build and
  Gemma remain pending. No new cloud work or GitHub push.

- TASK-005 persistent CPU process prerequisite added in services/inference.
  Fourteen synthetic tests verify bounds, readiness, process reuse, busy rejection,
  token preflight, deadline termination/reaping and explicit recovery. Full checks
  pass: 112 worker + 39 evaluation + 14 inference + 4 UI = 169 tests, lint/types/
  formatting/frontend build. Real Qwen host smoke stopped at the 4 GiB RAM guard.
  The later host smoke and D: Docker migration are now verified. Container build,
  limits and measurements remain unverified. No HTTP endpoint or cloud deployment.
  See ../services/inference/README.md. Next: implement and measure the bounded
  Linux serving container; resolve Gemma account access separately.

- TASK-005 fresh challenge: 40 new fictional documents, 64 chunks, 64 questions
  frozen before inference. Qwen 512 dense passes the declared development gate:
  100% document recall, 99.11% evidence recall, MRR 0.9613 on 56 answerable queries.
  All eight absent cases still return candidates. Five nonperfect dense queries
  reviewed; exact codes, temporal wording and multi-part passage coverage remain
  issues. Warm median/p95 0.329/0.403 s, OS peak 3.64 GiB, offline on D:. 39
  evaluation tests, frontend build, pip check and v1 regression pass. Previous
  worker/UI checks were not rerun for this evaluation-only change. See TEXT_V2_RESULTS.md.

- TASK-005 real local CPU benchmark: pinned Qwen3-Embedding-0.6B downloaded to
  D: and evaluated at 256/512/1,024 dimensions with two/four CPU threads. All
  dimensions have 100% document/evidence Recall@5 on 35 answerable development
  queries; 512-dimensional MRR is 0.9857. All five absent queries still return
  neighbors. Four-thread median/p95 query time: 0.324/0.376 seconds; sampled peak
  RAM about 3.58 GiB. This is isolated evaluation, not connected app search or
  cloud performance. 150 source/UI tests and frontend build pass. See CPU_BENCHMARK.md.

- Real core Supabase API harness: 31 checks pass on disposable Auth/PostgREST/
  Storage + PostgreSQL. Actual JWT login, private reads, denied client writes,
  tombstone visibility and Storage API deletion before SQL finalization verified.
  Explicit loopback gateway; no DB host port; synthetic data/containers removed.
  No desktop integration or background cleanup worker. See ../supabase/LOCAL_INTEGRATION.md.

- TASK-021 database lifecycle: 45 SQL assertions and four concurrent scenarios
  pass for ownership, atomic source-slot quota/idempotent saves, tombstones,
  database cleanup rollback and late-write protection. This fast suite still uses
  Auth/Storage metadata shims; the separate API suite uses real local services.
  No real user account, hosted RPC or desktop connection.
  See ../supabase/README.md for remaining quota/retention/external cleanup gates.

- FetchBroker bounds the entire fetch process, including hanging DNS/connect/TLS,
  kills/reaps cancelled or timed-out children and validates bounded responses.
  BookmarkPipeline passes fetched bytes to the offline Docker parser, preserving
  URL/time/hash/notes and passage provenance. Only controlled loopback integration
  is verified; no API, desktop ingestion, persistence or semantic results.

- Backend-only restricted HTTP transport: approved numeric address dialing,
  redirect revalidation, TLS identity checks and bounded page bodies. Tested only
  against controlled local peers; resolver/connector injection is trusted code.
- Host-side offline DockerJobRunner: fixed entrypoint/digest, bounded input/output,
  concurrency, execution timeout, cancellation and cleanup. Actual container
  resource/egress tests pass. Not an API, durable queue or live fetch broker.

- 10 October full quality checkpoint: 112 worker, 34 evaluation and four UI tests, ESLint,
  TypeScript, Prettier and frontend build pass. Native development build passes.
  Manual GitHub workflow authored; remote execution unverified.
- Links/bookmarks added to product scope and delivery plan in BOOKMARKS.md.
  Offline extraction implemented with ten synthetic tests. No bookmark UI, storage or fetcher.

- Server/developer-only embedding request client with batching, full-job token
  preflight, bounded HTTPS, index reordering and safe errors. Eight mocked tests
  pass; no real tokenizer/provider/export integration or cost measurement yet.

- Saved-vector evaluation adapter with exact normalized cosine ranking and equal-weight RRF (k=60) comparison to TF-IDF. Export metadata checks model/revision/templates/tokenizer/dimensions, corpus/index hashes and truncation. Initially synthetic math tests only; now complemented by the real CPU export above. The corpus remains fictional, while the generated vectors are actual model outputs.

- Offline TF-IDF keyword baseline and strict scoring harness with corpus/index fingerprints, per-category and per-query metrics. Twenty-one evaluation tests pass. Baseline text-v1 document/evidence Recall@5 is 0.9714 and MRR@5 is 0.8667; 4/5 absent queries return candidates. This is a tiny development comparator, not semantic search or an answerability system.

- Retrieval development corpus text-v1: 14 synthetic documents and 40 queries (35 answerable, 5 absent), with exact evidence mapped to 16 real processing chunks. Seven integrity tests pass. Export tool separates index/query inputs from relevance labels. See tests/evaluation/README.md and CPU_BENCHMARK.md for the first real model results.

- Transport-independent Python text processor: bounded typed request/results, strict UTF-8 TXT/Markdown, original source offsets, deterministic hashes/versioned passage IDs, structured safe errors. Twelve synthetic tests pass. No filesystem/network/model calls or new dependencies in this module.

- Desktop shell with fixture library, filters, reader, model lineup and preview policy screens.
- Motion selection feedback, optional reader Lenis, paused Thinking Orbs sample, local fonts/artwork/license notices.
- Four passing component tests, passing frontend and native development builds at the last implementation checkpoint.
- Legacy privacy fixes, documented audit and release follow-ups.
- Official Rust toolchain installed; C++ tools found; compatible Node available through scripts/desktop.ps1. Global npm shim remains broken; helper avoids it without changing global PATH.

## Not implemented / unverified

No real desktop import, connected worker/cloud endpoint, production embeddings, Supabase project connection, auth, durable search index, chat or signed installer. Processing and Qwen inference are tested in isolation. The frozen corpus fits the actual tokenizer; arbitrary/long passages still require token-aware production limits. No native/visual/E2E verification. Previous browser opening was declined; that limitation was not bypassed. Canvas is stubbed in component tests, so passing tests do not verify the orb renderer.

Frontend lint and format checks are configured; remote CI and native E2E remain unverified. The full initial baseline diff also reports pre-existing trailing-whitespace issues in legacy files; those are not hidden or counted as a clean full-diff check. Git repository: https://github.com/kratos1911/gather-desktop (private). origin is configured; main tracks origin/main. Baseline commit b89ceec was pushed and its remote hash verified. The TASK-001 baseline contains the existing implementation and workflow documents.

## Current task

TASK-005 fresh challenge verified on 12 October with settings unchanged from v1.
Next: measure a local serving container with explicit resource limits; verify
Docker image storage is on D: before large builds. The 512-dimensional candidate
advances only to this experiment, not final production selection. Independent
relevance review and the observed retrieval weaknesses remain open. EmbeddingGemma waits for license/access; visual
models need an image/OCR corpus; chat stays deferred. These remain unfinished.

TASK-021 core API slice verified locally on 9 October. Next: upload fencing and
external-object reconciliation, then processing job leases. Exact hosted parity,
desktop sessions and connected persistence remain pending. The CLI binding issue
was replaced with a disposable Compose harness using explicit loopback ports.

TASK-022 documents the system/security delivery plan. TASK-019A added dependency
locking/review; current source checks total 150 tests. The new recipe built and
passed offline smoke checks. TASK-023 records open scan findings; TASK-019B
has a tested offline Docker supervisor and plain-HTTP restricted transport.
Whole-broker DNS/process deadlines and controlled HTTP-to-parser integration
now pass. Browser/tool egress and production broker confinement remain open.
TASK-005 hosted deployment remains pending; local CPU evidence is now available.
No GitHub push authorized. Offline bookmark processing passes; live bookmark search remains pending. Chat deferred by user on 28 September.

## Next implementation

30 September final choice: Crawl4AI for public webpages and yt-dlp for supported
video metadata/available subtitles. Agent Reach is optional. See
docs/knowledge/EXTRACTION_STACK.md. Tools installed in the offline container only. Transcription,
visual video understanding and chat remain deferred. TASK-019 follows TASK-018.

TASK-018 completed: offline bookmark passages with source/field references and
TF-IDF retrieval tests. TASK-019 adapters/offline runner pass; next is TASK-023
remaining security review. TASK-019B controlled HTTP transport and offline Docker supervision now pass
local tests. FetchBroker and BookmarkPipeline now pass controlled end-to-end
HTTP/process/Docker parsing tests. Next: production confinement and browser/tool
egress; live invocation (019C) stays gated. No persistence or semantic indexing.
TASK-021 plans local Supabase schema/job/isolation tests. TASK-017 connects the flow.
Provider connection remains pending. v1/v2 semantic benchmarks now exist; add
independently reviewed real-world and larger-scale cases before release claims. TASK-002
audience research and TASK-003 visual QA remain open.

## Inputs needed before later gates

Supabase project/public configuration; audience/regions; operator/contact and final policies; cloud provider, budget, model/license/runtime selection; signing and public distribution destination. Do not request secrets in chat. Current .env is private legacy configuration and is not copied into the new app.

## Obsidian workspace

Project hub: [[docs/PROJECT_HUB]]. Shared repository notes are the source of truth;
concepts, ideas, templates and the search-flow canvas supplement the canonical
documents. Local template/daily-note configuration saved; Obsidian UI not verified.
Latest evaluation checks: 39 tests and frontend build on 12 October; the full
source/UI checkpoint was 150 tests on 10 October. Locked-image
smoke passes, including actual timeout cleanup; no smoke containers remain.

## Earlier checkpoints (superseded by the 1 October status below)

Six root prototype files moved unchanged to legacy/; three unused starter logos
removed. Original data, secrets, environments and user notes preserved. See
docs/REPOSITORY_AUDIT.md for all 109 original tracked-file dispositions.

Bookmark passage adapter implemented in services/worker/bookmark_passages.py.
Seven new synthetic tests; no desktop search, storage or actual embeddings.

TASK-019 partial: eight synthetic output-adapter tests pass. Markdown preserved,
subtitle cue timing/language tracked. No installed extractors or live requests.
Next: isolated runner and network enforcement.

## Subtitle parsing checkpoint

services/worker/subtitles.py now parses a bounded UTF-8 SRT/WebVTT subset into
normalized cues. Eight tests include byte-to-passage timestamp preservation.
TASK-019 remains partial; installed/pinned runners and live network checks remain.

## Network preflight checkpoint

TASK-019 partial: direct extractor pins recorded; eight synthetic destination
policy tests pass. No packages installed or real DNS performed. Connection/egress
isolation, transitive dependency lock and executable runner remain unfinished.

## Runner checkpoint (30 September history)

Bounded offline JSON runner and network-disabled Docker configuration added.
Docker CLI validates Compose, but Linux engine is unavailable after startup
attempt. Image build, package installation and runtime isolation are unverified.
Runner only consumes supplied extraction outputs; live URL extraction and enforced
public-only egress remain unfinished. TASK-019 remains partial.

## Historical checkpoint: 1 October

Docker Linux engine is ready. Extractor image built; installed Crawl4AI 0.9.4 and
yt-dlp 2026.8.19 verified inside it; pip check passes. Repeatable container smoke
checks pass for synthetic jobs, non-root UID, application write rejection, an
unreachable external route and absent checked personal paths. All 98 tests and
frontend quality/build checks pass. Earlier package/engine limitations above are
historical. TASK-019 remains partial: no live tool invocation or browser installed.
Next: dependency/image locking and enforced public-only egress before live fetching.
No paid resources or GitHub push.
