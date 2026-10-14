# Local CPU container verification

Verified 14 October 2026: real Qwen smoke passed after the RAM guard cleared.
Startup 15.781 s; ten short fictional requests 0.593–0.742 s; cgroup peak
4,155,457,536 bytes (3.87 GiB). Exit zero, no OOM, container removed. Model identity,
normalized 512-dimensional vectors and repeated-query consistency passed.
Evidence: ../../tests/inference/results/qwen-container-20261014.json.
The cgroup peak includes container-accounted memory such as file cache and cannot
be compared directly with the earlier Windows process RSS measurement.

This is a private test boundary for TASK-005, not a deployed or authenticated API.
The image runs Qwen through a bounded JSONL input stream. No port is published.
Only fictional text is used by the smoke launcher. Existing application/API
containers are outside this workflow and must never be stopped or modified.

## Repeatable build

All paths below are relative to the repository on D:. Docker's active data disk
must also remain on D:. Build inputs are staged under ignored
`output/inference-patched`, with an explicit context allowlist. Model weights and
Hugging Face credentials are excluded from the build context.

The patched Linux CPython 3.12 x86_64 lock contains all 34 resolved distributions.
PyTorch 2.14.1+cpu came from the official `https://download.pytorch.org/whl/cpu`
index; the other wheels came from `https://pypi.org/simple`. The pinned Python
base digest is in Dockerfile. Wheels retain installed package licence metadata;
the model export retains its model card and Apache-2.0 licence. A full dependency
licence/security review remains a release gate.

To reproduce downloads, use a separate limited Linux Python container with only
the D: wheel directory mounted. Download torch with `--no-deps` from its CPU
index first. Then use pip download with `--require-hashes`, this lock,
`--find-links` pointing to the wheel directory, `--only-binary=:all:` and the PyPI
index. Do not resolve new versions or use the Windows wheels for this image.

With those wheels and the previously verified Qwen snapshot available:

```powershell
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.prepare_inference_image
docker build --tag gather-inference:cpu-patched output/inference-patched
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_container --candidate --controls
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_container --candidate --profile compatibility
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_container --candidate --profile chunks
```

OS patch installation uses signed Debian repositories; Python wheel installation
remains offline and hash-locked. Model runtime remains network-disabled. The old
cpu-local image is preserved; `--candidate` selects cpu-patched and a separate
results folder. Compare six synthetic cases with both image variants, then run
`python -m scripts.compare_inference_upgrade`. This checks token counts, vector
tolerances and three small rankings; it is not a full retrieval evaluation.

The preparation script refuses a wheelhouse differing from the committed lock.
Only a deliberate reviewed upgrade uses `--update-lock`; do not use it for routine
builds. `--build-dir` must resolve under this repository's D: output directory.
It materializes and hash-verifies model files into `output/inference-model`,
without mounting the HF home or its token. The test launcher verifies hashes
again and rejects extra files. Manifest and launcher are trusted operator inputs;
this is not an upload interface or protection against a hostile host operator.

## Boundaries and evidence

- CPU: 2; memory: 5 GiB for Qwen, 512 MiB for synthetic controls; no extra swap.
- Non-root UID/GID 65532, read-only root/model, all capabilities dropped,
  no-new-privileges, 128 PIDs, 64 MiB temporary filesystem, no network or ports.
- Startup deadline: 90 seconds. Each inference: 15 seconds, plus bounded child
  cleanup. Launcher: 300-second outer test deadline with own-container cleanup.
- One request is processed at a time. Input frames are capped at 64 KiB;
  oversized frames close the stream rather than draining unlimited input.
  Existing text/token/batch limits apply after decoding. Bad JSON can recover;
  fatal model errors close the session. Recovery creates a fresh runtime.
- The private caller controls the stream; it is not public ingress. An eventual
  HTTP adapter still needs body/connection deadlines, authentication and quotas.
- Docker logging is disabled for the test. Embeddings stay in the private pipe;
  evidence stores timings and settings, not vectors or source text.
- The harness inspects actual container configuration, verifies normalized
  vectors/model identity and repeated-query consistency, and removes only its
  uniquely named container. Image and model export remain on D: for reuse.
- Real smoke uses ten short fictional requests. It measures model-load time,
  request latency and cgroup peak memory. It does not establish load capacity,
  maximum-token performance, cold Cloud Run latency or production cost.

Results go to ignored `output/inference-results`. Reviewed summaries belong in
`tests/inference/results`. Synthetic control tests cannot establish real-model
quality. Image vulnerability scanning, maximum-input profiling, HTTP integration,
Gemma comparison and connected desktop search remain separate gates.

## Extended profiles

Run the same launcher with `--profile long`, `--profile batch`, `--profile limits`
or `--profile sustained`. Keep them sequential; each rechecks free RAM and starts
a fresh isolated container. The long profile uses 512/1,024/2,048 exact tokens;
the batch requests two 2,048-token items. The pinned tokenizer adds one special
token to the repeated-word stress input; actual successful token counts are
recorded. This artificial text tests compute limits, not semantic quality.
The limits profile requests 2,049 tokens and a 4,200-token aggregate, then a valid
16-token request. Sustained runs 50 distinct short fictional queries sequentially.
These profiles do not test multiple users, concurrent throughput or memory leaks.

Failures and unexecuted cases are retained in the report, and the launcher exits
nonzero when a requested success times out. Limits are not relaxed to make a run
pass. The image itself is unchanged; test-only scripts are mounted read-only for
the expanded 21-test control suite. See PROFILE_RESULTS.md and IMAGE_SCAN_REVIEW.md
for the measured performance limitations and open security findings.
