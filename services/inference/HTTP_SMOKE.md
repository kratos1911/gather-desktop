# Real-model HTTP smoke

21 October: baked-model release candidate also passed, using `--release` with no
host model mount. Evidence: tests/inference/results/qwen-release-http-20261021.json.
Startup 18.55 s, four successful requests, peak 4.09 GiB under unchanged bounds.
The run's Windows diagnostic decode warning and focused binary-capture correction
are recorded; no second model run. Local ephemeral bearer, not Google IAM.
Earlier results below remain historical; no cloud cold-start claim.

Status, 17 October: **real local Linux HTTP smoke passed** in auth image
554ccb8a9d25ce960dbe1d61c1521a0413277f474172927d6f9891b9fb9bb7a8.
Evidence: tests/inference/results/qwen-http-20261017.json.

Startup 12.681 s; requests 0.819/0.781/4.688/0.683 s (10/26/512/26 tokens).
Peak container memory 4,275,261,440 bytes (3.98 GiB), below the unchanged 5 GiB
limit; exit 0, no OOM or outer timeout. All vector/identity, authorization rejection,
token-limit/recovery, stable repeat, readiness and cleanup assertions passed.
This is local loopback with an ephemeral bearer, not deployed IAM or load testing.

The initial 2.03 GiB RAM blocker was resolved after authorized unused Chrome
closure and a specifically approved one-time WSL page-cache release. Windows
reported 6.05 GiB free after reclaim settled; the guarded launcher then verified
model artifact hashes before loading. No container stop/restart or persistent
Docker setting changes were issued. All nine protected APIs were running before
the test; two showed recent restarts of undetermined cause. Do not attribute them
to this smoke or claim uninterrupted uptime. No further workload intervention.

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

This four-request local real-model HTTP acceptance check passed; cloud capacity
and real-model timeout/concurrent overload behavior remain unmeasured.
OS release findings and deployed cloud identity remain separate open gates.
