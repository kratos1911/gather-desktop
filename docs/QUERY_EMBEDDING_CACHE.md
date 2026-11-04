# Private encrypted query-embedding cache

4 November 2026: encrypted Upstash caching is deployed and verified in the
installed private app. The corrected miss/repeat pair confirms model reuse.

## Flow and safeguards

Auth -> owned metadata -> empty if proven unpublished; otherwise validate/token
count -> Redis vector hit or one normal embedding -> fresh owned search ->
relevance gate -> exact-version reads. Cache never supplies identity, documents,
search results or citations. Deletion/version/ownership checks remain fresh.

Keys HMAC-bind owner, exact query, model/revision/dimensions and prompt. HKDF
separates HMAC and AES-256-GCM keys; nonce/AAD prevent ciphertext movement.
No raw query, file, filename, bearer or plaintext vector enters Redis. Finite
unit-length 512-D validation and authenticated expiry reject bad/stale entries.
Active TTL600s is separate from document deletion; provider backup retention is
not claimed to end at TTL. Those release-policy inputs remain open.

Fixed GET/SET-EX only, approved 1s operation deadline plus existing helper cleanup, no
redirect/proxy inheritance/retry. Outages cause30s backoff and normal authorized
search within existing limits. Hits skip inference budget use; misses retain its
three-attempt cap. Empty/unauthorized/cancelled calls do no cache work. Enabled
startup requires trusted HTTPS origin and mounted secrets; default is off.
Diagnostics log fixed events only, never queries/keys/owners/vectors/tokens.

## Provider and evidence

User-created gather-cache, ID40316b37-032e-4eb6-984b-ae6ad3dfffe9, endpoint
https://relaxing-goshawk-225370.upstash.io. Native console verified Free, TLS,
AWS Mumbai/ap-south-1,500K monthly commands,10GB bandwidth and **250MB shown in
this account**, despite pricing advertising256MB. Quotas are shared.

Token/master key are DPAPI protected in ignored output/credentials/upstash-query-cache.dpapi;
hidden setup does no network I/O and refuses overwrite. Never bundle credentials.
Proposed backend access: two Secret Manager secrets, existing runtime identity only.

49 focused crypto/coordinator/config/session checks pass on pinned runtime and
the final image. Original host rejected its mismatched server
versions; no packages changed. Final image 8cff0f17326cafd02c9f3bd51272a2ece8278c5272aca4b4ec513a64117e6ccb
adds Python source only; existing cryptography50.0.2/package review still applies.
Live encrypted synthetic SET/GET passed with TTL600s: PC write406ms/read391ms,
zero model calls/retries. This is not semantic or Cloud Run latency evidence.
Receipts/build logs: output/upstash-cache/. A usage-limit approval review failed
once; the same check passed normally after the reported retry time.

## Hosted/native acceptance and remaining limits

Approved initial rollout installed the disclosure-bearing app and created two
named cache secrets with explicit runtime-only reader grants. API00010-d2g used
the original .5s limit: search succeeded through fallback, but Redis timed out and
the first embedding did not populate cache. CPU1 Linux reproduced the timeout;
helper startup alone took352ms. The timing-only 5s diagnostic was not acceptance
of the .5s gate. A strict corrected 1s probe passed at524ms write/445ms read.

With separate approval, deployed API00011-vn4 and used one additional embedding.
Fixed logs confirm miss -> stored -> hit. Both native searches returned the Cedar
image with exact citations and excluded the resume. HTTP durations13.87s/10.11s
are one observed pair, not p95 or a general speed claim. Exactly two embeddings
were used overall: initial fallback1 plus corrected miss1; repeat hit used none.
No files/model/schema changed. CPU1/2GiB/min0/max1, INR500 and Upstash Free remain.

Installed identity/GUI subsystem, disclosure rendering and installer build pass.
Safe receipts: corrected-deployment.json, corrected-paired-search-log.json,
live-acceptance.json and screenshots under output/upstash-cache/. Raw failure
and diagnostic receipts are retained. Next performance work is Auth/DB round trips;
fresh ownership remains mandatory. Public/provider-retention gates remain open.

References: [REST commands](https://upstash.com/docs/redis/features/restapi),
[security](https://upstash.com/docs/redis/features/security).
