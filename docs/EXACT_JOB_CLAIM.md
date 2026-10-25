# Exact-job claim repair

25 October 2026. Local implementation and verification complete. After explicit
user approval, migration8 was applied successfully to Gather's hosted database.
Metadata checks confirm installed=true, worker_allowed=true, and client/anonymous/
admission/private-core access=false. No hosted job claim or model request was run.

## Cause and scope

The operator accepted an explicit job ID but called the generic oldest-eligible
claim function before checking the returned ID. An older expired job could be
claimed and consume an attempt, after which the guard refused the mismatched job.
WorkerRun collapsed that guard failure into `unavailable` without a useful reason.
The browser frontend does not need to be running for the standalone worker.

Read-only hosted evidence from 24 October:
- Requested job efea703e-22e5-4663-b4e3-c9280c650a88: queued, attempts0.
- Older job caae0a28-c50c-4789-9eef-51e62c1fdd7b: processing, attempts2,
  error_code timeout, expired lease. No job processing was retried by the agent.
- Restricted worker TLS/login probe passed under the existing pilot profile.

## Change

Migration 202610250001_targeted_claim.sql is the eighth migration. It factors the
existing claim body into a private shared function. The existing FIFO entry point
remains available. A new restricted-worker entry point claims only a supplied
non-null job UUID; missing, backed-off, deleted or superseded targets return no
claim rather than falling through to another job.

The same advisory lock and global live-lease rule protect both entry points.
Source locks, 60-second lease, three-attempt cap, backoff, version boundaries and
fencing tokens are preserved. Clients and the coordinator cannot invoke the
new function; the shared private core is not executable by worker/client roles.
No source is deleted, no queue reset, no attempt counter manually altered.

PilotWorker routes its trusted CLI job ID to the new function. It retains returned
job/owner/original guards and distinguishes idle from an unavailable claim.
Failures retain only safe allowlisted codes/SQLSTATE or deadline reasons. Each
worker invocation writes a unique receipt under output/operator-pilot and returns
nonzero unless its requested work reached ready. No automatic retry was added.

## Verification

- 41 focused Python checks pass, including worker-only targeted transport, claim
  guard errors, redaction, receipts/exit status, cancellation and existing ingestion.
- Existing SQL ownership/lifecycle/lease/concurrency/publication/coordinator suite
  plus exact-claim cases pass in one disposable 256 MiB PostgreSQL container.
- Exact-claim cases cover older expired work remaining untouched, concurrent
  recovery, shared single-flight behavior, permissions, stale-token fencing,
  backoff, exhaustion, null/missing targets, replacements and deletion.
- Frontend build passes. No frontend/native assets changed; native rebuild not needed.
- No new model requests, production job claims or cloud scaling changes.

Automatic approval review initially blocked hosted Run pending action-time
confirmation. User explicitly approved; the same staged SQL then returned Success.
Read-only metadata verification passed in fatolholcjxpwocnpzws. Screenshot evidence:
output/operator-pilot/targeted-claim-applied-20261025.png. The next action is one
explicit retry of the same acknowledged job; processing success is not yet claimed.
