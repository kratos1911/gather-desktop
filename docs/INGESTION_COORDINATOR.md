# Trusted ingestion coordinator

16 October 2026. Internal backend slice; public uploads, real JWT verification,
cloud inference and desktop wiring remain separate gates.

## Entry points and flow

`services/worker/ingestion.py` exposes `submit(...)` and `run_once(repository, provider)`.
Submission accepts bytes, TXT/Markdown media, request ID and title; replacement
also supplies a source ID. It has no owner field. The repository connection must
carry identity derived by the server from a verified session. Never copy an owner
or database session setting from a desktop request.

```
Trusted submission -> parser validation -> transaction:
  source + idempotency receipt + version + original bytes + queued job
Worker claim -> lease-bound original read -> parser + token-bounded chunker
  -> private text staging -> reuse completed vectors -> embed missing passages
  -> validate/stage vectors -> atomic publication + ready
```

Migration `202610160001_ingestion_coordinator.sql` adds the smallest original
handoff: private, version-bound bytes committed with the job. Existing source
quotas, request fingerprints, immutable versions and source locks are reused.
No writable Storage/R2 path or public admission RPC is introduced. Database
originals are retained alongside staging until source cleanup; this deliberately
duplicates up to 64 KiB per version and is not the planned R2 adapter.

The new NOLOGIN coordinator role can only submit through its restricted function.
The worker can read an original and completed passage IDs only with the current
lease token. Neither role can read/write private tables directly. Source cleanup
cascades to handoff originals. Replays cannot recreate deleted sources.

## Processing and cancellation

The coordinator reuses `text_processing.process_request`, the pinned Qwen
512-token chunker and the existing embedding client's response validator. It
checks parser/chunker/model/revision/dimensions and raw hash/length against the
claim. Calls use one passage each, <=512 tokens and existing byte bounds.
Whole-job preflight allows at most 16 passages and 8,192 input tokens per attempt,
preserving the embedding client's default 16-request budget. The database's
256-passage ceiling is unchanged; larger coordinator jobs fail visibly before
inference rather than silently increasing budgets or truncating text. Durable
retries can repeat uncommitted inference; the existing three-attempt ceiling still applies.

Each operation uses a committed database transaction. A ten-second background
heartbeat renews the existing 60-second lease; the five-minute attempt ceiling
and three-claim retry budget remain unchanged. Renewals also bracket expensive
steps. Any heartbeat failure signals cancellation and prevents further writes.
Existing database fencing is the final authority for publication.

`RuntimeProvider` bridges an explicitly started existing Runtime and its pinned
tokenizer. It neither starts nor downloads a model and rejects request deadlines
above 15 seconds. Runtime now accepts a cancellation event, polling at 50 ms and
terminating/reaping its child on cancellation (cleanup can take up to four seconds).
A future cloud provider must implement equivalent bounded cancellation and raise
`InferenceError` for known transport/runtime failures; this is not an HTTP adapter.
Tokenizer callbacks are trusted, bounded server code, not user-supplied functions.

Completed vectors are reused only after the exact manifest has been validated
against the same immutable version and model settings. A recovered attempt embeds
only missing passages. No claim is made that failed, uncommitted inference can be
reused. Database retries/backoff remain authoritative; there is no additional
in-memory retry loop or polling daemon.

Failures return safe codes: timeout -> queued/backoff, transient runtime failure
-> temporarily_unavailable, invalid input/output -> failed. Lease loss or uncertain
database outcomes return `abandoned`; subsequent status/lease recovery determines
the truth, including an uncertain successful publication. No document or raw
exception details are returned or logged.

## Database adapter and verification boundary

`ingestion_repository.PostgresRepository` accepts a fresh DB-API connection factory.
It uses allowlisted functions, bound parameters, explicit commit/rollback/close,
five-second statements and three-second lock waits. Autocommit is rejected.
The factory must configure the restricted role, verified context, bounded connect
and network I/O, and supply a separate connection per call/heartbeat. No credentials,
driver dependency, production role membership or connection settings are created.
Driver/network setup is still an integration prerequisite; server statement limits
alone do not bound a broken network connection.

Focused control tests cover parameterization, error redaction, input/job budgets,
configuration/hash mismatches, cancellation and ordering. The disposable database
suite invokes the actual coordinator through a test-only psql function transport,
exercising atomic submission, recovery, vector reuse, retries, ownership,
replacement and deletion during a live heartbeat. Admin clock edits simulate lease
expiry/backoff; production contains no clock override. Only tests define the
synthetic provider; its expected protocol metadata and unit vectors are fixtures,
not evidence that Qwen generated them. No production fallback selects it.

See TASKS.md for results. Run `python scripts/check_database.py`, the focused
`test_ingestion.py` unit suite, and the inference control suite when cancellation
changes. Existing model-quality evidence was reused without new inference.

Next: configure and verify the real server transport/identity boundary and connect
published search/open adapters. Desktop integration and cloud deployment follow
their own acceptance/security gates; the sample UI has not become a live importer.
