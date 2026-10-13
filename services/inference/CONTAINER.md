# Local CPU container verification

This is a private test boundary for TASK-005, not a deployed or authenticated API.
The image runs Qwen through a bounded JSONL input stream. No port is published.
Only fictional text is used by the smoke launcher. Existing application/API
containers are outside this workflow and must never be stopped or modified.

## Repeatable build

All paths below are relative to the repository on D:. Docker's active data disk
must also remain on D:. Build inputs are staged under ignored
`output/inference-build`, with an explicit context allowlist. Model weights and
Hugging Face credentials are excluded from the build context.

The Linux CPython 3.12 x86_64 lock contains all 25 resolved distributions.
PyTorch 2.8.0+cpu came from the official `https://download.pytorch.org/whl/cpu`
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
docker build --network=none --tag gather-inference:cpu-local output/inference-build
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_container --controls
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_container
```

The preparation script refuses a wheelhouse differing from the committed lock.
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
