---
tags: [gather, learning, search]
---
# Search concepts

## Validate before staging output

Read all required build inputs before changing the destination, then hash and
write the same captured bytes. Missing files cannot leave a new partial staging
directory or overwrite an existing one. This does not make separate filesystem
writes atomic if a disk error occurs. See [[scripts/stage_zlib.py]].

## Prove a security backport with a failing control

The same bounded test should expose the bug in the original dependency and pass
with the fix. Verify the installed library too, not just compiled source. Keep
scanner findings separate: a local backport may still match an advisory by package
version. See [[services/inference/zlib/README]] for Gather’s zlib evidence.

## Background work needs CPU while idle

A live server instance is not a promise that background threads can run. Cloud
Run CPU allocation must match trusted-key refresh scheduling. Instance-based CPU
supports this but bills idle lifetime; minimum zero still allows shutdown.
Expired keys must still fail closed. See [[docs/CLOUD_PILOT_PLAN]].

## Model files are part of the serving contract

Pin the model revision and verify every expected file hash before loading. Reject
extra files too. Keep the model directory immutable afterward: a successful hash
check alone cannot stop later privileged modifications. A hash check does not
load the model or measure its performance. See [[services/inference/ARTIFACT_STARTUP]].

## Authorize identity pairs, not independent lists

An allowed email and an allowed account ID must belong to the same configured
pair. Checking two independent lists would accidentally accept crossed identities.
Gather shares one fresh key snapshot across both allowed callers; it does not
fetch keys separately for each request or caller. See [[docs/RECEIVING_IDENTITY]].

## Platform identity and application identity

Cloud Run checks permission to invoke the service; Gather independently verifies
the signed caller token. A proxy-processed header is not a substitute for a valid
application signature. Both boundaries need negative tests. Local fixtures cannot
prove a deployed IAM policy. See [[docs/CLOUD_IDENTITY]].

## Transport success versus CPU suitability

An HTTP 200 proves neither valid embeddings nor affordable hosting. Check vector
identity/shape, startup time, individual latency and peak memory. Four requests
are a smoke check, not reliable p95 or concurrent-user capacity evidence.
See [[services/inference/HTTP_SMOKE]].

## Shutdown evidence and dependency scans

A server can finish cleanup and then exit with its original termination signal.
Check that work and refresh threads stop, not merely whether exit status is zero.
Synthetic inference can verify that control flow; actual model resources still
need separate measurement. Likewise, scanner exit zero means the scan completed,
not zero vulnerabilities. See [[services/inference/SERVING_IMAGE]].

## Key rotation without a refresh storm

A token's unknown key ID must not cause an unrestricted network call. Gather's
prepared receiver refreshes on a bounded schedule instead. A failed refresh can
reuse still-fresh keys, but cannot extend their expiration. Once keys expire,
readiness and authentication fail closed. See [[docs/RECEIVING_IDENTITY]].

## A valid signature is only part of authorization

A signature establishes who signed a token and protects its contents. The receiver
must also check the intended service, lifetime and allowed caller. A correctly
signed token for another service or account is still rejected. The signing public
key must come from a trusted source; a request cannot nominate its own key.
See [[docs/RECEIVING_IDENTITY]].

## Findings, exposure and remediation

A scanner finding identifies a potentially affected package. Reviewing the vendor
advisory and actual application paths helps assess exposure; it does not itself fix
the library. Non-root/read-only settings reduce impact but do not prove safety.
Keep the finding until remediation or evidence-backed adjudication is complete.
See [[services/inference/OS_RISK_REVIEW]].

## Package locks and image checks

A version pin names a release; a SHA-256 lock identifies the exact package file.
An offline install uses only those reviewed artifacts. Linux tests then check that
the combined packages work together. Neither hashes nor passing tests prove the
absence of security flaws: scanning and release review remain separate.
See [[services/inference/SERVING_IMAGE]].

## Service tokens are different from user sessions

The application proves its service identity to inference with a short-lived token
whose audience names that exact service. The user's Supabase session separately
controls document ownership. Reading token fields helps reject mistakes; only the
receiving identity boundary verifies signatures and permissions. Refresh failure
must stop the call, not reuse an expired token. See [[docs/CLOUD_IDENTITY]].

## Search identity and version-bound reading

Cosine search compares vector directions only within the same model/revision and
dimension space. The authenticated database filters ownership and publication
before comparison. A result carries its source version: opening that version
either returns the same text or reports it unavailable after replacement/deletion.
This keeps citations trustworthy. See [[docs/PUBLISHED_SEARCH]]; unit-vector tests
verify the API contract, while semantic relevance still needs actual embeddings.

## Coordinator and durable handoff

A coordinator connects existing processing steps. Durable handoff means saving
the original with the job so a restarted worker can retrieve the same bytes.
Heartbeats renew permission to work; losing permission signals cancellation.
Recovery reuses completed vectors from the same version and computes only what
is missing. [[docs/INGESTION_COORDINATOR]] describes the internal implementation;
synthetic workflow tests do not establish semantic search quality.

## Atomic publication

Think of an index version as a draft: passages and vectors stay private until
every part is valid. One database transaction switches the published pointer
and marks the job ready. A replacement draft leaves the earlier complete version
available. Lease tokens stop an interrupted worker from publishing after another
attempt or deletion. See [[docs/TEXT_PUBLICATION]] for the implemented contract;
[[TASKS]] records verification, not a claim of connected semantic search.

## Fresh evaluation and failure review

On 12 October, [[docs/TEXT_V2_RESULTS|text-v2]] tested new examples with the same
model and settings. A corpus fingerprint locks sources, questions and expected
quotes before inference; later edits invalidate the experiment. New examples
authored by the same assistant are still not independently reviewed test data.

File recall and passage recall answer different questions. For maker-05, search
finds both printer manuals, but one actual rescheduling rule ranks sixth. The
file metric passes while the top-five passage metric exposes the missing evidence.
Likewise, a semantically similar archived rule can outrank the current one, and
an exact code can be easier for keyword matching than a dense embedding. Preserve
these failures and test proposed fixes separately rather than changing gold labels.

## Reliability concepts for the next implementation

- Dependency lock: freeze versions, including indirect packages.
- Artifact hash: check that downloaded bytes match the reviewed package.
- Image digest: identify a base image's contents instead of following a moving tag.
- Vulnerability triage: record applicability and unresolved risk; a successful
  install or a pinned version does not prove safety.

- Idempotency: retry a job without duplicating passages.
- Lease: a worker temporarily owns a job; expiry permits crash recovery.
- Generation: a complete index version activated only after validation.
- Tombstone: a deletion marker that blocks search and late worker publication.
- Reconciliation: retry unfinished cleanup because object storage and database
  writes cannot be one transaction.
- Egress enforcement: control the real network connection, not only its URL.

These production mechanisms are planned, not implemented. See
[[docs/DELIVERY_PLAN|Delivery plan]] for flows, acceptance tests and next tasks.

Return to [[docs/PROJECT_HUB|Project hub]]. This explains techniques; implementation
status is maintained in [[docs/MEMORY]] and [[TASKS]].

| Concept | Plain explanation | Role in Gather |
| --- | --- | --- |
| Parsing | Pull usable text and structure out of a format. | TXT/Markdown and supplied HTML are tested; PDF/Office/OCR integration is pending. |
| Metadata | Information about content, such as title or author. | Can make a bookmark useful even when page text is unavailable. |
| Chunking | Split a long source into smaller passages. | Current text processor uses 1024-character windows and 128-character overlap; model token limits still need validation. |
| Provenance | Record where a piece of text came from. | Source identity, parser version, content hash and offsets let results open the right evidence. |
| TF-IDF | Weight words by how often they occur in a passage and how uncommon they are across the collection. | Implemented keyword baseline; it does not understand synonyms by itself. |
| Embedding | Represent content as numbers so related meanings can be compared. | Real Qwen vectors are evaluated on the fictional corpus; connected app search remains pending. |
| Persistent inference | Load the model once, then reuse it for multiple requests. | Synthetic controls and real Qwen host smoke pass; container measurements pending. |
| Single-flight and hard deadline | Run one request at a time; stop the model process if its deadline expires. | Busy rejection and actual process cleanup tested. Container CPU/RAM limits remain pending. |
| Cosine similarity | Compare vector direction rather than magnitude. | Implemented for saved-vector evaluation; useful only within a compatible model space. |
| Vector database | Store and retrieve vectors with their source records. | Supabase Postgres/pgvector is planned, not connected. |
| Hybrid search | Combine keyword and semantic rankings. | Can help identifiers/paraphrases but must be measured; fixed RRF reduced ranking quality in the first Qwen test. |
| Reciprocal rank fusion | Combine result positions instead of incompatible score scales. | Evaluation implementation sums 1/(60 + rank) across the two lists. |
| Recall@5 | How much expected relevant material appears in the first five results? | Document and passage evidence are measured separately. |
| MRR@5 | Reward the first relevant result for appearing earlier in the top five. | A first-place hit scores 1, second place 1/2; no top-five hit scores 0. |
| Idempotency | Repeating a job should not create duplicate records. | Stable identities exist in text processing; durable job/storage enforcement is pending. |
| RLS | Database rules that restrict rows to their allowed users. | Required before private Supabase libraries go live. |
| SSRF | A submitted URL tricks a server into contacting a private destination. | Offline URL checks are not enough; future fetching needs DNS, redirect and connection enforcement. |

## Concrete example

A saved article says “pack a waterproof jacket.” Keyword search can find “jacket.”
Semantic search should also retrieve it for “what should I wear in the rain?”
That is intended behavior, not a result established by the current model tests.

The small keyword corpus missed its rain-packing query (q18); Qwen dense retrieval
found its evidence in the top five at all three tested dimensions. See
[[docs/CPU_BENCHMARK|Real CPU comparison]] and
[[tests/evaluation/BASELINE|Keyword baseline]]. This does not verify every possible
rain query or production search quality.

## What we measured on 10 October

- Token preflight counts the actual model tokens, including the query instruction.
  An input that is too long fails rather than losing its final paragraphs silently.
- Matryoshka dimension reduction takes a supported prefix of a model's vector and
  normalizes it again. At 512 dimensions the raw float payload is half of 1,024;
  model loading and embedding computation still happen at full model size.
- Warm latency measures an already loaded model. Our four-thread median was
  0.324 seconds. It excludes network/database time and does not prove cloud latency.
- Peak process memory was about 3.64 GiB by the OS measurement. Weight download
  size was only 1.21 GB; file size and runtime memory are different quantities.
- Held-out evaluation means fresh questions and sources not used to choose settings.
  Our initial set is a development comparator, so a broader frozen test is next.

## Search versus chat

Search returns matching sources and passages. Chat generates an answer using
retrieved passages, which introduces additional grounding and citation checks.
Chat is deferred; it is not required to finish the first search flow. Neither
workflow requires autonomous agents modifying files.

## Related technical references

- [[services/worker/README|Text-processing contract]]
- [[services/worker/EMBEDDING_CLIENT|Embedding request boundary]]
- [[tests/evaluation/README|Evaluation corpus]]
- [[tests/evaluation/VECTORS|Vector comparison protocol]]
- [[docs/BOOKMARKS|Bookmark extraction and limitations]]


## Dependency verification and timeout cleanup

A dependency lock records exact versions and file checksums. A checksum mismatch
stops installation, but a matching file can still contain a known vulnerability.
That is why the image is scanned separately. See [[services/worker/IMAGE_SCAN_REVIEW]].

A timeout stops waiting for a job; it may leave the actual worker running. The
Docker smoke harness therefore removes its uniquely named container even on an
error or timeout. This developer check passes; the production supervisor and
public-only network enforcement remain planned under TASK-019B.


## Runtime attack surface

Build tools install the software; the worker only needs to run it. Removing pip
and its bootstrap package from the worker removes unnecessary executable code.
The installer still exists in the developer build target and parent image layers,
so this is runtime protection, not permanent erasure. Available OS patches are
pinned and checked separately. Current rescan: 31 open records, four high; live
extraction is still gated. See [[services/worker/IMAGE_SCAN_REVIEW]].


## DNS pinning, redirects and worker supervision

A hostname can change addresses between checking it and connecting. The restricted
transport resolves once, checks every answer, then connects directly to an approved
number. TLS still checks the original hostname. A redirect starts a new check.
This is destination-address pinning, not certificate pinning.

The parser has no network at all. A host-side supervisor starts it with limited
resources, caps both output streams, and removes its container on timeout or
cancellation. Controlled tests pass; the fetch broker's full DNS deadline and
browser networking remain next. [[services/worker/SUPERVISION]] explains the limits.


## Whole-fetch deadline and the byte handoff

Socket timeouts do not necessarily stop a stuck DNS lookup. FetchBroker places
the whole fetch in a separate process; the parent can terminate that process when
time runs out. A small validated byte response then goes to the no-network parser.
This flow passes a controlled local test as of 8 October. It prepares passages;
it does not save a bookmark or create embeddings. See [[services/worker/SUPERVISION]].
# Database ownership foundation (8 October)

**Row-level security (RLS):** each query is filtered by the signed-in user's
identity. A forgotten owner filter in application code should not reveal another
user's source. Privileged database roles can bypass this and must stay server-side.

**Column privileges:** users can edit title/notes, but cannot change ownership or
processing lifecycle fields. **Composite foreign keys:** a version must reference
both its source and the same owner, preventing mixed-owner relationships.

**Tombstone:** a deletion timestamp hides the source and its versions immediately.
Removing stored objects reliably still needs a future durable cleanup workflow.
The current suite has 45 SQL assertions and four concurrent scenarios; the Auth
contract is emulated in tests. Full Supabase and connected search remain pending.

## Atomic saves and safe retries (9 October)

**Transaction:** saving the source, its receipt and its quota charge succeeds
together or rolls back together. **Idempotency key:** a request UUID lets the
database recognize a retry and return the original ID without another charge.
Changing the payload with the same key is rejected.

**Row lock:** one user's competing saves take turns checking the same quota row,
so two requests cannot both spend the last available slot. This currently limits
source count, not bytes or model costs.

**Durable cleanup request:** deleting writes both a tombstone and pending cleanup
record. A rollback leaves the request available for retry. Database cleanup
releases quota once; the receipt survives to stop late save retries recreating
the source. A future background worker and external Storage reconciliation are
still required. Version writes lock/check the parent to stop late derivatives.

## Why deleting a file takes two steps (9 October)

The database stores the file's record; Storage holds its bytes. A database
transaction cannot make both services change atomically. We first hide the source
and retain a cleanup request, then remove the bytes through Storage's API, then
finish database cleanup. If interrupted, retrying repeats safe operations.
The source's quota slot remains occupied until finalization succeeds.

31 local core API checks now verify this order with real synthetic files and
real Auth-issued JWTs. Storage metadata is never deleted directly by SQL. A
remaining metadata record blocks finalization; preventing a late upload after
that check still needs future upload leases/fencing and orphan reconciliation.
There is no deployed background cleanup worker or desktop connection yet.

## CPU container checkpoint (13 October)

**Source grouping and neighbor expansion (15 October):** choose a seed passage
per file, then add at most the immediately adjacent passages from that exact
version. Slice original text once to avoid duplicated overlap and preserve
citations. Reserve each seed's space before adding context. This improves what
the reader sees without rerunning embeddings or changing source rankings.
Known-case context coverage is now complete; larger/unseen libraries remain
unverified. [[docs/SEARCH_CONTEXT]] holds the limits and evidence.

15 October retrieval follow-up: [[docs/CHUNK_RETRIEVAL_RESULTS]]. A token limit
counts model pieces, not characters. A 512-token chunk can be larger than the old
1,024-character chunk for English; text-v2 consolidates 64 passages into 40.
The paired experiment changes only chunk policy and keeps model/query vectors
fixed. Main-set retrieval improves, but long conditional rules can cross a boundary.

**Strict evidence coverage** requires the whole supporting span in one retrieved
passage. **Union coverage** checks whether several retrieved passages from the
same source jointly cover it without gaps. This diagnostic is not an implemented
reader/context feature. Boundary strict recall is 50%, union is 87.5%; one
multi-part query still misses both relevant late passages despite finding the
files. Next: bounded context assembly with exact source offsets and version/owner
checks, plus passage diversity. Preserve failures rather than shortening labels.

15 October checkpoint: dependencies patched; scan down to 28 findings/1 high.
The new helper counts actual model tokens, splits at readable boundaries and
preserves source offsets plus overlap. It targets <=512 tokens per request;
real candidate checks now pass on six compatibility cases and five chunks
(306–500 tokens, 3.05–5.88 s each). This verifies numerical compatibility and
bounded processing on these fixtures, not search relevance on real documents.
It is not wired into the desktop yet; new boundaries still need retrieval-quality
evaluation. Linux file cache can occupy host RAM even after a model exits;
approved one-time clean-cache release cleared the memory guard without stopping
APIs. It is not a permanent memory setting or a production performance fix.

14 October follow-up: short queries and long document chunks have different
compute costs. Fifty short queries passed, but a 2,048-token chunk hit the 15 s
deadline. A maximum accepted token count is not a latency promise. Smaller chunks
may help, but must preserve useful context and be evaluated for retrieval quality.
An image scan also found 56 dependency vulnerability records, including 12 high.
Isolation reduces exposure; dependency fixes and regression tests are still needed.

The model stays loaded in a separate process so each search avoids reloading
weights. A hard deadline stops that process if inference hangs. Docker places
another boundary around it: CPU, RAM and process limits, read-only files and no
network. These controls reduce resource use and access; they do not authenticate
users or make the image production-ready. The new private stream has bounded
frames and handles one request at a time. Eighteen synthetic tests pass inside
Linux. On 14 October the real model also passed ten short fictional requests:
15.78 s startup, 0.59–0.74 s per request and 3.87 GiB peak container memory. This
does not yet establish performance for long documents or concurrent users.
See [[services/inference/CONTAINER|Container checks and limits]].

## Durable scheduling and fencing (implemented prerequisite)

A durable job survives the worker connection closing. An idempotency key makes
repeating the same request return the same job/version. A lease gives one worker
temporary permission; recovery changes the token so the old worker cannot change
state. Deleting or replacing the source cancels its old jobs under the same source
lock. Three attempts and finite leases prevent endless retries. A processing target
is not a published search version: complete vector validation/activation is still
next. See [[docs/INGESTION_JOBS]] for evidence and remaining integration boundaries.

## Query coordination and stale citations

A query is embedded once in the same model space as stored passages. Ranking
identifies candidates; exact-version reads supply trusted source text for bounded
neighbor expansion. If the source changes between these calls, omit that result
instead of silently attaching the old citation to new text. Implemented internally;
synthetic tests and local real-session API checks pass. Model/cloud transport and
desktop wiring remain pending. See [[docs/QUERY_SEARCH]].

## Whole-request deadlines

A socket timeout limits a stalled socket operation; a server can still trickle
bytes slowly. A whole-request deadline bounds DNS, connection and reading together.
Gather's service client runs HTTP in a short-lived helper and stops that helper
on timeout/cancellation. This does not cancel remote model computation; the model
server needs its own deadline. Locally verified; hosted integration pending.
See [[docs/SERVICE_CLIENTS]].

## Client disconnect versus model deadline

Closing an HTTP connection does not guarantee model work stops. The local
inference endpoint independently uses Runtime's compute deadline; a hung synthetic
worker is reaped even after its client disconnects. Invalid credentials never
reach the model. A service credential authenticates the backend caller, not the
owner of a document. Locally verified; public identity/deployment pending.
See [[docs/INFERENCE_HTTP]].

## User identity versus service identity (planned)

Supabase identifies the person and protects their documents. Google service
identity identifies which backend may call the model; it does not grant that
backend ownership of every document. The model only needs bounded input text,
not database or file-store credentials. Scale-to-zero can save idle capacity but
adds startup delay; it is not a free-or-fast guarantee. See [[docs/CLOUD_RUN_DESIGN]].

## Lifespan, readiness and admission

Lifespan loads one model process before serving and closes it on shutdown.
Readiness says whether that process can accept work; a running web server alone
is not proof of a ready model. Admission rejects excess inference immediately
instead of building a hidden queue. Async serving lets health checks respond
while the blocking model runs elsewhere. See [[docs/INFERENCE_ASGI]].
