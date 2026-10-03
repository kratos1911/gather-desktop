# Initial extractor container

Status: the hash-locked image rebuilt successfully after Docker recovery; offline
smoke checks pass on 3 October 2026. Crawl4AI 0.9.4 and yt-dlp 2026.8.19 are installed
inside the container only; pip check reports no broken requirements. The full image
rescan has 31 open records (four high). OpenSSL/PCRE2 are patched; runtime pip
and ensurepip are removed. See [dependency review](DEPENDENCY_REVIEW.md) and
[scan review](IMAGE_SCAN_REVIEW.md). Networking remains disabled.

The runner consumes a supplied extraction-result JSON object, not a live URL job.
Required fields: backend (crawl4ai or yt-dlp), source_id, url, result,
backend_version, fetched_at; optional notes. It returns a processed document or
a generic error. Input cap 256 KiB, output cap 2 MiB. No arbitrary command/options.
Caption-file support exists separately and is not exposed through this runner yet.

With the Docker Linux engine running:

```
docker build --target installer -t gather-extraction-installer -f services/worker/Dockerfile .
docker compose -f compose.extraction.yaml build
docker compose -f compose.extraction.yaml run --rm -T extractor
```

Supply one JSON request through stdin and close stdin. No ports, mounts or secrets
are configured. Runtime networking is fully disabled; build-time package downloads
are separate. The Dockerfile now pins the base digest, 96 application wheels and
bootstrap pip with hashes. It does not launch extractors or install Chromium.
An external supervisor must enforce wall-clock timeout; the runner itself has no
wall-clock cancellation. Do not deploy this as an authenticated production API.

Run `python scripts/check_extractor_container.py` from the repository root after
building. It verifies synthetic success/error jobs, package versions, non-root UID,
application-directory write rejection, an unreachable external route and absence
of the checked personal paths. This is not a production security audit or a live
extraction test. Each uniquely named probe container is explicitly removed after
exit or timeout, before closing inherited command pipes on Windows. Runtime
checks verify patched Debian versions and absent pip/ensurepip; hash probes use
the developer-only installer target. Build that target before running checks. A deliberate timeout check passes. This developer harness is not
the production job supervisor required by TASK-019B.

Next: TASK-023 dependency remediation, then
enforced public-only egress, tool invocation and live
compatibility tests. This preparatory runner does not complete live extraction.
