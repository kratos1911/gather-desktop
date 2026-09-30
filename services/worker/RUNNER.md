# Initial extractor container

Status: configuration validated; image build/runtime unverified because the local
Docker Linux engine is unavailable. No tools installed on the host. TASK-019 partial.

The runner consumes a supplied extraction-result JSON object, not a live URL job.
Required fields: backend (crawl4ai or yt-dlp), source_id, url, result,
backend_version, fetched_at; optional notes. It returns a processed document or
a generic error. Input cap 256 KiB, output cap 2 MiB. No arbitrary command/options.
Caption-file support exists separately and is not exposed through this runner yet.

After the Docker engine is available:

```
docker compose -f compose.extraction.yaml build
docker compose -f compose.extraction.yaml run --rm -T extractor
```

Supply one JSON request through stdin and close stdin. No ports, mounts or secrets
are configured. Runtime networking is fully disabled; build-time package downloads
are separate. The Dockerfile installs direct pinned tools but does not launch them
or install Chromium. Transitive dependencies and base-image digest remain unlocked.
An external supervisor must enforce wall-clock timeout; the runner itself has no
wall-clock cancellation. Do not deploy this as an authenticated production API.

Next: working Docker engine, successful isolated build and package/version checks,
locked image/dependencies, enforced public-only egress, tool invocation and live
compatibility tests. This preparatory runner does not complete live extraction.
