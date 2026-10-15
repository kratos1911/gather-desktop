# Durable ingestion jobs

15 October 2026. Implemented scheduling prerequisite, not a working importer.
Migration: `supabase/migrations/202610150001_ingestion_jobs.sql`.

## What works

A trusted coordinator can create a version and its job in one transaction for an
existing live, quota-accounted file source. The owner/request key is idempotent;
a different payload with that key is rejected. A replacement atomically selects
a new processing target and cancels previous jobs. This target is **not** a
published/searchable version. Job-bound source hashes/parser identities cannot
be changed. Job metadata also pins chunker, model/revision and dimensions.

```
Existing accepted source -> enqueue version + job -> queued
queued -> exclusive lease -> processing
processing -> transient failure -> delayed queued (at most three attempts)
processing -> invalid input / exhausted attempts -> failed
processing -> lease expires -> new attempt with a new token
any job -> source deleted or replaced -> cancelled
Ready/searchable publication: not implemented or exposed in this slice
```

A lease is temporary permission to change a job. Recovery gives a new random
token; the old worker cannot renew or fail the job. Parent source locks serialize
worker updates with deletion/replacement. Deletion hides status immediately and
cancels all jobs. Existing external-cleanup checks are retained; database cleanup
cascades versions, jobs and processing targets after the original cleanup gate.
Late enqueue calls cannot resurrect a deleted source, even after physical cleanup.

## Boundaries and limits

- `enqueue_text_job` is migration-owner/coordinator-only. No client or worker
  execute grant. Its owner parameter must come from the future verified API
  identity, not a desktop payload. It requires configured source quota and checks
  source ownership. Creating the source and enqueueing together remains API work.
- A new NOLOGIN `gather_ingestion_worker` role can only claim, renew and fail via
  restricted functions. No direct table reads/writes, enqueue, cleanup or helper
  execution. No login credentials or deployment role membership provisioned.
  It is a trusted cross-owner dispatcher role, never an end-user credential.
- Owner status RPC derives identity from `auth.uid()` and omits lease tokens and
  internal fingerprints. Anonymous invocation denied; wrong/missing owner or
  deleted source returns no rows. Tests use an Auth-contract shim, not real JWTs.
- At most one **live database lease globally**, conservatively matching the
  measured single-flight CPU runtime; thus also at most one per owner. Claims
  use a transaction advisory lock and `SKIP LOCKED` parent row locking. No polling
  daemon exists yet. Each call handles at most one candidate; an exhausted crash
  attempt becomes failed and the dispatcher must poll again for other work.
- Three total claims per job, including crash recoveries. Explicit transient
  failure backs off 5 then 10 seconds plus 0–5 seconds jitter. Invalid input is
  terminal. Errors are a fixed enum, never raw exceptions or document content.
- Lease: 60 seconds, renewable up to five minutes from that attempt's claim.
  These are scheduler limits, **not changes to the inference 15-second request
  deadline or memory budgets**. A future runtime must actually stop stale work;
  database fencing alone does not prevent an expired process consuming CPU.
- Existing TXT/Markdown input limit remains 64 KiB; job metadata accepts the
  evaluated 256/512/1024-dimensional configurations. Identity metadata is not
  proof of valid input or vectors: the coordinator/publication boundary must
  verify bytes, SHA-256, actual model revision, shape and finite values.
- New defensive cap: 16 retained jobs/versions per source. Existing request replay
  still works at the cap. No automatic eviction that loses idempotency evidence.
  This is a local initial bound, not an approved public subscription allowance.
- No content stored here, new uploads, public signup, API endpoint, cloud resource
  or vector model call. Production privacy, retention, rate/byte quotas, original
  immutability and upload fencing remain gates in PRIVACY_RELEASE_AUDIT.md.

## Verification

Run `python scripts/check_database.py`. It uses the existing pinned PostgreSQL
image, 256 MiB / 1 CPU, bounded tmpfs, no network/host ports/host data mounts, and
removes only its uniquely named test container. Schema constraints and permission
checks use real PostgreSQL with synthetic identities/content metadata. The existing
ownership/deletion suite runs because this migration adds a tombstone trigger and
cascade relationships that can affect it.

`tests/database/ingestion_jobs.sql` covers idempotency, invalid inputs/ownership,
immutable provenance, no forged ready state, token permissions, bounded retries,
expiry, recovery, supersession, tombstones, cleanup, transaction rollback,
heartbeat ceiling and retained-metadata cap. Five additional real-connection
scenarios cover duplicate enqueue, competing claims, competing recovery,
replacement/heartbeat and deletion/heartbeat. Committed leases survive the
claiming worker connection closing. Clock expiry is simulated with admin-only
fixture updates; no timing sleeps or production clock overrides are introduced.

Latest results and total checks are recorded in TASKS.md / PROGRESS.md.
Raw local log: `output/database-checks/ingestion-jobs-20261015.log` (ignored).
Frontend production build passes. No frontend/native inputs changed; native
rebuild unnecessary. No real Auth/PostgREST, Storage/R2, inference, OS/database
restart, sustained load or deployed worker behavior is claimed by these checks.

## Next slice

Verified original admission plus immutable passage/vector staging and atomic
publication. Validate complete coverage, offsets/citations, text/hash/version and
embedding identity/dimensions before exposing readiness. Publication must lock the
live source and validate the **current unexpired lease token and target version in
the same transaction as all writes/activation**; calling a checker in a separate
transaction is unsafe. Add missing/invalid vector, partial-batch, stale-worker and
delete/publication race tests. Then connect the trusted dispatcher, authenticated
API, search/context repository and finally desktop import/search/open/delete.
