# Restricted transport and offline supervision

TASK-019B is partial, verified locally on 3 October 2026. Neither component is
connected to desktop imports, a public API or live extraction. No site was scraped.

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
The OS resolver and connection establishment still require an outer process-level
deadline before live use; the function alone is not a whole-job time limit.
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

1. Isolate the fetch broker itself in a supervised process and test hanging DNS,
   slow connect/TLS, cancellation and bounded outputs across the whole job.
2. Connect broker results to the isolated parser with a narrow contract. No
   general proxy/tunnel or user-configurable resolver/connector is exposed.
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
