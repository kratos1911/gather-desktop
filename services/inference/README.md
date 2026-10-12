# CPU serving prerequisite

TASK-005 remains partial. `runtime.py` is a private Python process boundary,
not an HTTP service or deployed container. No desktop search is connected.

The parent loads a trusted engine in a spawned child once, waits for readiness,
then serves sequential requests through an internal pipe. Concurrent calls fail
with `busy`; there is no unbounded queue. A deadline or model failure terminates
and reaps the child, clears readiness and requires an explicit restart. Cleanup
can add up to four seconds after the inference deadline. `close()` waits for an
active request's bounded deadline; it is not an immediate cancellation API.

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

The response includes no user ownership information. A future authenticated
coordinator must enforce ownership, quotas and document-version publication.
Compatibility with the existing HTTPS embedding client is not wired yet.

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
On 12 October this check stopped at the RAM guard; no serving timing is claimed.

## Next gate

Docker's data disk was observed on C: on 12 October. The user is moving it to D:.
Do not build/download large images until the actual new location is verified.
Next: separately locked Linux CPU image, read-only/non-root runtime, no network,
read-only verified model mount, explicit CPU/memory/PID limits, and measured
container startup, warm requests, readiness, hard timeout and cleanup. OS resource
limits and HTTP body limits are not supplied by this Python primitive.

EmbeddingGemma terms are accepted per the user. Local Hugging Face login remains
unverified. Keep that download/evaluation separate; its pooling/runtime must be
implemented from its own model configuration, not assumed to match Qwen.
