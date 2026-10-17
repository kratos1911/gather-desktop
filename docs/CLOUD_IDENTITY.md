# Outbound Google service identity

## Header handoff update, 18 October

CloudInferenceClient now sends the same metadata-issued token in Authorization
and X-Serverless-Authorization. Cloud Run checks the latter when both are present;
Gather verifies the signed Authorization token independently. The stripped platform
header is never an application credential or fallback. Missing, stripped or
ambiguous application authorization remains rejected. Public bind guard unchanged.

The cloud client tightens its token ceiling to 7,168 ASCII characters so two
copies leave space within the existing 16 KiB incoming-header limit. Larger tokens
fail before inference HTTP; no limit increase, second token fetch or automatic
retry. Actual platform-added header size still requires deployed verification.

33 focused identity/verifier/transport checks and frontend build pass. The new
handoff fixture uses ephemeral RSA keys and a simulated platform transformation;
it proves local client/verifier compatibility, not Google signing, IAM or ingress.
The previously built image predates this source change; package the reviewed source
before a pilot. No models, Docker operations, cloud requests or deployment used.

Reference inspected 18 October: [Google service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service).

### Required pilot evidence, not executed

- Inspect actual IAM: invoker check enabled, no allUsers/allAuthenticatedUsers,
  only approved service accounts; verify exact audience and account subject IDs.
- Authorized platform and application tokens: /embed succeeds with valid output.
- Missing/wrong-audience/non-invoker platform token: rejected by Cloud Run even
  when the application token is valid; prove application inference was not called.
- Valid platform token with missing/tampered/wrong-caller application token:
  Gather rejects before inference; no fallback to the platform header.
- Verify signed Authorization survives the real proxy and total headers fit limits.
- Keep logs free of token values, queries, vectors and document content.

Next local prerequisite: trusted startup wiring and explicit allowed API/worker
identities. Current receiver binds one caller; a two-caller deployment must not be
claimed supported until that startup/authorization contract is implemented/tested.
Actual pilot requires separate project/region/spend approval and security gates.

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
