# CPU profile results — 14 October 2026

Image: `sha256:b04ad84cd1474204823070015a7f87537243714cffcb5c044789824b80b54f50`.
Pinned Qwen revision, float32, two CPU threads, 512-dimensional normalized output.
Docker limits unchanged: 2 CPUs, 5 GiB RAM, no additional swap, no network,
non-root/read-only, 15-second request deadline. This is a shared Windows/Docker
machine, not dedicated Cloud Run hardware. No cloud costs were incurred.

| Profile | Observed result |
| --- | --- |
| 512-token document | Passed, 5.645 s |
| 1,024-token document | Passed, 13.632 s; little margin before deadline |
| 2,048-token document | Failed: deadline_exceeded; child stopped, exit 2, no OOM |
| Two 2,048-token documents | Failed: deadline_exceeded; child stopped, exit 2, no OOM |
| 2,049-token item / 4,200-token aggregate | Both rejected with token_limit; valid 16-token request afterward passed in 0.728 s |
| 50 consecutive short queries | All passed; median 0.710 s, nearest-rank p95 0.935 s, range 0.637–1.042 s; peak 3.64 GiB |

Long and batch profile cgroup peaks were approximately 3.64 GiB. The largest
requests were terminated early; these peaks do not show their full-run memory
requirements. Cgroup memory includes file cache and differs from process RSS.
All owned test containers were removed after each attempt.

Evidence files under `tests/inference/results` retain both passed and failed
outcomes. No runtime limits were changed. Twenty-one synthetic protocol/reporting
tests pass on Windows and inside the Linux container; frontend build passes.

## Implication

The configured token ceiling is a validation limit, not a guarantee that every
allowed request completes within the deadline. The current 2,048/4,096 budgets
are too optimistic for this CPU/deadline combination on this machine. Proposed
next step: benchmark smaller chunks and bounded per-job batches, then choose an
ingestion/query policy without truncating content silently. A 512-token candidate
needs diverse-text and retrieval evaluation; one repetitive stress input is not
enough to declare a safe maximum. Do not increase timeouts to hide this finding.

The image also has unresolved package vulnerabilities. Upgrade/retest/rescan
before API integration; see IMAGE_SCAN_REVIEW.md. These tests do not verify
retrieval quality, public deployment, concurrency capacity or long-duration leaks.
