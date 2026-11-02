# Measured ingestion performance

Scope: the existing private TXT/Markdown/PDF pipeline. No model, parser/chunker
identity, vector dimensions, source offsets, citation or publication changes.
Implemented and enabled in Gather's hosted private API after the approved
comparison. Do not infer general file-size, cold-start or p95 guarantees from
the small fixture measurements below.

## Changes

- StageClock records claim, lease renewal, reading, parsing, chunking, staging,
  embedding and publication. Dispatcher selection and whole dispatch wall time
  are separate. DB totals include helpers/connections and connect/context/execute
  time. Preparation runs concurrently, so its duration must not be added to the
  serial stage totals.
- After a valid trusted claim/manifest/lease, StartupProvider can begin bounded
  readiness preparation while the worker reads, parses and stages. No text is
  sent before validation. Inference waits for readiness and remains sequential.
  Invalid input, shutdown and lease loss cancel preparation. The existing 60s
  startup deadline, three readiness GETs, 15s inference and no-replay rules remain.
  The new background-task cleanup cap is 3s, covering the existing helper's 2s
  cleanup plus polling; it does not extend working deadlines.
- Optional worker-only, job-scoped helpers retain database connections. Admission
  connections remain fresh and bound to verified users. Main work and heartbeat
  use separate sockets. Reset runs before reuse; every transaction rechecks the
  restricted login, sets the fixed local role/empty worker user context and
  reapplies SQL 5s/lock 3s limits. Fixed guard/context commands are batched to reduce
  round trips. Commit/rollback boundaries and SQL lease/version fences are intact.
- At most two physical DB helpers still exist per API process. Idle cached
  helpers can be evicted for fresh work; active helpers are never shared/evicted.
  Credentials use private stdin only. Framed messages keep 2 MiB/1 MiB limits and
  sequence checks; each helper accepts at most 128 operations. Per-call 5s default
  or explicitly selected 15s deadlines still kill/reap helpers, including blocked
  reads/writes. Uncertain operations are never replayed. Job completion closes
  its helpers; no global pool of user sessions is introduced.

References: [Psycopg connection reset](https://www.psycopg.org/docs/connection.html#connection.reset)
and [PostgreSQL transaction-local settings](https://www.postgresql.org/docs/current/sql-set.html).

## Controls and evidence

Trusted flags: GATHER_PIPELINE_TIMING, GATHER_WORKER_DB_REUSE and
GATHER_EARLY_MODEL_START. All default off. The approved comparison uses the same
image first with timing only, then with both optimizations. Existing service
sizes, minimum 0/maximum 1, two accounts, quotas and three model attempts per API instance
remain. No database migration, new service, secret or model deployment.

The exact candidate image passes 112 focused checks at 512 MiB/1 CPU. Disposable
PostgreSQL checks cover real restricted logins, owner isolation, contaminated
session reset, separate heartbeat, idle eviction, SQL failure, deletion fencing,
privilege changes and pinned-tokenizer/PDF composition at the same memory limit.
These use synthetic vectors, not semantic-search evidence. Frontend build passes;
no native assets changed, so the desktop executable does not need rebuilding.

Current API: gather-library-pilot-00005-gkw, Mumbai, image
sha256:2c557d18f7e6d0a5dac28252663ea28234fbab9f0bffddc49224d8d8d50ae498.
All three performance flags are 1. Baseline revision was 00004-9kb, same image with
timing 1/reuse 0/early-start 0. The model service/image/settings were unchanged.

The local same-source test reduced 10 fresh connections/helpers to 1. Its timings
are in output/processing-speed/local-comparison.json. A read-only hosted Sydney
pooler probe also verified reused TLS sessions, context reset and the batched
guard. These Windows-to-DB measurements are not Cloud Run end-to-end timings.
No documents were read or jobs claimed by those scheduling probes.

Stage logs allow only fixed names, durations, counts and mode booleans. Text,
filenames, user/source IDs, tokens, credentials, SQL parameters and raw provider
errors are excluded. Unknown/content-shaped/non-finite metrics are dropped. Logs
use the existing Cloud Logging destination; no replay or usage analytics is added.

## Approved comparison

scripts/benchmark_processing.py verifies the exact hash/body of the existing
generated hosted-pilot.pdf under real pilot B Auth before replacing any version.
It performs two baseline and two optimized imports, at most four real embeddings.
Same source/bytes/model space; no new source slot, search or deletion. Prior text
stays published until each replacement commits. Personal files are untouched.

The password is entered locally; tokens remain in memory. The process waits at
most 15min for the approved candidate deployment, without model requests. Import
IDs and failed/uncertain outcomes remain in safe receipts; nothing retries itself.
Status observation retains 30 reads/5min. A stopped comparison requires review.
Cold starts are classified from platform logs where available. Warm/cold cases
must be reported separately; no p95, general speedup or removed cold-start claim
can come from four small samples. Readiness preparation is recorded separately.

## Hosted results

Same generated 1090-byte, two-page PDF, one passage per version; real Supabase Auth,
database/publication and the pinned CPU model. Every job reached ready on attempt 1
and its exact saved body/hash reopened. Four distinct successful HTTP 200 /embed
requests are confirmed by Cloud Run logs, two in each revision. No searches,
deletions/new source slots or personal-file processing were performed.

| Measurement | Baseline samples | Optimized samples |
| --- | --- | --- |
| Server worker wall time | 39.34s, 40.52s | 18.62s, 17.80s |
| Dispatch including selection | 42.98s, 44.03s | 22.48s, 21.55s |
| In-job DB helpers/connections, including heartbeat | 12, 12 | 2, 2 |
| Ready observed by operator client | unavailable, 60.66s | 35.34s, 33.30s |

All four processing windows had no model cold start observed in platform logs.
Operator readiness preparation before the comparison took 35.39s; a later check
took 4.24s. Those are separate from the paired warm processing measurements.
Actual cold-start-overlap latency was not measured here; scheduling/cancellation
were verified with controlled fixtures. Physical startup still exists with minimum 0.
The two improvements were enabled together, so do not assign the whole gain to
one feature or claim that CPU boost caused it. DB totals can include overlapping
heartbeat time and must not be added to worker wall time.

The first client harness incorrectly required HTTP 200 for import instead of its
correct HTTP 202. The server had accepted and completed the job. The harness
stopped without a replay; the failure remains in the receipt. After a local
client fix and real HTTP tests, explicit --resume-ack reused the original request
key, recovered the same published version and consumed no extra inference.
Its interrupted client wall time is deliberately unavailable, while the original
server timing is retained. The other three client observations were uninterrupted.

That correction adds explicit expected_status=202 support for the local operator
client; HTTP 200 remains the default for Auth/DB/model clients. The approved server
image 2c557d18… was kept unchanged because its runtime uses the original 200 paths.
Eighteen local operator/HTTP regression checks cover the correction and safe
acknowledgement recovery. These check groups overlap; do not sum them as unique
tests. The local correction requires no additional deployment or model request.

Ignored evidence lives in output/processing-speed/: hosted comparison JSON,
embedding-request-evidence.json, local/read-only DB timings, exact-image/runtime
proof and the two deployment receipts. Current state is in MEMORY/TASKS; dated
work is recorded once in PROGRESS. Logs isolate warm inference itself at about
0.39–0.57s HTTP /embed latency on this tiny fixture; remaining total time includes DB/setup, admission,
selection and polling/network overhead. Larger documents may behave differently.
