# CPU serving prerequisite

17 October: FastAPI/Uvicorn lifecycle adapter locally verified; see
../../docs/INFERENCE_ASGI.md. Public binding is blocked pending IAM. Eight ASGI
and 15 runtime tests plus frontend build pass; no real-model HTTP/cloud claim.

16 October: authenticated loopback HTTP adapter now wraps the existing Runtime.
Nine synthetic-engine endpoint tests and frontend build pass; see
../../docs/INFERENCE_HTTP.md. No real-model HTTP run or public/cloud deployment.
Earlier stream-only statements below describe historical checkpoints.

15 October: cpu-patched contains updated AI/OS dependencies and a token-aware
512-token source-slice helper. 25 focused checks pass; rescan is 28 findings/1 high.
Real six-case compatibility and five-chunk timing checks now pass. See UPGRADE.md;
the helper is not yet connected to desktop ingestion. Deployment remains gated.

Paired retrieval evaluation also passes the text-v2 gate; boundary stress reveals
split conditions and a multi-part passage miss. Next: bounded context/coverage
before ingestion integration. See ../../docs/CHUNK_RETRIEVAL_RESULTS.md.

14 October follow-up: extended profiles and security review are complete, with
open findings. Fifty short requests passed; long/max-batch requests timed out.
The image scan reports 56 records, including 12 high. See PROFILE_RESULTS.md
and IMAGE_SCAN_REVIEW.md. Deployment/API integration remains gated on remediation.

TASK-005 remains partial. `runtime.py` is a private Python process boundary.
The isolated Linux image now builds and passes 18 synthetic control tests;
real container-model smoke passed on 14 October (see CONTAINER.md). It is not
an HTTP service or cloud deployment. No desktop search is connected.
See [CONTAINER.md](CONTAINER.md) for reproducible checks and limits.

The parent loads a trusted engine in a spawned child once, waits for readiness,
then serves sequential requests through an internal pipe. Concurrent calls fail
with `busy`; there is no unbounded queue. A deadline or model failure terminates
and reaps the child, clears readiness and requires an explicit restart. Cleanup
can add up to four seconds after the inference deadline. `close()` waits for an
active request's bounded deadline. `infer(..., cancel=event)` now observes a
coordinator cancellation signal at 50 ms polling intervals and reaps the child;
cleanup can add up to four seconds. See ../../docs/INGESTION_COORDINATOR.md.

Only operator-owned code may supply the engine factory/configuration. The pipe
uses Python serialization and must never be exposed to clients. The Qwen adapter
accepts a local directory; the smoke launcher verifies its manifest and hashes
before loading. There is no implicit download, remote model code or credential
lookup. The model cannot invoke tools or execute document instructions.

## Contract and limits

Request: `{"role":"query","texts":["When does the museum open?"]}`.
Roles: query or document. Unknown fields are rejected. Queries receive the same
instruction used in the frozen Qwen benchmark; documents retain their text.

| Boundary | Current implementation |
| --- | --- |
| Input | 1–4 strings; 8 KiB UTF-8 each; 16 KiB total before prompting |
| Tokens | Exact prompted tokenizer count, 2,048 per item, 4,096 total; no truncation |
| Model | Pinned Qwen3-Embedding-0.6B; local float32 CPU, two Torch threads |
| Vectors | Last-token pooling, first 512 dimensions, L2 normalization |
| Readiness | Set after model load; request path checks child liveness |
| Deadline | 90 seconds startup, 15 seconds inference by default |
| Output | Model/revision/dimensions, ordered vectors, prompt-token count |
| Failures | Fixed errors; no exception bodies or document content in errors |

The response includes no user ownership information. The internal coordinator
now enforces version/configuration checks and uses the embedding client's response
validator; real authenticated server and cloud transport integration remain pending.

## Verification

`python -m unittest discover -s tests/inference -v` uses synthetic engines to
exercise process reuse, busy rejection, input/token budgets, timeouts, crashes,
cleanup, redacted failure messages and explicit recovery. These are not semantic
quality results. The normal project check script includes this suite.

From the project folder, the real-model host check is:

```powershell
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_runtime
```

It requires 4 GiB free RAM, verifies the D: snapshot, uses three fictional inputs,
and writes timing/process evidence to ignored `output/model-benchmark/serving`.
On 12 October this check stopped at the RAM guard. On 13 October it passed:
startup 14.239 s; three sequential requests 0.505/0.669/0.709 s; process reused
and cleanly reaped. Post-request RSS was 2,725,130,240 bytes (2.54 GiB), not peak.
This small Windows host check does not establish throughput, container limits,
worst-case input latency or Cloud Run cost. Recorded evidence is in
`tests/inference/results/qwen-host-20261013.json`.

## Next gate

Docker's data disk was migrated and verified on 13 October at
`D:\DockerDesktop\DockerDesktopWSL\disk\docker_data.vhdx`. The stopped source and
destination matched SHA-256; Docker restarted with the original inventory intact.
The old C: data disk was removed after verification. D: image storage is now ready.
The Linux CPU image is separately hash-locked and built. Its launcher verifies
read-only/non-root configuration, disabled network and explicit CPU/memory/PID
limits. Eighteen synthetic tests pass inside it, including deadlines and recovery.
Real container smoke now passes: 15.781 s startup, ten short fictional requests
0.593–0.742 s, 3.87 GiB cgroup peak within a 5 GiB ceiling. Next: maximum-input
and load profiling plus image security review. HTTP ingress remains unimplemented.

EmbeddingGemma terms are accepted per the user. Local Hugging Face login was
verified on 13 October with credentials stored on D:, but the token's account
receives HTTP 403 indicating model access is not approved. Check same-account
access before downloading. Keep that download/evaluation separate; its pooling/runtime must be
implemented from its own model configuration, not assumed to match Qwen.
