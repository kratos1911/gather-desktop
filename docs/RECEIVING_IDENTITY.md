# Receiving service identity — local verifier

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
