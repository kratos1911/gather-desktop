# Explicit Cloud Run startup

19 October 2026. Implemented and verified on the Windows host with synthetic
engines/identities. Linux packaging, real Google IAM and deployment remain pending.

## Two deliberate entry points

`services.inference.startup` remains loopback-only. Setting PORT or K_SERVICE
does not enable public binding or change its default port. Existing local
commands and the Docker stream entry point remain unchanged.

The new `services.inference.cloud_startup` module explicitly requests the cloud
listener. It requires identity and intended deployment-policy JSON files, a
verified immutable model directory, and an ASCII decimal PORT in 1..65535.
There is no guessed port, host option, local bearer or credential fallback.

Cloud Run requires `0.0.0.0` and supplies PORT; external TLS is handled by the
platform. See [Google's container contract](https://docs.cloud.google.com/run/docs/container-contract).

## Operator-owned configuration

Existing identity JSON example (fictional, not usable cloud identities):

```json
{"audience":"https://gather-fixture.run.app","callers":[{"email":"gather-worker@sample-project.iam.gserviceaccount.com","subject":"123456789"}]}
```

Separate intended deployment-policy example:

```json
{"audience":"https://gather-fixture.run.app","invoker_members":["serviceAccount:gather-worker@sample-project.iam.gserviceaccount.com"],"invoker_check_required":true}
```

Both files are bounded at 4 KiB and reject unknown/duplicate fields. The policy
reuses IdentityConfig validation: one or two explicit service-account members,
no allUsers, duplicates or disabled checks. Its audience and member set must
exactly match the configured receiver identity. Identity subject/email pairing
continues to be enforced by the existing signed-token verifier.

Example future container command, not a deployment instruction:

```text
python -m services.inference.cloud_startup --identity /config/identity.json --deployment-policy /config/deployment-policy.json --model /model
```

Only this explicit composition selects `0.0.0.0:PORT`. The shared server factory
also rejects public binding with local bearer auth, arbitrary callbacks, missing
or mismatched policy, invalid ports or other public host values. It requires the
actual ManagedGoogleServiceAuth object created for the application.

## What this proves, and what it does not

Configuration is checked before model artifact reads. The existing snapshot hash
verification, offline loading and managed-auth lifespan are reused. Trusted keys
are obtained before model startup, and readiness still requires fresh keys and a
ready runtime. One worker, body/header limits, receive deadline, busy admission,
compute deadline and five-second graceful shutdown are retained. Proxy-header
trust and access logging remain disabled. Validation errors avoid file/token details.

The JSON declares intended IAM policy; it does not query Google or prove that
Invoker checking is deployed. Actual service permissions, token/header handoff,
readiness probes, shutdown and idle key refresh require the approved cloud pilot.
Instance-based CPU is still the proposed scheduling choice, subject to spend
approval. No model weights were bundled, no live Google calls made, no public
listener opened by these new configuration tests, and nothing was deployed.

## Verification and next step

- 11 cloud configuration/CLI tests: explicit mode, local default, auth type,
  audience/members, disabled/broad/duplicate policies, ports, input size,
  early configuration/artifact failures and sanitized startup failure.
- 32 existing startup, verifier, refresh and ASGI cases pass with synthetic keys
  and engines; ASGI cases exercise real loopback HTTP and cancellation.
- 18 packaging/staging/notice checks and the frontend build pass.
- Cloud source included in exact staging allowlist. Docker preflight failed:
  Linux engine pipe absent. No restart or repeat attempted; no new Linux image.

Next: start Docker normally, then build a separate candidate and run the same
focused Linux tests with bounded resources. Retain current zlib scan findings,
licence review and pilot approval gates. This milestone does not connect the
sample desktop UI to live inference.
