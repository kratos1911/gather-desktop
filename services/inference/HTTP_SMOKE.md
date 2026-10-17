# Real-model HTTP smoke

Status, 17 October: tooling verified with synthetic engines; real run blocked by
2.03 GiB available host RAM versus the unchanged 4 GiB guard. Docker Linux and
the auth candidate exist; D: has 85.3 GiB free, and model directory/manifest exist.
Full artifact hashes are checked by the launcher before any model load. The CIM
memory read was unavailable; psutil supplied the valid measurement. No retry,
app closure, protected workload change or model load occurred.

## Run after memory is available

```powershell
.\output\model-benchmark\venv\Scripts\python.exe -B -m scripts.check_inference_container --candidate --profile http
```

This reuses the existing guarded launcher, model integrity checks, unique container,
2 CPUs, 5 GiB ceiling with no extra swap, read-only mounts/root, non-root identity,
network isolation, 15-second inference deadline and 300-second outer limit. Only
its owned container is removed. HTTP stays on container loopback; no published
port, cloud account, model download or image rebuild is needed. Host scripts are
mounted read-only as test tooling, not packaged production code.

The profile starts the real Qwen runtime and ASGI server, then checks readiness,
missing-credential rejection, two existing short compatibility fixtures, a known
512-token passage, a 2,049-token rejection and repeated-query recovery. Four
successful requests must return pinned model/revision, 512 finite normalized
values, correct counts and stable repeat output. The model process must be reused
and reaped at shutdown. An ephemeral local bearer is never written to the report.

Evidence is written to output/inference-results/patched/qwen-http.json, including
image ID, startup time, individual HTTP latencies, cgroup peak memory, exit/OOM
state and failed/unexecuted behavior. No percentile or throughput claim is made
from four requests. This does not measure cold Cloud Run scheduling, TLS/network
latency, IAM, multi-user load or retrieval relevance. Synthetic timeout/overload
and actual SIGTERM evidence remain in the existing suites; this profile does not
claim new real-model timeout/overload measurements.

## Verified tooling

Seven focused host checks pass (three new harness checks and four existing
launcher/report checks); three new harness checks also pass in the Linux auth
candidate with 512 MiB and no model mount. Valid synthetic output passes; invalid
vectors fail while cleanup remains required. Incorrect CLI mode fails before
Docker operations. Required frontend build passes; UI/native inputs unchanged.

Real-model HTTP acceptance remains **unverified** until the guarded run succeeds.
OS release findings and deployed cloud identity remain separate open gates.
