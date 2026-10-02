# Initial extractor container

Status: the prior image built and offline smoke checks passed on 1 October 2026.
Crawl4AI 0.9.4 and yt-dlp 2026.8.19 installed inside the container only; pip check
reported no broken requirements. The 2 October hash-locked rebuild failed after
C: filled and Docker storage reported read-only/I/O errors. Latest recipe is not
runtime-verified. See [dependency review](DEPENDENCY_REVIEW.md). TASK-019A is partial.

The runner consumes a supplied extraction-result JSON object, not a live URL job.
Required fields: backend (crawl4ai or yt-dlp), source_id, url, result,
backend_version, fetched_at; optional notes. It returns a processed document or
a generic error. Input cap 256 KiB, output cap 2 MiB. No arbitrary command/options.
Caption-file support exists separately and is not exposed through this runner yet.

With the Docker Linux engine running:

```
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
extraction test. Each probe container is removed after exit.

Next: restore Docker storage health, rebuild/smoke/scan the locked image, then
enforced public-only egress, tool invocation and live
compatibility tests. This preparatory runner does not complete live extraction.
