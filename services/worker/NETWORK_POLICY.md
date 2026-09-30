# Extractor network boundary

`approve_destination(url, resolver)` validates public HTTP(S) destinations on
ports 80/443. Resolver returns a list/tuple of at most 32 IP strings; every answer
must be public. Literal addresses skip DNS. The result preserves the normalized
URL, hostname, port and immutable approved addresses. Errors do not expose the
resolver's exception text. No real DNS, connections or browser operations occur.

This is preflight only. The future transport must connect to approved addresses
without a second DNS lookup, verify TLS for the original hostname, and apply the
same checks on redirects, subtitle downloads and browser subresources. Controlled
egress is also needed for browsers/tools that open their own connections. Do not
enable arbitrary user-URL fetching merely because this helper returned success.
Timeouts for DNS and actual I/O must be enforced by the execution boundary.

Direct package pins live in requirements-extraction.txt. They are not a complete
transitive lock or an installed environment. PyPI metadata reviewed 30 September:
- https://pypi.org/project/crawl4ai/0.9.4/ (Apache-2.0)
- https://pypi.org/project/yt-dlp/2026.8.19/ (Unlicense)

Eight mock-resolver tests pass. Actual container isolation, installed extraction,
public-site compatibility and end-to-end SSRF tests are still pending.
