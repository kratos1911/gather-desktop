# Cloud ingestion integration pilot

21 October 2026. A developer-only end-to-end backend probe now composes the
existing ingestion coordinator, cloud HTTP client, atomic SQL publication and
query/context coordinator. The desktop remains a sample preview.

## What is connected

`services/worker/cloud_provider.py` supplies the existing CloudInferenceClient
with a hash-verified pinned tokenizer. Only tokenizer bytes are loaded locally;
no model weights, Transformers model, download or new dependency is needed.
The same provider contract serves document ingestion and query embedding.
Production defaults still obtain keyless identity from Google's metadata service.
There is no deployed API/worker yet to run that default composition.

The client permits an explicitly supplied trusted token provider with exactly
matching identity config and get/invalidate methods. It is never selected from
user input. `scripts/check_cloud_ingestion.py` alone defines a developer pilot
provider: a short-lived Google impersonation token arrives over stdin, is checked
for expected audience/caller/expiry, and is never written or printed. These claim
checks are not signature verification: real Cloud Run IAM and the receiving
signature verifier perform authentication. No key download, automatic refresh,
shared-secret fallback, credential CLI argument or desktop secret is introduced.

## Reproduction and boundaries

Preview: `./scripts/python.ps1 -m scripts.check_cloud_ingestion` (no network).
Execution requires explicit `--run`, Docker and the existing database image,
the D: tokenizer snapshot and the model-benchmark Python environment (tokenizers).
The operator pipes a newly minted caller ID token to stdin; never paste it into
chat. Use the exact Gather audience and personal account from pilot.json. At most
three model requests per run, no automatic retries; failures count against the cap.
One separate authenticated `/ready` request precedes ingestion, with the unchanged
15-second deadline. Cold readiness failure stops before creating a database.
It does not guarantee the instance will remain warm or solve product startup UX.

Only a random `gather-cloud-pilot-*` database container is created: 256 MiB,
one CPU, no network, ports or persistent volumes, removed in finally. The existing
SQL bootstrap simulates trusted user context; it is NOT Supabase Auth/PostgREST
or a production repository adapter. Synthetic bytes are the only cloud content.
Actual migrations, leases, passage staging, vector publication, pgvector search,
exact-version reads and deletion are used. No R2 or hosted Supabase writes occur.
One-source retrieval proves plumbing, not relevance or absence detection.

## Evidence and next gate

The user uploaded digest b1e299d..., deployed revision
gather-inference-pilot-00001-d4z and applied scoped caller/invocation grants.
User-reported anonymous request: 403. User-reported real authenticated embedding:
512 values, pinned revision, 1.06 seconds. This is limited positive/anonymous
evidence, not all negative authorization scenarios or complete IAM inspection.

Agent pilot first failed. Read-only Gather logs showed a 200 request taking
35.976689370 seconds alongside startup activity, beyond the 15-second client
budget. No inference deadline increased. A separate readiness preflight was
added; the next explicit run passed at 2026-10-21T13:46:34Z with two real model
requests (one document, one query). Duplicate submission, ready publication,
search/open, foreign-owner SQL read rejection and deletion visibility passed.
Deleted search was checked with a stored real document vector, not another model
call. Safe receipt: tests/inference/results/cloud-ingestion-20261021.json; local
copy: ignored output/cloud-ingestion-pilot.json. Token and
vector values are absent. The failed attempt has no structured receipt; later
failures record safe stage/code in output/cloud-ingestion-failure.json.

57 focused checks pass (22 identity/composition, 35 ingestion/search/transport).
The transport tests initially failed under restricted loopback permissions;
the same tests passed under the owning user, without code/limit workarounds.
Three tokenizer parity cases match the existing pinned AutoTokenizer; no model
loaded. Required frontend build passes; UI/native assets unchanged.

Next: authenticated backend application/session boundary and production database
connection, then real desktop import/search/open/delete. Hosted user ownership,
per-user quotas, remaining negative cloud-auth cases and cold-start UX remain
gates. Keep pilot spend supervised; budget alerts are not a hard cap. This work
does not make another deployment, grant IAM, change Intrixshield or stop APIs.
