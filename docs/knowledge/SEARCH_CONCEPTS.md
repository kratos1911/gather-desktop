---
tags: [gather, learning, search]
---
# Search concepts

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
| Embedding | Represent content as numbers so related meanings can be compared. | Genuine model output is pending; fabricated vectors are only math test fixtures. |
| Cosine similarity | Compare vector direction rather than magnitude. | Implemented for saved-vector evaluation; useful only within a compatible model space. |
| Vector database | Store and retrieve vectors with their source records. | Supabase Postgres/pgvector is planned, not connected. |
| Hybrid search | Combine keyword and semantic rankings. | Helps exact identifiers and paraphrases; end-to-end integration is pending. |
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

The current small keyword corpus missed its rain-packing query. See
[[tests/evaluation/BASELINE|Measured baseline and limitations]]. High aggregate
scores on a tiny development set do not prove production search quality.

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
