# Bounded service clients

22 October Auth diagnostics: password-grant errors alone may read <=4096 bytes of
uncompressed JSON to extract fixed allowlisted codes (invalid credentials, email
confirmation/provider, banned user or CAPTCHA). Descriptions and other fields
never cross the helper boundary. Unknown, malformed or large bodies retain the
generic error. All non-Auth error bodies remain unread. HTTP/cleanup deadlines
and redirect/proxy policy are unchanged. See HOSTED_FLOW_PILOT.md for evidence.

16 October 2026. Server-side adapters in `services/worker/service_clients.py`;
shared fixed-process HTTP boundary in `service_transport.py`. No dependencies,
credentials, public routes or hosted resources were added. Evidence: TASKS.md.

## Connections

- `SessionClient(base, public_key, token, cancel=event)` implements the query
  coordinator's API callable. Only Auth user lookup and the two published read
  RPCs are allowed. HTTP methods and exact payload fields are checked locally.
  The bearer token is fixed for the lifetime of the instance; create another
  instance when the session changes. No automatic refresh or retry.
- `InferenceClient(base, credential_value, count_tokens)` implements the existing
  ingestion/query provider contract. It sends raw role/texts to fixed `/embed`,
  after checking exact prompted token counts. The future server must apply the
  runtime template once and return its pinned model/revision/dimension/vector
  contract. Existing coordinators validate the response before staging/search.
  INFERENCE_HTTP.md now supplies a locally verified authenticated loopback server;
  production ingress and cloud identity remain pending.

Operator-configured HTTPS origins only, without paths, credentials, queries or
fragments. Never obtain origins, transports or model credentials from desktop
payloads. `_test_loopback=True` explicitly allows plain HTTP only to 127.0.0.1
for disposable tests; there is no automatic fallback. Normal HTTPS uses Python's
certificate/hostname verification. Deployment CA/DNS/TLS integration is unverified.

Session credentials require a publishable key or legacy anon JWT plus an
authenticated user JWT. Local parsing rejects obviously privileged credentials;
it does NOT verify signatures or grant authorization. Auth/PostgREST remains
responsible for signature, expiry and ownership checks. A forged role claim
cannot substitute for server verification. Pass the same cancellation event to
SessionClient and search to stop an in-flight read as well as inference.

## Limits and failure behavior

| Boundary | Limit |
| --- | --- |
| Session request | 5 seconds wall-clock |
| Inference request | 15 seconds wall-clock |
| Helper cleanup | Up to 2 additional seconds |
| JSON request body | 64 KiB |
| Response | 4 MiB; identity encoding and application/json only |
| Concurrent HTTP helpers | One per server process; excess fails busy, no queue |
| Model input | Existing 4 texts / 8 KiB each / 16 KiB total; 2,048 tokens each / 4,096 total |

The parent starts an isolated Python helper, supplies credentials/body only via
stdin, and terminates/reaps that helper on timeout or cancellation. DNS, TLS,
headers and slow body reads fall under the same deadline. No proxies, Python
startup hooks or unrelated environment secrets are inherited. Credentials are
absent from process arguments; response/error bodies are never logged. This is
an I/O deadline boundary, not an OS sandbox or remote-compute cancellation.

Redirects are refused. Response size is checked while reading; malformed JSON,
duplicate keys and NaN/Infinity literals are rejected. Authentication/rate/timeout/
busy failures have fixed codes, with no automatic retry or provider fallback.
No response cache is introduced. Killing a local HTTP helper does not guarantee
that a remote server has stopped processing; the future inference handler must
enforce its own runtime deadline and resource limits.

## Verification and remaining gates

Controlled loopback peers verify request headers, fixed routes, template handling,
oversized input/output, invalid JSON/type/encoding, redirects, safe error mapping,
timeouts, cancellation, busy rejection and helper cleanup/recovery. These use no
real credentials or models. The local Supabase harness routes all three existing
coordinator integration cases through SessionClient; see TASKS.md for run status.

Local authenticated HTTP handler now verified (INFERENCE_HTTP.md). Remaining:
production ingress and managed-service credential mechanism, live TLS integration, per-owner quotas/rate limits, image and
licence release gates, privileged ingestion identity/driver verification, desktop
sessions and UI wiring. No production readiness or semantic-quality claim.
