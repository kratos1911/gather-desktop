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
