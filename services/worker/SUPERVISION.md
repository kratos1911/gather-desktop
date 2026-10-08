# Restricted transport and offline supervision

TASK-019B is partial, with whole-fetch process supervision and a controlled
fetch-to-parser pipeline verified on 8 October 2026. No desktop route, public API
or live user-link extraction is enabled. Only synthetic loopback sites were used.

## Implemented boundaries

`restricted_fetch.fetch_page` is a backend-only GET transport. It approves every
DNS answer, dials an approved numeric IP without a second resolution, checks the
peer and preserves TLS hostname/SNI verification. Three redirects are allowed,
each revalidated; HTTPS downgrade is denied. It sends no cookies, user headers,
credentials or referrer, ignores proxy environment variables and never executes
scripts or follows embedded assets. Known NAT64 translation ranges are denied.

Only HTML, XHTML and plain text are accepted. Response bodies have a 64 KiB limit
including chunked transfers; compressed bodies are rejected. Conflicting framing,
duplicate content lengths, oversized declared bodies and truncated content fail.
Headers are bounded by http.client's line/count limits while parsing, followed by
a 16 KiB aggregate acceptance check. This is not a 16 KiB peak-memory guarantee.
Socket timeouts and an established-connection deadline abort stalls/slow headers.
FetchBroker now supplies the outer process deadline for DNS, connection/TLS and
body reads. The transport function alone is still not a whole-job time limit.
No retries or alternate-address fallback are implemented.

`supervisor.DockerJobRunner` runs the existing supplied-output parser using only an
operator-selected local image digest and fixed entrypoint. Jobs cannot provide
commands, Docker options, mounts, environment variables or destinations. It uses:

- network none, non-root UID, read-only filesystem, dropped capabilities and no
  new privileges; no host mounts, daemon socket, application secrets or ports;
- 1 GiB RAM, no additional swap, one CPU, 64 processes, 64 MiB temporary space;
- 256 KiB input, 2 MiB plus one newline stdout, 8 KiB stderr; Docker logs disabled;
- one active job per supervisor process, immediate busy response, default
  30-second execution timeout (operator maximum 60), cancellation and cleanup.

Creation has a separate 15-second control-command timeout; cleanup has bounded
control-command waits. Execution timeout is not an end-to-end response SLA.
Both output streams are drained concurrently with bounded retention; diagnostics
are not returned. Random job names identify the exact container to remove on
success/failure/timeout/cancellation. Removal precedes pipe closure on Windows.
Failure to clean up is reported, not treated as successful completion.

## Evidence and reproduction

Run the normal source quality checks, then build the runtime and run:

```
python scripts/check_worker_supervisor.py
```

The Docker script uses synthetic fixtures and trusted test subclasses to exercise
success, invalid JSON, timeout, cancellation, stdout/stderr overflow, failed and
malformed worker output, recovery and absence of leftover containers. Direct
connections to public/private/metadata IPv4 addresses are denied. Kernel cgroup
memory/swap/CPU/process settings, read-only path, UID and absent daemon socket are
checked. Test-only command substitution is not a feature of job payloads.

15 transport tests include real loopback HTTP fixtures, DNS/redirect rebinding,
limits, stalls/slow headers and mocked TLS identity/failure checks. Trusted test
connectors map public-address policy decisions to loopback; the production address
policy is not relaxed. TLS handshakes against a controlled certificate server and
real public compatibility have not been tested. No public DNS/site access occurs
in these tests. Five supervisor unit tests check prelaunch rejection/busy behavior;
nine destination-policy tests include NAT64 denial.

## Remaining acceptance gates

1. Fetch-process deadlines and the bounded broker-to-parser contract are now
   verified locally; production host/container confinement and deployment remain
   open. No general proxy/tunnel or request-supplied connector is exposed.
2. Real public compatibility and controlled certificate-server TLS integration
   remain unverified; current TLS hang/identity probes use trusted substitutes.
3. Design and verify browser/yt-dlp egress enforcement for every redirect,
   subtitle URL and subresource before allowing their own network calls. The
   plain-HTTP component does not implement a browser proxy/firewall.
4. Durable jobs, leases, crash/orphan reconciliation, cross-process quotas and
   authenticated API are still planned. A killed supervisor/failed daemon needs
   an external reconciler; cleanup here only covers a running supervisor.
5. Keep TASK-023 dependency findings and privacy/provider gates open. No release,
   production hosting, browser automation or semantic-result claim.

References checked 3 October:
[OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html),
[Python HTTP client](https://docs.python.org/3.12/library/http.client.html).


## Whole-fetch broker and page pipeline (8 October)

FetchBroker launches one fixed Python child per fetch with a URL-only JSON input.
The parent enforces a default 15-second deadline (operator maximum 60 seconds)
from before launch through receipt, covering blocked DNS, connect and TLS calls.
Process creation is an OS call and is not forcibly interruptible; elapsed time is
checked afterward. Cleanup waits are separately bounded. This is not a real-time
response SLA. The child cannot choose a command, connector or resolver from job
input, and the parent rejects extra/duplicate result fields and malformed bytes.

Limits: 8 KiB request, 128 KiB response envelope, 64 KiB decoded body, 8 KiB stderr,
one active fetch per host process. Both output streams are drained concurrently;
timeout/cancellation/overflow kills and reaps the child, then closes its pipes.
Valid output from a still-running child is never published. Child code is fixed
and does not spawn subprocesses; this is not a general process-tree supervisor.
The child uses isolated Python startup and an environment allowlist containing
only Windows system-directory variables. It receives no inherited provider keys,
proxy settings or Python startup overrides. A separate process is NOT an OS
filesystem, memory or network sandbox; those production deployment gates remain.

BookmarkPipeline validates source ID/URL/notes, calls FetchBroker, then sends a
bounded `http-page` job to DockerJobRunner. The offline adapter parses HTML/XHTML
or UTF-8 plain text and prepares all passages. It preserves original/final URL,
fetch time, redirect count, body hash, source notes and actual parser provenance.
It does not label this as Crawl4AI output or semantic indexing. Repeated extraction
with the same supplied timestamp/content is deterministic; durable job retry and
fetch-time reuse still belong to the future coordinator.

Fetch failures/cancellation do not invoke the parser or mark anything ready.
The caller still owns its saved bookmark/notes; this layer has no persistence,
retry queue or save/delete operations. A future coordinator must preserve that
record on enrichment failure. Parser errors remain explicit worker results.

Nine subprocess broker tests and six adapter/pipeline tests pass. They cover stuck
DNS/connect/TLS substitutes, cancellation, output flooding, invalid envelopes,
no inherited secrets, process reaping, recovery and cancellation between stages.
`python scripts/check_bookmark_pipeline.py` verifies the full local path with a
loopback page/redirect, real fetch child and real offline Docker parser. Its trusted
connector maps an approved public-looking test hostname to loopback; production
policy is not relaxed. No public DNS or real user documents are used.
