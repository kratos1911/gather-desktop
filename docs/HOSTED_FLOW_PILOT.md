# Authenticated hosted text-flow pilot

Current processing checkpoint: source 5a4c1c59-9313-4982-a1b4-c8dd73dd30c1 was
acknowledged, job 7ecced47-982e-45fb-ad77-301f56a46ffe returned queued /
temporarily_unavailable before any inference. Failure handler tombstoned it.
Operator SQL confirms cancelled, attempts=1, deleted, source_hidden=true,
text_staged=false, passages_staged=0. Physical cleanup remains pending. Do NOT
resume this cancelled/deleted source or delete the receipt to force another run.

Offline replay with the actual pinned tokenizer and injected fixture vectors
reaches ready; no local model/network used. This rules out an obvious deterministic
tokenizer-wrapper failure in that replay, not all possible hosted failures. The
original error lacks step/reason; deletion's code=deleted is cleanup, not root cause.
Need existing Postgres ERROR/WARNING logs for 22 October ~07:15–07:30 UTC
(12:45–13:00 IST). Do not request another full run simply to collect missing logs.

Worker now emits fixed internal diagnostic.step and sanitized database reason on
failure/abandonment, and the runner preserves them. Thirty worker/runner tests and
frontend build pass. No hosted retry, limit increase or inference was performed.
Warm min=1 remains active under the prior approval; restore min=0 after pilot or
operator stop. Rotation of exposed DB passwords remains user-deferred.

Current cloud state: user approved temporarily keeping one warm instance for the
pilot. Agent applied service-level min=1/max=1 at 2026-10-22T07:11:44Z only to
Gather. Image and resource limits compare unchanged; authenticated /ready passes.
Actual invoker policy contains only the dedicated pilot caller, no public member.
Safe local receipt: output/pilot-warm-scaling.json. Idle billing is now active.
RESTORE MINIMUM ZERO immediately after the pilot (or if the operator stops).
This is a pending cleanup obligation, not completed work. No automatic timer or
hard spending cap is claimed. Original import receipt remains unchanged/eligible;
operator should run the guarded --run --resume-import command once while warm.

Latest retry checkpoint: explicit resume stopped at readiness before receipt
archival/import. Original request receipt is unchanged (zero model calls). New
platform log at 07:03:05 UTC shows /ready -> 429, no available instance; new instances
began starting ~5 seconds later and TCP startup passed at ~07:03:48 UTC. This is
consistent with scale-to-zero between operator steps. No further request was sent
by the agent. Repeated full-run warm handoffs should stop until capacity is decided.

Historical proposal (now approved/applied above): service-level minimum=1/maximum=1 for
gather-inference-pilot during the supervised pilot, retaining image/CPU/memory/IAM.
Explicit personal account and Gather project only. This adds idle billed time under
the INR 500 pilot budget until restored to minimum=0.
Concrete commands for approved execution/rollback:

```powershell
gcloud run services update gather-inference-pilot --min=1 --max=1 --region=asia-south1 --project=gather-development-511211 --account=kpanigrahi5602@gmail.com
gcloud run services update gather-inference-pilot --min=0 --max=1 --region=asia-south1 --project=gather-development-511211 --account=kpanigrahi5602@gmail.com
```

Local readiness diagnostics now report safe DNS/TLS/connection/network/deadline
categories as well as HTTP statuses; bodies and tokens remain hidden. Sixteen
runner checks and frontend build pass. Capacity was changed only after explicit
approval, as recorded above; no live inference was requested by the agent.

Latest import checkpoint: failed receipt stage=import, zero model calls, no source
acknowledged. Operator queried the exact request ID and reported no save receipt.
Read-only EXPLAIN resolved the actual function signature (not function execution):
10.422 s total, 8.922 s connection/setup. Second sample separated credential loading
(0.0 s), TLS/login (7.562 s) and full connection/role setup (9.046 s). These are
samples from this operator's network, not production latency guarantees. This
establishes a blocker to the fresh-connection five-second deadline; it does not
prove every possible import failure is resolved.

User explicitly approved a 15-second DB-operation allowance for this pilot only.
Production defaults stay at five seconds; SQL's five-second statement and three-
second lock limits and inference's 15-second limit are unchanged. Pilot Lease
cleanup wait now follows the explicit repository bound (at most 16 seconds).
An actual non-mutating all-zero job/lease lookup reached the hosted function and
returned expected stale_lease / SQLSTATE 55000 in 5.703 s using the approved bound.
40 focused checks and frontend build pass; no hosted import was rerun by agent.

After the operator's no-row check, resume once with:

```powershell
.\scripts\python.ps1 -m scripts.check_hosted_flow --run --resume-import
```

This explicitly attests that the failed import was reviewed. It accepts only the
same project's failed, unacknowledged import with zero model calls and a canonical
request ID. It refuses an acknowledged source, later stage, successful run or an
already resumed import. Old receipt is archived under ignored output/hosted-pilot
before reuse of the SAME request ID, preserving server idempotency and evidence.
There is no automatic retry. Safe receipt now retains fixed LibraryError/database
codes and allowlisted SQLSTATE/deadline reasons through the private exception
chain, never raw SQL/server messages. Physical cleanup remains administrator-only.

Latest startup checkpoint: operator auth-only check passed both sessions. The
subsequent full run failed before admission at cloud readiness. Actual Cloud Run
request log shows GET /ready -> 429, zero reported request latency, with platform
message "no available instance". Startup TCP checks completed later. Agent then
made one readiness-only request against the changed state; it succeeded without
inference. No hosted receipt/source was created by the failed full run.

Runner now supports --check-startup without user passwords/Auth/DB operations and
reports safe cloud_startup_http_NNN statuses without reading error bodies. No
automatic retries or capacity/timeout changes. Eleven runner tests and frontend
build pass. Cold-start admission remains a production concern; this is diagnosis
and a verified warm-state handoff, not a permanent availability fix.

Latest diagnostic checkpoint: operator run stopped at A sign-in, before document
admission or model calls. Both emails are confirmed in the operator's SQL result.
Agent read-only settings check confirms signup disabled and email/password enabled.
Actual cause remains unknown; do not assert a wrong password from the old generic
message. Use `./scripts/python.ps1 -m scripts.check_hosted_flow --check-auth` next.
This prompts for the same two test-user passwords and verifies actual Auth sessions
without loading DB credentials, acquiring Google tokens or importing/calling models.
It stops after the first failed login, with no automatic retry.

The bounded transport now extracts only five known Auth error codes from <=4096
bytes of identity-encoded JSON at the exact password-grant route. Other error
descriptions/bodies stay private; malformed/unknown/oversized errors fall back to
safe generic transport codes. Existing deadlines, no-proxy/no-redirect rules and
generic endpoint behavior are preserved. 25 focused checks (including actual local
HTTP error handoff and auth-only no-work assertions) and frontend build pass.
Reference: https://supabase.com/docs/guides/auth/debugging/error-codes

Prepared 22 October 2026. The operator created pilot A/B Auth accounts and showed
both quotas as source_limit=2, used=0. Public project key was verified/saved under
ignored output, and public signup was disabled by the operator. This runner is
prepared and control-tested; a successful hosted document flow is NOT yet claimed.

## Run once

```powershell
.\scripts\python.ps1 -m scripts.check_hosted_flow --run
```

Uses the selected Sydney project only, encrypted backend credentials and two hidden
prompts for the existing test-user passwords. It obtains a short-lived Google caller
token with explicit personal account/Gather project flags. It never prints passwords,
session tokens, Google tokens or vectors. No Docker, downloaded weights, public signup,
email, IAM grant or deployment. Existing project Python has tokenizer and psycopg2;
the model-benchmark venv lacks psycopg2. Three pinned tokenizer counts match across
both runtimes, so the project launcher is used without installing dependencies.

Preflight verifies target/public key, stored credentials, closed signup and real Auth
identity for both test emails. One isolated startup/readiness request allows at most
60 seconds to observe a cold model container, within the existing 90-second model
startup guard. This is explicitly separate from unchanged 15-second inference and
five-second DB limits; Cloud Run's own timeout may still reject startup. No automatic
retry. A cold-start failure before admission creates no document.

## Actual test and evidence

1. Submit one fixed synthetic TXT through LibrarySession; repeat its request ID to
   confirm stable source/job/version identity. B cannot see the draft or delete it.
2. Existing coordinator uses the real bounded database driver, pinned tokenizer,
   cloud embeddings, private staging and atomic publication. It must publish ready.
3. Real query embedding -> actual hosted pgvector ranking -> exact-version source
   read. A sees the exact original; B cannot open or search it.
4. A deletes; reads/status/search must immediately hide the source.

Plan two model requests (one passage and one query); hard cap remains three through
the existing BoundedProvider. The two later ownership/deletion searches replay only
the identical real query response in memory, validated through the existing search
coordinator. This proves session/database isolation and visibility, not fresh model
calls for those replays or a general relevance benchmark. No synthetic vector fallback.

The worker wrapper stops before source reads/inference if the global claim returns
an unexpected job. Such a lease expires normally. Run in the dedicated pilot project
without another worker. This is supervised developer execution, not production dispatch.

Safe state is written before import to output/hosted-pilot/receipt.json. It records
request/source/job/version IDs, stages, request/replay counts and outcome only.
An existing receipt blocks reruns. Unacknowledged import marks cleanup outcome as
unknown; the request ID lets the operator investigate an uncertain DB commit. Failures
after acknowledged submission attempt an owner-authorized tombstone. No retry loop.

## Physical cleanup is a separate operator step

Deletion removes visibility and cancels late writes, but the restricted logins cannot
invoke the administrator cleanup finalizer. The receipt retains cleanup_pending=true.
After reviewing the receipt, run the exact source-specific finish_source_cleanup SQL
through the dashboard as administrator. Do not claim original bytes/passages were
removed until that succeeds. Preserve receipt history and clear/rearm it only after
reviewed cleanup; never rerun simply to get a passing result.

Seven new control tests plus six LibrarySession regressions pass (13 total), covering
matching query replay, cancellation, unexpected jobs, failure tombstones, uncertain
submission and startup token/deadline/no-retry behavior. Preview and required frontend
build pass. No real hosted/model test was run by the agent in this milestone because
the operator must provide the hidden user passwords locally. Remaining hosted execution,
physical cleanup, cold-start UX, HTTP application and desktop integration are explicit
gaps. User-deferred rotation of chat-exposed database passwords remains outstanding.
