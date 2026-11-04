# One fresh authentication per search request

Implementation/image and approved hosted comparison pass. API00012-x89 is live.
Scope is performance item1 only: no connection pooling, batching, model or UI change.

PilotSession retains its fresh Auth verification and private-user/fixture guards.
Its SessionClient search_authentication context shares the resulting canonical
user ID with the existing coordinator in the same synchronous request. The first
Auth call still reaches Supabase; the second consumer makes no duplicate HTTP
call. No decoded-JWT shortcut, caller-supplied owner or cross-request identity cache.

The scope binds client origin, bearer headers and thread. Changed configuration,
nested/parallel borrowing and cancellation fail closed. Only the user ID is kept,
returned by copy; malformed Auth data is not memoized. Finally clears state and
releases the lock on success/error/cancellation. The next search verifies again,
including when its embedding is already in Redis. Every non-Auth RPC remains fresh;
RLS, publication/version checks, citations and all limits remain authoritative.

## Local evidence

Ten new synthetic/loopback cases verify one real HTTP Auth request per scope,
fresh subsequent verification, denial after revocation, mutation/thread/cancel
guards and unchanged private access gates. They do not prove hosted JWT/RLS.
101 focused checks pass across the packaged run and one corrected harness case:
the operator-receipt test needs a temporary /app/output mount in its read-only
container. Production filesystem settings are unchanged. Frontend build passes; native assets did
not change, so no native rebuild is required. No new package or inference call.

The Windows restricted runner could not reach its loopback peer; the host check
passed. Existing HTTP-flow doubles still used retired recovery route names and
lacked the new context protocol; only those test fixtures were updated. Their
original assertions and production routes/permissions were preserved.

Candidate40fcacab2d1a104c60bb4296f9339f68d4d2a920f288002a2d1694faafe3f4b1
extends the verified cache image. Safe evidence/build context: output/search-auth/.
The prepared live probe uses a hash-fenced saved real Qwen vector for a fictional
question with exact matching model/revision/dimensions/prompt. It is an Auth/HTTP
comparison against the current owned library, not relevance or new inference proof.
With specific approval, deployed the verified image with CPU1/2GiB/min0/max1,
secrets/IAM, Redis policy and INR500 allowance unchanged. Native/files/schema
were not changed. Before/after HTTP durations for identical cached museum-01:
10.25s -> 7.84s; both200/cache-hit, zero new model requests. This single observed
pair is not p95 or a general speed guarantee. It does not assess relevance of
that fictional question to the current library. Receipts: baseline-log.json,
after-log.json, deployment.json and live-acceptance.json under output/search-auth/.
Connection pooling and batched reads remain separate future work.
