# Extractor network boundary

`approve_destination(url, resolver)` validates public HTTP(S) destinations on
ports 80/443. Resolver returns a list/tuple of at most 32 IP strings; every answer
must be public. Literal addresses skip DNS. The result preserves the normalized
URL, hostname, port and immutable approved addresses. Errors do not expose the
resolver's exception text. No real DNS, connections or browser operations occur.

This helper is preflight only. The new backend-only restricted_fetch transport
dials approved numeric addresses and rechecks redirects, with TLS hostname
verification. Local controlled tests pass; it is not connected to live jobs.
Known NAT64 ranges are denied in addition to other non-public/special addresses.
Browser/tool egress and whole-broker DNS deadlines remain open. See
[supervision](SUPERVISION.md) for tested boundaries and remaining acceptance.

Direct package intent lives in requirements-extraction.txt; the complete hashed
wheel lock and installed environment are reviewed in DEPENDENCY_REVIEW.md.
PyPI metadata initially reviewed 30 September:
- https://pypi.org/project/crawl4ai/0.9.4/ (Apache-2.0)
- https://pypi.org/project/yt-dlp/2026.8.19/ (Unlicense)

Nine mock-resolver policy tests pass. Offline Docker isolation and supervisor
checks pass. Live extractor/browser networking and public-site compatibility
remain unverified; these are not end-to-end live SSRF tests.
