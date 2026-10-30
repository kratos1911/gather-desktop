# Model availability and explicit recovery

Current extension: automatic workers use the separately approved bounded startup
GET retry policy; operator identity reuses the established in-memory expiry cache.
Manual diagnostic checks still do not retry embeddings. Current deployed/native
evidence and remaining gates: [private delivery](PRIVATE_DESKTOP_DELIVERY.md).

26 October 2026. Diagnostics/manual readiness check implemented and locally
verified. No automatic ingestion or inference replay. The older generic model
failure remains unconfirmed; live observations below have narrower evidence.

## Authenticated flow

Explicit Check model connection -> POST `/v1/model-status` with `{}` and user
bearer -> existing Auth/two-pilot-user verification -> unchanged process budget
-> fresh Google backend identity -> fixed private Cloud Run GET `/ready`.
No document/query/embedding is submitted. Caller URLs/owners are rejected.
Response is exactly `{state, used, limit}`. Readiness is a last-check snapshot,
not continuous health or proof of embedding success; empty search stays disabled.

| State | Evidence / explicit recovery |
| --- | --- |
| ready | Exact readiness response; embedding/search still needs its own validation |
| model_identity_unavailable | Backend caller acquisition failed before model HTTP; inspect CLI/account/network/configuration |
| model_access_denied | Model HTTP401/403; check caller/audience/IAM, not Supabase user password |
| model_busy | Local contention or exact app JSON busy; wait and check deliberately |
| model_rate_limited | HTTP429 without proven app busy; startup/platform/capacity cause unknown |
| model_deadline | Deadline reached; no automatic resend. GET readiness submitted no embedding; inference outcome can be unknown |
| model_not_ready | Exact false readiness/model_unavailable; inspect service if persistent, do not guess why |
| model_budget_exhausted | Existing three-attempt cap reached; no further request sent. Review spend before intentionally starting a new operator session |
| model_unavailable | Unknown/malformed/service errors remain generic and redacted |

Known errors retain legacy codes for ingestion retry mapping. ModelServiceError
implements both existing inference and embedding exception contracts so the
shared embedding wrapper preserves only the safe reason. Unknown exceptions
stay generic. API emits only fixed code/status pairs; frontend reads at most
4 KiB of an error response and rejects unknown/extra fields or mismatched status.

## Bounds and cost

Outbound identity-plus-HTTP retains 15 seconds. Identity acquisition requests
five seconds; operator gcloud now receives that allowance instead of silently
using its separate 15-second default. Worker/standalone minting keeps that default.
No HTTP starts after the outbound deadline. API/transport/cleanup limits remain.

Three inference attempts per API/worker process remain, failures included.
Probes never increment/reset them. Exhaustion is reported locally without a
cloud probe. These are pilot safety counters, not billing/token meters. No
polling, inference retry, queued requests, warming/minimum-instance change,
deployment, IAM/dependency change or new migration. Explicit GETs may wake/load
the service and incur startup/instance charges; budget alerts are not a hard cap.

## Verification

123 focused Python checks pass: diagnostics, controlled real loopback transport,
identity, search/session/API, operator/hosted-runner controls, ingestion and local
HTTP composition. All test providers/documents/identities are synthetic.
48 frontend checks, build/lint/format/diff pass. Production bundle hashes remain
unchanged; existing native artifact reused. No benchmark, Docker workload,
hosted document operation or live embedding was run.

Coverage: Auth before probes, exact target/headers, cancellation, unchanged cap,
no retries, unknown-body redaction, wrapper reason preservation, strict counters,
account-change late replies, explicit UI activation, retained empty-library guard.
First tests caught the wrapper collapsing diagnostics; fixed without weakening
redaction. One mock assertion was corrected to inspect call args rather than
the mocked class constructor signature; its Auth assertion remains.

## Live observations

Only Gather local servers were started after expired process handles/no listeners.
Existing pilot-A sign-in and listing worked. No other process was stopped.

1. First manual app check stopped at identity acquisition, used=0. No model HTTP.
2. One isolated token mint with the same five-second allowance passed in 3.45 s.
   Token discarded, never printed/saved. This proves capability at that point;
   it does not establish the preceding transient failure's cause.
3. With that prerequisite verified, one further explicit app check reached
   model_deadline, used=0. No automatic retry/embedding, and no further probes.
4. Read-only log lookup found a matching recent GET `/ready` at
   2026-10-26T17:51:45.547426Z: HTTP200, latency 30.994315877 s. This is consistent
   with readiness completing after the client's deadline. Startup/network/
   platform causes were not independently isolated; no retroactive diagnosis of
   the older incident or perpetual present-readiness claim.

Evidence: `output/model-availability/manual-check-20261026.png`, `verification.json`.
UI correctly says readiness timeout submitted no embedding. A successful in-app
ready result on an explicit later check and a fresh post-idle embedding remain
unverified. Reuse prior selected-file semantic evidence; do not recreate the
cleaned document for this check. Next: deliberate readiness confirmation, then
separately scope automatic import processing and its ownership/resource gates.
