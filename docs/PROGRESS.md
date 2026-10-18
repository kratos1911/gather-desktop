# Rebuild progress

Final zlib scan: 28 findings (1 high, 1 medium, 26 low). Scout still flags
CVE-2026-85091 on +gather1; no suppression applied. The targeted defect is fixed
and regression-verified independently, not scanner-cleared. Evidence:
tests/inference/results/zlib-scan-20261018.json. Scanner exited zero; temporary
archive cleanup hit a file lock, so no forced deletion was attempted.

## 18 October: zlib fix built and tested

Resumed after approval-review usage limit (previous compiler build never ran).
Read stronger Debian maintainer evidence; chose narrow upstream backport instead
of claiming not-affected. Isolated toolchain first lacked build-essential; added
that declared build prerequisite. Offline source builds used one CPU/1 GiB.
Unpatched regression failed as required; patched source and actual installed
library passed. Debian standard/shared/64-bit tests passed. New zlib-candidate
contains only local runtime package, not compiler tools. Compression/PyTorch
archive checks, 14 focused tests and frontend build pass. Artifacts stay on D:.
Initial Scout request rejected due metadata egress; user explicitly approved
that scan before retry. No bypass, model run, push or deployment.
See services/inference/zlib/README.md for reproduction, hashes and limits.

## 18 October model attribution and Linux package verification

Retained pinned model card (hash matches model-manifest) and official Apache
licence; five supplements now packaged. Staging rejects missing required
upstream attribution. Ten focused tests and frontend build pass. Preflight:
Docker Linux available, about 3.60 GiB free RAM and 85.27 GiB D: space. CIM needed
read permission. Initial network-none build missed cache and failed at apt;
restoring original network mode reused every existing layer and built in seconds.
No package pin changes. Isolated 128 MiB/one-CPU, read-only, network-none container
verified all notice text hashes, 47 wheels, 177 notices, five supplements and
non-root user; 87 OS copyright files present. Existing nine layers identical.
Image and bundle hashes saved in notices-image-20261018.json. Existing images,
models, API containers and cloud resources unchanged. Copyright presence is not
complete native licence clearance; unresolved OS findings retained.

## 18 October missing licence corrected and packaging implemented

Fetched exact tokenizers upstream tag tree and licence files; recorded hashes
and immutable URLs. Added offline locked-wheel notice collector and Docker COPY.
Focused checks reject modified/missing wheels and changed/escaping supplements.
Nine checks plus frontend build pass; real 47-wheel staging includes 177 notices
and three supplements. No existing image modified; container build verification
remains pending. Debian bug 1146895 still lists our version as affected with no
fixed package; retained findings and did not silently patch/remove native code.
No paid deployment, model load or protected workload mutation.

## 18 October: bounded cloud pilot proposal and licence inventory

Reviewed official Cloud Run CPU allocation, pinned model licence declaration and
Debian zlib status. Found request-based CPU incompatible with assuming timely idle
key refresh. Proposed instance-based allocation with explicit cost approval;
no settings applied. Inventoried and hash-verified all 47 current serving wheels;
tokenizers has no detected notice file. Initial 41-wheel older staging directory
was identified and replaced with current auth staging before recording evidence.
No runtime changes, model/Docker tests, paid resources or protected workloads.
Existing verification retained; JSON/lock/document consistency checked locally.
See CLOUD_PILOT_PLAN.md for acceptance, sequencing and teardown boundaries.

## 18 October: real public-key endpoint compatibility

Ran one live key fetch through the existing ManagedGoogleServiceAuth in an
isolated 256 MiB/one-CPU/64-PID read-only non-root startup-candidate container.
Exit zero, two keys accepted in 0.505 s; remaining TTL 299.495 s. Credential-free
request to Google public certificates only; no token, user content or model.
Missing authorization still rejected. Container removed automatically. No code
changes, new installs, paid resources, protected API changes or push. Existing
model/Linux test/frontend evidence retained; deployed IAM remains unverified.

## 18 October: Docker packaging blocker resolved

User opened Docker; Linux engine and all nine API containers confirmed running.
Preflight 2.69 GiB RAM/85.27 GiB D: free permitted 512 MiB synthetic checks, not
a real-model load. Built startup-candidate from cached dependencies, then all
51 packaged Linux checks passed (15.322 s). Compared rootfs layer hashes: eight
base/dependency layers unchanged, final source layer changed. Retained dated
17 October scan evidence rather than repeating it; 28 OS findings remain.
No source/frontend changes, model run, API intervention or Docker settings changes.

## 18 October: verified model artifact entry point

Portable manifest derived from prior verified snapshot, retaining ten exact hashes
and sizes. New entry point rejects invalid policy/artifacts before constructing
Runtime; public bind stays blocked. First sandbox lifecycle test invocation stalled
in the previously observed asyncio path; stopped only its test PIDs, then 13 focused
checks passed with permission. Frontend build passed. Real artifact hashes checked
in 1.357 s, no inference. Build context staged with unchanged lock. One Docker
preflight found no Linux engine pipe; no retry or protected workload changes.

## 18 October: explicit API/worker receiver policy

Added immutable paired email/subject receiver configuration and bounded strict
startup JSON. Reused the existing verifier, managed refresh and ASGI lifecycle;
both callers share one key fetch/thread. Rejected ambiguous legacy two-invoker
configuration instead of silently accepting only one. Four startup tests plus 32
existing identity/lifecycle checks and four staging checks pass; frontend build
passes. No model loading, network key fetch, image rebuild, deployment or push.

## 18 October: Cloud Run token handoff preparation

Reviewed Google primary documentation: X-Serverless-Authorization takes platform
precedence when both headers exist. Added dual-header cloud client path, retaining
independent application signature checks and all deadlines. 33 focused local
identity/verifier/transport checks and frontend build pass. Deployed IAM/header
preservation remains unverified; public binding blocked and existing image predates
this code. No model rerun, paid resources, Docker workload change or push.

## 17 October: real CPU inference over HTTP verified

User authorized unused-app closure, then specifically approved one-time WSL file-
cache release. Closed windowless Chrome background processes. Cache release
initially left Windows at 2.92 GiB; after reclaim settled, 6.05 GiB passed the guard.
Nine protected APIs were running; mailflow-rules-api and email-api showed recent
restarts of undetermined cause. No stop/restart or persistent settings commands
were issued. Ran the existing guarded HTTP profile once: all assertions passed,
no OOM/timeout, owned test container cleaned up. Startup 12.681 s, four requests
0.819/0.781/4.688/0.683 s; peak 4,275,261,440 bytes. Retained real-model evidence
and limits in services/inference/HTTP_SMOKE.md. No source changes, so prior
harness checks/frontend build reused. No deployment or push.

## 17 October: bounded HTTP check prepared

One preflight confirmed Docker/image, model paths and 85.3 GiB free on D:. CIM
RAM query was unavailable; psutil reported 2.03 GiB. Did not retry unchanged
conditions or close apps. Implemented HTTP profile through the existing container
launcher and verified seven host checks plus three Linux synthetic checks.
Frontend build passed. No real-model performance or cloud readiness claimed;
services/inference/HTTP_SMOKE.md records the command, boundaries and blocker.

## 17 October: Linux auth image and signal cleanup

Final patched image: 39 Linux checks pass; scan exits 0 with 28 retained OS
findings and no Python findings. Deployment remains blocked.

Built a separate receiving-auth candidate using cached wheels plus six pinned
additions. Synthetic tests verify signature admission, refresh expiry and actual
Linux SIGTERM cancellation/join. The first signal assertion failed because Uvicorn
re-raises SIGTERM after graceful cleanup; changed the fixture to observe cleanup
inside lifespan and expect signal exit, then its focused rerun passed.
Four host staging tests and frontend build also passed. Initial scan exited zero
but reported 31 findings, including three high pyasn1 0.6.3 issues. Downloaded
0.6.4 from PyPI without changing shared environments; rebuilt the isolated candidate.
Final verification is recorded in services/inference/SERVING_IMAGE.md. No findings
suppressed, no models loaded, no cloud provisioning or API workload changes.

## 17 October: managed Google-key refresh lifecycle

Added fixed-endpoint key retrieval, strict upstream cache freshness and snapshot
rotation under one lifecycle thread. No request-triggered fetch or stale extension;
initial key failure prevents model startup, shutdown cancels/joins work. Thirty-
second minimum attempts preserve resource bounds during unknown-key traffic/outage.
38 focused mocked/synthetic and loopback checks plus frontend build pass. A sandbox
event-loop socket stall was traced and the exact tests rerun with loopback access;
no model/API/container interventions. No live Google evidence claimed. Linux
packaging, real platform header/IAM checks and OS findings remain open.

## 17 October: receiving-token verifier

Reused installed google-auth/cryptography; recorded exact local dependencies.
Added expiring immutable RSA public-key snapshot and pinned account subject/email,
strict RS256/header/claim checks and library signature verification. No request-led
key fetching, credential discovery or fallback. Readiness now reflects auth-key
expiry. Eight new signed synthetic-key tests and nine ASGI tests pass; frontend
build passes. Public binding remains blocked. Google key provenance/lifecycle and
Linux image integration remain separate, explicit gaps in RECEIVING_IDENTITY.md.

## 17 October: OS advisory review and focused ingress regression

Read Debian trackers and zlib maintainer/fix sources. Corrected the interpretation
of "no fix": upstream code fix exists, but vendor package and affected-range
resolution remain open. Tar dispute and extraction prerequisites recorded without
silently dismissing the scanner. No arbitrary OS removal or custom backport.
Added compressed/archive rejection regression: five cases never call inference,
then valid recovery succeeds. Focused host test and frontend build pass. Docker
engine absent at one preflight; used existing D: test environment, no model loads,
restart, protected workload changes or repeat scan. OS_RISK_REVIEW.md records limits.
Updated learning rules to keep interview questions bounded and development moving.

## 17 October: Linux serving packaging and synthetic verification

Reused the cached CPU wheels and base/OS layers. Downloaded seven exact serving
wheels to D:, recorded hashes/licence metadata and generated a separate combined
lock. Added serving staging to existing preparation script; old model hashes
cannot drift, model materialization is skipped and source inclusion is explicit.
Changed digest implementation to bounded streaming for the available Python 3.10.
Review tightened directory exceptions; a marker exclusion check and cached rebuild
confirmed identical runtime layers. Four staging tests, eight Linux ASGI tests,
offline dependency consistency, non-root/pip-removal smoke and frontend build pass.
No model loads, shared dependency changes, cloud deployment or protected API changes.
Remaining security and deployment gates are in services/inference/SERVING_IMAGE.md.

Scout's completed SARIF report recovered after its tool session ended; exit code
was unavailable. Reviewed 28 findings: 1 high/1 medium/26 low, no Python-package
findings. No suppression or approval: unfixed zlib/tar remain blockers. Raw report
checksum and compact reviewed records retained. No repeat scan was necessary.

## 17 October: outbound managed identity client

Added bounded metadata token acquisition using the existing isolated transport,
expiry/audience/caller cache checks, intended invoker policy validation and explicit
CloudInferenceClient. No shared-secret fallback. Review fixed unhashable malformed
policy handling and invalid timeout handling; provider configuration is read-only.
12 mocked identity tests and 11 existing loopback transport tests pass, as does the
frontend build. Synthetic JWTs do not verify signatures or deployed IAM. No cloud
access, models, Docker, UI or protected workloads changed. Public binding remains
blocked. Next Linux packaging/security and cloud gates: CLOUD_IDENTITY.md.

## 17 October: ASGI adapter and lifecycle verification

Reused installed FastAPI/Uvicorn with explicit auth, lifespan model ownership,
readiness and one active inference. Added pinned protocol hooks for total TCP
receive deadline and header limits; shutdown signals cancel active/startup work.
Runtime.start now accepts an optional cancellation event using existing cleanup.

Dependency review found shared h11 0.14.0 affected by upstream GHSA-vqfr-h8mv-ghfj.
Created D: system-package-inheriting venv and hash-verified h11 0.16.0 using the
existing model lock. No shared installation modified. Added exact local dependency
pins and startup rejection for unreviewed h11/Uvicorn versions. Full Linux lock,
security scan and image validation remain open.

All eight loopback ASGI tests and 15 focused runtime tests pass; dependency/public
bind guard rechecked after review. Frontend build passes. No Docker/model workload
needed. Actual Linux signal delivery and real-model HTTP behavior unverified;
Windows test directly invokes SIGTERM handling. No public binding/deployment/push.

## 17 October: production hosting and service identity plan

Completed CLOUD_RUN_DESIGN.md after repository inspection and official-document
research. Proposed FastAPI/Uvicorn single web process with existing Runtime child,
Google ID-token invocation for private inference, separate Supabase user identity,
and bounded ingestion execution retaining PostgreSQL job authority. No provisioning.

Found two deployment gaps explicitly: current localhost/stream container is not
Cloud Run ingress-ready; measured local startup can consume the entire current
client deadline. Plan requires cold-start measurement/UX or separately approved
warm capacity before release. Memory filesystem, image storage/licence/security,
IAM isolation, cost limits, shutdown, staged rollout and rollback documented.
Local links/canvas JSON checked; no runtime or frontend changes warranting reruns.
Prior 16 October verification retained. Next step is local ASGI adapter after quiz.

## 16 October: authenticated loopback inference endpoint

Added a local HTTP adapter around the unchanged Runtime with explicit service
secret injection, constant-time auth checks, input/header bounds, four connection
slots, no request queue for model work and a five-second total receive deadline.
Runtime retains its at-most-15-second computation deadline and cleanup. No auto
model start/restart, weights, cloud spending or shared workloads touched.

Eight initial tests passed; review added a client-disconnect case demonstrating
independent server deadline/reaping. All nine endpoint tests now pass with the
synthetic engine and real local HTTP/client transport. Frontend build passes.
Unchanged database/client/model suites retained. Public server/TLS/IAM selection
and real-model-over-HTTP validation remain unverified. No push.

## 16 October: bounded session and inference client adapters

Added fixed-service JSON clients using isolated request helpers. Five-second
session and 15-second inference deadlines include DNS/TLS/body; cancellation
kills/reaps only the request helper. Limits, fixed routes, no redirects/retries,
credential validation and safe errors documented in SERVICE_CLIENTS.md. Inference
client targets the existing runtime JSON contract; no HTTP server exists yet.

11 controlled-loopback tests, 23 query/context tests and frontend build pass.
First loopback run could not connect under sandbox restrictions; approved network
run passed. Review added helper-reaping/environment assertions, which also pass.
Docker preflight: engine 29.7.2, all five pinned images cached, about 2.05 GiB RAM
available, no preexisting test stack. All 67 API checks passed with the new session
adapter; exact fixtures and disposable stack removed. No unrelated workload,
model, native build or paid resource changes. Learning quiz preference saved in
RULES.md. No push. Remaining boundaries and next task in MEMORY.md.

## 16 October: query coordinator API verification unblocked

Docker 29.7.2 ready; all five pinned images cached, about 2.99 GiB RAM available,
94.6 GiB D: free, no existing test stack. Initial sandbox pipe access was denied;
authorized Docker access succeeded. One isolated run passed all 67 API checks,
including the three coordinator cases. Exact context, second-user isolation and
replacement during rank/open verified using injected synthetic vectors. Fixtures
and temporary stack removed successfully. Evidence in TASKS.md. No source changes,
model loads, API workload changes or push. Prior 23 focused tests and frontend
build remain applicable; no redundant rerun. Production transport remains next.

## 16 October: query embedding and bounded result context

Connected the existing query inference contract, authenticated published RPCs and
context assembler through an internal coordinator. Review fixed seed ranks after
source grouping and stale-result omission. 23 focused tests and frontend build
pass; syntax-check of updated API harness passes. No SQL/UI/model changes.

One preflight found Docker's Linux engine pipe absent; RAM inspection was denied
by the sandbox, D: had about 94.7 GiB free. No heavy run or unchanged retry was
attempted. Three real-session coordinator cases are prepared but unverified.
Explicit synthetic providers are test-only; no live semantic-search claim.
User action to unblock: start Docker Desktop and wait for its Linux engine.

## 16 October: authenticated published search and reader

Added owner-derived exact pgvector search and version-required text opening via
the existing PostgREST/JWT boundary. 64 real Auth/REST/Storage checks and frontend
build pass using synthetic users/documents/vectors. Drafts, other owners, old
versions and deleted sources remain inaccessible as specified. See TASKS.md.

The first stack run failed before Auth readiness. A diagnostic run identified a
missing pg_hba network rule introduced by the earlier minimal database startup
script. Restored access only for three test service roles on directly connected
private networks; the database still publishes no host port. The corrected run
passed and removed its stack/fixtures. Added redacted startup diagnostics so the
next startup failure is actionable without a diagnostic-only rerun.

Preflight: Docker 29.7.2, all images cached, 2.56 GiB available RAM and 94.66 GiB
free on D:. Protected workloads untouched; no models or paid resources used.
Real query embedding, privileged ingestion transport, desktop wiring and hosted
release remain unfinished. Canonical and Obsidian-linked notes updated locally.

## 16 October: internal ingestion coordinator

Continued clean b23cd01 on codex/durable-ingestion-jobs. Added version-bound
original handoff and restricted admission/read functions, parameterized DB-API
adapter, existing-parser/chunker/embedding orchestration and runtime cancellation.
Review added job-wide request preflight and reuse of committed vectors on recovery.
196 database checks, 10 coordinator unit tests, 27 inference controls and frontend
build pass. An actual ten-second heartbeat cancelled a synthetic request after
deletion; interruption after one stored vector recovered without re-embedding it.
Tests use protocol fixtures, not model-generated semantic vectors.

Docker was initially unavailable. After the user started it, the sandbox denied
pipe access; approved escalation enabled the same isolated harness. Preflight:
Docker 29.7.2, cached database image, 2.44 GiB free RAM, D: 94.69 GiB free.
Only disposable 256 MiB database work and synthetic process tests ran; no models,
app closures, protected API changes or paid resources. Frontend/native files were
unchanged. Canonical state, concepts and Obsidian flow updated. Local commit only.
Remaining integration boundaries and evidence are recorded in TASKS.md.

## 15 October: verified text and atomic publication

Extended the clean c7bdd9f checkpoint with verified UTF-8 original bytes, private
passage/pgvector staging and atomic published-version/ready activation. Reviewed
and fixed premature ready transitions, Unicode empty-text agreement, transactional
rollback coverage and Windows checkout line endings for the test startup script.
169 database checks pass (105 retained + 64 new); frontend build passes. Separate
test-role bootstrap/pgvector smoke and Compose validation pass. Full API stack
was not rerun; no live embeddings or semantic quality measured. Evidence paths and
remaining work are in TASKS.md, contracts in TEXT_PUBLICATION.md.

One preflight: Docker 29.7.2, 4.18 GiB available RAM, 94.69 GiB free D: storage,
required PostgreSQL/pgvector image cached. Only disposable named test containers
were used, with no shared API changes, models, app closures or paid resources.
No native rebuild: native/frontend inputs unchanged. Canonical state and linked
Obsidian concept/flow notes updated. Changes committed locally only.

## 15 October: durable ingestion scheduling prerequisite

Added a private Postgres job ledger tied to immutable source versions, with
idempotent enqueue, single live lease, capped retries/heartbeat, fenced recovery,
owner-only status and transactional cancellation on replacement/deletion.
96 SQL assertions plus 9 concurrency scenarios pass in the isolated 256 MiB
database harness. Frontend build passes. One preflight: Docker 29.7.2, image
cached, 3.89 GiB free RAM, 94.69 GiB free on D:. No model calls or protected API
changes. Existing tombstone/cleanup checks remain intact. New scheduler limits
and honest gaps documented in INGESTION_JOBS.md. Ready/publication, original
admission, real JWT/worker integration and desktop flow remain unfinished.

## 15 October: expressive desktop preview

Implemented the user-requested GSAP-inspired visual direction with original CSS,
licensed local typography and existing Motion. Fixed tested return-focus handling
and reduced-motion sample behavior. Five UI tests, lint and frontend/native debug
builds pass; scoped browser checks recorded in DESIGN_REVIEW_20261015.md.
No model tests, Docker changes, API changes or remote push. Native QA remains open.


## 2026-10-15 — bounded source context with no new inference

Verified clean checkpoint 33f5716. Implemented one-source-per-result grouping and
immediate contiguous-neighbor expansion with exact owner/version/hash citations.
Bounds: 100 candidates/snapshots, five sources, 8 KiB/window, 32 KiB total text;
reserve seed bytes first and report omissions. All input identities and ranges
are validated before any result. It remains a pure component, not connected auth,
repository, API or UI behavior. Review added explicit malformed-Unicode rejection
and a regression test for preserving later seeds' reserved byte budget.

Replayed hash-verified saved vectors with unchanged model/prompt/chunks/rankings.
Known boundary context coverage reached 1.0 from 0.875 top-five union coverage;
text-v2 stayed 1.0 with no per-query coverage regressions. Expanded context is a
different metric from original strict passage recall; no ranking improvement is
claimed. Ten absent queries still return context. Stress sources have only two
chunks, so larger/unseen-document coverage remains unverified. Evidence and
limits: SEARCH_CONTEXT.md and tests/evaluation/results/search-context-20261015.json.

Nine focused tests and frontend build pass. No heavy preflight/model run was
needed; no Docker, app/process, dependency or cloud changes. One agent, no new
inference calls, no push. Updated three-milestone plan and linked Obsidian notes;
next is backend coordination with trusted owner/version reads and durable lifecycle
safeguards. Existing privacy/security and deployment gates remain in force.

## 2026-10-15 — paired chunk-policy retrieval measured

Added frozen six-source/ten-query fictional boundary stress alongside unchanged
text-v2. A separate tokenizer-only authoring pass deliberately positioned two
conditional spans across candidate boundaries; disclose this as structural,
non-blind development evidence. Legacy/candidate layouts, source labels, protocol,
request order and pinned image are hashed before inference. Both policies share
model/query configuration; inference receives no labels. Existing exports/indexes
are preserved. Strict evidence misses are retained; supplemental union coverage
requires continuous same-source intervals. Added stale-fixture, label-preservation,
legacy-equivalence and gap/overlap/source-isolation checks.

Real run: 178 requests, 284.98 s overall, 13.78 s startup, request range
0.637–6.972 s, about 4.00 GiB cgroup peak, no timeout/OOM, exit zero; owned
container removed. text-v2 dense main gate passes: recall 1.0, MRR 0.9792 and
strict evidence 1.0; paired legacy 1.0/0.9613/0.9911. Boundary strict evidence
stays 0.50 while union improves to 0.875. Three questions have intentionally split
conditions; another multi-part question misses both late passages. All ten absent
queries return candidates. All query regressions and remaining misses reviewed in
CHUNK_RETRIEVAL_RESULTS.md; full metrics/hashes in
tests/evaluation/results/chunk-retrieval-20261015.json. RRF remains a comparator.

Docker was closed, then failed initial startup with inaccessible sailor-ingest.sock.
User approved closing/reopening the failed app; Explorer launch recovered engine
29.7.2 without reset/deletion/settings changes. Released clean Linux cache once;
RAM guard still stopped the first ready-engine attempt. After user authorized
unused-app closure, background Teams/WhatsApp were stopped and 4.10 GiB became
available. Chrome remained open. No individual API stop/update commands. No
container was created for failed engine/low-RAM attempts. No cloud or downloads.

44 evaluation tests, 26 inference tests and frontend build pass. Independent code
review identified outer-timeout evidence loss; fixed it and added a mocked test
verifying failure persistence and owned-only cleanup. No runtime/native assets
changed, so image/executable rebuilds were unnecessary. Next: bounded same-source
context assembly and multi-part passage coverage before ingestion integration.
TASK-005 remains partial; security/licence gates stay open. Notes and Obsidian
flow updated. Local checkpoint only; no GitHub push.

## 2026-10-15 — real patched-model compatibility and chunk timing passed

User authorized clearing unnecessary background apps and running the remaining
checks. Requested graceful window closure for Task Manager and Settings; both
accepted the request but their processes were later still present, so full app
exit is not claimed. Preserved the session, Docker and unrelated API containers.
The significant memory relief came from two explicitly approved, transient
clean-page-cache releases inside Docker's Linux environment. Host free RAM reached
4.81 GiB before compatibility and 5.08 GiB before chunks. Two intermediate chunk
attempts stopped at the unchanged 4 GiB guard; no test container was created for
those attempts. Windows reclaimed Linux memory with a delay. No persistent setting
changes, forced app termination or Docker restart.

Candidate image 5d84bdf24729 passed six real Qwen compatibility cases: exact token
counts, minimum paired cosine 0.999999999996, maximum coordinate difference
4.33e-7, unchanged three tested rankings. Five chunks (495/494/380/500/306 tokens)
passed in 5.883/4.569/4.127/4.591/3.053 seconds, below the 15 s deadline. Both
profiles exited zero without OOM; peak cgroup memory about 3.95 GiB under the
unchanged 5 GiB ceiling. Both owned test containers were removed. Curated reports:
tests/inference/results/patched-{compatibility,comparison,chunks}-20261015.json.
No private document inputs. No changes to runtime, models, dependencies or desktop
assets; prior 25 control tests/frontend build were not repeated for evidence/docs.

All nine unrelated API containers were listed running during the check; two had
recent start times, so uninterrupted service or health is not claimed. This work
did not issue stop/restart/update commands against them or inspect their APIs.
Next: retrieval-quality evaluation with new chunk boundaries before ingestion
integration; unresolved image findings and licence review still gate promotion.
TASK-005 remains partial. Updated canonical notes, Obsidian concepts and flow map.
No cloud resources or GitHub push.

## 2026-10-15 — save patched candidate; real checks still RAM-blocked

Recorded the 14 October upgrade work: separate cpu-patched image, Torch 2.14.1+cpu,
Transformers 5.19.0, 34 hash-locked Linux wheels and exact OpenSSL/PCRE2 fixes.
Transformers wheel matched its PyPI checksum; installed dependency consistency
passed. Added deterministic <=512-token/8-KiB source slicing with bounded overlap,
exact offsets, versioned IDs and explicit failures. Existing parser/index formats
and runtime budgets unchanged. 25 focused tests passed on Windows and candidate
Linux; frontend build passed. Baseline six-case vector export succeeded; candidate
comparison and chunk timing have not run due to the RAM guard.

Completed rescan: 172 packages, 28 findings (1 high/1 medium/26 low), down from
56/12 high. No Python records remain. Unfixed zlib/tar findings stay open. Raw
SARIF hashed and curated inventory saved; locked temporary-archive warning
retained without deletion/restart workaround. Candidate is not deployment-approved.

15 October recheck: Docker 29.7.2 available, free RAM 2.1 GiB. Kept the 4 GiB
guard. Closing Docker would prevent these tests and affect existing APIs, so it
was not closed. All storage remains on D:, baseline image retained, no unrelated
API/container changes or cloud provisioning. No GitHub push.

## 2026-10-14 — sustained/long-input profiles and image security review

Extended the trusted launcher with long, batch, limits and sustained profiles;
it now retains failures/unexecuted cases and exits nonzero for failed profiles.
Added three reporting regression tests and a read-only scripts mount for the
control suite. 21 tests passed on Windows and inside Linux; frontend build passed.
No runtime/image changes, so no image or native desktop rebuild was needed.

Pinned AutoTokenizer confirmed the stress text's extra special token; corrected
input construction before running. Real 512/1,024-token requests took 5.645/13.632 s.
The 2,048-token item and two-item maximum batch timed out at the existing 15 s
deadline; no OOM and cleanup succeeded. Token-overflow rejection/recovery passed.
50 sequential short queries passed: median 0.710 s, nearest-rank p95 0.935 s,
range 0.637–1.042 s, cgroup peak 3.64 GiB. Shared-machine, artificial input evidence,
not multi-user capacity or retrieval evaluation. Temporary RAM guard stops were
respected; subsequent attempts ran once memory cleared. All owned containers removed.

Scout 1.24.0 indexed 163 packages: 56 records (12 high/7 medium/37 low) across
16 vulnerable packages. Raw SARIF hashed; curated inventory and triage recorded.
Cache/temp stayed on D:. Scanner reported a locked temporary archive on cleanup;
no deletion/restart workaround. Primary PyTorch advisory and Transformers fix
reviewed. Safetensors/offline/pinned-config restrictions reduce exposure but do
not clear package vulnerabilities. Dependencies unchanged; remediation/rescan is
the next gate. No deployment, unrelated API changes or GitHub push.

## 2026-10-14 — real Linux CPU inference smoke verified

After Docker was opened and host RAM reached 4.20 GiB, the prepared isolated
container completed ten fictional requests. Startup 15.7807 s; request range
0.5934–0.7419 s; whole launch/run/inspect interval 23.7699 s. Cgroup peak
4,155,457,536 bytes (3.87 GiB) includes container-accounted memory, not just model
process RSS. The 2-CPU/5-GiB/no-extra-swap, offline, read-only, non-root settings
passed assertions. Pinned model identity, normalized 512-dimensional vectors
and repeated-query consistency passed. Exit zero, no OOM, test container removed.
Evidence: tests/inference/results/qwen-container-20261014.json. No runtime changes;
prior synthetic tests/frontend build retained rather than rerun for documentation.
This is a short-input smoke, not a throughput, maximum-input or cloud cost result.
Next: maximum-input/load profiling and image security/licence review before API
integration. Existing API containers untouched; no cloud work or push.

## 2026-10-13 — isolated Linux inference image and protocol controls

Added private JSONL serving with 64 KiB frame limit, recoverable malformed JSON,
fatal timeout session closure and guaranteed runtime cleanup. Added minimal D:
build/model staging, 25-distribution Linux wheel hash lock, offline install,
non-root image and a unique-container smoke launcher with resource/configuration
assertions. The model export copies only verified artifacts and retains licensing;
no HF credentials or personal files enter the context or model mount.

The initial PyTorch download timed out; retry succeeded from its official CPU
index. Other wheels came from PyPI. Fixed wheel metadata selection to ignore
vendored nested distribution metadata. Image build and pip consistency pass.
Docker emits a heuristic ENV-name warning for HF_HUB_DISABLE_IMPLICIT_TOKEN;
its value is the literal switch 1, not a secret. Runtime pip/ensurepip removed.

Verified 18 synthetic inference tests on Windows and the limited Linux container,
including failures/deadlines/recovery, plus frontend production build. Reviewed
control evidence: tests/inference/results/container-controls-20261013.json.
Real Qwen smoke stopped safely at the 4 GiB RAM guard; free RAM fell from 4.55
GiB before build to about 2.4 GiB afterward. No real container measurements are
claimed. Container security scan/licence review, maximum-input profiling and
HTTP integration remain open. No existing API containers changed, no Docker
restart/settings changes, no cloud provisioning and no GitHub push.

## 2026-10-13 — Docker disk migration completed

Manual attempts produced the decisive log: Robocopy returned 1 (successful copy),
but Docker 4.90.0 treated it as failure and retained C:. A same-sized destination
file existed, but full offline SHA-256 comparison showed it stale after continued
source activity. Saved private inventory, stopped Desktop/WSL, copied the 32.83 GB
source under an exclusive read lock, then verified destination SHA-256 against
the stopped source. Both matched before restart.

Backed up settings, set CustomWslDistroDir to D:\DockerDesktop\DockerDesktopWSL
through a hidden Windows process outside AppData virtualization, then started
Docker through Explorer. Engine 29.7.2 responds; 9 container IDs, 64 unique image
IDs and 1 named volume match exactly. All nine containers restarted. D: file
locked/in use and its modification time advanced; C: remained unlocked/unchanged.
Windows Get-DiskImage returned Attached=false for both, so that query alone did
not establish the WSL mount. Settings, lock and write evidence establish D: use.

After specific cleanup approval, removed only the obsolete C: docker_data.vhdx.
C: free space increased to 36.3 GiB; D: 32.74 GiB. Settings backup, inventories,
hashes and completion evidence remain ignored under output/docker-migration.
No factory reset, distro unregister, application code change or model download.
Unrelated application behavior was not tested; no frontend rebuild needed.
Gemma gated access remains denied. Nothing pushed to GitHub.

References: https://github.com/docker/desktop-feedback/issues/550 and
https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy/#exit-return-codes.

## 2026-10-13 — Docker and Hugging Face setup attempt

User explicitly authorized both the Docker move and local HF login setup.
Opened an interactive login window pointing HF_HOME to the ignored D: benchmark
directory. User entered the credential locally. whoami authentication succeeds;
token role is fine-grained. A gated config metadata request returns HTTP 403.
Sanitized error classification indicates account-level model approval absent,
so initial token-scope suspicion is not established. No credential printed.

Docker first showed sailor-ingest.sock access/rename startup failure. Normal stop
failed; supported force-stop succeeded. Launch via Windows Explorer recovered
the GUI and engine (29.7.2). Used Resources > Advanced > Browse to select the
created D:\DockerDesktop folder; Docker proposed D:\DockerDesktop\DockerDesktopWSL.
Apply/restart and move confirmation did not persist the location. A second
selection also reverted to C:. Read-only destination/setting checks find no VHDX
on D:. Backend log shows restart-needed checks for the intended destination,
but no completed migration was established. Docker data was not manually moved,
deleted or reset. Existing containers remain visible; unrelated app functionality
was not tested. Disk relocation and gated model access remain unfinished.

No app code changed, model downloaded, cloud provisioned or GitHub push performed.

## 2026-10-13 — real persistent Qwen host smoke

Rechecked prerequisites: 5.81 GiB available RAM allowed the existing smoke to
run. It verified the D: model manifest/hashes and loaded real Qwen on two CPU
threads. Startup 14.2385 s; three fictional requests 0.5050/0.6686/0.7090 s.
512-dimensional vectors returned, same process reused and cleanup passed.
Post-request RSS 2,725,130,240 bytes is not a peak measurement. Raw measurement
copied to tests/inference/results/qwen-host-20261013.json with scope/date.

Docker data disk still exists in its C: directory; no configured alternate
location found. No token file found in D: benchmark HF home or normal user HF
home, and no HF credential environment variable is configured. No credentials
read or printed. Container builds/Gemma remain pending these prerequisites.
No runtime/frontend changes; prior 169-test/frontend checkpoint not rerun.
No model download, paid provision, native rebuild or GitHub push.

## 2026-10-12 — persistent CPU serving prerequisite

Selected TASK-005 scope: reusable model process with input/token limits,
single-flight admission, startup readiness, hard request deadlines and cleanup.
Implemented services/inference with a local-only Qwen adapter and a D:-only,
hash-verifying real-model host smoke launcher. No endpoint or image was built.

Evidence: 14 synthetic inference tests pass (including whole-batch token budget,
startup hang, model crash, timeout/reap/restart and concurrent rejection).
Full check runner passes 112 worker, 39 evaluation, 4 UI tests and frontend
lint/types/format/build; the expanded 14-test inference suite separately passes
after its last test addition: 169 total. Initial sandbox loopback restrictions
blocked existing HTTP tests; rerun with approved local network access passed.
No native inputs changed, so no desktop executable rebuild was needed.

Real Qwen serving smoke stopped before loading at the 4 GiB available-RAM guard.
Docker's actual data disk was found on C:, so no large image pull/build was
attempted. User will move it to D:. Gemma terms are accepted per user, but no
local HF token file existed at the checked locations; user will sign in locally.
No credentials, models or output artifacts added to Git. No cloud provisioning
or GitHub push. Container resource enforcement, serving measurements and Gemma
comparison remain unverified; the prior v1/v2 benchmarks remain unchanged.

Next: verify Docker disk destination, available RAM and HF access, then measure
the real serving runtime and package/test its constrained Linux CPU container.

## 2026-09-26 — foundation

Completed:
- Inspected the existing PyQt/Python implementation.
- Confirmed user direction: Windows-first desktop, Tauri + React, Supabase vectors, semantic search first and document chat second.
- Wrote project blueprint, delivery gates and interface/motion direction.
- Identified original bugs: first-chunk-only indexing in the desktop path, moving source files, inconsistent metadata, incomplete persistence and stale vectors after deletion.

Environment findings:
- This directory is not currently a Git repository.
- Node reports v22.7.0.
- The currently resolved npm command fails because its npm-cli.js target is missing.
- Rust is not available on PATH or at the standard user cargo location checked.
- Visual Studio Installer exists; the required C++ workload has not been verified.
- Supabase connectivity, credentials and project configuration have not been tested.

No existing source files, original documents, legacy databases or environment secrets were modified. No cloud resources were created and no personal files were uploaded.

Next: resolve the desktop development toolchain, scaffold apps/desktop and build the labelled interactive prototype. In parallel with implementation work, settle the hosting budget and model strategy before introducing a paid dependency. A working Windows installer remains unverified until Tauri prerequisites are available.

Budget update: user requires free operation. Keep Supabase Free for a bounded initial release; revise processing to a bundled local worker and local models. No paid hosting or inference dependency. Verify shared quotas, local hardware requirements and Supabase inactivity behavior before release.

Model research: clarified Gallery-inspired multimodal scope; added MODEL_STRATEGY.md with primary sources and provisional model shortlist. Read development hardware: Ryzen 7 4800H, approximately 16 GB RAM, RTX 3050 Laptop GPU with approximately 4 GB VRAM. No model downloads or benchmarks performed. Photos/OCR are now explicit delivery requirements.

## 2026-09-26 — step 1 implementation

Built the new Tauri + React + TypeScript scaffold in apps/desktop. The working product name is Gather; branding remains provisional. Added a responsive sample library, combined type/text filters, no-results recovery, reader with explicit document scope, disconnected-chat state, and model lineup screen. GSAP entrance transitions respect reduced-motion preferences. All content is labelled synthetic; nothing claims to be semantic search yet.

Toolchain: installed the official Rust stable minimal MSVC toolchain (without modifying global PATH). Verified existing Visual Studio C++ tools. Added scripts/desktop.ps1 to select a compatible installed Node version and bypass the broken npm shim. Installed and locked JavaScript dependencies. Removed the template opener plugin and greeting command; the shell exposes no custom filesystem/shell capabilities. Added a content security policy.

Verification: three component tests passed (combined filters/empty-state recovery, selected-source navigation, and honest unconnected import/model states). TypeScript and production frontend build passed. Initial native Windows compilation passed. Dependency audit reported zero known vulnerabilities at installation time; this is not a security guarantee.

Visual review: the browser tool rejected opening the local preview because permission was declined. No alternate browser or screenshot workaround was attempted. Actual visual appearance, zoom, native interactions and motion remain unverified.

Next checkpoint: review this interface, then add the local processing boundary and a small reproducible embedding benchmark with synthetic text. The four recommended models are accepted starting candidates; no model weights have been downloaded and no Supabase project has been connected.

Final step-1 build: Tauri build --debug --no-bundle succeeded with bundled frontend assets. Executable: apps/desktop/src-tauri/target/debug/gather-desktop.exe. This is a development executable, not a signed installer. Runtime/visual verification remains pending. The temporary browser preview server was stopped.

## 2026-09-26 — design rules and attachment audit

Recorded every user-specified anti-template rule in DESIGN_AVOID_LIST.md, including the interpretation of the two garbled font/texture fragments. Added AGENTS.md so future work reads these rules. Reviewed all seven named design resources; adoption versus inspiration is explicit in the avoid-list resource table.

Implemented Motion-based selected-filter feedback, optional Lenis reader scrolling and a paused, labelled Thinking Orbs example. Removed Lucide and GSAP dependencies, reveal animation, slogan headings, serif heading styles and brightness/fade hover behavior. Added a local original contour SVG, spacing tokens and policy navigation. Main text/button token contrast ratios: 11.95:1, 6.35:1 and 9.30:1; this is not a full-screen accessibility audit.

Read and applied the supplied six-item audit prompt. Added PRIVACY_RELEASE_AUDIT.md with Found / Changed / You still need to for each item and a summary. Added accurate current-state policy screens; production policies and a working copyright report contact remain explicit release gates. No fictitious age gate, unsubscribe, billing or report endpoint was introduced where the underlying feature is absent.

Legacy code changes: removed Google Docs viewer URL requests containing local paths, changed fallback rendering to plain text and redacted dynamic console prints in main.py, main1.py and chroma.py. All three parsed successfully without running them. Data files and environment credentials were not read or changed.

Bundled production dependency license notices in public/THIRD_PARTY_NOTICES.txt. Every installed production package had a license file in the scan. Known-token-pattern source/bundle scan found no matches; this is not an exhaustive secret audit. Dependency installation reported no known vulnerabilities.

Component tests pass (four tests); canvas rendering is explicitly stubbed in jsdom tests and is not visually verified. Native appearance, keyboard navigation, zoom, optional scrolling and orb animation remain pending visual review. Previous browser access denial was respected; no browser workaround was used.

Final verification: all four component tests, TypeScript/frontend build and native Windows build with embedded assets passed after the final policy-footer changes. The existing gather-desktop.exe now contains this update. No cloud services or model downloads were activated.

## 2026-09-26 — TASK-001 structured workflow and version-control baseline

Adopted the user's Read -> Understand -> Plan -> Implement -> Test -> Review -> Fix -> Commit -> Update documentation loop. Added canonical PRD, architecture/design entry points, rules, tasks with acceptance criteria, decision log, current memory, test plan, security requirements and a blank future-public-config .env.example. Updated AGENTS.md and README to use these entry points. Generic Next.js/Vercel/Inter examples did not override the desktop stack or design avoid-list.

Found an existing repository on main with no commits and no remote, and reused it. Explicitly staged the current source, configuration, licenses and documentation as the first recovery checkpoint. Verified 74 baseline paths: no private-data directories, environment secrets, dependencies, model caches or compiled outputs were staged; no file exceeded 1 MB; known secret-token patterns returned no findings; Markdown links resolved. These are bounded checks, not an exhaustive security certification.

Four component tests and the production frontend build passed again. Relevant documentation diff whitespace issues were fixed. The full initial baseline diff reports existing whitespace issues in legacy/template files; no unrelated legacy formatting rewrite was performed. Lint remains unconfigured, native/visual QA remains unverified, and a public repository/remote is not configured. No product runtime changes in this checkpoint, so the prior native build evidence is retained rather than claiming a new native QA run.

TASK-001 is complete in the baseline commit containing this entry. Next: TASK-004 local processing contract using synthetic text only. Audience research, visual review and automated lint/CI remain explicit tasks. Nothing was pushed, published or uploaded.

## 2026-09-26 — GitHub repository created

At the user's request, created private repository https://github.com/kratos1911/gather-desktop using the existing authenticated GitHub account. Connected origin, pushed main, and verified remote commit b89ceec matches local HEAD. Reviewed all 74 tracked files before upload; excluded personal document folders, environment secrets, dependencies and build outputs. No model weights or original documents were uploaded. This is source hosting, not a production application release.

## 2026-09-27 — TASK-004 text-processing contract and cloud decision

User explicitly selected cloud AI, with hosting deferred. Recorded ADR-009,
superseded local inference in canonical architecture/product/rules/current state,
and labelled earlier blueprint/model research as historical where applicable.
Cloud provider, budget, queue and runtime remain undecided. No paid provisioning,
model downloads or external document processing occurred. Updated preview copy
to say cloud processing is planned and disconnected.

Implemented a dependency-free Python processing module in services/worker:
strict bounded JSON/base64/UTF-8 input, TXT/Markdown preservation, exact Unicode
code-point source ranges, deterministic content hashes/versioned passage IDs,
bounded overlap and fixed structured errors. Original source bytes are never
modified. No filesystem, network, logging, persistence or model calls in the
processor. Two committed fixtures and generated test inputs are synthetic.
The module is reusable in a future cloud worker, not an active server.

Verification:
- Bundled Python: `python -m unittest discover -s tests/worker -v`: 12 tests pass.
- `scripts/desktop.ps1 test` with compatible Node on PATH: four component tests pass.
- `scripts/desktop.ps1 build`: TypeScript/frontend build pass.
- Tauri CLI `build --debug --no-bundle`: final frontend/native development build
  passes; updated executable at apps/desktop/src-tauri/target/debug/gather-desktop.exe.
- Staged diff whitespace check passes. Explicit staged path review excludes
  private/generated content; limited known-token/private-key scan found no matches.

Review: clarified code-point versus JavaScript UTF-16 offsets, preserved BOM and
CRLF, rejected duplicate JSON keys/invalid request IDs/control bytes, verified
complete source reconstruction and deterministic retry identity. Removed stale
local-download wording found in the preview during review. Content identity is
not authorization; future persistence must scope deduplication by owner.

Limits: 64 KiB source is a conservative module limit, not the planned upload
limit. Character chunking still requires tokenizer validation in TASK-005.
Durable jobs, IPC/API integration, auth, semantic search, chat and cloud cost/
retention controls are unimplemented. Native runtime/visual/E2E QA remains
unverified; browser denial was respected. Lint is still unconfigured.

Checkpoint branch: feature/text-processing-contract. TASK-004 is complete to
its isolated processing criteria. Next is TASK-005 synthetic retrieval fixtures,
queries and expected evidence before cloud benchmark/provider deployment.

## 2026-09-27 — TASK-005 retrieval corpus preparation

Created text-v1, an original fictional English development set: 14 TXT/Markdown
documents, 40 queries and 37 labelled evidence spans across 35 answerable queries.
Categories: 20 paraphrase, 6 exact, 4 confusable, 3 late-document, 2 multiple-source
and 5 absent questions. Near-match receipts/schedules/bookings/stock figures
serve as distractors. A longer workshop handbook puts relevant evidence beyond
the first 1,024 characters. Absent questions have authored rationales.

Added scripts/prepare_text_evaluation.py using only standard-library code and
the existing processor. It validates unique IDs/questions, exact evidence,
chunk containment, late/multiple-source categories and absent labels; exports
index and queries separately from gold labels; pins a canonical corpus hash.
Default invocation prints inventory only. Generated exports stay in ignored
output/evaluation/text-v1, not in Git. No model/cloud/personal data was accessed.

Checks: seven evaluation unit tests pass; preparation/export produces 16 chunks
and fingerprint 07836c70107491a5a44d7d00c7f50bb69802c62b871841537e74163a8fdf6a4c.
TypeScript/frontend build passes. No UI/native inputs changed, so no native or
component rerun was needed. Reviewed source quotes and labels against documents;
staged diff whitespace and limited secret/path checks pass.

Documented document Recall@5, evidence Recall@5, MRR@5, category reporting,
missing-run rejection and separate absent-answer behavior. Scorer implementation,
lexical baseline and model benchmarks remain pending. The small authored corpus
is deliberately labelled development-only: no independent/held-out, multilingual,
visual/OCR, 10,000-chunk performance, isolation or chat quality claims.

TASK-005 stays partial. Next: offline scoring harness and lexical baseline,
followed by provider/model selection with budget before any paid evaluation.

## 2026-09-27 — TASK-005 scorer and keyword baseline

Implemented scripts/score_text_evaluation.py: label-free TF-IDF cosine ranking,
complete-run validation and per-query/category document Recall@5, MRR@5 and
evidence Recall@5. Runs pin both corpus and processed-index hashes; unknown,
duplicate, incomplete, mismatched or nonfinite results are rejected. Array order
defines rank. Document deduplication precedes the five-document cutoff; passage
scoring uses five chunks, with overlap counted once per expected evidence span.

Measured the unchanged text-v1 development corpus: document/evidence Recall@5
34/35 = 0.9714285714, MRR@5 0.8666666667. Only q18 misses expected evidence;
four of five absent questions return candidates. No answerability or semantic
claim is made. Reviewed this high score against the tiny 14-document/16-chunk
corpus and documented its limitations in tests/evaluation/BASELINE.md rather
than tuning data or claiming the product target achieved.

Checks: 21 evaluation tests pass, including 14 new scorer/baseline tests with
hand-calculated outcomes, stale/incomplete result rejection and cutoff cases.
Both direct baseline and saved-run CLI scoring pass. TypeScript/frontend build
passes. No desktop/native code changed; no native/component rerun claimed.
Reviewed staged paths and diff whitespace; limited secret scan found no matches.
Generated run/report JSON remains under ignored output/evaluation/text-v1.

No models, provider SDKs, network calls, personal data or paid resources involved.
TASK-005 remains partial until model/tokenizer/dimension/cost/latency benchmarks.
Next: provider/model benchmark configuration and adapter; budget/provider must
be selected before hosted evaluation. Cloud deployment remains deferred.

## 2026-09-27 — TASK-005 vector comparison foundation

Added scripts/evaluate_vectors.py: a saved-embedding adapter, consistent-space
validation, stable L2 normalization/exact cosine ranking, and equal-weight
reciprocal rank fusion with TF-IDF (k=60). Requires complete versioned exports
with model/revision/templates/tokenizer/dimensions, corpus/index hashes and no
truncation. Keeps zero/negative cosine candidates without claiming answerability.
CLI comparison retains provenance/configuration/rankings/reports together.

Explained techniques and controlled-comparison methodology during implementation
and in tests/evaluation/VECTORS.md. Cloud provider/producer is not implemented;
this checkpoint is a consumer for eventual exported embeddings. No model weights,
API calls, uploads, credentials or spending were involved.

## 2026-09-27 — Embedding request client; provider deferred

Added a server/developer-only client with token/request caps, all-input preflight,
bounded batches, response-index reordering, dimensions/model/vector checks,
optional usage accounting, HTTPS timeout/body bound/no redirects and sanitized
errors. Tests inject mock transport and tokenizer; none performs a network call.
Read Together's official embeddings API shape as candidate protocol only; model
availability and live provider behavior remain unverified. No default endpoint,
credentials, CLI or automatic retry. Token caps are not dollar spending limits.

User has no provider account and deferred it; no provider-specific benchmark,
truncation assurance or genuine vector export is claimed. User also required
explicit permission for every future push; recorded in AGENTS.md/RULES.md.
Twenty worker tests (eight new), 29 evaluation tests and frontend build pass.
No native assets changed. Continue independent TASK-011 quality tooling next.

Checks: 29 evaluation tests pass, including eight new hand-calculated vector
tests for cosine, magnitude stability, ties, invalid vectors, incomplete/mixed/
stale/truncated exports and rank-based fusion. TypeScript/frontend build passes.
No native or UI changes, so no native/component rerun. Reviewed staged paths and
diff whitespace; limited credential-pattern scan found no matches.

No real vector export/CLI quality benchmark has been run. Synthetic vectors are
test fixtures only; the prior TF-IDF measurements are unchanged. TASK-005 remains
partial. Next: provider/model/budget selection and a genuine embedding producer
with batching, token validation, bounded requests and usage accounting.

## 2026-09-28 — Local quality checks and bookmark scope

TASK-011: added frontend ESLint, explicit type/format checks, a fail-fast local
runner and a manual-only GitHub workflow. Fixed formatting reported on the first
run. Final local runner passes: 20 worker + 29 evaluation + four UI tests (53),
ESLint, TypeScript, Prettier and frontend build. Rebuilt native development
executable with `cargo build --locked --features tauri/custom-protocol`; passed.
No runtime/visual/E2E or remote CI verification claimed. Dependency installation
reported zero known vulnerabilities; this is not a complete security audit.

User added links/bookmarks, including social/video, blog and gaming URLs.
Recorded scope, flow, extraction limits, source provenance and restricted-fetch
requirements in BOOKMARKS.md and the product/architecture/design/security plans.
Technique: save first, enrich metadata/readable text separately, then reuse
chunking and retrieval. Preserve a URL/notes fallback when extraction is blocked.
TASK-016 is offline synthetic parsing; TASK-017 connects private persistence,
restricted network access and search. No bookmark functionality implemented yet.

Provider accounts, paid calls and cloud deployment remain deferred. Changes stay
local; no push or remote workflow dispatch authorized.

## 2026-09-28 — TASK-016 offline bookmark extraction; chat deferred

Implemented URL normalization/validation, metadata and main/article text extraction,
body fallback, paragraph offsets, content hash/version and explicit unavailable
reasons. Bounded UTF-8 input and HTML nesting; preserves notes when extraction
is unavailable. No network requests, model calls, personal inputs or dependencies.
This does not save bookmarks in the desktop or produce semantic search results.

Ten new synthetic tests cover URL rejection, metadata-only video links, malformed
HTML, Unicode/entities, malicious elements, limits, deterministic extraction and
fallback. Full local quality runner passes: 30 worker + 29 evaluation + four UI
tests (63), lint, types, formatting and frontend build. No native inputs/assets
changed; no native rebuild or visual/runtime verification claimed this turn.

Chat deferred per user. Next TASK-018 connects bookmark evidence to versioned
passages and keyword retrieval, independently of provider setup. Live fetching
still requires network security and privacy gates. Keep all commits local.

## 2026-09-30 — Obsidian project knowledge base

Found an existing .obsidian vault in the repository with a root daily note and
Untitled.canvas. Preserved both. Added PROJECT_HUB, concept glossary, accepted
ideas/open questions, maintenance workflow, session/idea templates and a search
flow canvas with implemented/planned/deferred states. Added AGENTS maintenance
instructions so future work consults and updates these notes. Configured local
template and daily-note paths; ignored .obsidian settings/workspace in Git.

Checked new internal links, canvas IDs/edges/file references and configuration
JSON on disk. No Obsidian window interaction or visual verification performed.
Documentation-only change; no app tests/build rerun. Latest code evidence remains
63 tests and frontend quality/build checks from 28 September. Corrected stale
worker-test counts in state/task summaries. TASK-018 remains next. No push.

## 2026-09-30 — Agent Reach integration direction

Reviewed the upstream English README and package metadata. Recorded the user's
extraction-toolkit preference, public-page adapter scope, third-party reader
boundary, desktop-session Instagram limitation and separate save/index states.
Updated Obsidian hub, bookmark/architecture notes, current state and TASK-019.
No package installed, browser session accessed, URL scraped or model invoked.
Documentation-only checkpoint: diff and local note references checked; application
checks not rerun. TASK-018 remains next and chat remains deferred. No push.

## 2026-09-30 — Extraction stack accepted

Recorded user acceptance of Crawl4AI plus yt-dlp. Updated current architecture,
bookmark plan, TASK-019, state and Obsidian hub; retained Agent Reach research
with an explicit superseded banner. Added EXTRACTION_STACK with scope, source
links, adapter boundaries and acceptance gates. No dependencies installed or
network extraction performed. TASK-018 remains the next implementation task.
Documentation-only checks: internal links and diff whitespace; no app build or
tests rerun. Prior 63-test result remains historical evidence. No push.

## 2026-09-30 — Repository cleanup

Inventoried all 109 tracked files, read tracked bytes, parsed Python syntax without
execution and checked active entry points/references. Archived six original root
prototype files unchanged in legacy/ with explicit unsupported/reference status.
Deleted three unreferenced scaffold SVG logos and root .DS_Store metadata. Kept
native icons, lockfiles, licences, source, tests and documentation. Preserved
private data/secrets, environments, generated outputs and user canvas. No legacy
code was run; this was not a full correctness/security review of every module.

Checks: 30 worker + 29 evaluation + four UI tests pass; lint, types, formatting
and frontend build pass. Native development executable rebuilt successfully via
cargo build --locked --features tauri/custom-protocol. Visual/runtime verification
remains pending. Updated onboarding, architecture and Obsidian hub/state; full
per-file record in REPOSITORY_AUDIT.md. TASK-018 remains next. No push.

## 2026-09-30 — TASK-018 bookmark passage adapter

Implemented bounded HTML extraction to field-specific versioned passages, reusing
text-processing request validation/chunking. Preserved original URL, exact field
offsets, extraction status/reason and semantic_ready=false. Revision/source/field
identities distinguish retries, edited notes and separate sources. Notes and URL
remain processable when extraction is unavailable; invalid field processing
returns no partial document. Documented contract in services/worker/BOOKMARK_PASSAGES.md.

Seven new tests pass, including late-document TF-IDF retrieval resolving back to
source URL and matching excerpt. Full runner: 37 worker + 29 evaluation + four UI
= 70 tests; lint, types, format and frontend build pass. No native inputs changed,
so native build not rerun. No live scraping, storage, model or UI integration.
Updated Obsidian hub and canvas. TASK-019 is next. No push.

## 2026-09-30 — TASK-019 output normalization checkpoint

Added pure Crawl4AI Markdown/metadata and yt-dlp single-video metadata/normalized
subtitle-cue adapters. Preserves backend version, retrieval timestamp and final
URL where supplied; handles HTTP/extraction failures without copying raw errors.
Cue timing/language/automatic flags survive passage chunking. Added generic text
bounds and input checks; no tools, subprocesses, models or network fetching.

Eight new synthetic tests pass. Full checks: 45 worker + 29 evaluation + four UI
= 78 tests; lint, types, formatting and frontend build pass. No native inputs
changed; native build not rerun. Official protocol docs reviewed; actual package
compatibility is unverified. TASK-019 partial: isolated runner, pins/licenses,
VTT/SRT parsing and network/privacy checks still pending. Obsidian notes updated.
No push.

## 2026-09-30 — Subtitle parsing checkpoint

Added bounded SRT/WebVTT caption parser: UTF-8/BOM/line-ending handling, timestamp
validation, cue identifiers, display-markup removal, entity decoding, overlap
preservation and size/count limits. Unsupported formats and malformed blocks
raise generic errors without returning a partial transcript. This is a subset,
not full WebVTT rendering/conformance. No external dependencies or live downloads.

Eight new tests, including subtitle bytes through yt-dlp output adapter to passage
cue references. Full runner passes: 53 worker + 29 evaluation + four UI = 86 tests;
lint, types, formatting and frontend build. Native inputs unchanged; no rebuild
or visual QA claimed. TASK-019 still partial; next isolated/pinned extraction
runners and network controls. Updated Obsidian state/hub. No push.

## 2026-09-30 — Extractor destination policy and direct pins

Implemented pure public-destination preflight with injected DNS, all-answer
validation, port restrictions, sanitized resolver errors and immutable approved
addresses. Eight tests cover mixed/private/metadata/special ranges, malformed or
large answers, literal IPs, numeric hosts and changed DNS answers. This does not
perform network I/O or prevent rebinding unless the future transport uses the
approved addresses. No isolation or live runner claim.

Recorded PyPI-verified direct pins in requirements-extraction.txt. Not installed;
transitive lock and complete dependency licence review remain pending. Full
checks pass: 61 worker + 29 evaluation + four UI = 94 tests; lint, types, formatting
and frontend build. Native assets unchanged; no native rebuild. TASK-019 partial.
Next: enforced network execution boundary and isolated extractor environment.
No cloud provisioning, personal browser access or push.

## 2026-09-30 — Offline runner and container configuration

Added bounded one-job stdin/stdout runner with strict fields, duplicate-key
rejection, generic errors and no shell dispatch. Added Dockerfile, allowlisted
build context and Compose configuration with no network, no host mounts,
non-root/read-only filesystem, dropped capabilities and resource limits.
Compose configuration validates. Docker Linux engine unavailable; attempted
hidden Docker Desktop start but engine remained unreachable. Image build and
installed packages/isolation unverified; no live scraping performed.

Four runner tests added. Full local runner passes 65 worker + 29 evaluation + four
UI = 98 tests, lint/types/format/frontend build. No native inputs changed. TASK-019
remains partial: restore Docker engine, build/lock image, enforce egress and add
live tool execution. No push, browser-session access or paid provisioning.

## 2026-10-01 — Built and checked offline extraction container

Docker Linux engine became available. Built the image successfully; verified
Crawl4AI 0.9.4 and yt-dlp 2026.8.19 package metadata and pip dependency consistency.
Added repeatable scripts/check_extractor_container.py: synthetic success/error
jobs, semantic_ready false, UID 65532, rejected application-directory write,
unreachable external route, and absence of /app/.env and /app/data all pass.
Smoke containers removed on exit. These probes do not certify production isolation.

Reran 65 worker + 29 evaluation + 4 UI = 98 tests, lint, types, formatting and
frontend build successfully. No native inputs changed; no native rebuild needed.
Updated canonical status, hub, extraction note and Obsidian flow canvas. TASK-019
remains partial: dependency/base-image locks, public-only egress, browser runtime
and actual tool invocation/live compatibility remain open. No live scraping,
cloud provisioning, personal-document processing or push performed.

## 2026-10-02 — Search-first system and delivery plan

Reviewed desktop fixture path, native capabilities/CSP, offline runner, network
preflight, Compose and product/security notes. Product Design preflight found no
saved context; existing project conventions were used. DELIVERY_PLAN.md records
target flows, a minimal backend, private data model, leases, version publication,
deletion races, hybrid retrieval, security controls and ordered acceptance gates.
ADRs 026–028 are proposals; TASK-019A/B/C and TASK-021 describe implementation work.
Consulted official Supabase, pgvector, OWASP, Tauri and Cloud Run references.
No runtime changes, cloud deployment, paid call or push. The prior 98-test result
is historical evidence, not a new test run. Documentation diff checks pass;
architecture artifact evidence is recorded separately after generation.

Architecture artifact: .archify/architecture-gather-plan-20261002-081351/.
Archify deliver and strict provenance check passed all nine structural checks,
with zero errors/warnings/crossings and 13 verified source references at c0b628f.
Browser/perceptual checks not run because the prior browser restriction remains;
standalone delivery used instead of finalize's browser gate. The artifact README
records this limitation and the aspirational text-size target miss. Hub and
Obsidian flow canvas link the plan. No application source changed or runtime
tests rerun. Planning and artifact checkpoints committed locally; nothing pushed.

Artifact review follow-up: Git flagged 15 whitespace-only lines in the generated
viewer. Preserved generated bytes and recorded the exception rather than alter
the hash-bound output. Added exact-byte Git attributes for candidate/HTML/receipt
to keep provenance stable on Windows checkouts. Authored-document checks pass.

## 2026-10-02 — Extractor lock and advisory review; storage blocker

Recorded user's OKF acceptance as an optional later linked-note/export feature,
not a replacement for Supabase/hybrid retrieval or the later RAG chat path.
Added ADR-029, learning notes and the deferred idea; no OKF runtime installed.

TASK-019A: resolved the existing tested image's 96 application packages into exact
Linux/amd64 CPython 3.12 wheel hashes and declared license inventory. Pinned the
base platform manifest, added hash-enforced wheel-only installation and separate
pip 26.2.1 bootstrap lock after advisory review of base pip 25.0.1. Added repeatable
lock/advisory scripts, exact installed-package smoke comparison and eight tests
for drift/omissions/bad artifacts, inventory consistency and fail-closed feed errors.

Full local checks pass: 73 worker + 29 evaluation + four UI = 106 tests, lint,
types, formatting and frontend build. No native inputs changed. PyPI lookup of
96 packages plus target pip succeeded with zero lookup errors and one affected
package: NLTK 3.10.3, GHSA-8mgp-746c-j5xp. No patched release listed; recorded a
live-extraction gate. The advisory script correctly exits nonzero for this finding.

Docker no-cache rebuild failed after C: reached zero free space and Docker reported
read-only filesystem / image-store I/O errors. Stopped the build client. Scout's
first temporary export ran out of C: space; a project-drive retry failed on Docker
storage. No successful new-image build, smoke, intentional hash-mismatch rejection
or OS scan claimed. No user files/caches/images were deleted or storage reset.
TASK-019A stays partial. Restore storage and restart Docker, then rebuild/test/scan.
Details: services/worker/DEPENDENCY_REVIEW.md. Notes/hub/canvas updated; no push.

## 2026-10-03 - Docker recovery and locked-image verification

Resumed after Docker restart. No-cache image build completed successfully with
hash-enforced wheel installation and pip check. Exact locked package comparison,
synthetic success/error jobs, non-root UID, read-only application path, unreachable
external network and excluded personal paths pass. An actual pip probe rejects a
wrong artifact hash and accepts its correct hash.

Added unique smoke-container names and explicit removal in finally, including
client timeout. Three mocked cleanup tests pass; a real deliberately sleeping
container times out and is removed. No gather-smoke containers remain. This is
developer verification tooling only, not TASK-019B production job supervision.

Docker Scout full scan completed: 51 records, 10 high / 7 medium / 34 low / no
critical. Aliases may overlap. IMAGE_SCAN_REVIEW.md records the image/report hash,
complete inventory and remediation categories. OS patches, pip bundled libraries
and NLTK remain open. Static inspection found Crawl4AI NLTK tokenizer/downloader
paths; no live extraction was executed. TASK-023 now tracks remediation before
networked execution. TASK-019A build/audit acceptance is verified, not security
readiness or completion of TASK-019.

Full quality runner passed: 76 worker + 29 evaluation + four UI = 109 tests,
ESLint, TypeScript, Prettier and frontend build. No native inputs/assets changed;
no native rebuild or visual/E2E claim. State, task board, decision, dependency,
runner, test, delivery and Obsidian hub/concept/canvas notes updated. No paid
resources, personal documents or GitHub push. Changes committed locally.

## 2026-10-03 - TASK-023 available fixes and full rescan

Pinned installed OpenSSL/libssl/provider to 3.5.7-1~deb13u3 and PCRE2 to
10.46-1~deb13u3 using authenticated Debian security metadata. Removed pip and
ensurepip from runtime; developer installer target retains checksum/dependency
checks. Build succeeded, reusing unchanged hashed-wheel install layers. Runtime
smoke verifies all 96 application versions, patched OS versions, absent installer
modules, isolation, synthetic jobs and installer hash rejection/acceptance.

Rescan completed: 31 records (4 high, 2 medium, 25 low), versus 51 (10/7/34).
Twenty-one prior records disappeared; CVE-2026-95619 is newly reported by the
refreshed feed. Complete report hashes, inventories, references and dispositions
are in IMAGE_SCAN_REVIEW.md. Remaining NLTK/GCC/zlib and lower-severity records
stay open; TASK-023 is partial. No clean-security/live-extraction claim. Scout
reported a locked temporary archive during cleanup, but wrote a valid SARIF.

Real smoke exposed delayed Windows cleanup: subprocess.run can wait for child
pipes after killing Compose. Changed to explicit process lifecycle, kill/remove
before closing pipes. Three regression tests cover ordering, auto-removal and
cleanup errors. Real 120-second sleep now cancels within a 20-second budget;
whole final smoke completed in under ten seconds. No smoke containers remain.

Full checks passed: 109 tests, lint, types, format, frontend build. After cleanup
change, all 76 worker tests and real smoke were rerun successfully. No native
inputs/assets changed. Docs and Obsidian notes/canvas updated. Local commit only;
no cloud spending, browser use, real documents or GitHub push.

## 2026-10-03 - TASK-019B controlled transport and offline supervisor

Added backend-only restricted_fetch: public-address approval, numeric-IP dialing
without second DNS, peer/TLS identity checks, per-redirect validation, downgrade
rejection, bounded identity-encoded page bodies and safe errors. It does not
follow scripts/assets, forward cookies/headers, or use proxy environment settings.
Known NAT64 translation ranges are now denied. Fifteen tests use controlled local
HTTP peers plus injected resolver/TLS checks; no public sites or DNS were queried
by the test suite. Initial stall test exposed a missing explicit read timeout on
an injected socket; fixed it and reran all worker checks. Slow-header rejection
and elapsed-time bounds also pass. Whole-broker DNS deadline remains open.

Added host-side DockerJobRunner with operator image digest, fixed command,
network none, non-root/read-only/capability limits, one local concurrency slot,
input/stdout/stderr caps, timeout/cancellation and exact-container cleanup.
Five prelaunch unit tests and real Docker adversarial probes pass: supplied-output
success/error, timeout, cancellation, excessive stdout/stderr, invalid output,
failed process, recovery, direct public/private/metadata egress denial, absent
socket/secrets, read-only path, UID and cgroup resource limits. No job containers
remain. Docker supervision is not a durable queue or a hosted API; supervisor
crash/orphan reconciliation and distributed quotas remain planned.

Validation: scripts/check.ps1 passed the 96-worker/29-evaluation/four-UI suite,
lint, TypeScript, Prettier and frontend build. Added the slow-header case and reran
all 97 worker tests successfully: current total 130 tests. Final image rebuilt;
check_worker_supervisor.py passed against it. Scout rescan completed with the same
31 advisory IDs (4 high, 2 medium, 25 low), documented with image/report hashes.
Scout temporary archive cleanup reported a file lock; valid SARIF was retained.
No dependency findings were suppressed. No native inputs changed or native E2E
claim made. Browser access, live extraction, paid AI and public deployment remain
off. TASK-019B remains partial: next is a supervised fetch-broker process covering
DNS, then parser integration and browser/tool egress. Canonical docs, concepts,
Obsidian hub and flow canvas updated; local commit only, no GitHub push.

## 2026-10-08 - Whole-fetch deadline and controlled page-to-passages flow

Implemented FetchBroker with one fixed child process per URL, parent deadline
covering DNS/connect/TLS/body operations, cancellation, bounded input/output and
safe errors. Child startup is isolated; only Windows system-directory variables
are inherited, with no provider/proxy/Python environment settings. Timed-out and
cancelled processes are killed/reaped and pipes closed; valid output from a child
that remains running is not published. This is lifecycle isolation, not a host
filesystem/memory/network sandbox or general process-tree supervisor.

Added http-page adapter and BookmarkPipeline. Actual fetched HTML/XHTML or UTF-8
plain bytes pass to the network-none Docker parser; source notes, original/final
URL, timestamp, redirects, body hash and passage provenance are preserved. This
is explicitly restricted-http output, not simulated Crawl4AI or semantic results.
Fetch failure/cancellation never invokes the parser; durable bookmark preservation
still belongs to the future storage/coordinator layer.

Nine broker and six page/pipeline tests added. Tests simulate blocked DNS, connect
and TLS within real subprocesses, check output flooding/schema failures, recovery,
reaping, secret environment exclusion and cancellation between stages. A first
oversize-result fixture exceeded Windows command-line length; changed only that
fixture to construct its large output inside the child, then verified rejection.
Full quality runner passed with 110 worker + 29 evaluation + four UI tests and
lint/types/format/frontend build. Added two more edge cases and reran all 112
worker tests successfully: current total 145. No native inputs changed.

Docker image rebuilt successfully with unchanged package layers.
check_bookmark_pipeline.py passed: loopback HTTP redirect -> real broker child ->
real offline Docker parser -> passages, plus metadata-redirect rejection before
parsing. No real websites, browser tools, personal documents or paid services used.
No job containers remain. Scout rescan: 29 records (2 high, 1 medium, 26 low),
versus 31 on 3 October. No package fixes were made this turn: two GCC records are
no longer reported by the feed and one advisory severity changed. Full current
inventory, image digest and SARIF checksum recorded in IMAGE_SCAN_REVIEW.md.
The scanner again reported a locked temporary archive during cleanup but wrote
valid SARIF. Remaining dependency and production gates stay open.

Canonical docs, Obsidian hub/concepts and flow canvas updated. TASK-019B remains
partial for browser/tool egress, production broker confinement and public/TLS
compatibility. Local persistence TASK-021 can proceed independently. No push.
# 8 October 2026: TASK-021 source ownership foundation

Added Supabase-targeted sources/source_versions migration and disposable pinned
PostgreSQL 17 checks. Nineteen SQL assertions pass: two-user isolation, own
metadata persistence, owner/lifecycle write denial, anonymous/missing identity,
composite owner foreign key and tombstone/dependent-version visibility. The
container uses no network/ports/host mounts, bounded tmpfs, and was removed after
the run. Unrelated Docker services were not changed.

Existing quality runner also passes: 112 worker + 29 evaluation + 4 UI tests,
lint, type checks, formatting and frontend build. No native inputs changed.
Reviewed SQL privileges and ownership boundaries; no client insert/delete grants
until quota/cleanup APIs exist. Updated canonical notes, Obsidian hub/concepts
and flow canvas. Changes committed locally only; no push.

Limits: this uses a test-only Auth contract shim on PostgreSQL, not full Supabase
services or JWT validation. Storage/RPC, durable jobs, quota/retry/delete races,
worker persistence and desktop integration remain pending. TASK-021 stays partial.
Live extraction security gates and cloud AI account deferral remain unchanged.

## 9 October 2026: atomic saves and database cleanup

TASK-021 now includes source-count quotas, idempotent save receipts, atomic
tombstone/cleanup requests, database-only cleanup and late-version write guards.
45 SQL assertions plus four concurrent scenarios pass on disposable PostgreSQL.
These cover repeated/conflicting saves, rollback, quota exhaustion, ownership,
late retry after deletion, duplicate cleanup and derivative write/delete races.
No default production quota, account creation, Storage or desktop connection.

Docker was initially unavailable; the later run with Docker access succeeded.
The initial sandboxed quality run could not complete local-network tests and was
stopped. The authorized run outside the sandbox passed all 145 existing tests,
lint, typecheck, formatting and frontend build. No native inputs changed.
Updated architecture, decision, state, task, test and Obsidian hub/concepts/map.
Local checkpoint only; no push. TASK-021 stays partial for Supabase integration,
external cleanup, byte/rate budgets, receipt retention and processing leases.

## 9 October 2026: real core Supabase API and original-file deletion checks

Added a private originals migration and Storage-presence guard before SQL cleanup.
A new disposable Compose harness runs actual Auth/PostgREST/Storage with synthetic
users and TXT bytes. All 31 API checks pass, including JWT login, ownership, denied
client mutations, immediate tombstone visibility, failed-cleanup preservation,
Storage API byte removal, interruption before finalization and retry safety.
The 49 database checks and existing 145 tests also pass, plus lint, types,
formatting and frontend build. No native inputs changed.

The initial CLI experiment exposed ports beyond loopback despite its documented
network option. It was stopped before proceeding; the final harness explicitly
publishes only 127.0.0.1:55431 and checks Docker bindings. The first Auth setup
disabled email/password login with email signup; the final setup keeps the
provider enabled and public signup disabled. Test schema permission/startup
issues were fixed and verified against the actual APIs.

CLI initialization enabled its usage-reporting setting; it was disabled during
setup. No product telemetry was added. Its stopped test volumes/networks were
removed, as were the successful harness's users/files/containers. Downloaded
tooling remains ignored and image caches remain; unrelated workloads were not
changed or pruned. No cloud resources or paid calls; local checkpoint only.

Updated tasks/state/architecture/security/test notes and Obsidian hub/concepts/map.
TASK-021 remains partial: this verifies core services, not hosted parity or desktop
persistence. Upload fencing, background cleanup/reconciliation, session lifecycle,
production dependency review and processing job leases are still open.

## 2026-10-10: real Qwen CPU benchmark on D:

User authorized model testing with downloads on D: due to low C: storage, then
chose Qwen first while EmbeddingGemma license acceptance is pending. Read canonical
docs and retained the search-first scope; chat and visual/OCR tests remain deferred.
Recorded later Cloud Run CPU/R2/Supabase choices without deploying paid resources.

Added a dedicated D: environment/cache/temp runner, fixed Qwen commit and artifact
hash verification, safetensors-only offline loading with remote code disabled,
exact-token preflight and real vector exports into the existing cosine/RRF scorer.
CPU dependency versions are frozen in a separate developer constraints file.
Unit tests cover token overflow/special tokens, invalid vectors, normalization and
rejection of C: storage. The new environment is isolated from the worker image.

Download: ten artifacts, 1,207,487,158 bytes; revision
97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3. All model/dependency artifacts remain in
ignored output/model-benchmark on D:. Download/package network restrictions required
approved reruns. Available RAM initially measured about 2 GiB; asked the user to
free memory. They agreed, and both actual runs passed the 4 GiB pre-load guard.

Both two/four-thread CPU float32 runs completed on all 16 passages and 40 queries.
Actual maximum input was 159 passage tokens and 35 prompted-query tokens; no input
was truncated. Dense 256/512/1,024 dimensions each scored 100% document/evidence
Recall@5 on 35 answerable queries; 512-dimensional MRR was 0.9857. Fixed RRF reduced
MRR; 1,024-dimensional hybrid also lost q18 evidence. All five absent questions
still return neighbors. These are genuine model outputs on a small fictional
development set, not production accuracy or an answerability evaluation.

Warm median/p95: 0.707/0.888 seconds at two threads; 0.324/0.376 at four. OS peak
working set about 3.64 GiB. Model loading follows hash reads, so its time is not
cold-start evidence. Laptop results do not predict Cloud Run prices or capacity.
Full raw vectors/reports stay ignored; concise machine-readable evidence with
raw-artifact hashes is in tests/evaluation/results/qwen-cpu-20261010.json.

The full check runner passed 112 worker, 33 evaluation and 4 UI tests, lint, types,
formatting and frontend build. Existing loopback tests initially failed/stalled
inside the network sandbox; the approved full rerun passed. A final storage-guard
test was then added and the evaluation suite rerun (34 tests). Pip check passes.
Native assets/inputs were unchanged. No personal files, hosted inference, app
integration, paid deployment or GitHub push. TASK-005 remains partial; next is a
broader evaluation and bounded serving-container measurement before selecting
dimensions/fusion and deployment sizing. Updated canonical and Obsidian notes/map.

## 2026-10-12: frozen fresh text challenge and failure review

Continued TASK-005 with a bounded, reviewable evaluation slice. Read the canonical
docs, security/test notes and existing scorer/producer. Authored text-v2: 40
fictional Markdown sources, 64 processing passages and 64 questions across eight
new domains. Current, archived and neighbouring records compete. Eight evidence
spans start beyond character 2,300; eight requested facts are absent. No personal
documents or external source material were used. This is not independently
labelled or blind evaluation, and sources are only 166–2,736 characters long.

Validated evidence offsets and froze corpus/labels before inference using
d23f63392759b5db751f1a024468908d8d6b3832652ddbdb7234264c8eb4d25b.
Added fixed corpus selection across preparation, benchmark and scoring; freeze
mutation checks; separate v2 output locations; corpus/index hashes in timing
metadata. Inference still receives only prepared passages and queries. Preserved
v1 semantics, canonical fingerprint, lexical scores and twelve raw artifact hashes.

Available RAM initially measured 0.78 GiB; user agreed to free memory. It reached
5.54 GiB before the test, and the actual model passed its pre-load guard. Reused
the existing pinned D: Qwen snapshot offline, with four threads and unchanged
prompt/chunker/float32/cosine/RRF. No model download or cloud provisioning.
All 64 passages and queries completed; actual tokens 32–171 and 28–39 respectively.

Primary 512 candidate passed the three predeclared >=0.90 gates: document
Recall@5 1.0, evidence Recall@5 0.9911, MRR@5 0.9613 on 56 answerable questions.
Median/p95 warm query time 0.329/0.403 seconds; indexing 39.73 seconds; OS peak
working set 3.64 GiB. These are local short-input timings, not cloud latency/cost.
All eight absent questions return candidates. Fixed RRF lowers MRR at every
dimension. 1,024 improves MRR while 512 has better evidence recall; no universal
or final production winner is selected.

Reviewed every nonperfect 512-dense case: a needed second-source passage ranks
sixth, historical/current intent is confused in two cases, a solo/team rule is
confused, and an exact code ranks third. No labels, queries or retrieval settings
were adjusted after the results. Preserved per-category/failed-query evidence and
raw-file hashes in tests/evaluation/results/qwen-text-v2-20261012.json. Detailed
interpretation and next acceptance are in docs/TEXT_V2_RESULTS.md.

Verification: 39 evaluation tests, frontend production build, pip check, v1
lexical regression and old-artifact hash verification pass. Five new tests cover
the frozen corpus, source/query/label mutation rejection, evidence offsets,
disjoint inputs, label separation, output paths and cross-corpus rejection.
Unchanged worker/UI suites and native build were not repeated. Updated canonical
docs and Obsidian hub/concepts/flow map. Local commit only, no GitHub push.

TASK-005 remains partial. Next: a private local serving container with measured
CPU/RAM/concurrency limits, token/request bounds, readiness and failure behavior;
verify Docker storage is on D: before large builds. Retrieval weaknesses and
independent real-world relevance review remain open before release claims.
