# Verified text and atomic publication

15 October 2026. Local database slice implemented; no connected importer,
hosted inference API or desktop semantic search is claimed.

## Contract

Migration: `supabase/migrations/202610150002_text_publication.sql`. Reuses
INGESTION_JOBS.md's owner-bound versions, global single lease, retry budget,
source locks, target fencing and deletion cleanup.

1. A trusted coordinator enqueues immutable source metadata. A worker claims
   the job, then calls `gather_private.stage_text(job, token, bytes, media, manifest)`.
   The function verifies the actual bytes against the version's SHA-256 and job's
   exact byte length/media. It enforces the existing 64 KiB limit, UTF-8 parser
   identity, control-character and empty-text rules. TXT and Markdown are UTF-8
   text; MIME agreement is not a claim that Markdown has a unique binary signature.
2. Manifest entries contain only `id`, `start`, `end`. At most 256 passages,
   8 KiB per passage, ordered advancing Unicode codepoint ranges, complete source
   coverage and no gaps. Overlap is allowed. Passage bodies are sliced inside
   PostgreSQL from verified original text, preserving BOM, CRLF and Unicode.
   IDs/citations are preserved from the trusted processor, not regenerated.
3. `stage_vectors(job, token, model, revision, dimensions, rows)` accepts only
   that job's pinned identity and dimensions (256/512/1024). Each row names an
   existing passage and a numeric vector. pgvector rejects nonfinite/overflowing
   float32 values; unit norm tolerance is 0.001, matching normalized embeddings.
   A storage call accepts at most 16 rows / 512 KiB JSON. This new transport cap
   does not increase the inference batch/token limits. A bad row rolls back the
   entire batch. Exact retries succeed; conflicting manifests/vectors fail.
4. `publish_text(job, token)` locks the live source, checks current target and
   unexpired lease, and requires every expected passage to have a valid vector.
   One transaction changes the published pointer and job to `ready`. A trigger
   rejects a ready transition without its matching publication receipt/live lease.
   Staging is immutable through worker APIs after publication.
5. A lost-response publication retry returns the same version only for the same
   token receipt and still-current target. It performs no new activation, so it
   can safely succeed after the original lease was cleared. Deleted/superseded
   versions cannot use this exception. Token receipts store hashes, not raw tokens.

The **processing target** and **published version** are separate. Replacement
processing can fail while the previous complete publication remains readable.
Source locking serializes replacement, deletion and publication. A tombstone
immediately excludes the source from subsequent reads; existing cleanup cascades
through originals, passages, vectors and receipts. Transaction snapshots already
read by a caller cannot be retroactively erased.

## Read and trust boundaries

Private tables have no client or worker table grants. The trusted NOLOGIN worker
has only narrowly granted functions; it processes multiple owners and must never
be an end-user credential. Existing composite foreign keys bind job/version/source
ownership. Client callers cannot choose an owner for publication or claim work.

`public.read_published_text(source)` derives ownership from `auth.uid()` and returns
only the live source's published passage bodies, offsets, IDs, version/hash/parser,
chunker and model identity. Other owners see no rows; anonymous access is denied.
It exposes neither original bytes, staged content nor vectors. It intentionally
does not require the previous job to remain `ready` after a replacement cancels it.

The worker is trusted to use the declared chunker/model and tokenizer bounds.
Database metadata validation cannot prove which model generated a vector. This
slice provides the publication/read boundary, **not** a vector-search RPC or an
authenticated dispatcher. Search/context repositories must consume the published
pointer and enforce identity/deletion when their adapters are connected.

## Verification and limitations

`python scripts/check_database.py` includes `scripts/check_publication.py` with
real PostgreSQL/pgvector transactions, parser-produced synthetic Markdown (BOM,
CRLF, combining characters, emoji) and synthetic unit vectors. It verifies byte
integrity, malformed coverage, private reads, batch rollback, incomplete publication,
idempotency, transactional rollback, competing publish calls, lease recovery,
replacement/deletion races and cascading cleanup. Existing lifecycle and bounded
retry checks also run because the new ready state affects them. These tests are
storage/security evidence, not live semantic retrieval or model-quality evidence.

The harness now uses the already-cached, digest-pinned Supabase PostgreSQL image
for pgvector. It keeps 256 MiB / 1 CPU / 100 PIDs and 192 MiB disposable tmpfs,
no network or host ports, and only a read-only test startup script mount. No
shared API containers are changed. A separate bootstrap smoke verifies the real
API harness's role initialization; full Auth/PostgREST/Storage were not rerun.

Current results are in TASKS.md. Logs are under ignored `output/database-checks/`.
Production rate/byte quotas, original-upload fencing, retention, real JWT checks,
provider security/licensing and desktop integration remain release gates. The
16-version retention cap is unchanged; do not evict history or raise limits silently.

INGESTION_COORDINATOR.md now connects internal submission and worker execution to
these functions and the parser/inference interface. Next: real authenticated
transport and published-search/open adapters. Synthetic integration remains
separate from eventual cloud inference checks.
