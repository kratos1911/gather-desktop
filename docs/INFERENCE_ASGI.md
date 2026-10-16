# ASGI runtime adapter

17 October 2026. `services/inference/asgi.py` adds FastAPI/Uvicorn serving and
lifecycle handling around the existing Runtime. This is locally verified code,
not a deployed or production-ready service. See TASKS.md for measured evidence.

## What changed

Trusted code creates `create_app(runtime, authenticate)` then `create_server(app)`.
Authentication is mandatory and has no permissive default. Only the explicit
LocalBearer checker is supplied today; Google IAM/managed identity remains next.
The server factory rejects every bind except 127.0.0.1 until that boundary exists.
No default app, import-time model loading, credential discovery or public CLI.

FastAPI lifespan starts one Runtime child and closes it during shutdown. Startup
now accepts a cancellation event, using the existing process cleanup. The async
request handler runs blocking inference in a thread, preserving responsive health
checks. An event-loop admission flag rejects simultaneous inference with 429;
it does not create a work queue or additional model processes.

`/ready` is a minimal readiness response, not an authentication endpoint. It only
returns true after startup succeeds, while Runtime is ready and shutdown has not
begun. `/embed` preserves the existing request, byte, token and response contracts.
Docs/OpenAPI routes are disabled. Public binding, docs and proxy-trusting headers
are not enabled through defaults.

The pinned Uvicorn H11Protocol extension enforces four accepted connections,
16 KiB request-line/headers, bounded wire bytes and a five-second total receive
deadline from TCP acceptance. ASGI validates exact content length, JSON/content
type/encoding and byte limits before invoking Runtime. Every successful response
closes the connection; writes have a five-second async deadline. Health and model
responses use no-store; access logging is disabled. Header reception must be
bounded at the protocol layer because ASGI receives headers only after parsing.

The shutdown signal hook marks readiness false and signals active/startup Runtime
work to cancel before Uvicorn drains tasks. Runtime terminates/reaps its child;
lifespan closes it. Model compute remains at most 15 seconds plus existing cleanup.
No automated retry, startup reattempt or post-timeout recovery is added. A cancelled
request task marks the instance stopping rather than prematurely freeing admission
while inference still runs. Replacing an unready instance is a deployment concern.

## Dependencies and reproducibility boundary

`services/inference/requirements-asgi-local.txt` pins the tested Windows/Python3.10
dependency set. FastAPI 0.141.1 and Uvicorn 0.54.0 were already present; no shared
packages were altered. The test venv lives under ignored `output/asgi-checks/venv`
on D: and inherits available packages. h11 0.16.0 was installed only there using
the existing inference lock's SHA-256 verification and no dependency resolution.
The server rejects other h11/Uvicorn versions because parser safety and protocol
hooks must be explicitly reviewed before upgrades.

The shared h11 0.14.0 remains untouched and must not run this adapter. Its upstream
[request-smuggling advisory](https://github.com/python-hyper/h11/security/advisories/GHSA-vqfr-h8mv-ghfj)
lists 0.16.0 as patched. Metadata licences reviewed: FastAPI/Pydantic/h11 MIT,
Uvicorn/Starlette BSD-3-Clause. This is not a complete dependency vulnerability
audit. A combined Linux model/ASGI hash lock, image rebuild/scan and licence
inventory are still required; do not copy the local requirements into the Linux
lock or claim a hermetic environment from inherited system packages.

Focused checks:

```powershell
.\output\asgi-checks\venv\Scripts\python.exe -m unittest discover -s tests/inference -p test_asgi.py -v
.\output\asgi-checks\venv\Scripts\python.exe -m unittest discover -s tests/inference -p test_runtime.py -v
```

The full project checker accepts this interpreter through its existing `-Python`
parameter. A fresh machine must prepare the pinned dependencies first. No test
downloads a model. Test engines are never production fallbacks.

## Verified scope and limits

Eight real Uvicorn/loopback tests with a synthetic Runtime engine cover existing
client interoperability, one-child reuse, auth/JSON/token bounds, disabled docs,
public-bind/dependency rejection, responsive readiness during busy inference,
deadline failure/unready state, total slow-header/body deadlines, startup
cancellation and the shutdown signal handler. Fifteen runtime tests pass.
Frontend build passes. No unchanged database suite rerun.

The signal test invokes Uvicorn's SIGTERM handler on Windows; actual Linux OS
SIGTERM delivery/container shutdown has NOT been verified. Real-model-over-ASGI,
load/latency/memory, TLS and Cloud Run identity are also unverified. The original
standard-library HTTP server remains a separate local reference test adapter.

Next: bounded Google ID-token acquisition and fail-closed deployment identity
configuration; then combined Linux image/security and real-model pilot gates.
Finish the user's learning quiz before another major implementation change.

References: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/).
Uvicorn 0.54.0 installed Config, H11Protocol and Server source was inspected for
the exact hooks used here; these hooks are guarded by the version check.
