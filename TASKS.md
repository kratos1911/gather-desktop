## 25 October: worker cold-start guard

Real receipt for efea703e-22e5-4663-b4e3-c9280c650a88 confirms exact-job routing reached embedding; cloud log identifies 429/no available instance. Reused existing scoped warm/readiness guard before WorkerRun, keeping inference15s and retry limits unchanged. 19 focused guard/operator checks plus frontend build pass. No new live claim/model call or capacity change made during fix; live retry remains pending.

## 25 October: exact-job repair deployed

User approved the hosted migration at action time. SQL editor returned Success; read-only function/ACL query returned true,true,false,false,false,false for installation, worker, client, anonymous, admission and private core. No hosted processing or model call. Source/old-job data unchanged by this function-only migration. Exact-job fix is deployed; live worker outcome remains pending.

## 25 October: exact-job claim repair

Local complete, hosted application pending explicit approval: shared claim core plus restricted targeted entry point, operator routing, safe diagnostic receipts and truthful exit status. 41 focused checks, existing SQL regressions/new targeted cases and frontend build pass. No unrelated jobs processed/deleted or attempts reset. See docs/EXACT_JOB_CLAIM.md for cause, evidence and deployment gate.

## 24 October: Chrome fetch receiver fix

Reproduced default client network_unavailable versus wrapped client receiving HTTP failure from local API; direct browser request also reached API. Fixed transport invocation and added receiver-sensitive regression. 25 frontend tests, build, lint/format pass; production asset hashes identical. Temporary credential-free diagnostic pages removed. No model or hosted document operations performed by diagnostics. Existing operator page needs refresh/new sign-in before the live import check.

## 24 October: restricted operator library pilot

Implemented loopback HTTP serving, bounded worker stop/recovery, typed browser transport and session-scoped state, plus development-only fixed-content UI. 49 backend checks and 24 frontend checks pass; lint, formatting, frontend and native debug builds pass. Signed-out layout/focus verified; authenticated hosted UI acceptance is pending. Exact evidence and commands: docs/OPERATOR_LIBRARY_PILOT.md. No paid resources, model calls, Docker work or public release. User requested stopping after this ongoing milestone.

## 22 October: bounded application API adapter

Implemented five fixed ASGI library routes and trusted per-bearer composition. Validation, safe errors, disconnect/deadline cancellation and retained single-flight slot verified: 17 focused API/session tests pass (exit 0). Hosted pilot receipt passes separately; operator reports physical cleanup=true. Frontend build passes; no model/Docker/cloud runs. See docs/LIBRARY_API.md. Server launch, real HTTP integration and worker lifecycle remain next.

# Delivery tasks

## Manual pilot upload helper

Added scripts/upload-pilot-image.ps1 for user-run upload. Preview verifies the
exact image and local Linux engine; -Upload requires an explicit account, uses
a restricted temporary Docker auth directory and removes its token file in
finally. Preview and missing-account rejection checked; frontend build passes.
Actual authentication/push not executed or claimed verified.

## 21 October: real pilot identity configured locally

Verified Gather caller uniqueId and repository location through personal account.
Created identity/deployment-policy files and digest-pinned Dockerfile.pilot.
A 128 MiB network-none non-root container validates readable, immutable config;
frontend build passes. Found and fixed missing traverse permission on the initially
created /config directory before any upload. Model layers reused. Evidence:
tests/inference/results/pilot-configured-20261021.json. Next: private image upload.

## 21 October: real baked-image release check complete

Exact release candidate passed four real Qwen HTTP requests plus unauthorized,
token-limit/recovery, readiness, process reuse and cleanup checks; no model mount.
Startup 18.55 s, peak 4.09 GiB, no OOM/outer timeout. Kept the run's Windows stderr
capture warning in evidence; corrected capture and passed two pipe/four synthetic
HTTP tests plus frontend build. No repeated benchmark. Local image verification
complete; cloud IAM/cold-start and final approval remain pending personal login.

## 20 October: release image and Gather-only pilot preparation

Partial milestones 1/2: built baked-model candidate, native notice collection,
bounded release HTTP harness, and deployment settings manifest for Gather only.
34 identity/startup tests plus 8 release/harness tests pass; frontend build and
isolated 128 MiB image integrity/permissions check pass. New real-model inference
not run (3.09 GiB available versus 4 GiB threshold). Personal gcloud sign-in missing;
browser project verified. See docs/RELEASE_AND_PILOT.md for exact next actions.
No deployment approval inferred from INR 500/project/region planning choices.

## 19 October: Linux cloud-startup verification complete

Separate cloud-startup-candidate built; all 49 Linux checks pass, including real
SIGTERM cleanup. No model loaded, no host port or external network. Eight base/
dependency layers match prior candidate; no fresh scan. Previous frontend build
reused. Evidence: tests/inference/results/cloud-startup-linux-20261019.json.
Next: complete native attribution and immutable model-bearing release packaging;
cloud pilot still requires project/region/spend and actual IAM acceptance.

## 19 October: guarded cloud startup, host verified

Implemented separate cloud_startup module, intended-policy/PORT validation and
public-bind guard requiring ManagedGoogleServiceAuth. Local entry point unchanged.
11 cloud tests + 32 existing auth/startup/HTTP cases + 18 staging checks pass;
frontend build and real 47-wheel source staging pass. Synthetic identity/model
fixtures only. Linux image not built: Docker engine pipe unavailable. Next is
bounded Linux candidate verification after Docker starts, then remaining pilot
gates. See docs/CLOUD_STARTUP.md. No deployment or resource-limit increases.

## 19 October: validate all staging inputs before writes

Done: read package, patch, manifest and installer before creating/writing the
target; validate hashes against captured bytes. Retain CLI missing-patch test;
add missing-installer, missing-manifest and existing-output preservation cases.
18 focused staging/notice tests and frontend build pass. No model/container run.
Scope: input failures; not an atomic filesystem transaction for disk-write errors.
Next milestone: explicit guarded Cloud Run entry point.

## CLI collaboration workflow

Added docs/CLI_WORKFLOW.md and AGENTS.md handoff rules: one writer, scoped
changes, explicit commit ownership and independent verification. Also fixed
Python launcher text-pipeline forwarding discovered during documentation work.
Pipeline smoke, five staging tests and frontend build pass.

## Windows CLI runtime launcher

Added scripts/python.ps1 and agent instructions. Five staging tests pass via
launcher; isolated checks pass with empty PATH/redirected LOCALAPPDATA, spaced
arguments, child exit 7, and invalid explicit runtime. Frontend build passes.
Windows PowerShell 5.1 subprocess was blocked by AuthorizationManager in this
environment; verified current PowerShell runtime, without policy bypass.

Final zlib scan: 28 findings (1 high, 1 medium, 26 low). Scout still flags
CVE-2026-85091 on +gather1; no suppression applied. The targeted defect is fixed
and regression-verified independently, not scanner-cleared. Evidence:
tests/inference/results/zlib-scan-20261018.json. Scanner exited zero; temporary
archive cleanup hit a file lock, so no forced deletion was attempted.

## 18 October zlib backport verified

Pinned Debian source plus adapted upstream error-state fix built as local
zlib1g +gather1. Same dynamic regression fails on original image and passes on
patched candidate. Debian zlib tests, nine compression/archive roundtrips,
PyTorch archive check, 14 focused staging tests and frontend build pass.
Image staging/installation fail on changed package, patch or base version.
Evidence: tests/inference/results/zlib-build-20261018.json and zlib-image-20261018.json.
No scanner suppression, model loading, protected API changes or deployment.

## 18 October notice image verified

Completed model attribution packaging and mandatory supplemental-notice gate.
Ten focused tests, real wheel staging, frontend build and bounded Linux notice
verification pass. All nine prior image layers match; only notice layer added.
Evidence: tests/inference/results/notices-image-20261018.json. No model test or
new vulnerability scan. Next: guarded cloud startup implementation independently
of unresolved OS/native release review. No deployment or push.

## 18 October notice packaging

Exact tokenizers 0.23.3 licence files retained with immutable provenance.
Nine focused staging/notice checks pass; actual 47-wheel collection passes
(177 embedded notices, three supplements); frontend build passes. Dockerfile
copies the bundle on future builds; existing image not rebuilt or promoted.
Remaining: model/native attribution and unresolved OS adjudication/remediation.
See services/inference/licenses/README.md. No model benchmark or cloud changes.

## 18 October cloud pilot review

Completed review artifact: docs/CLOUD_PILOT_PLAN.md. All 47 serving wheel hashes
verified against requirements-serving.lock; notice inventory saved. tokenizers
notice gap and existing OS findings remain open. Corrected CPU-allocation
proposal for background key refresh. Documentation/JSON checks pass; unchanged
51 Linux checks, real HTTP smoke and frontend build retained, not rerun.
Next local task: exact-version licence notices and OS adjudication evidence.

## 18 October live Google public-key fetch passed

One bounded Linux request accepted two Google signing keys in 0.505 s; freshness
and missing-credential rejection passed. No real identity token/model/IAM test.
Evidence: tests/inference/results/live-google-keys-20261018.json. No code changed;
reuse 51 Linux checks and the prior unchanged frontend build. Next: consolidate
remaining licence/OS security gates and prepare a concrete gated cloud pilot.

## 18 October startup image verified

Built separate startup-candidate after Docker became available. 51 focused Linux
checks pass in 15.322 s; no model loaded. Eight base/dependency layers match prior
scanned image exactly; only source differs. Prior scan and unchanged frontend
build reused explicitly. Evidence: tests/inference/results/startup-image-20261018.json.
Actual Google compatibility/IAM and OS release gates remain open.

## 18 October artifact startup verified locally; packaging blocked

Added packaged pinned manifest, bounded exact-file hash verification and explicit
loopback startup entry point using existing Qwen Runtime/auth lifecycle. 13 focused
checks and frontend build pass; real snapshot hash check passed in 1.357 s without
model loading. Staged 47 locked dependencies/source. Docker Linux pipe absent;
updated image build remains unverified. See services/inference/ARTIFACT_STARTUP.md.

## 18 October trusted receiver startup composition

Bounded strict operator JSON, immutable one/two caller pairs and shared key
refresh now compose through the existing ASGI lifespan. Cross-paired email/sub
claims reject. Missing keys prevent runtime startup; cleanup remains shared.
40 focused checks and frontend build pass. No models/cloud/Docker. Image staging
includes startup.py, but existing image predates this change. See RECEIVING_IDENTITY.md.

## 18 October cloud header handoff locally verified

Cloud client sends paired platform/application authorization with a tighter
7,168-character token limit within unchanged receiver limits. Synthetic signed-key
handoff rejects absent/stripped/duplicate app authorization. 33 focused tests and
frontend build pass. No model/Docker/cloud operations. Pilot acceptance and next
trusted startup/multiple caller gap recorded in docs/CLOUD_IDENTITY.md.

## 17 October real-model HTTP smoke passed

Four real Qwen HTTP requests passed with pinned identity/512-dimensional vectors,
missing-credential rejection, 2,049-token rejection and subsequent recovery.
Startup 12.68 s; 512-token passage 4.69 s; peak 3.98 GiB; clean exit and cleanup.
Evidence: tests/inference/results/qwen-http-20261017.json. Cloud IAM, real-model
load/timeout behavior and existing OS release gates remain open. No code changed;
reuse the passing focused harness checks and frontend build from 6495f13.

## 17 October HTTP smoke tooling; real run blocked

Added a four-request real-model HTTP profile to the existing guarded container
launcher. Reuses model integrity/resource checks and existing fictional fixtures;
records startup, latency, peak memory, rejection/recovery and cleanup. Seven host
checks, three Linux synthetic harness checks and frontend build pass. Real run
not attempted: 2.03 GiB free versus 4 GiB guard. See services/inference/HTTP_SMOKE.md.

## 17 October Linux auth packaging

Final patched image: 39 Linux checks pass; scan exits 0 with 28 retained OS
findings and no Python findings. Deployment remains blocked.

Packaged verifier/managed refresh and six hash-locked dependencies, retaining all
41 prior hashes. Added actual Linux SIGTERM fixture covering busy inference
cancellation, HTTP 503 and auth thread cleanup. Four staging checks and frontend
build pass. Initial Linux run: 38 passed; signal test expected the wrong exit
status. Reviewed Uvicorn signal re-raise behavior, corrected the assertion, and
focused rerun passed. Scan found three high pyasn1 findings; patched to 0.6.4.
Exact final image, scan and test evidence: services/inference/SERVING_IMAGE.md.
No real model, Google IAM proof, deployment or protected workload changes.

## 17 October managed key refresh

Implemented fixed Google certificate fetch using existing bounded subprocess HTTP,
64 KiB/eight-key bounds, Cache-Control/Age/Date freshness and a 300-second cap.
Managed auth atomically rotates validated snapshots, prevents overlap and limits
attempts to one per 30 seconds per instance. Request paths never fetch. ASGI keys
load before model startup; shutdown cancels/joins refresh work. Failure retains
old keys only until unchanged expiry. 10 new checks + 28 existing checks pass (38),
and frontend build passes. All key responses mocked; no live Google/model/Docker.
Windows event-loop sandbox socket stall diagnosed with bounded traceback; exact
test processes stopped and loopback-permitted rerun passed. No repeated blind retry.
Next Linux packaging and lifecycle validation; release gates remain in
docs/RECEIVING_IDENTITY.md.

## 17 October receiving signature verifier

Local complete slice: GoogleServiceAuth uses google-auth for real RS256 verification
with a bounded expiring trusted key snapshot, exact service subject/email/audience
and strict header/claim validation. ASGI readiness respects snapshot expiry.
Eight new synthetic-key checks plus nine ASGI checks pass (17 total); frontend
build passes. No model/Google requests or installations. Key provenance/retrieval,
rotation lifecycle and Linux packaging remain incomplete; public bind guard stays.
Next: bounded trusted-key retrieval/refresh. Details: docs/RECEIVING_IDENTITY.md.

## 17 October OS advisory and ingress review

Completed scoped primary-source review in services/inference/OS_RISK_REVIEW.md;
no OS change or risk acceptance. Upstream zlib fix exists but installed Debian
remediation/classification unresolved; tar is disputed. Retain scan findings.
Added one regression: five compressed/archive inputs rejected before inference,
then valid recovery. Focused Windows loopback check and frontend build pass.
Docker unavailable; new Linux check pending without repeated retries. Existing
image/eight Linux checks retained. Next: receiving cloud-token verification locally.
Interview checkpoints limited to 1–2 important questions per major milestone.

## 17 October Linux serving packaging

Combined 41-distribution Linux lock preserves all 34 model package hashes and adds
seven serving packages. Offline install/pip check, four staging tests, eight Linux
synthetic ASGI checks and frontend build pass. Non-root and pip removal verified.
Review tightened exact build-context exclusions; a harmless stale-file marker was
excluded by Docker. Cached verification rebuild preserves runtime manifest/config.
No model load or protected workload changes. Security/release review, real-model
HTTP, actual OS SIGTERM and receiving IAM remain open; see
services/inference/SERVING_IMAGE.md for evidence and image identities.

Recovered and reviewed the complete Scout SARIF report after the tool session
ended; process exit status unavailable, scan not rerun. 28 findings (1 high,
1 medium, 26 low), none for Python. High zlib and medium tar have no fix listed.
Deployment remains blocked. Reviewed records: tests/inference/results/serving-image-scan-20261017.json.

## 17 October outbound cloud identity client

Local slice complete: fixed metadata acquisition, expiring per-service token cache,
validated intended invoker configuration and CloudInferenceClient with one shared
15-second acquisition/HTTP budget. No secret fallback or automatic retry.
12 synthetic identity checks, 11 existing loopback transport checks and required
frontend build pass. Reviewed malformed configuration and made cache configuration
read-only. No real tokens, Google requests, models or Docker used.
Actual IAM/receiving auth integration is incomplete; public binding remains blocked.
See docs/CLOUD_IDENTITY.md. Next: Linux packaging/security review after learning quiz.

## 17 October ASGI runtime adapter

TASK-005 serving slice implemented and verified locally: FastAPI/Uvicorn lifespan,
mandatory auth injection, minimal readiness, single-inference admission, bounded
protocol receive/write behavior and shutdown/startup cancellation. Public binding
fails closed pending IAM. Eight Uvicorn/loopback synthetic-engine tests and 15
runtime tests pass; focused dependency-guard recheck and frontend build pass.
No weights, Docker, external APIs or paid resources used.

Created isolated D: test venv inheriting existing packages; installed only the
existing hash-locked h11 0.16.0 there. Shared h11 0.14.0 left untouched and rejected
by the server guard. Tested dependency pins and limitations in INFERENCE_ASGI.md.
Combined Linux hash lock/image/security scan and real OS SIGTERM remain unverified;
Windows tests invoked the signal handler directly. Next: quiz, then bounded Google
ID-token adapter and fail-closed deployment identity. No cloud deployment claim.

## 17 October cloud hosting and identity design

Planning milestone complete: docs/CLOUD_RUN_DESIGN.md maps local components to
application API, IAM-protected CPU inference and bounded ingestion execution.
Reviewed current official Cloud Run identity/runtime/memory/timeout/scaling/budget
and FastAPI lifecycle guidance. Defined separate user/service identities, least
privilege, artifact/startup strategy, pilot resource proposal, cold-start and cost
gates, ordered acceptance criteria and rollback. No resources or IAM changed.

Validated local Markdown links and Obsidian canvas JSON; documentation-only,
so compatible endpoint/frontend results from 16 October are retained, not rerun.
Next: learning quiz, then local production ASGI adapter/lifecycle (step 1).
Dependency pins/review and cloud identity integration remain unimplemented.

## 16 October authenticated local inference endpoint

TASK-005 HTTP boundary slice verified locally: service bearer authentication,
fixed /embed contract, bounded headers/body/connections, total read deadline and
existing independent Runtime compute deadline. Loopback-only integration server;
no public production ingress, managed identity or cloud deployment claimed.
Nine synthetic-engine HTTP tests pass, including existing client round-trip,
wrong credentials before body reads, invalid input/framing, busy/token rejection,
slow headers, hung-worker reaping and deadline enforcement after client disconnect.
Frontend build passes. No real model, Docker or native inputs changed.

Contract: docs/INFERENCE_HTTP.md. Earlier API and client suites retained, not
rerun because their implementations did not change. Next major step requires a
learning quiz, then production ingress/identity design and release-gate review;
private ingestion driver/auth and desktop wiring remain outstanding.

## 16 October bounded service connections

TASK-021 client slice verified locally: fixed-session Auth/published-read client,
prepared runtime-compatible inference client, HTTPS-only defaults, exact route
allowlists, request/response limits, whole-call deadlines, cancellation and helper
cleanup. No automatic retries, credential discovery, redirects or model startup.
11 controlled-loopback transport tests + 23 existing query/context tests pass;
frontend build passes. All 67 real local API checks pass with the coordinator
using SessionClient. Evidence: output/database-checks/service-clients-api-20261016.log.
Test fixtures/stack removed. The restricted loopback run initially failed due to
sandbox network access; authorized rerun passed. No model loads or native changes.

Contract: docs/SERVICE_CLIENTS.md. Inference HTTP handler, remote authentication,
TLS/provider integration and hosted deployment remain incomplete. Next major step:
authenticated HTTP boundary around the existing runtime, preceded by the user's
learning quiz. Privileged ingestion transport and desktop wiring remain separate.

## 16 October query-to-context coordination

TASK-021 internal query slice verified through local Auth/REST; production remains partial.
23 focused tests pass (14 coordinator + nine existing context checks), and
scripts/desktop.ps1 build passes. Tests cover query/template bounds, identity,
invalid vectors, auth failure, cancellation, stale readers, citation integrity,
original ranking and bounded snapshot reads. All provider/session fixtures are
synthetic. Follow-up: 67 real local Auth/REST/Storage checks pass, including the
three new coordinator cases. Log: output/database-checks/query-api-20261016.log.
Temporary stack and generated fixtures removed. No model load or native rebuild.
Prior focused checks/frontend build retained: no implementation changed this run.
Contract: docs/QUERY_SEARCH.md. Next: bounded session/inference transport and
private ingestion identity verification before desktop wiring.

## 16 October authenticated published search and reader

TASK-021 read API slice complete locally: exact cosine search restricted to the
owner's current publications and matching model space; version-bound reader with
exact text/hash/offsets. Real Auth/PostgREST tests cover token tampering, anonymous
access, owner isolation, drafts, replacement, deletion and invalid query vectors.
64 API checks pass (31 retained lifecycle/storage checks + 33 new read checks).
Frontend build passes. Evidence: output/database-checks/published-api-20261016.log
and published-api-frontend-20261016.log. Synthetic vectors prove ordering and API
boundaries, not natural-language retrieval quality. No model or native rebuild.

Fixed the disposable harness's missing private-network database access rule;
startup failures now retain bounded, redacted diagnostics before cleanup.
Contract: docs/PUBLISHED_SEARCH.md. Next: query-text embedding/context integration
and privileged ingestion transport verification. Desktop and cloud deployment
remain separate milestones. Earlier database/model evidence was not rerun.

## 16 October internal ingestion coordinator

TASK-021 coordinator slice complete locally: trusted-context submission commits
source/job/original together; the worker claims, parses, chunks, embeds missing
passages, stages and publishes through existing contracts. Heartbeats cancel
active work after lease loss; recovered attempts reuse committed vectors.
196 database checks pass (169 retained + 27 coordinator checks), plus 10 focused
coordinator unit tests, 27 inference-control tests and the required frontend build.
Evidence: output/database-checks/coordinator-20261016.log,
coordinator-unit-20261016.log, coordinator-runtime-20261016.log and
coordinator-frontend-20261016.log. All embeddings in these runs are synthetic.
No model loaded; native inputs unchanged, so no native rebuild required.

Contract/limits: docs/INGESTION_COORDINATOR.md. Database integration uses a psql
test transport; the DB-API adapter has unit checks, not live-driver/network proof.
Real JWT/API, cloud inference and desktop integration remain incomplete. Next:
verify server identity/transport and connect published search/open adapters.
TASK-021 overall remains partial; no production readiness or deployment claimed.

## 15 October verified text publication

TASK-021 publication slice complete locally: actual-byte validation, immutable
private passage/vector staging, complete-coverage/count checks, atomic ready
transition, prior-version visibility and stale/deleted-worker fencing. See
docs/TEXT_PUBLICATION.md for contracts and limits. 169 database checks pass:
105 existing lifecycle/scheduling checks plus 64 publication checks. Frontend
build passes; Supabase test-role/pgvector bootstrap smoke and Compose validation
pass. Local logs: output/database-checks/publication-20261015.log and
publication-frontend-20261015.log. Synthetic unit vectors, no inference evidence.
No native rebuild required: frontend/native inputs unchanged. Full real API stack
was not rerun. Next: trusted coordinator and published search/context adapter;
whole TASK-021 and desktop import/search flow remain partial.

## 15 October durable ingestion scheduling

TASK-021 scheduling prerequisite complete locally: owner/request idempotency,
atomic version/job creation for an existing source, exclusive leases, crash
recovery, bounded retries, immutable provenance, deletion/replacement fencing,
private worker functions and owner-only status. 96 SQL assertions (51 new) plus
9 concurrent scenarios (5 new) pass; frontend build passes. Evidence/scope:
docs/INGESTION_JOBS.md and output/database-checks/ingestion-jobs-20261015.log.
Historical scheduling-only result; the publication slice above supersedes its
former next step. Whole backend import/search flow remains partial.

## 15 October desktop redesign

TASK-003 visual slice implemented: forest/citron/coral theme, local OFL Manrope,
responsive library/reader/setup/policies, focus restoration and reduced-motion
controls. Five UI tests, lint, frontend and native debug builds pass. Browser
inspection/contrast/reflow evidence: docs/DESIGN_REVIEW_20261015.md. Overall task
remains partial for native/accessibility QA. No push; backend plan unchanged.


## Current three-milestone path (15 October)

| Order | Outcome | Prerequisites | Completion criteria / status |
| --- | --- | --- | --- |
| 1 | Bounded source context and multi-part coverage | Verified saved vectors and source offsets | **Local component complete:** nine focused tests and frontend build pass; saved-vector replay recovers all known evidence in both sets without new inference. See docs/SEARCH_CONTEXT.md. API/desktop integration remains pending. |
| 2 | Backend TXT/MD import → index → search → open → delete | Existing schema/worker; trusted owner/version repository, durable jobs, idempotency, quotas, upload fencing and storage cleanup; relevant privacy/security gates | Test the full backend flow with isolated identities, restart/retry, stale versions and deletion visibility. No hosted provisioning is implied. |
| 3 | Desktop end-to-end flow | Milestone 2, session/credential handling and release prerequisites | Native import, truthful processing states, search/context citations, reader and delete survive restart; verify errors, keyboard access and isolation. |

Later optional work: chat, additional format adapters, ranking refinements and
visual polish. Security/licence fixes remain prerequisites to production, not
optional improvements. TASK-005/007 overall remain partial. Continue milestone 2
with one bounded backend slice; do not rerun model experiments without a relevant
input/configuration change or new evaluation question.

## 15 October paired chunk retrieval evaluation

TASK-005 evaluation slice complete: frozen text-v2 plus six-source/ten-query
boundary stress set, both policies on the same patched Qwen512 image. All 178
requests passed, 0.637–6.972 s each, about 4.00 GiB peak under unchanged limits.
Main dense gate passes: document recall 1.0, MRR 0.9792, strict evidence recall
1.0 versus legacy 1.0/0.9613/0.9911. Stress dense strict recall remains 0.50;
union coverage improves to 0.875. Split conditions and a multi-part passage miss
remain unresolved; no default fusion or production chunking change.

44 evaluation tests, 26 inference tests and frontend build pass. Failure reports
now survive outer timeout; test verifies only owned-container cleanup. Evidence:
tests/evaluation/results/chunk-retrieval-20261015.json and
docs/CHUNK_RETRIEVAL_RESULTS.md. Next: bounded same-source context assembly and
multi-part passage coverage, then ingestion integration; security/licence gates
remain. TASK-005 overall partial. No push or cloud deployment.

## 15 October patched-image checkpoint

Built separate cpu-patched image with Torch 2.14.1+cpu, Transformers 5.19.0,
34 hash-locked wheels and exact OpenSSL/PCRE2 fixes. Rescan completed on 14 October:
28 records (1 high/1 medium/26 low), down from 56/12 high. Remaining zlib/tar
findings are open. Added a 512-token/8-KiB source-slice preparer preserving Unicode
offsets, overlap and stable IDs; existing parser/index and runtime budgets unchanged.
Not yet wired into desktop ingestion. 25 focused tests passed on Windows/candidate
Linux and frontend build passed on 14 October. Baseline six-case export captured.

15 October real checks now pass: six candidate vectors match the baseline within
tolerance, token counts and three tested rankings unchanged. Five chunks (306–500
tokens) return valid embeddings in 3.053–5.883 s, under the unchanged 15 s deadline;
peak 3.95 GiB under the 5 GiB ceiling. Evidence: tests/inference/results/
patched-{compatibility,comparison,chunks}-20261015.json. Memory was freed through
approved transient Linux clean-cache release; no API stop or Docker restart.
Next: retrieval-quality evaluation with new boundaries before ingestion integration,
plus remaining security/licence review. No deployment or push. TASK-005 partial.

## 14 October extended CPU profiles and security review

TASK-005 measured: 512 tokens 5.645 s, 1,024 tokens 13.632 s; 2,048-token item
and 4,096-token batch failed the unchanged 15 s deadline with clean termination,
no OOM. Over-limit rejection plus valid-request recovery passed. Fifty sequential
short queries passed: median 0.710 s, p95 0.935 s, cgroup peak 3.64 GiB.
Evidence: tests/inference/results/qwen-{long,batch,limits,sustained}-20261014.json.
No failures discarded. 21 control/reporting tests pass on Windows and Linux;
frontend build passes. Runtime image unchanged. TASK-005 remains partial.

Scout reviewed that exact image: 56 records (12 high, 7 medium, 37 low), no
suppression. See services/inference/IMAGE_SCAN_REVIEW.md and PROFILE_RESULTS.md.
Next: patch OS packages, compatibility-test a maintained CPU AI stack, rescan,
and evaluate smaller chunks/batches before API integration. No deployment,
existing API changes, Docker restart or GitHub push.

## 14 October real Linux Qwen smoke passed

TASK-005 container smoke slice verified: 2 CPUs, 5 GiB RAM ceiling, no extra swap,
network disabled, non-root and read-only configuration assertions passed. Startup
15.781 s; ten short fictional requests 0.593–0.742 s; cgroup peak 3.87 GiB.
Pinned identity, 512-dimensional normalized vectors and repeated-query consistency
passed. Container exited zero and was removed. Evidence:
tests/inference/results/qwen-container-20261014.json. This supersedes the RAM
blocker below. No runtime code changed; previous 18 control tests/frontend build
were not rerun for this evidence-only update. Next: maximum-input/load profiling
and image security/licence review. Whole TASK-005 remains partial. No API changes,
cloud deployment or GitHub push.

## 13 October isolated inference container checkpoint

TASK-005 remains partial. Built gather-inference:cpu-local on D: from a pinned
Python base and 25 hash-locked Linux CPU wheels. Private bounded JSONL adapter,
verified model export and isolated test launcher implemented. Eighteen synthetic
tests pass both on Windows and inside the Linux container, including malformed
frames, oversized-frame closure, deadlines, child cleanup and explicit recovery.
Actual Docker configuration assertions pass for CPU/RAM/swap/PID limits, non-root,
read-only mounts/root and disabled network. Frontend production build passes.
Evidence: tests/inference/results/container-controls-20261013.json.

Real Qwen container smoke stopped before creating a container at the 4 GiB host
RAM guard; measured free memory then about 2.4 GiB. No real container latency or
peak-memory result yet. Next: rerun the prepared real smoke after memory is free,
then maximum-input profiling and image vulnerability/licence review before API
integration. Existing API containers/settings untouched. No cloud deploy or push.

## 13 October Docker migration verified

Storage prerequisite complete: D:\DockerDesktop\DockerDesktopWSL\disk\docker_data.vhdx
is active after a stopped-source refresh and full SHA-256 verification. Before/
after inventory identical: 9 containers, 64 images, 1 volume. All nine containers
restarted; unrelated application behavior was not tested. Old C: data disk removed
with approval after verification; C: free space about 36.3 GiB. Settings backup and
private inventory/hash evidence live in ignored output/docker-migration.
Next TASK-005: build/measure bounded Linux CPU serving image. Gemma account-level
access remains denied despite valid local login. No model/container build this turn.

## Earlier 13 October setup follow-up (disk blocker superseded above)

HF login saved on D: and API authentication verified; EmbeddingGemma still returns
403 with account-level model-access denial. Same-account access approval needs
checking. Docker engine recovered from startup socket error and responds as
29.7.2. Two settings-based disk moves reverted to C:; D:\DockerDesktop exists but
contains no migrated VHDX. Container builds remain paused. No reset/data deletion.

## 13 October real serving smoke

TASK-005: pinned Qwen persistent host process passed with three fictional inputs,
two CPU threads and 512-dimensional vectors. Startup 14.239 s; requests
0.505/0.669/0.709 s; process reuse and cleanup verified. Post-request RSS 2.54 GiB,
not peak. Evidence: tests/inference/results/qwen-host-20261013.json.
Docker data disk remains on C:; HF login unavailable at checked locations.
Container limits/performance and Gemma comparison remain pending. No runtime
code changed; prior 169-test checkpoint retained, not rerun for documentation.

## 12 October fresh text challenge

TASK-005 second local slice complete: 40 new fictional documents, 64 passages,
64 questions (56 answerable), corpus/labels frozen before inference. Unchanged
Qwen/prompt/chunker/cosine/RRF evaluated at 256/512/1,024 dimensions. The primary
512 candidate passes declared >=0.90 gates: document recall 1.0, evidence recall
0.9911, MRR 0.9613. Five nonperfect dense queries reviewed; all eight absent
questions still return candidates. Do not claim blind or real-world evaluation.
39 evaluation tests, frontend build, pip consistency and v1 regression pass;
twelve v1 raw artifacts still match recorded hashes. See docs/TEXT_V2_RESULTS.md.

Next TASK-005 slice: local serving-container measurement with explicit CPU/RAM/
concurrency/request limits and D: image storage verified first. 512 dimensions is
an experimental candidate, not a final production selection. Exact identifiers,
temporal distinctions and multi-part passage coverage remain quality follow-ups.
No cloud deployment or GitHub push is authorized by this checkpoint.

## 10 October CPU benchmark checkpoint

TASK-005 local slice complete: real Qwen3-Embedding-0.6B export with immutable
revision and safetensors hashes; D:-only environment/cache/temp/output; token
preflight; 256/512/1,024-dimensional dense and RRF evaluation; two/four CPU-thread
memory/latency measurements. 112 worker + 34 evaluation + 4 UI tests, lint,
typecheck, formatting, frontend build and pip check pass. See docs/CPU_BENCHMARK.md
and tests/evaluation/results/qwen-cpu-20261010.json for detailed evidence.

TASK-005 overall stays partial. Historical next acceptance (now measured above): larger frozen unseen text set
and failure review before selecting model/dimensions/fusion, then a bounded CPU
serving-container test. EmbeddingGemma requires user license acceptance; visual
models need image/OCR fixtures. Cloud measurement, production runtime/security,
inference quotas and connected desktop-to-pgvector search remain unverified.
Local model tests do not authorize paid deployment. No GitHub push.

## 2 October planning checkpoint

TASK-022: delivery/security plan documented in docs/DELIVERY_PLAN.md. Planning
only; runtime gates remain open. Ordered next work:

| Task | Status | Acceptance |
| --- | --- | --- |
| TASK-019A | Build and audit verified, 3 October | Base digest + 96 wheel hashes + bootstrap pip lock and declared license inventory. No-cache build, dependency consistency, smoke and actual hash-rejection checks pass. Full image scan completed with open findings; remediation tracked in TASK-023. See services/worker/DEPENDENCY_REVIEW.md |
| TASK-023 | Partial: available patches verified | Patched OpenSSL/PCRE2; removed runtime pip/ensurepip; rebuilt and rescanned: 31 records (4 high, 2 medium, 25 low), down from 51. 21 previous records gone; one newly reported GCC advisory. Remaining unpatched/applicability review and build-tool exposure stay open. Smoke verifies fixes and prompt timeout cleanup. 8 October code-image scan: 29 records (2 high, 1 medium, 26 low), with unchanged package versions; feed differences are not new fixes. See services/worker/IMAGE_SCAN_REVIEW.md |
| TASK-019B | Partial: whole-fetch deadline and page pipeline verified, 8 October | Nine broker subprocess tests and six adapter/pipeline tests added; stuck DNS/connect/TLS, cancellation, output limits, cleanup and controlled HTTP-to-Docker-parser flow pass. Browser/tool egress, production broker confinement and public compatibility remain open. Live use gated by 023. See services/worker/SUPERVISION.md |
| TASK-019C | After 019B | Actual Crawl4AI/yt-dlp invocation on approved public tests, bounded output and truthful fallback |
| TASK-021 | Partial: core Supabase APIs verified, 9 October | 49 database checks plus 31 real Auth/PostgREST/Storage checks pass: owner JWT/RPC, private originals, tombstone visibility, API byte removal before SQL finalization and interruption/retry. Disposable core stack, not complete hosted parity. Upload fencing, background cleanup, byte/rate quotas, processing leases and desktop connection remain pending. See supabase/LOCAL_INTEGRATION.md |

TASK-021 can advance if live-site checks are blocked. No paid AI account needed
for local schema work. TASK-005 remains provider-gated. Follow vertical slices
in DELIVERY_PLAN.md. No runtime work is claimed by this planning checkpoint.

Current checkpoint: local quality checks pass; remote CI execution pending. Links/bookmarks accepted on 28 September. Next: TASK-019B production broker confinement/browser egress, or TASK-021 local persistence while live-use security gates remain open. Chat deferred. Provider/account/live tests remain deferred; no pushes without an explicit request.

| ID | Task | Status | Acceptance / evidence |
| --- | --- | --- | --- |
| TASK-001 | Establish docs, current state and local Git baseline | Done | Canonical documents and links reviewed; 74 baseline paths scanned with no private/generated inclusions; four tests and frontend build pass; local baseline commit contains this record; no remote publish |
| TASK-002 | Validate audience and comparable products | Ready | Record user interviews/feedback or explicitly unvalidated hypotheses; compare primary-source alternatives; decide initial audience/regions |
| TASK-003 | Desktop shell and design verification | Partial | Frontend/native build and four component tests pass; actual visual, keyboard, zoom and motion checks still pending after browser permission denial |
| TASK-004 | Transport-independent text processing contract | Done | 12 standard-library tests pass; strict JSON/base64/UTF-8 and 64 KiB source limit; source offsets, hashes/versioned IDs, overlap and retry determinism verified; no personal imports or cloud writes; see services/worker/README.md |
| TASK-005 | Cloud-oriented embedding evaluation | Partial: paired chunk retrieval measured | 44 evaluation/26 inference tests and frontend build pass. 178 real requests; text-v2 candidate dense gate passes, boundary strict/union evidence 0.50/0.875 exposes context and multi-part misses. No connected HTTP/desktop ingestion. Remaining context/coverage, security/licence, Gemma/visual and cloud measurement gates stay open. See docs/CHUNK_RETRIEVAL_RESULTS.md |
| TASK-006 | Supabase identity and private schema | Needs project configuration | Versioned migrations; supported signup/session/logout flow; enforce audience decision; RLS and two-user isolation tests; secure session storage; quota policy |
| TASK-007 | Text import-to-search vertical slice | Depends on 005/006 | Import TXT/MD -> durable processing -> all passages -> real search -> reader -> deletion; retry/restart/dedup/isolation tests; user-readable errors |
| TASK-008 | Native document formats | Depends on 007 | PDF/DOCX/PPTX parsers; preserved page/slide/section references; long-document and malformed-file cases; scanned pages correctly identified |
| TASK-009 | Photo and OCR retrieval slice | Depends on 007 | JPEG/PNG and scanned text ingestion; SigLIP plus OCR; separate vector spaces and rank fusion; actual source results; category-specific evaluation |
| TASK-010 | Selected-source chat slice | Deferred by user, 28 September | Pin Qwen runtime/quantization; scoped retrieval, streaming, cancellation, citations, missing-evidence and injection tests; measured resource limits |
| TASK-011 | Automated quality checks | Partial | 12 October: 112 worker + 39 evaluation + 14 inference + 4 UI = 169 tests, lint/types/format/build pass. Inference suite added to local check script. Manual CI workflow authored, not pushed/executed remotely. No native E2E claim |
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
## 21 October: cloud ingestion composition

22 October scaling gate: old fixture cleaned by operator. New run failed pre-import
while synchronous warm update waited45s; audit acceptance/rollback timing inspected.
Async update + bounded generation/Ready observation + HTTP probe share startup60s.
61 focused checks/build pass; actual scoped warm/ready/restore test passes, min0/max1
confirmed. No new document/model requests. Operator new-after-cleanup attempt next.

22 October current: pilot handshake connect10 inside approved total15 and scoped
warm-capacity cleanup implemented. Actual worker readonly TLS/role check and 56
focused tests/preview/frontend build pass. Min0/max1 restored after long manual gap;
cost not measured. Cancelled fixture needs admin physical cleanup, then explicit
--new-after-cleanup; no cancelled-job resurrection or hosted retry. Defaults intact.

22 October worker diagnostic milestone: hosted pilot source acknowledged then
cancelled/tombstoned after temporary pre-staging failure (operator SQL: one attempt,
no staged text/passages; receipt: zero inference). Added safe worker step/reason
retention; 30 worker/runner checks and frontend build pass. Offline pinned-tokenizer
fixture replay reaches ready. Old root cause needs existing Postgres error logs;
no hosted retry. Cancelled source must not resume; admin physical cleanup pending.

22 October cloud action approved/applied: Gather min=1/max=1 temporarily; image,
resource limits and private caller policy verified, authenticated readiness passes.
16 runner tests and frontend build pass. Original import receipt unchanged;
operator guarded resume next. Restore min=0 after pilot is still pending and must
be completed. Idle billing disclosed; no automatic cost cap/timer claimed.

22 October recurring startup block: resumed import not reached; unchanged receipt.
Second platform 429 followed by startup verified in logs. Warm-instance proposal
is concrete but awaits cost/capacity approval; no scaling changes. Sixteen runner
checks and frontend build pass for safe readiness IO diagnostics. Full flow pending.

22 October import blocker: no save receipt found by operator; measured connection
setup ~9 s cannot fit five-second whole-call bound. Explicit user-approved pilot
override 15 s implemented; production default, SQL and model limits unchanged.
Guarded request-ID-preserving resume + safe diagnostic codes added. 40 focused
checks, non-mutating hosted function lookup (55000, 5.703 s) and frontend build pass.
Full hosted flow and administrator cleanup remain pending. See HOSTED_FLOW_PILOT.md.

22 October startup diagnostic: actual platform /ready 429 "no available instance"
preceded completed startup; subsequent readiness-only probe passes. Both Auth users
already verified by operator. Added safe status/startup-only mode; 11 runner checks
and frontend build pass. Full hosted flow and physical cleanup remain unverified;
no capacity or inference-limit changes. See docs/HOSTED_FLOW_PILOT.md.

22 October diagnostic: hosted run failed before import at A sign-in. Email
confirmation/provider verified; cause unknown. Auth-only mode and bounded fixed
Auth error codes implemented. 25 focused checks and frontend build pass; operator
must run --check-auth before another full pilot. No model or credential changes.

22 October hosted-runner milestone prepared: check_hosted_flow.py reuses real
Auth, LibrarySession, DB transport and cloud provider. Seven new controls + six
session regressions pass; preview, tokenizer parity (3 cases) and frontend build
pass. Live execution awaits operator user-password prompts. Cleanup finalizer is
admin-only and must follow visibility deletion; no completed hosted flow claim.
See docs/HOSTED_FLOW_PILOT.md.

22 October current checkpoint: credential helpers/read-only probe verified.
14 focused checks and frontend build pass; operator stored DPAPI bundle, both
restricted hosted logins and decryption now checked by agent. Public project key
and hosted Auth session remain missing; no hosted document/model calls performed.
See docs/HOSTED_SUPABASE_SETUP.md. Supersedes earlier build-blocked notes below.

22 October latest partial: operator reports hosted password setup success. Added
local Windows DPAPI credential store/loader with hidden-prompt command; 12 tests
and synthetic real DPAPI roundtrip pass. User must store credentials locally;
no hosted import/search evidence yet. Password rotation deferred by user. Required
build still pending after approval-review usage-limit rejection; uncommitted.

22 October follow-up partial: operator password setup helper prepared for the
user-created Sydney roles. Six local checks and preview pass. Live TLS/password
update/login unverified; frontend build blocked by approval-review usage limit.
No commit yet. See docs/HOSTED_SUPABASE_SETUP.md.

Latest prerequisite complete locally: bounded database driver with separate
admission/worker identities and fixed role/function selection. Eight new tests
plus ingestion/library regressions (24 total), five disposable real-driver
integration groups and frontend build pass. Initial lease timestamp encoding
failure fixed; both test containers removed. Hosted config/TLS, approved production
driver packaging and application HTTP remain open. See docs/DATABASE_TRANSPORT.md.

Subsequent milestone: authenticated library boundary implemented in
services/worker/library_session.py. 17 new real local Auth/PostgREST assertions
pass: forged JWT blocks work, verified owner propagation, duplicate import,
queued/ready status, two-user isolation, exact reads, foreign replacement rejection
and immediate deletion visibility. Existing stack checks also pass and clean up.
41 distinct focused checks (30 library/ingestion/search + 11 transport) and frontend
build pass. Synthetic vectors, test-only admission transport; no hosted DB driver,
public HTTP API, signup or desktop wiring claim. See docs/LIBRARY_SESSION.md.

Done for developer pilot only: cloud_provider.py loads a hash-verified tokenizer,
CloudInferenceClient accepts a trusted identity-matching provider (metadata default
unchanged), and check_cloud_ingestion.py reuses the coordinator and search against
real cloud embeddings and disposable SQL. Two model requests; duplicate/ready/
search/open/foreign-owner SQL read/deletion checks pass. 22 composition/identity
and 35 ingestion/search/transport tests pass, three tokenizer parity checks and
frontend build pass. Initial restricted-loopback tests failed then passed with
owning-user access. First pilot failed with a 35.98 s cloud request; separate
bounded readiness preflight precedes successful repeat. No limits raised.
Evidence/boundaries: docs/CLOUD_INGESTION_PILOT.md. Not hosted JWT/DB, desktop,
quality evaluation or cold-start resolution. No pushes or protected API changes.
