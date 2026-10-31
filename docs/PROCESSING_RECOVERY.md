# Recovery eligibility and startup handling

Follow-up to the private PDF slice. The owner-selected existing import reached
ready after one explicitly approved recovery, using two model requests. Its text
was not opened, searched or copied into development evidence. Metadata-only
listing showed both saved PDFs ready. No duplicate source or quota increase.

## Recovery contract

Migration14, `202610310003_recovery_readiness.sql`, adds owner-scoped wrappers
around the existing listing/status functions. They preserve pagination and add
only `can_resume`. The private helper checks the current target, automatic-job
membership, owner, deletion, attempt cap, backoff and lease expiry. A cursor or
this hint never grants authority: the original recovery transaction still locks
and checks the exact job/attempt. No direct private-table/helper grants.

The client shows Resume only for an eligible job. Active processing has no Resume
button; expired leases remain recoverable. A rejected stale request refreshes
metadata once, never processing itself. Status refresh keeps the matching card's
attempt/error/hint current. Accepted recovery after reconnect restores bounded
metadata watching; it does not automatically retry inference. Listing and status
do not generate embeddings. Older servers retain a conservative queued fallback.

The existing three-call model allowance is unchanged. Exhausted recovery is
rejected before changing intent; admission rejects a file known not to fit the
remaining allowance. This per-instance counter is not a billing meter or a durable
account quota. Existing jobs/attempts, originals and publication fences are reused.

## Startup and measured limits

Keep at most three readiness GETs inside60s. Retry only startup429/503, with waits
of10s then20s, instead of consuming all probes immediately. Warm readiness returns
on its first probe. The synthetic clock case proves this scheduling policy, not
a live latency guarantee. Inference stays15s and is never replayed automatically.
Cloud logs contain allowlisted startup outcomes/counters, never whole result
objects, provider bodies, credentials or document text.

The user approved startup CPU boost on the existing inference service: runtime
2CPU/5GiB stays fixed, with4CPU during startup and10s afterward; min0/max1 remains.
Google bills that boosted period. Source:
https://docs.cloud.google.com/run/docs/configuring/services/cpu#startup-boost
The model image/identity/weights did not change. API CPU throttling was already
disabled and was ruled out as the cause.

Observed platform startup: earlier unboosted29.11s; boosted rollout30.92s. These
are different starts, not a controlled benchmark, and show no demonstrated boost
benefit. A later operator readiness check passed in4.28s including identity setup.
The selected recovery request at18:41:14UTC completed at18:42:22UTC on31 October:
about68s overall. Startup checking began at18:41:48UTC; these coarse timestamps do
not identify every stage's cost. Do not claim instant processing or a measured
percentage improvement. Profile parsing/DB connections/staging/inference before
choosing the next latency change; persistent connections must preserve role,
owner, whole-operation deadlines and lease-heartbeat isolation.

## Deployment and evidence

Explicitly approved/applied to Supabase `fatolholcjxpwocnpzws`. Existing Gather
API revision `gather-library-pilot-00003-dpb`, image
`sha256:ae5a05c14d30aa1c259f962f766ece08ec5e778635f835a64041558c84b196d1`,
CPU1/512MiB, min0/max1. Model revision `gather-inference-pilot-00002-jpv` retains
imageb1e299de… with startup boost enabled. No new service, secret, IAM binding,
larger quota or always-warm instance. The aggregate INR500 allowance remains;
budget alerts are not a guaranteed billing cap.

Verification:60 focused checks pass in the exact Linux API image at512MiB/1CPU;
eight isolated SQL groups pass with synthetic identities. All68 frontend checks,
lint/format/build and native rebuild pass. The new reconnect-watching regression
and single-refresh regressions are frontend-only; they required no second API image or model request. Initial local
Python checks stalled in restricted execution; normal Windows execution completed,
and the exact image passed. One stale test route expectation and synthetic lease
timestamps were corrected without weakening implementation constraints.

Ignored evidence: output/recovery-fix/ contains migration/ready screenshots,
image verification, deployment/boost/readiness receipts and selected status logs.
The ready-flow executable was F2FA2A1D…; the subsequent reconnect-watching rebuild
has separate packaging evidence. Clean-machine install/signing and broader model
quality remain unverified. No personal-content preview or live deletion was used.
