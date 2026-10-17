# Receiving service identity — local verifier

## Trusted startup composition, 18 October

`services/inference/startup.py` parses operator-owned JSON bytes (maximum 4 KiB)
with exactly audience and callers. Each of one or two caller entries has exactly
email and subject. Unknown fields, duplicate JSON keys, empty/oversized lists,
invalid accounts and repeated emails/subjects fail closed. Configuration is frozen;
request claims cannot add callers. The email/subject pair must match together.

`create_trusted_app(raw_identity, runtime)` connects this policy to the existing
ASGI lifespan and one ManagedGoogleServiceAuth instance. Both callers share a
single key snapshot/fetch thread, cooldown and expiry. Valid keys precede runtime
startup; missing keys prevent model load, and shutdown closes both. Runtime is
supplied by trusted artifact-loading code; this factory does not verify artifacts,
read environment defaults, bind publicly or bypass IAM.

Example shape (fictional identities; never deploy unchanged):
```json
{"audience":"https://gather-model-example.run.app","callers":[
  {"email":"gather-api@sample-project.iam.gserviceaccount.com","subject":"123456789"},
  {"email":"gather-worker@sample-project.iam.gserviceaccount.com","subject":"987654321"}
]}
```

40 focused checks pass: four new startup/pairing checks, 32 existing identity/
managed-auth checks, four staging checks. Frontend build passes. Tests use synthetic
RSA keys/mocked Google responses, no real model or cloud IAM. Legacy single-caller
constructors still work; legacy configs naming two invokers now fail rather than
silently omitting the second caller. Packaging allowlist includes startup.py;
the existing built image has NOT been rebuilt and predates these changes.

Next: verified model-artifact startup/entry-point assembly, then package and verify
that exact candidate. Actual IAM, public ingress, licence/OS security, project/
region/spend approval and deployed negative-token tests remain separate gates.


## Header pairing, 18 October

See [[docs/CLOUD_IDENTITY]]: cloud client sends the platform and application
headers separately. Receiver still trusts only the signed Authorization token.
Local signed-key handoff/rejection tests pass; deployed proxy/IAM remains unverified.
Local real-model HTTP is now verified in [[services/inference/HTTP_SMOKE]].

## Linux integration update, 17 October

The verifier and managed refresh are now included in the 47-package Linux candidate.
Synthetic signed-token admission, key freshness and actual SIGTERM cleanup were
verified together; see [[services/inference/SERVING_IMAGE]] for exact image/test
and remediation evidence. Historical pending-packaging statements below are
superseded by this update. Live Google/IAM/header behavior and real-model HTTP
remain unverified; public binding remains blocked.

## Managed refresh update (17 October)

`ManagedGoogleServiceAuth` now owns the verifier snapshot and refresh lifecycle.
ASGI acquires trusted keys before starting the model, then starts one refresh
thread. Shutdown signals its cancellation event and joins the thread; readiness
also requires fresh keys. The initial fetch fails startup if unavailable.

Fetches use only `https://www.googleapis.com/oauth2/v1/certs`, default verified TLS,
no proxies/redirects/credentials, the existing isolated helper's five-second total
deadline and at most two seconds cleanup. The response is limited to 64 KiB/eight
keys. Freshness uses Cache-Control max-age, Age and Date, capped at 300 seconds;
network elapsed time is conservatively deducted. Stale, noncacheable, compressed
or malformed responses cannot replace the snapshot. Key parsing/validation must
complete before atomic replacement. No remote key URL is accepted from a token.

Refreshes occur at 80% of remaining freshness, with a 30-second minimum interval
and 240-second maximum. A nonblocking lock prevents overlapping refresh attempts.
Failures retry through the scheduled loop at 30 seconds, never through inbound
requests. The previous snapshot survives only to its unchanged expiry. Very short
upstream freshness or outages may therefore cause temporary unavailability; this
does not justify accepting stale keys. Unknown key IDs never initiate network I/O
and can remain rejected until a scheduled refresh. Limits are per verifier instance;
the deployment must retain the planned single web worker.

Ten new mocked transport/rotation/lifecycle tests, eight verifier tests, nine ASGI
tests and eleven existing transport checks pass (38 total). Frontend build passes.
The first host run stalled in Windows event-loop socket initialization under sandbox
restrictions; a bounded stack trace identified it, only those test processes were
stopped, and the run passed with loopback permission. No application-code workaround.
No live Google endpoint, real service token, model or Docker workload was used.

Next: package these dependencies/modules in the Linux candidate and verify the
lifecycle there. Live Google response/header handoff and deployed IAM remain
unverified, and public binding remains blocked. OS release findings remain open.
The original snapshot-only milestone below is retained as implementation history;
its key-retrieval gap is now addressed locally, not yet proven against Google.

## Original snapshot verifier

17 October 2026. `GoogleServiceAuth` is a synchronous, network-free authentication
callback for the existing ASGI app. It verifies RSA signatures with google-auth
2.59.1/cryptography 50.0.2; it does not implement cryptographic primitives itself.
The locally tested dependencies are recorded in requirements-asgi-local.txt.
No packages were installed or shared environments modified for this milestone.

## Contract

Trusted startup code supplies IdentityConfig, the allowed service account's numeric
subject ID, and a public certificate/key snapshot. Email and subject must both
match, preventing email-only authorization after account recreation. Public keys
are not secrets, but their provenance is a security boundary: requests must never
supply them. Google key retrieval is not implemented in this slice.

Snapshots contain at most eight RSA 2048–4096-bit keys, at most 8 KiB per PEM.
Caller-supplied freshness must be no more than the trusted key response's remaining
freshness, capped locally at 300 seconds. Wall and monotonic expiry both apply.
The copied snapshot is immutable; replacing it requires trusted lifecycle code,
which remains to be integrated. There is no stale-key fallback or per-request
network fetch on an unknown key ID. Missing/invalid configuration fails startup.

Requests need exactly one Authorization Bearer value, at most 8 KiB for the token.
Only RS256 is allowed; duplicate JSON claims, malformed tokens, unknown keys,
remote key references and unsupported JOSE headers are rejected. Issuer, exact
audience, exact subject/email, verified-email boolean and integer issued/expiry
times are checked. Maximum lifetime is 3660 seconds, with zero clock-skew allowance;
optional not-before is enforced. Rejection checks cannot authorize: the library
must verify the signature before returning success. Errors reveal no token details.

The ASGI adapter rejects failed authentication before calling inference. Its
readiness endpoint also becomes unavailable when the key snapshot expires.
LocalBearer remains available only for existing local checks. Public binding is
still unconditionally blocked; a supplied key snapshot cannot enable it.

## Evidence and open integration

Eight new tests use ephemeral synthetic RSA keys and real signature verification.
They cover tampering, untrusted signers, signed wrong claims, algorithm/header
confusion, duplicates, snapshot expiry/configuration, and actual loopback admission.
Together with nine existing ASGI tests, all 17 pass in the isolated D: Windows
environment. Frontend build passes. No Google calls or model loads occurred.

This is not evidence of deployed Google IAM. Trusted HTTPS key retrieval, rotation
and lifecycle scheduling, Linux dependency hashes/image inclusion, current security
review and deployed auth/header behavior remain unfinished. The previous 41-package
Linux image does not contain this new verifier. Existing Docker-unavailable blocker
was not retried. Do not use a manually supplied synthetic key for production.

Next: bounded trusted Google key retrieval/refresh, sharing existing transport
limits, with fail-closed expiry and no refresh storm from attacker-chosen key IDs.
Then package and test on Linux. Deployment remains separately gated.

References inspected:
- [Google JWT verification API](https://google-auth.readthedocs.io/en/latest/reference/google.auth.jwt.html)
- [Google token verification guidance](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [Cloud Run service identity and header behavior](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)

Cloud Run may strip signatures from a platform-auth header. The future deployed
integration must preserve a verifiable application token where needed and keep IAM
enabled; this local verifier does not prove that header handoff works on Cloud Run.
