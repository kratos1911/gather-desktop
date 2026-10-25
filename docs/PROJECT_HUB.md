---
tags: [gather, project]
---
# Gather project hub

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Delete control added to search results and verified in current UI]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Hosted UI search/open confirmed by user; deletion and cleanup remain]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Per-request token refresh, categorized search diagnostics, and clean operator shutdown]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Per-request operator identity refresh and safe search diagnostics; restart API before one UI check]].

Current: [[docs/OPERATOR_LIBRARY_PILOT|Search failures now identify session, model or database stage; restart API before one diagnostic UI search]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Search failures now report safe dependency categories; restart API before one UI recheck]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Worker ready; frontend runtime discovery fixed; UI search/open next]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Worker startup readiness now precedes exact-job claim]]. Live retry pending; no new model call by agent.

Current: [[docs/EXACT_JOB_CLAIM|Exact-job repair applied and permissions verified]].

Latest: [[docs/OPERATOR_LIBRARY_PILOT|Chrome connection bug fixed; refresh/sign-in before live import]].

Current: [[docs/OPERATOR_LIBRARY_PILOT|Restricted operator UI and loopback backend locally verified]]. Hosted acceptance through the new UI remains pending; stop at this milestone per user.

Current implementation: [[docs/LIBRARY_API|Bounded library HTTP adapter; server composition next]]. Hosted pilot passed; final cleanup confirmed by operator. Earlier pilot-status entries below are historical.



Latest: [[docs/HOSTED_FLOW_PILOT|Scaling gate verified; min0 confirmed; fresh operator run next]].

CURRENT: [[docs/HOSTED_FLOW_PILOT|Clean cancelled fixture, then start new guarded run]].
Minimum zero restored; future full runs release temporary warmth on exit.

Current: [[docs/HOSTED_FLOW_PILOT|Processing failed before staging; Postgres log needed]].
Source is tombstoned, physical cleanup pending; warm min=1 still active.

ACTIVE PILOT: [[docs/HOSTED_FLOW_PILOT|Warm min=1 verified; guarded resume next]].
Restore minimum zero after testing or operator stop; idle billing active.

Latest: [[docs/HOSTED_FLOW_PILOT|Measured DB setup delay; approved pilot-only bound and guarded resume]].

Latest: [[docs/HOSTED_FLOW_PILOT|Cold-start 429 diagnosed; readiness now verified]].
Both user logins pass; next operator full run remains pending.

Current blocker: [[docs/HOSTED_FLOW_PILOT|Auth-only diagnostic for hosted pilot A sign-in]].

Next operator action: [[docs/HOSTED_FLOW_PILOT|Run the authenticated hosted text pilot once]].

Latest: [[docs/HOSTED_SUPABASE_SETUP|Encrypted credentials and hosted TLS logins verified]].
Next: public project API key and real pilot Auth session before hosted flow testing.

Hosted setup: [[docs/HOSTED_SUPABASE_SETUP|Sydney project, migrations and private password prompts]].

Current connection milestone: [[docs/DATABASE_TRANSPORT|Real driver, restricted roles and deadlines]].
Local verification passes; next is application HTTP admission and hosted setup.

Latest: [[docs/LIBRARY_SESSION|Authenticated library flow and two-user verification]].
Next: production database/HTTP composition; desktop remains sample mode.

Current: [[docs/CLOUD_INGESTION_PILOT|Real cloud-vector backend pilot and boundaries]].
User deployed private inference; developer SQL flow passes. Next is authenticated
application/database composition, then desktop wiring. Earlier pending-deployment
entries below describe prior checkpoints.

Upload instructions: [[docs/RELEASE_AND_PILOT|User-run private registry upload]].

Pilot identity: [[deploy/cloud-run/identity.json|Verified caller configuration]];
[[deploy/cloud-run/Dockerfile.pilot|Local configured image]]. Upload pending.

Real release checkpoint: [[docs/RELEASE_AND_PILOT|Baked Qwen image passed local HTTP smoke]].
Next: personal Gather CLI sign-in and final pilot approval; no deployment yet.

Release/pilot: [[docs/RELEASE_AND_PILOT|Built candidate, Gather project, INR 500 plan and blockers]].
No deployment; personal CLI sign-in and real-image RAM prerequisite remain.

Linux checkpoint: [[docs/CLOUD_STARTUP|49 packaged startup/security/shutdown checks passed]].
Next: model release packaging and remaining attribution/pilot gates.

Cloud startup: [[docs/CLOUD_STARTUP|Explicit mode and host verification]].
Next: Linux image verification after Docker starts; no deployment yet.

19 October: staging input preflight verified; [[TASKS|Checks and next milestone]].
Next is guarded Cloud Run startup, not deployment.

Start here in Obsidian. Updated 18 October 2026.

Collaboration: [[docs/CLI_WORKFLOW|Desktop and CLI handoffs]].

Windows CLI: [[AGENTS|Runtime instructions]]; use scripts/python.ps1 for lightweight checks.

Zlib fix: [[services/inference/zlib/README|Local backport and original-versus-fixed evidence]].

Notice image: [[tests/inference/results/notices-image-20261018.json|Linux bundle verified; release gates remain]].

Notice packaging: [[services/inference/licenses/README|Verified upstream licences and staged bundle]].

Pilot review: [[docs/CLOUD_PILOT_PLAN|Configuration, gates and acceptance]].
No cloud resources deployed; see this plan for the next local prerequisite.

Live keys: [[docs/RECEIVING_IDENTITY|Google public-key compatibility passed]].
Real service-account token and deployed IAM remain unverified.

Startup artifacts: [[services/inference/ARTIFACT_STARTUP|Verified files and entry point]].
Updated Linux startup image verified: 51 focused synthetic checks pass.

Identity handoff: [[docs/CLOUD_IDENTITY|Dual headers and cloud pilot checks]].
Locally verified; [[docs/RECEIVING_IDENTITY|Trusted startup and paired callers]]
now implemented. Artifact startup packaging passes; actual service-account token/IAM remains pending.

HTTP evidence: [[services/inference/HTTP_SMOKE|Bounded real-model HTTP check]].
Real local Qwen HTTP smoke passed; measurements and remaining cloud gates recorded.

Linux auth update: [[services/inference/SERVING_IMAGE|Packaging, shutdown and scan evidence]].
Verifier and refresh lifecycle tested with synthetic inference/mocked keys.
Google/IAM and security release gates remain open; local model HTTP is verified.

Security review: [[services/inference/OS_RISK_REVIEW|OS findings and ingress evidence]].
Release findings remain open; receiving cloud authentication can proceed locally.

Packaging: [[services/inference/SERVING_IMAGE|Linux serving candidate and gates]].
Combined dependencies and synthetic Linux HTTP verified; no model/cloud promotion.

Identity update: [[docs/CLOUD_IDENTITY|Outbound service tokens and trust boundary]].
Client verified with synthetic tokens; actual IAM and public ingress still gated.

Implementation update: [[docs/INFERENCE_ASGI|ASGI serving and lifecycle]] verified
locally with synthetic engines. Cloud identity/Linux image remain pending.

Planning update: [[docs/CLOUD_RUN_DESIGN|Cloud hosting, identity and next steps]].
Documented direction only; no deployment or paid provisioning.

Backend update: [[docs/INFERENCE_HTTP|Authenticated local inference endpoint]]
now works with the bounded inference client and synthetic engine. Production
identity/ingress and cloud deployment remain pending. See [[TASKS]] for evidence.
[[docs/PUBLISHED_SEARCH|Authenticated published search and reader]]
now complements [[docs/INGESTION_COORDINATOR|Internal ingestion]]. See [[TASKS]] for
evidence and [[docs/MEMORY|Current state]] for remaining integration work.

UI update: [[docs/DESIGN_REVIEW_20261015|Expressive preview redesign and checks]].
See [[docs/DESIGN_DIRECTION|Color, typography, motion and provenance]]. The visible
app is still a sample workspace; native/accessibility QA remains open.

Current: [[docs/SEARCH_CONTEXT|Bounded context and cached-vector replay]]. Known
split/multi-part evidence recovered without new model calls. See [[TASKS]] for
the three-milestone path; backend coordination is next. Context is not connected
to the desktop yet, and production security gates remain open.

Latest: [[docs/CHUNK_RETRIEVAL_RESULTS|Paired chunk retrieval results]]. All 178
requests passed. Main set: 100% document/evidence recall, MRR 0.9792. Boundary
stress: 50% strict evidence, 87.5% combined coverage. Finding the file is not
enough when the supporting passage is split or missing. Next: bounded same-source
context assembly and multi-part passage coverage. 44 evaluation/26 inference
checks and frontend build pass; no connected ingestion or deployment yet.

Latest: [[services/inference/UPGRADE|Patched CPU candidate and 512-token slices]].
25 focused checks pass; scan improved from 56/12 high to 28/1 high. Real candidate
comparison now passes (six cases, unchanged tested rankings); five chunks take
3.05–5.88 s, peak 3.95 GiB. Next: retrieval quality with new chunk boundaries,
then ingestion integration. Security/licence gates remain; no desktop wiring yet.

Newest: [[services/inference/PROFILE_RESULTS|Extended CPU results]] and
[[services/inference/IMAGE_SCAN_REVIEW|Security review]]. Fifty short requests
passed (median 0.71 s); 2,048-token/max-batch requests timed out. Scan found 56
records, 12 high. Next: dependency remediation/rescan and smaller-chunk evaluation
before connecting inference to the app. Limits unchanged; 21 control tests pass.

Latest: [[services/inference/CONTAINER|Isolated Linux CPU container]] builds on D:
and passes 18 synthetic control tests. Limits: 2 CPUs, non-root/read-only,
network disabled; real-model memory ceiling 5 GiB. Real Qwen container smoke
passed: 15.78 s startup, ten short requests 0.59–0.74 s, 3.87 GiB cgroup peak.
Next: maximum-input/load measurement and image security review.
Existing API containers are outside this work. See [[docs/MEMORY|Current state]].

Setup update: Docker's disk now runs from D:, verified by full pre-start SHA-256,
active file locking and unchanged 9-container/64-image/1-volume inventory.
Old C: data disk removed after verification; about 36.3 GiB is now free on C:.
Local Hugging Face login works from D:, but that token's account still gets 403
for EmbeddingGemma. Next: bounded CPU serving container on D:.
See [[docs/MEMORY|Current state]] before model/container work.

Newest verification: real persistent Qwen host smoke now passes. Startup 14.24 s,
three requests 0.51–0.71 s; same process reused and cleanly stopped. Post-request
RSS 2.54 GiB, not peak. Docker disk migration is now complete; Gemma access is denied.
See [[services/inference/README|Serving evidence and remaining gates]].

Newest: [[services/inference/README|Persistent CPU serving prerequisite]].
Process reuse, input/token limits and actual timeout cleanup have 14 synthetic
checks; 169 total tests and frontend quality/build checks passed on 12 October.
Docker storage migration from C: to D: is verified. Hugging Face login
works; Gemma terms acceptance/access must match the token's account. Container runtime remains unverified.

Latest: [[docs/TEXT_V2_RESULTS|Fresh text challenge and failure review]]. Forty
new sources and 64 questions are frozen; real Qwen 512 passes the development
gate with 100% document recall and 99.11% evidence recall. Exact-code/temporal
ranking and a missed multi-part passage remain open. 39 evaluation tests and
frontend build pass. Next: a local serving container with explicit resource limits.

10 October checkpoint: [[docs/CPU_BENCHMARK|First real Qwen CPU benchmark]] is verified on D:.
All 35 answerable development queries have relevant documents in the top five;
the set is too small to choose a production winner. Four-thread warm median
0.324 seconds; sampled peak RAM 3.58 GiB. 150 tests and frontend build pass.
EmbeddingGemma terms are now accepted; local access/runtime remains unverified.
Visual/OCR and chat are not tested.

Docker recovery is verified: hash-locked build and offline checks pass. Current
security gate: the 8 October scan reports 29 records, including two high.
Package versions are unchanged this turn; scan/feed changes are not new code
fixes. TASK-023 remains partial after earlier OpenSSL/PCRE2 and installer fixes.
See [scan review](../services/worker/IMAGE_SCAN_REVIEW.md). Source quality checks
cover 145 tests. OKF remains a later optional export idea (ADR-029).

[[docs/DELIVERY_PLAN|Current delivery and system design plan]] explains the target
architecture, flows, security tests and next tasks. TASK-023 retains unresolved
security gates. TASK-019B transport and offline supervision pass controlled tests;
Whole-fetch deadlines and controlled fetch-to-parser integration now pass.
Production confinement and browser/tool egress remain open. See
[[services/worker/SUPERVISION|Verified worker boundaries]].

[Explorable target architecture](../.archify/architecture-gather-plan-20261002-081351/gather-plan.html)
has nine passing structural checks and verified plan references; browser/visual
review was not performed. Save/search flow diagrams are inside DELIVERY_PLAN.md.

## Goal and present focus

Find saved files and links without remembering their names or exact wording.
Search first; document chat is deferred. Desktop: Tauri + React + TypeScript.
Cloud AI is planned on Google Cloud Run, CPU first; Supabase Free is the intended
vector backend and R2 stores originals. The user created a Google Cloud account.
No deployed app/inference endpoint is verified. The local benchmark is separate.

## Navigate the project

| Question | Authoritative note |
| --- | --- |
| What works now? What remains unverified? | [[docs/MEMORY|Current state]] |
| What is done and what is next? | [[TASKS|Delivery board and acceptance criteria]] |
| What happened, and what was tested? | [[docs/PROGRESS|Work journal]] |
| What are we building? | [[docs/PRD|Product requirements]] |
| How will the parts work together? | [[docs/ARCHITECTURE|Architecture]] |
| Why did we choose this approach? | [[docs/DECISIONS|Decision record]] |
| What do the techniques mean? | [[docs/knowledge/SEARCH_CONCEPTS|Search concepts]] |
| What ideas are agreed or still open? | [[docs/knowledge/IDEAS_AND_QUESTIONS|Ideas and open questions]] |
| How should it look? | [[docs/DESIGN|Design]] and [[docs/DESIGN_AVOID_LIST|Avoid list]] |
| How will we verify and protect it? | [[docs/TEST_PLAN|Tests]], [[docs/SECURITY|Security]], [[docs/PRIVACY_RELEASE_AUDIT|Release gates]] |
| How are bookmarks handled? | [[docs/BOOKMARKS|Bookmark specification]] |
| How should these notes be maintained? | [[docs/knowledge/OBSIDIAN_WORKFLOW|Obsidian workflow]] |

Open [[docs/knowledge/Search flow.canvas|Search flow canvas]] for the visual map.

## Latest verified development checkpoint

As of 8 October, 145 tests passed (112 worker, 29 evaluation, four UI), with lint,
types, formatting and frontend build. Locked-image smoke and timeout cleanup pass.
Native build previously passed; visual verification and remote CI remain unverified.

Implemented building blocks: desktop fixture preview, TXT/Markdown processing,
offline bookmark extraction, TF-IDF baseline, saved-vector comparison and a
mock-tested embedding request client. This is not a working end-to-end semantic
search app yet. Details and evidence belong in the linked state and task notes.

## Immediate next step

The broader frozen text set is measured. Continue TASK-005 with a bounded
serving-container test before committing to model dimensions, fusion or cloud sizing.
[[docs/CPU_BENCHMARK|Benchmark method and evidence]] explains dense retrieval,
dimension reduction, timings and their limits. Local downloads are on D: only.

TASK-021 now has 49 database checks plus 31 real Auth/PostgREST/Storage checks;
see [[supabase/LOCAL_INTEGRATION|Local API verification and limits]]. Private
original access and API deletion before SQL finalization pass. The disposable
stack is removed after checks; desktop persistence is not connected. Next: upload
fencing, background reconciliation and job leases.
[[docs/knowledge/SEARCH_CONCEPTS|Concepts]] explains the cleanup ordering.

Extraction stack accepted 30 September: [[docs/knowledge/EXTRACTION_STACK|Crawl4AI and yt-dlp]].
Agent Reach is optional; selected tools are installed in the offline Docker image,
but live invocation and desktop integration remain pending.

TASK-018 is complete: offline bookmark passages and keyword retrieval tests.
TASK-019 offline runner and container smoke checks pass; next are dependency remediation,
public-only network enforcement and actual extraction execution. Then connect private storage,
restricted fetching and genuine cloud embeddings as their prerequisites become
available. Chat stays deferred. Commit locally; push only on the user's request.

Repository organization: [[docs/REPOSITORY_AUDIT|File-by-file cleanup audit]].
