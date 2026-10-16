# Outbound Google service identity

Local client milestone verified on 17 October 2026. No Google requests, credentials,
IAM changes or deployments were used. This is not proof of deployed authorization.

## Flow and boundaries

Trusted API/worker → MetadataTokenProvider → fixed Google metadata identity endpoint
→ cached short-lived ID token → CloudInferenceClient → target /embed.

IdentityConfig requires an exact HTTPS run.app origin, a dedicated service-account
email, one or two explicit service-account invokers including that caller, and
invoker checking enabled. These are intended policy settings, not a read of actual
IAM. Custom audiences/domains are deliberately unsupported in this first slice.
The client is server-only; no tokens belong in the desktop app.

Metadata acquisition uses the existing isolated HTTP helper, no inherited proxies
or redirects, a fixed metadata destination and Metadata-Flavor request/response
checks. It accepts at most 8 KiB and has a five-second total acquisition deadline.
Acquisition and inference HTTP share a 15-second budget; existing forced helper
cleanup can add at most two seconds per helper. The model runtime independently
enforces its compute deadline. A caller timeout alone cannot stop remote work.

Cache checks include exact audience, caller email, issuer, RS256 header, integer
expiry/issued time and a 60-second expiry margin. A monotonic cache deadline also
prevents wall-clock rollback extending reuse. These decoded claims are sanity
checks, **not signature verification**. Cloud Run IAM must verify the Google token
and authorize the caller. Near-expiry refresh failure returns an error, never an
old token or shared secret. Concurrent token acquisition returns busy; there is
no automatic HTTP retry. A rejected token is invalidated.

Public ASGI binding is still blocked. Actual deployed policy inspection, rejection
of anonymous/wrong-audience/wrong-caller requests and the receiving server's cloud
auth wiring remain release gates. No local configuration can prove those gates.

## Evidence and next step

- 12 synthetic identity tests: configuration, claims, caching/expiry, refresh
  failure, cancellation/busy, metadata limits, shared deadline and no fallback.
- 11 existing loopback transport tests pass after shared helper extraction.
- Required desktop frontend build passes; no UI/native inputs changed.

Next: reproducible Linux serving dependencies/image and security review, followed
by resource-preflighted real HTTP/startup/shutdown checks. Cloud pilot and actual
IAM verification require separate approval. No model benchmark rerun is needed
for this client-only change.

Reference inspected: [Google service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service).
