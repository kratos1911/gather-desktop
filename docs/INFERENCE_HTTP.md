# Authenticated local inference HTTP boundary

16 October 2026. `services/inference/http_server.py` wraps an explicitly started
Runtime; `/embed` uses the existing query/document JSON contract. No real model
was loaded for this milestone. Completion evidence is recorded in TASKS.md.

## Use and trust

Trusted server code creates `InferenceServer(runtime, secret, port=...)`, then
runs `serve_forever()`. The caller owns `runtime.start()`, `shutdown()`,
`server_close()` and `runtime.close()`; requests cannot load, restart or select a
model. The existing InferenceClient can call this server with its explicit
loopback test option. There is no default token, credential discovery or CLI
that accepts secrets on the command line.

The server requires a 32–256-character service bearer secret supplied by trusted
operator code. Use a cryptographically generated secret outside tests. Compare
in constant time; reject missing/duplicate/wrong authorization before reading the
body or running inference. This credential is for trusted backend services, NOT
desktop users. It is not a user JWT, ownership check or Cloud Run IAM credential.

Binding is restricted to 127.0.0.1. This standard-library HTTP adapter is for local
integration, not public production ingress. Managed-service identity, TLS,
secret rotation, per-owner quotas and a production serving stack must be designed
and verified before deployment. Do not expose this port publicly.

## Request and computation limits

- At most four active connections and a bounded listen backlog. Excess accepted
  connections close without starting more handler threads. Runtime still permits
  only one inference at a time; concurrent model calls receive 429, not a queue.
- Five-second total header/body deadline, 16 KiB combined request-line/header
  budget and 64 KiB body limit. Reject duplicate Content-Length, transfer encoding,
  compressed bodies, duplicate JSON keys, invalid JSON and unknown runtime fields.
- Exact POST `/embed`, `application/json`, one request per connection. Other
  methods/paths do not run the model. Input bytes/batch/token limits remain those
  in runtime.py; server-side tokenizer checks cannot be bypassed by the client.
- Runtime compute deadline is at most 15 seconds, plus its existing bounded
  cleanup (up to four seconds). Client disconnection does not remove this limit.
  It does not yet trigger immediate compute cancellation; a hung worker is still
  terminated/reaped when its deadline expires.
- Replies are bounded to 128 KiB with no-store and connection-close headers;
  socket writes have a five-second timeout. No request bodies, credentials or
  raw exception messages in logs/errors.

Model timeout returns 504; busy 429; input/token failure 400; unavailable/crashed
model 503. No automatic restart or retry. The client may reach its own deadline
before server cleanup finishes; a client timeout is not proof of stopped remote
work. The server independently enforces that bound.

## Evidence and next boundary

Tests use a synthetic engine in the real Runtime child process and loopback HTTP.
They cover authenticated client round-trip, wrong credentials before body reads,
malformed/framing/header limits, model token checks, busy responses, total slow
header deadline, model timeout/reaping and client disconnect. No semantic quality,
real-model-over-HTTP, TLS or cloud performance claim.

Next: production ingress/managed identity and deployment design, plus unresolved
image/licence gates. Private ingestion driver/authentication and desktop wiring
remain separate work. Quiz the user on this milestone before another major change.
