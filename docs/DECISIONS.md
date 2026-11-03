26 October: preserve only fixed model diagnostics through the existing inference and embedding exception contracts; unknown upstream text remains redacted. Keep readiness an explicit authenticated GET, separate from embedding, per-process attempts and service-wide billing. Preserve five-second requested identity allowance, 15-second outbound operation and three inference attempts; never automatically resend after unknown outcomes. See MODEL_AVAILABILITY.md.

26 October: reuse the authenticated listing RPC for one bounded publication preflight before query embedding. Only a complete page can prove no publication; incomplete pages retain normal search to avoid false negatives. Return genuine empty context rather than synthetic vectors or treating database failure as emptiness. No new SQL function, limits or retries. See EMPTY_LIBRARY_SEARCH.md.

26 October: choose a private two-account TextFiles pilot after the user delegated scope selection. Keep default fixed-content guards; a UI checkbox cannot enable the backend. Require review/confirmation, actual-byte validation and <=3 pinned-tokenizer passages before storage to fit the unchanged provider budget. Never clear a request ID after any earlier uncertain send. General upload release gates remain open; see PRIVATE_TEXT_FILES.md.

26 October: use an unsigned versioned position cursor, immutable creation time plus UUID ordering and independent auth.uid() ownership on every page. Keep published and processing versions separate; restore data after authentication without persisting browser credentials. Listing must never initiate inference or processing. See SAVED_LIBRARY.md.

25 October: the development operator API should fetch a fresh short-lived pinned Google caller token per inference request rather than keep an hour-long token for its process lifetime. On shutdown, print a fixed clean-stop message rather than a Python traceback. Do not cache refresh credentials or auto-retry model calls.

25 October: the operator API lives longer than an access token. Mint Google caller identity per inference request using the fixed operator account, project, audience and service account; never cache it across requests or expose it to the browser. Keep inference timeout and no-automatic-retry limits unchanged.

25 October: report safe search-stage categories to the operator instead of one generic backend 503. This supports targeted diagnosis without reading or logging upstream body text. The previous database-category incident remains unconfirmed; do not infer its cause from an empty Cloud Run error log.

25 October: keep search dependency errors as separate fixed codes (session, model, database) because one generic 503 misled operator debugging. Never forward raw third-party error bodies. No automatic inference retry after a startup failure.

25 October: frontend developer scripts may use an explicitly selected GATHER_NODE runtime or the existing Codex-bundled Node path when ordinary PATH lacks a supported version. Keep version checks, avoid global PATH mutation/software installation, and surface a precise missing-runtime error.

25 October: gate operator worker claiming on model startup readiness under the existing approved run-scoped warm-capacity context. Do not increase inference deadlines or consume job attempts during scale-from-zero admission failures. Restore min0 after the bounded worker run, never hold warmth across interactive UI handoffs.

25 October: select an operator's requested job inside the database claim transaction, not after a FIFO claim. Share the existing single-flight/lease implementation so targeted work cannot consume an unrelated job's attempt budget. Keep idle/claim-failure distinct and emit fixed safe receipt diagnostics; never reset retries or remove unrelated work to unblock a pilot.

24 October: wrap injected/default fetch in a plain function invocation; storing native fetch as a client method changes its receiver and fails in Chromium. Keep a receiver-sensitive regression because permissive Node mocks missed this. Network error text alone is not evidence the API is stopped.

24 October: expose the first UI connection only as a development-browser operator pilot, restricted server-side to existing test users and fixed synthetic content. Keep public/native connected mode gated. Use explicit loopback Host and one-origin CORS, separate bounded worker invocation, session-only tokens and immutable retry payloads. Cancellation leaves durable recovery intact and does not claim rollback. No permanent warm capacity or automatic cloud retries.

22 October: reuse LibrarySession behind a dependency-free ASGI adapter. Keep worker execution separate from queued HTTP admission, and retain the operation slot until its thread finishes after timeout/disconnect. Do not confuse cancelling a response with rolling back a committed database write. No public listener until composition, rate/security and privacy gates are verified.

# Architecture decisions

22 October: separate Cloud Run scaling acceptance from readiness. Submit min1 with
--async, observe the target's current generation/Ready state under the existing
startup deadline, then make one authenticated /ready request with its remaining
budget. Acknowledged min0 restore remains synchronous. Avoid a second independent
long wait or inference retry; retain operator-only scoped capacity and rollback.

22 October: make pilot warmth a run-scoped lease after hidden prompts, restored
to minimum zero in finally. Keeping minimum one across manual handoffs caused
hours of idle reservation; the operator runner must release it on success/failure
and expose uncertain rollback. Keep explicit personal/Gather CLI scope and no
public/IAM/image/resource changes. OS-kill recovery remains an operator obligation.
Pilot handshake allowance is ten seconds inside the approved fifteen-second total;
production connect/operation defaults and SQL/model limits remain unchanged.

21 October: keep existing transaction/function contracts and add an isolated
Psycopg helper per DB operation. A socket timeout alone cannot bound DNS or commit;
the parent enforces five seconds plus one-second cleanup. Separate admission and
worker logins, fixed transaction-local roles, explicit verified owner and no
retry preserve fencing/idempotency. Reuse the installed driver for local proof;
production dependency approval and hosted TLS verification remain separate.

21 October: use one internal LibrarySession bound to the original user bearer.
Resolve import ownership through actual Supabase Auth and keep published reads,
job status and deletion under that same session. Do not substitute a service key
or accept an owner field. Reuse existing private admission and public owner-scoped
RPCs. Hosted connection/HTTP admission remains a separate composition gate.

## 20 October: isolated Gather pilot and bounded release artifact

Use gather-development-511211, asia-south1, INR 500 maximum total pilot budget.
Never use primeval-splice-467909-k5/Intrixshield or alter its configuration.
Use explicit account/project arguments after personal-account CLI sign-in.
Package verified immutable model files into the tested serving image, retain
hash-pinned source notices, and verify the baked image instead of mounting host
weights for its final smoke. Reuse unchanged model layers. Exact audience matching
remains required while allowing Google's documented multi-label run.app origins.
These decisions prepare a pilot, not authorize provisioning or waive findings.

## 19 October: explicit cloud composition, preserved local default

Use a separate services.inference.cloud_startup module. Environment variables
alone must never enable public binding. Validate intended IAM policy through the
existing IdentityConfig and match it to the receiver's callers; require the actual
managed verifier in the server factory. Retain the existing bounded HTTP/lifecycle
implementation. This declaration is not evidence of deployed Google permissions;
real IAM/header/cold-start acceptance stays in the approved pilot. See CLOUD_STARTUP.md.

## 18 October: maintain a narrow local zlib backport

User prioritized fixing zlib. Debian maintainers confirm the older direct-write
error path can retain invalid input state; absence of non-blocking API is not
an exemption. Adapt upstream df84af25 to the installed 1.3.1 source, retaining its
return expression and resetting only the two input fields. Use a separately
versioned local Debian package with pinned hashes and original-versus-patched
regression evidence. Replace it with a verified official update when available.
This resolves the tested error path, not every release gate or scanner finding.
Details and source provenance limits: services/inference/zlib/README.md.

## 18 October proposal: CPU allocation must support key refresh

CLOUD_PILOT_PLAN.md supersedes the earlier request-based billing proposal.
Background refresh cannot assume idle CPU under that mode. Prefer instance-based
CPU for a supervised pilot, retaining minimum zero and fresh-key rejection.
This is a proposal requiring spend approval, not authorization to change billing.
An alternative request-driven refresh design requires its own bounded design and
verification; do not add it implicitly or relax freshness.

## 18 October: separate Cloud Run and application token headers

Use X-Serverless-Authorization for platform invocation and preserve Authorization
for independent signed-token verification. Use one acquired token, no extra fetch,
static-secret fallback or larger receive limit. Cloud-client token cap is 7,168
characters to budget both copies. Google documented precedence motivates this
choice; actual deployed handoff/IAM remains a required test, not an assumption.
See CLOUD_IDENTITY.md for source and acceptance checks.

## ADR-059: scheduled trusted-key refresh, independent of request key IDs

Use the existing isolated HTTP helper for one fixed Google HTTPS certificate URL.
Honor upstream freshness, capped at five minutes, and atomically replace only fully
validated snapshots. A single lifecycle thread refreshes with a 30-second minimum
interval; inbound unknown keys cannot amplify network calls. On transient failure,
retain still-fresh keys without extending their expiry. Prefer temporary denial
over stale trust. Startup fetch precedes model loading; shutdown cancels and joins.
This is locally verified behavior, not deployed IAM or a live-key validation claim.

## ADR-058: bounded offline receiving verifier before trusted-key lifecycle

Use Google's JWT library with explicit RS256 and exact service-account subject as
well as email. Requests cannot select signing keys or endpoints. Trusted key
snapshots expire within five minutes; expiration rejects auth and readiness.
Separate verification from trusted HTTPS key retrieval/rotation so neither token
parsing nor attacker-selected key IDs can initiate unbounded network work. Keep
public binding blocked until real IAM/header handoff and other release gates pass.
See RECEIVING_IDENTITY.md for local evidence and incomplete production integration.

## ADR-057: additive Linux serving lock without model dependency drift

Keep the existing CPU lock and Dockerfile; add a separate combined serving lock
containing exactly those original dependencies plus seven serving dependencies.
Staging verifies original wheel hashes even on lock regeneration, uses exact code
allowlists and skips model copying. Reuse cached artifacts on D:; preserve the
stream entry point and public-bind guard until receiving cloud auth is implemented.
Hash pins support repeatable Python installation, not archived Debian availability
or proof of security. See services/inference/SERVING_IMAGE.md for evidence/gates.

## ADR-056: explicit metadata identity with bounded cache lifetime

Reuse the isolated HTTP helper for Google metadata acquisition, with a fixed
destination and five-second bound inside the 15-second inference HTTP budget.
Require explicit caller/audience/intended invokers, no ADC key-file lookup or secret
fallback. Cache only until expiry minus 60 seconds using wall and monotonic clocks.
Claim inspection is configuration validation, not cryptographic authentication.
Keep public binding blocked until receiving auth and actual IAM gates are verified.
See CLOUD_IDENTITY.md; no cloud changes are authorized by this local implementation.

## ADR-055: lifecycle-owned ASGI runtime with guarded serving dependencies

Use FastAPI lifespan and one Runtime child; offload inference while preserving
nonqueued admission and responsive readiness. Cancel startup/active work from
the Uvicorn shutdown hook before draining tasks. Pin the protocol implementation
and patched h11 parser; keep total receive protection below ASGI header parsing.
Public binding remains disabled until managed identity is configured/tested.

Reuse installed packages for local verification with patched h11 isolated on D:;
do not alter unrelated environments or conflate the local dependency snapshot
with a reproducible Linux production lock. See INFERENCE_ASGI.md for remaining
gates and verification scope.

## ADR-054: production hosting and service identity direction (17 October)

Plan separate Cloud Run application API and IAM-protected CPU inference, using
short-lived service ID tokens and dedicated least-privilege accounts. Supabase
user sessions/RLS still govern document ownership. No service-account key files
or local shared bearer secret promoted into the desktop/cloud identity scheme.

Propose FastAPI/Uvicorn single web process around existing Runtime; preserve its
limits, one inference at a time and 2-CPU/5-GiB pilot budget. Do not ship the local
standard-library server as public ingress. Region/spend approval, managed-token
implementation, cold-start policy and release gates remain pending. The initial
min-zero/max-one experiment does not guarantee latency, availability or cost caps.
See CLOUD_RUN_DESIGN.md for sources, identity matrix and acceptance order.

## ADR-053: verify inference HTTP locally before production ingress (16 October)

Wrap the existing process runtime without changing model behavior or deadlines.
Use an explicitly injected service bearer credential and strict loopback binding
for local integration. Separate five-second header/body reception from bounded
model computation; a disconnected client cannot disable server-side termination.
Limit handler connections and reject busy model work instead of queuing. Keep
public deployment, mature production ingress and managed identity as separate
review gates, rather than present the standard-library server as cloud-ready.
See INFERENCE_HTTP.md.

## ADR-052: bounded fixed-service clients before hosted inference (16 October)

Reuse the existing JSON contracts with fixed per-session credentials and allowed
read routes. Use an isolated helper for each HTTP request, following the existing
fetch broker's process-deadline approach, so DNS and trickling responses cannot
outlive the request budget. No bookmark-fetch policies are relaxed: these clients
accept operator configuration only. Keep one nonblocking HTTP slot per process,
5/15-second deadlines and bounded bodies. Do not add a dependency or cloud service.
Inference HTTP handler/auth and remote TLS verification remain explicit next gates.
See SERVICE_CLIENTS.md.

## ADR-051: internal query coordinator with exact-version context (16 October)

Reuse the ingestion provider contract, query template, published RPCs and existing
context algorithm. Authenticate through a single-user transport before inference;
never take an owner ID from the request. Limit reads to five selected sources,
validate every candidate, and omit stale citations rather than open replacements.
Keep one query embedding and no automatic retries. Boundaries and pending real
transport/deployment verification are explicit in QUERY_SEARCH.md.

## ADR-050: reuse PostgREST for authenticated published reads (16 October)

Expose two narrowly granted SQL functions through the existing Supabase JWT
boundary. Derive ownership from auth.uid(), filter by published pointer and exact
model identity, then use exact cosine ranking. Materialize eligible vectors before
distance calculation to exclude incompatible dimensions. Require the search
version when opening content, so stale citations fail instead of changing meaning.
Reuse the existing context assembler later; no second ranking/context service or
custom JWT verifier is introduced. Large-library performance and production query
rate/deadline controls remain gates. See PUBLISHED_SEARCH.md.

## ADR-049: bounded internal coordinator and durable original handoff (16 October)

Reuse the existing database queue, parser, token chunker and publication functions.
Store bounded original bytes in a private version-bound table in the same
transaction as submission, avoiding an uncoordinated local-file handoff or a new
queue/storage subsystem. R2 remains the production originals target. Keep owner
identity outside the payload, supplied by a verified server context to a narrowly
granted internal coordinator role. Production authentication remains a prerequisite.

Use ten-second heartbeat renewal plus cooperative runtime cancellation backed by
process termination. Reuse only committed vectors from the exact validated
manifest/version. Preflight at most 16 single-passage requests / 8,192 tokens per
job; preserve all existing database and inference limits. Require explicit provider
injection, with synthetic implementations confined to tests. No cloud fallback,
automatic model startup or deployment is introduced. See INGESTION_COORDINATOR.md.

## ADR-048: private staging and separate publication pointer (15 October)

Keep validated originals/passages/pgvector values in the existing database's
private schema. Restrict writes to lease-fenced worker functions, and separate
the processing target from the active publication so replacement failures do not
hide prior complete content. Publish the pointer and ready state in one source-
locked transaction; retain a hashed token receipt for safe lost-response retries.
Reuse existing version/owner foreign keys and cleanup rather than another store
or queue. Read published passages through auth.uid(), never from client-visible
staging. No vector-search endpoint or actual inference is implied by this slice.

Cap vector storage batches at 16 rows/512 KiB while preserving existing source,
passage, inference and retry limits. Use real pgvector in disposable tests via
the cached digest-pinned Supabase PostgreSQL image, keeping original memory/CPU
limits. The startup shim initializes only test roles, not vendor services; its
temporary bootstrap port avoids false readiness. See TEXT_PUBLICATION.md.

## ADR-045: bounded source context after ranking

Use source-neighbors-v1: first-ranked seed per source, at most five sources from
100 candidates, one neighbor per side, contiguous ranges only, 8 KiB/window and
32 KiB total text. Reserve seed bytes before expanding. Retain exact source/version
citations and reject visibility/integrity mismatches before output. The trusted
repository must enforce authentication, ownership and current-version/deletion
checks; this pure component cannot replace them. Context is for readers, not an
automatic increase to model input limits. Replay saved verified vectors first;
known-case coverage improved without new inference. See SEARCH_CONTEXT.md for
evidence and limits; source ranking and default fusion are unchanged.

## ADR-044: compare chunk policies with fixed source evidence

15 October: compare legacy 1,024-character/128-character-overlap chunks against
the prepared 512-token/64-character-overlap policy using the same pinned patched
image, prompts, dimensions and query vectors. Freeze source/query/label hashes,
both index hashes, protocol and request order before inference. text-v2 documents
all fit in 512 tokens, so this compares consolidation there; a separate frozen
six-source boundary fixture tests longer inputs and conditional evidence.

Preserve exact evidence quotes and offsets across layouts. A quote not fully
contained in any chunk stays a strict evidence miss. Report continuous union
coverage across the first five passages separately, never as a replacement for
strict recall. Wrong-source text, overlap duplication and gaps cannot supply
missing evidence. Keep absent questions outside recall/MRR and report their
candidate returns without claiming answerability.

The predeclared text-v2 gate is >=0.90 document recall, strict evidence recall and
MRR, with no metric dropping more than 0.02 against the paired legacy result.
Boundary stress is diagnostic, including deliberately placed split conditions;
do not tune the fixture, overlap or rankings after observing scores. Keep
production ingestion unchanged until the measured limitations are reviewed.

Outcome: text-v2 gate passed; boundary dense strict evidence remained 0.50 despite
union coverage reaching 0.875. A multi-part query still missed both late passages.
Proceed to bounded same-source context assembly/coverage evaluation before
ingestion integration. Keep RRF diagnostic: it helps stress cases but lowers
text-v2 MRR versus dense. See CHUNK_RETRIEVAL_RESULTS.md; no retrospective tuning.

## ADR-043: separate patched candidate and token-aware source preparation

14–15 October: use maintained CPU Torch 2.14.1+cpu / Transformers 5.19.0 releases,
exact Linux wheel hashes and pinned Debian security updates in a separate image.
Retain the baseline and compare six synthetic token/vector/rank cases before
promotion. Fewer scan findings are not a production-security approval.

Prepare document slices with a trusted server-side tokenizer callback, <=512
tokens and 8 KiB, one slice per request, exact Unicode offsets and bounded overlap.
Keep existing index/parser versions unchanged until explicit integration/reindexing
and retrieval validation. On 15 October, real six-case compatibility and five-chunk
timing checks passed after approved transient clean-cache release. The RAM guard
was not bypassed and existing APIs were not stopped by this work. Keep candidate
promotion gated on remaining retrieval/security/licence review. End users still
do not download models.

## ADR-042: preserve failed CPU profiles and gate integration on remediation

14 October: retain the 15-second request deadline and 5 GiB memory ceiling.
2,048-token single and 4,096-token batch requests timed out; do not raise limits
or claim that accepted token budgets guarantee completion. Smaller chunks/batches
are the next candidate, requiring diverse-text and retrieval validation before
changing production policy. Fifty short sequential queries passed; concurrency
and long-duration memory behavior remain unverified.

Keep the exact benchmark image unchanged for comparison. Its scan has 56 open
records, including 12 high. Before API integration, patch OS packages and
compatibility-test a maintained CPU Torch/Transformers stack, regenerate locks,
remeasure and rescan. Avoid silently crossing a major library version during a
measurement task. No security finding is dismissed solely by sandboxing.

## ADR-041: prove the CPU container before adding network ingress (13 October)

Use a private bounded JSONL adapter for the next TASK-005 slice. This tests Linux
model serving without prematurely exposing an unauthenticated API. Hash-lock
the 25 Linux CPU dependencies separately from Windows, stage a minimal build
context on D:, and mount only a materialized/hash-verified model directory.
Never mount the Hugging Face home or token. Install offline; retain package and
model licence metadata. Remove pip and its bootstrap from the runtime image.

Run as non-root with read-only root/model, no network/ports, no capabilities,
no-new-privileges, 2 CPUs, 5 GiB RAM with no extra swap, 128 PIDs and 64 MiB tmpfs.
Use a unique container identity and remove only that test container. Existing
API workloads and shared Docker settings are explicitly out of scope. Keep the
4 GiB host free-memory guard; do not weaken it to obtain a benchmark result.

Build/dependency consistency and 18 synthetic Linux tests pass. Real container
smoke passed on 14 October after RAM became available: short requests at
0.593–0.742 s with a 3.87 GiB cgroup peak. Keep the 5 GiB test ceiling; these short
inputs do not establish worst-case sizing. No cloud deployment, production
security claim or public ingress is authorized by these local tests.

## ADR-040: persistent inference behind a killable process (12 October)

Keep the loaded model in a separate reusable process. A timed-out thread cannot
reliably interrupt native model work, so timeout handling terminates and reaps
the child. Reject concurrent requests rather than accumulating a queue; require
an explicit restart after failure. This is a private serving primitive, not an
HTTP API, OS resource sandbox or Cloud Run deployment. Use the frozen Qwen prompt,
revision and 512-dimensional space; do not replace the benchmark protocol.

Fourteen synthetic tests pass. The real host smoke passed on 13 October after
RAM became available; Docker storage on D: was subsequently hash-verified and
switched successfully on 13 October, clearing the packaging storage prerequisite. User confirmed
Gemma terms accepted and will authenticate locally; no token requested in chat.

## ADR-039: freeze fresh cases and preserve retrieval failures (12 October)

Advance TASK-005 with text-v2 rather than tune v1. Author 40 fictional sources
and 64 questions across eight new domains, including archived/current and related
records, eight late passages and eight absent cases. Freeze sources and relevance
quotes with a canonical hash before inference. Validate changes and reject mixed
corpus outputs. Keep v1 locations and twelve recorded artifact hashes intact.

Use unchanged Qwen revision, prompt, chunker, float32, exact cosine and RRF k=60.
512 dimensions was the primary candidate before results, with >=0.90 thresholds
for document/evidence Recall@5 and MRR. It passes (1.0/0.9911/0.9613). Advance it
to a bounded CPU serving-container experiment, not a final production selection.
1,024 has higher MRR and 512 better evidence recall; small samples do not prove
a universal optimum. RRF lowers overall MRR, so it remains a comparator.

Preserve the five nonperfect 512-dense cases and absent-neighbor behavior. Do not
edit labels or tune prompts to erase them. Exact identifiers, temporal distinctions
and multi-part evidence coverage need separate retrieval work. These examples
were authored by the assistant after v1, not independently labelled/blind. No
Cloud Run deployment, cost inference, additional model download or push occurred.

## ADR-038: measure self-hosted CPU embeddings on D: before deployment (10 October)

Latest user choices supersede provider-deferred notes: Google Cloud Run,
self-hosted CPU AI first, R2 originals, Supabase Free Auth/Postgres/pgvector.
The cloud account exists; no application deployment is verified by this task.
R2 is object storage, not a replacement vector database. Per-user/global storage
admission and request/compute quotas remain to be implemented; budget alerts
are not spending caps. Existing local Supabase Storage tests do not verify R2.

User permits local model downloads/testing on D: because C: has little space.
Use an isolated D: venv/cache/temp/output and CPU-only wheel, pinned model
safetensors, no remote model code, anonymous download and offline inference.
Model artifacts are ignored by Git. This developer benchmark does not change the
cloud deployment requirement or require end users to download weights.

User explicitly chose Qwen first; EmbeddingGemma terms have not been accepted.
Keep that candidate pending without bypassing the gate. Keep chat deferred and
require a separate visual corpus for SigLIP/OCR rather than scoring them as text
models. Reuse text-v1 and the existing strict cosine/RRF scorer, with labels
excluded from inference. Reject token overflow before model execution.

Measured all three Qwen dimensions on two/four threads. 512 dimensions has the
best development-set MRR (0.9857), but no production winner is selected from
35 answerable examples. Fixed RRF lowered ranking quality versus dense; expand
the evaluation before choosing fusion. Laptop timing is not Cloud Run billing
or service capacity. See CPU_BENCHMARK.md for reproducible evidence and limits.

## ADR-037: verify core APIs and order Storage cleanup before SQL (9 October)

Use real Auth, PostgREST and Storage images with a disposable PostgreSQL database
to move beyond identity shims. Auth/Storage install their own schemas; the harness
supplies test roles and exercises real JWTs. Image digests are pinned. Only the
gateway has an explicit loopback port; database/file data lives in bounded tmpfs.
This verifies core API behavior, not complete hosted/CLI/default-grant parity.

The CLI's recommended network-level loopback setting still published on all
interfaces in this environment. Stop that stack and use explicit Compose port
bindings verified before fixtures. Do not change Docker's global settings or
unrelated workloads. The CLI is not required by the final test runner.

Create a private, bounded original-file bucket with owner/live-source read policy.
Keep client upload/overwrite/delete denied. Remove bytes via the Storage API;
SQL finalization refuses remaining source-prefix object metadata. A failed or
interrupted external removal retains the cleanup request and slot charge.
31 API checks pass, including two-owner isolation and retry after external removal.
No background worker is implemented. In-flight privileged uploads, signed URLs,
orphan reconciliation and byte/rate budgets need explicit follow-up gates.

## ADR-036: serialize source quotas and preserve deletion receipts (9 October)

Use per-owner quota row locks to serialize saves and cleanup. Store source,
receipt and slot charge atomically; derive owner from auth.uid() and restrict
security-definer functions with an empty search path and explicit grants.
No default allowance: trusted administration must configure it. This is a
source-count quota only; byte/rate/inference budgets remain future gates.

Retain minimal idempotency receipts after database cleanup so a repeated save
cannot resurrect a deleted source. Reusing the key with changed input fails.
Retention/account erasure needs a future explicit policy. Deletes create durable
cleanup requests and tombstones together, retaining quota until cleanup commits.
Database-only cleanup has no worker grant and must not finalize future Storage
assets before verified external deletion. Version writes lock the live parent.
45 SQL assertions and four concurrency scenarios pass on PostgreSQL with a
test-only Auth contract; no full Supabase/desktop integration claim.

## ADR-035: verify source ownership before enabling ingestion (8 October)

Start TASK-021 with Supabase-targeted SQL migrations and a disposable PostgreSQL
17 harness. The system drive has about 2.7 GB free; avoid the full Supabase stack
and leave unrelated Docker services untouched. Test-only auth.users/auth.uid
contracts permit actual role/RLS checks but do not prove JWT, Auth or Storage.
Pin the test image by digest, use bounded tmpfs/no network/no host ports, clean up
only the generated test container. No application data is retained.

Clients may read their records and edit title/notes. Creation, ownership,
versions and deletion are not client-writable. Composite owner/source foreign
keys stop inconsistent privileged writes. Tombstones hide dependent versions;
cleanup and quota transactions must precede enabling lifecycle APIs. Do not add
vector dimensions or ready states before model/publication contracts exist.

## ADR-034: supervise the entire fetch and pass bytes to offline parsing (8 October)

Use one fixed Python child per fetch so the parent deadline also covers blocked
OS DNS and TLS/connect operations. Bound both streams and the decoded result,
allowlist inherited environment, kill/reap on timeout/cancel, and never publish
partial or still-running output. No arbitrary child code comes from job data.
The host process boundary is lifecycle control, not a production OS sandbox.

Add an explicit http-page adapter instead of relabelling raw HTML as Crawl4AI
output. Preserve URL, fetch time, redirects, raw-body hash and actual parser
provenance; plaintext remains literal. Pass bytes into the existing network-none
Docker runner. Failures leave persistence decisions to the future coordinator;
no save/index or semantic readiness is claimed. Browser/tool egress, durable job
recovery, external compatibility and open dependency findings remain release gates.

## ADR-033: separate restricted fetching from offline parsing (3 October)

Introduce a small backend-only page transport that approves each DNS/redirect
hop, dials numeric approved addresses and preserves TLS hostname checks. Do not
forward cookies or execute page scripts/assets; reject compressed/unbounded data.
Known NAT64 ranges are denied to avoid translating a public-looking IPv6 address
into private IPv4. Test injection is trusted code, never a request option.

Keep the supplied-output parser on network none behind DockerJobRunner, with
fixed operator-selected image digest/entrypoint, bounded I/O and resources,
timeout/cancellation and exact-container cleanup. No Docker socket in the worker.
Plain HTTP transport is not browser egress enforcement, and socket deadlines do
not bound OS DNS. TASK-019B remains partial until a whole-broker process deadline
and integration are tested. Durable crash cleanup and global quotas remain later
coordinator responsibilities. See services/worker/SUPERVISION.md.

## ADR-032: patched runtime without Python installer tooling (3 October)

Keep the existing reviewed base and 96 application wheel pins. Add exact Debian
security versions for OpenSSL/PCRE2, then remove pip plus ensurepip from the runtime
filesystem. A separate named installer target retains build-time pip/hash checks.
This reduces runtime attack surface; it does not erase parent layers, make the
installer target safe for untrusted jobs, or freeze Debian repository availability.
Do not delete package metadata to hide scanner findings. Full rescan and runtime
absence/version probes verify the change; remaining findings stay open in TASK-023.

Windows subprocess timeout cleanup must remove the named Docker container before
closing inherited pipes, since killing Compose alone can wait for its child job.
A deliberate 120-second job now aborts and cleans up within a 20-second test budget.

## ADR-031: separate scan completion from security readiness (3 October)

The locked image now builds and passes offline restrictions. Its completed scan
still has open findings, including OS packages and pip bundled dependencies.
Track all records in IMAGE_SCAN_REVIEW.md and remediate through TASK-023 before
live execution. Do not treat a top-level package upgrade or disabled networking
as dismissal of a bundled-library advisory. Developer smoke jobs use unique names
and explicit cleanup on timeout; this does not replace the production supervisor.

## ADR-029: retain OKF as an optional extension (2 October)

User accepted keeping the recommendation: Open Knowledge Format may later support
portable linked notes and Obsidian exports. Keep keyword/vector retrieval and
Supabase as the search core; selected-source RAG chat remains deferred. Preserve
originals/citations and evaluate generated knowledge before indexing it as trusted
material. No OKF package or runtime added. Official format reference:
https://github.com/GoogleCloudPlatform/open-knowledge-format

## ADR-030: hash-locked extraction inputs, explicit review gates

Freeze the tested Linux/amd64 application package set as 96 exact wheel artifacts.
Pin the Python base by platform digest and bootstrap pip separately. Reject source
builds/unhashed dependencies during installation; don't assume a lock is proof of
security. Keep declared-license inventory and a repeatable advisory lookup that
fails visibly on feed errors/findings. NLTK's unpatched advisory and the incomplete
OS scan remain gates before live execution. Rebuild verification is blocked by
Docker storage health on 2 October. See services/worker/DEPENDENCY_REVIEW.md.

## 2 October proposals: ADR-026 through ADR-028

- ADR-026: propose a modular Python/FastAPI backend and trusted coordinator with
  separate restricted extraction. Retain Tauri/Supabase; recommend Cloud Run for
  later HTTP/batch hosting, subject to budget and egress feasibility. No service
  provisioned. Avoid additional brokers/GKE until measured requirements justify them.
- ADR-027: propose private Postgres jobs with atomic claims, leases, bounded retries
  and reconciliation. Source/version/job persistence is transactional; dispatch is
  recoverable. Requires concurrency, lease expiry, quota and deletion-race tests.
- ADR-028: propose separate keyword/semantic readiness and immutable generations.
  Activate only complete indexes, preserve old versions on failed refresh, and
  enforce tombstones at publication. Never substitute fake vectors for real AI.

These are planning defaults, not implementation claims. Details, tradeoffs,
dependencies and acceptance gates: [DELIVERY_PLAN.md](DELIVERY_PLAN.md).

Recorded 26 September 2026 from this project's existing decisions. Accepted means product/architecture direction, not implemented functionality.

| ADR | Decision | Reason / consequences | Status |
| --- | --- | --- | --- |
| 001 | Windows-first Tauri + React + TypeScript | User selected desktop; retain modern UI and controlled native boundary. Rust/toolchain and installer QA required. | Accepted |
| 002 | Supabase Free, Postgres + pgvector | User preference if free; auth, RLS and vectors together. Shared quotas/inactivity and online search are constraints. Chroma is contingency, not simultaneous backend. | Accepted |
| 003 | Local worker and inference | Original zero-recurring-cost approach; retained for history. | Superseded by 009 |
| 004 | Specialized model pipeline | EmbeddingGemma text, SigLIP visual, PaddleOCR scanned text, Qwen3.5 4B chat/vision. Runtime, versions, dimensions and quantization need measured selection. | Candidates accepted; benchmark pending |
| 005 | Separate embedding spaces + hybrid ranking | Text/image vectors are incompatible; keyword results preserve exact-name lookup. Group by original file. | Accepted |
| 006 | RAG first, no agentic file actions | Core need is reliable search and grounded answers. Model-directed tools/actions remain out of scope. | Accepted |
| 007 | User's anti-template design rules | Local fonts, solid surfaces, restrained interactions. GSAP blanket reveals and Lucide removed. Lenis optional, Motion selection, paused orb sample. | Implemented; visual QA pending |
| 008 | Structured delivery loop and Git checkpoints | User requested documented, small, tested, reviewed tasks through production. Adapt web examples to desktop, preserve the agreed stack. | Accepted |

Change a decision by adding an entry with alternatives, evidence and migration consequences. Do not silently replace accepted choices. MODEL_STRATEGY.md holds candidate research; resource/licensing notes live in DESIGN_AVOID_LIST.md.

## ADR-009: cloud AI, deployment deferred (27 September 2026)

User explicitly chose cloud-hosted AI to avoid end-user model downloads. Desktop
and Supabase Free stay; inference moves behind an authenticated cloud service.
Cloud provider, budget, runtime and queue are not selected and no paid resources
are authorized yet. Prior laptop-based model candidates need cloud cost/quality
evaluation. Shared provider credentials must never enter the desktop bundle.
Uploads/inference require ownership, quotas, retention disclosures and the
privacy release gates before real user content. Local SQLite job orchestration
is no longer the default target; durable cloud jobs will be designed later.

## ADR-010: bounded, transport-independent text contract (27 September 2026)

TASK-004 uses the Python standard library with strict UTF-8 input and exact
Unicode code-point source offsets. Preserve original text rather than normalize
away citation positions. Content hashes and versioned chunk IDs make retries
deterministic, but are never ownership credentials. Start with 64 KiB sources
and 1,024-character passages; actual tokenizer limits are TASK-005's gate.
Do not add an HTTP service, provider SDK or desktop bridge to test extraction.

## ADR-011: source-grounded retrieval development fixtures (27 September 2026)

Use original fictional TXT/Markdown documents with manually authored evidence
quotes. Derive exact offsets/acceptable overlapping chunks through TASK-004
rather than hand-maintaining chunk IDs. Fingerprint source content, questions
and labels; keep expected answers out of model inputs. Distinguish document
retrieval from evidence retrieval and absent-answer behavior. This authored
English development set is not independently reviewed or held out; broader
corpora and visual/OCR evaluation remain required before release claims.

## ADR-012: untuned lexical comparator and strict scoring (27 September 2026)

Use standard-library TF-IDF cosine retrieval as an inexpensive, reproducible
keyword baseline. No query-specific synonyms, stopwords, stemming or label access.
All positive-score chunks are ranked; score document recall after deduplicating
sources, but evidence recall on the first five chunks. Preserve absent queries
outside answerable metric denominators and do not equate candidates with answer
claims. Require complete rankings, valid source/chunk pairs and matching corpus
and processed-index hashes. This comparator is not production retrieval or proof
that embeddings are unnecessary. No provider dependency or paid resource added.

## ADR-013: saved-vector adapter before hosted inference (27 September 2026)

Decouple embedding production from offline comparison using a versioned export.
Validate consistent spaces and complete results before exact normalized cosine
ranking; compare it with TF-IDF and equal-weight RRF (constant 60). Use exhaustive
search for the small evaluation set so approximate-index behavior cannot obscure
model comparisons. Keep all similarity signs; do not invent an abstention
threshold. Tag synthetic vectors explicitly and never report their scores as
model quality. Real provider selection/token checks/usage accounting remain open.

## ADR-014: local quality command and manual CI (28 September 2026)

Use ESLint/TypeScript/Prettier plus the existing Python and UI tests/build in one
local command. Pin added development dependencies and commit the lockfile.
GitHub workflow is manual-dispatch only; authored but not run or pushed. Native
build/QA remains separate. User explicitly controls all pushes.

## ADR-015: bookmarks as library sources (28 September 2026)

User requested links including blogs, gaming sites and Instagram video URLs.
Save URL/notes first and enrich asynchronously; reuse the passage/vector pipeline.
Distinguish bookmark saving, available metadata, extracted page text and actual
video understanding. Inaccessible content remains a useful saved link. Build
synthetic extraction first, then owner-scoped persistence and restricted cloud
fetching. See BOOKMARKS.md for states, SSRF controls and release gates.

## ADR-016: search first and offline bookmark parsing (28 September 2026)

User deferred chat until later. Prioritize source ingestion and search; chat is
not a first-search release gate. Use a bounded standard-library HTML parser for
the initial offline contract, preserving metadata/text provenance and unavailable
states. This is a conservative heuristic, not universal article extraction or an
SSRF-safe fetcher. Real-world parser evaluation and cloud fetching remain pending.

## ADR-017: one documentation set for Obsidian and development (30 September 2026)

User requested ongoing Obsidian reference and documentation. Use the repository
as the existing vault, with PROJECT_HUB linking canonical documents. Add learning
notes, idea/session templates and a status-labelled canvas; avoid a duplicate
task ledger. Keep Obsidian settings/workspace local, preserve personal notes, and
do not enable services or community plugins. Update this knowledge base during
development checkpoints; app UI behavior remains unverified.

## ADR-018: Agent Reach-backed extraction adapters (30 September 2026)

User requested Agent Reach for saved links. Prefer selected upstream tools behind
explicit worker adapters; Gather owns durable bookmarks, passage provenance,
embeddings and retrieval. Toolkit setup is not a production fetching API.
Instagram's documented desktop Chrome-session path does not fit the current
cloud-worker plan. Public-page integration remains pending review and tests.
See docs/knowledge/AGENT_REACH.md for sources, limits and delivery gates.

## ADR-019: Crawl4AI and yt-dlp selected (30 September 2026)

User accepted the recommended stack: self-hosted Crawl4AI for webpages and yt-dlp
for supported video metadata/available subtitles. Supersedes ADR-018's core
Agent Reach preference; Agent Reach remains optional. Use explicit adapters and
preserve existing save/index/fetch security boundaries. No autonomous agent,
media download, transcription or visual video analysis is part of the initial
adapter. faster-whisper and chat remain deferred. Open-source licensing does
not make cloud operation free. Implementation order: TASK-018, TASK-019, TASK-017.

## ADR-020: archive historical prototype rather than discard it

On 30 September the user requested repository cleanup. Preserve the old PyQt,
Ollama, Chroma and agent experiments unchanged under legacy/ for reference, with
explicit unsupported status. Remove only unreferenced scaffold logos and OS
metadata. Preserve private data, environments, user notes and build dependencies.
Historical audit paths describe the old layout and remain historical evidence.

## ADR-021: field-specific versioned bookmark passages

TASK-018 reuses the existing text processor independently per URL, metadata,
notes and page-text field. Preserve exact field offsets and label evidence types;
version the whole extracted bookmark so retries remain stable and refresh changes
cannot share stale chunk IDs. IDs are not access control. TF-IDF remains an
offline test baseline, not claimed semantic search. No evaluation imports in the
worker. Crawl4AI/yt-dlp output normalization follows as TASK-019.

## ADR-022: normalize extractor output before enabling execution

Use pure Crawl4AI/yt-dlp output adapters and the existing passage builder. Preserve
Markdown without HTML reparsing; subtitle chunks retain overlapping timing cues,
language and automatic-caption provenance. Backend version/fetch time participate
in revision identity. Caller-supplied fixtures are not proof of live extraction.
Keep TASK-019 partial until isolated runners, pins and network checks exist.

## ADR-023: bounded caption parsing before downloads

Use a strict retrieval-oriented UTF-8 SRT/WebVTT subset, not a browser renderer.
Preserve overlapping/repeated cues and multiline text; strip display markup and
ignore VTT NOTE/STYLE/REGION blocks. Reject malformed cue blocks atomically.
Keep download/network execution separate and TASK-019 partial. Reference:
https://www.w3.org/TR/webvtt1/ (checked 30 September 2026).

## ADR-024: destination preflight is separate from network enforcement

Use an injected resolver and reject any non-public/mixed DNS answer, alternate
numeric host notation and non-web ports. Return immutable approved addresses.
The future transport must connect without resolving again and preserve TLS
hostname verification; browser subresources and redirects require the same
boundary. Do not equate DNS preflight tests with SSRF-safe live extraction.
Direct pins selected from PyPI: Crawl4AI 0.9.4 (Apache-2.0), yt-dlp 2026.8.19
(Unlicense). Transitive licences/lock and installed compatibility remain pending.

## ADR-025: network-disabled initial container

Use a dedicated extraction build context allowlist, non-root/read-only runtime,
resource limits, no host mounts and network_mode none for supplied-output jobs.
Do not enable networking until controlled egress and redirected/subresource
connections are enforced. Docker base tag and transitive pins are not yet locked
by digest. The current container is a preparatory artifact, not verified isolation.

## ADR-046: expressive desktop visual system (15 October)

The user's redesign brief supersedes single-accent/system-font-only guidance.
Use forest navigation, citron primary selection and coral secondary highlights,
self-hosted OFL Manrope UI and system document text. Keep light reading surfaces,
solid controls and original artwork. Use existing Motion/CSS; no GSAP dependency
or showcase source copying. Preserve fixture honesty and reduced motion. Evidence
and outstanding native QA: DESIGN_REVIEW_20261015.md.

## ADR-047: private PostgreSQL scheduling before publication (15 October)

Extend existing sources/versions and cleanup, rather than introduce another queue
service. Commit version/job/processing-target together for an accepted source;
retain owner-scoped idempotency. Use a NOLOGIN worker with only claim/renew/fail
functions, source-before-job locking and fresh-token fencing. Clients read status
through auth.uid(); no client enqueue grant. No ready transition until complete
passage/vector validation and atomic publication exist.

Keep 64 KiB text input, one live lease globally (conservative measured CPU
single-flight), three attempts; choose 60-second renewable leases capped at five
minutes and exponential transient backoff plus jitter. Cap retained jobs at 16
per source without silently evicting idempotency records. These are initial local
scheduler bounds, not new inference limits or production allowances. Publication,
original admission, rate/byte quotas and a dispatcher remain separate gates.
See INGESTION_JOBS.md for implementation and evidence.
## 21 October: explicit developer identity, metadata remains production default

Reuse CloudInferenceClient and ingestion/search contracts rather than a second
HTTP pipeline. Trusted composition may inject a provider bound to the identical
IdentityConfig; production defaults to metadata. Keep the short-lived operator
token provider exclusively in the opt-in pilot script, fed through stdin. Verify
tokenizer bytes before parsing and load no local weights. Check readiness before
pilot ingestion without extending the 15-second client/model limits. This does
not resolve cold-start UX or replace hosted user authentication.

## 27 October 2026: deliver complete flows and defer only dependent checks

The user requests faster delivery. Group supporting code, UI, failure handling
and focused verification into complete user-flow milestones. A pending hosted
readiness result blocks hosted acceptance, not independent local implementation
using injected providers. Consolidate user-only steps near acceptance when safe.
Keep one agent, actual evidence, existing limits and separate cloud/destructive
approvals. This reduces handoffs and repeated work; no measured time/credit saving
or completion date is claimed. Current sequence belongs in TASKS.md.

## 31 October 2026: durable intent, owned cleanup and explicit private distribution

Reuse existing jobs/leases/publication; commit an opt-in marker only with new
admission. Recovery must name the current owned job and observed attempt to fence
late duplicate clicks/replacements. Owner cleanup wraps the existing guarded
finalizer, acknowledges completion idempotently and restores pending work from SQL.

Keep outbound concurrency one: inference may wait for a status operation within
its existing deadline. Operational startup failure stays retryable, never invalid
content. Reuse the established expiry/skew/monotonic token cache. The user explicitly
approved at most three readiness GETs within the same60s; embeddings never replay.

The user approved the specific Gather-only API/secret deployment under the existing
aggregate INR500 allowance. Native clients use a fixed HTTPS endpoint/public key;
DB/Google secrets remain backend-only. Use explicit separate private build/CSP and
isolated-copy installer bundling. Retain actual failed evidence and the zlib scan
flag alongside backport proof. Clean-Windows/signing/public-release gates stay open.

## 31 October 2026: one connected collection, not a second pilot workflow

Use the existing authenticated workspace in the main private Library instead of
maintaining a sample library beside the working feature screen. Keep sample data
only in its separately labelled build. Borrow mymind's minimal composition while
retaining Gather's fonts, identity and real-format limits. Put consent/review and
diagnostics behind deliberate actions. Preserve session generations, explicit
search, exact published versions and confirmed cleanup; visual integration must
not introduce a new data pipeline or automatic model requests.

## 31 October 2026: bounded PDF extraction in the existing publication flow

Reuse admission, jobs, leases, chunking, embeddings and atomic publication for
native-text PDFs. Pin pypdf6.21.4 and isolate each extraction in a disposable Linux
process with memory/CPU/wall limits and no credential environment. This is not an
OS filesystem/network sandbox; public hostile-file intake remains gated. Reject
scanned/blank pages instead of claiming OCR. Preserve original bytes/hash while
validating extracted text with a separate hash and contiguous numbered page map.
Keep the existing 64 KiB and three-passage pilot bounds. Expose PDF selection only
when the authenticated server advertises the approved capability. Exact-version
owned reads supply page metadata; no second indexing or search implementation.

## Recovery follow-up: database eligibility and bounded startup scheduling

Render recovery from an owner-checked lease/backoff/target/attempt hint instead
of treating every processing job as resumable. Keep the existing exact-attempt
transaction authoritative. Refresh metadata after a refusal rather than replaying
processing. Restore bounded watching after reconnect. Space the already approved
readiness GETs within the same60s, preserving all inference/SQL/resource limits.
The user explicitly approved startup-only CPU boost; retain measured startup
results and do not call this a proven speedup. Avoid another model/image change
until per-stage timing identifies the next useful performance change.

## 1 November 2026: bounded reuse and overlapping independent preparation

Measured fresh helper/connect setup dominated the small-PDF worker path. Reuse
only trusted worker sessions within one job, keep user admission fresh, recheck
restricted login/context/timeouts on every transaction and retain two physical
helpers with separate heartbeat sockets. Fixed guard/setup SQL can be batched;
function parameters, commit boundaries, ownership and lease fences stay intact.
Kill uncertain calls under the same deadlines and never replay them automatically.

Start one bounded readiness task after a trusted claim/lease, while independent
parsing/staging proceeds. Cancel and join it on failure/lease loss. Report its
overlapping time separately. Use allowlisted operational measurements in existing
logs, not document/usage telemetry. Enable via trusted flags after an approved,
same-input comparison; retain failed harness evidence and distinguish cold/warm
cases. CPU/memory/model changes were unnecessary for the measured warm gain.

## 2 November 2026: installer evidence and exact packaging identity

At the user's request, test the existing installer on their development PC
without enabling virtualization or changing protected workloads. Keep that result
separate from clean-machine acceptance, including missing-runtime and offline
branches. Use a bounded D: test installation and preserve app/cloud data.

Tauri changes its bundle marker from UNK to NSS when producing NSIS packages.
Pin the unbundled source hash and permit exactly that byte substitution; reject
all other differences. Do not equate byte identity with signing or independent
security approval. Retain the initial raw-hash harness stop and its resolution.

## 2 November 2026: bounded DOCX body extraction in the existing pipeline

Use the standard ZIP/XML libraries under a shared disposable parser slot; no new
Office runtime, package or model. Bound expansion and XML complexity, reject
active/ambiguous constructs, and never fetch relationships. Preserve binary and
extracted-text identities separately. Cite extracted paragraphs, not invented
Word pages. Keep typed format staging wrappers over one common validator with
existing publication/lease fences and private per-format metadata. Enable only
through a trusted server capability after explicit hosted approval; reuse the
same two-account pilot rather than opening general Office uploads.
