# Local CPU embedding benchmark

TASK-005, 10 October 2026. Developer evaluation only; end users will use the
planned cloud service. Qwen first, as requested after the user confirmed that
EmbeddingGemma terms have not yet been accepted. Chat remains deferred.

## Verified results

Qwen3-Embedding-0.6B ran successfully on the Ryzen 7 4800H laptop, CPU only.
Model revision: `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`. Ten downloaded
artifacts total 1,207,487,158 bytes (1.21 GB decimal). Weights, dependencies,
caches and outputs occupy about 5 GB on D:; no model files were directed to C:.
The executable code uses PyTorch 2.8.0+cpu and Transformers 4.57.6. Exact
transitive versions are in scripts/benchmark-cpu-constraints.txt. These are
benchmark pins, not a production dependency security approval.

| Retrieval method | Document Recall@5 | MRR@5 | Evidence Recall@5 |
| --- | ---: | ---: | ---: |
| TF-IDF baseline | 97.14% | 0.8667 | 97.14% |
| Qwen 256 dimensions | 100% | 0.9714 | 100% |
| Qwen 512 dimensions | 100% | 0.9857 | 100% |
| Qwen 1,024 dimensions | 100% | 0.9714 | 100% |
| RRF, 256 or 512 dimensions | 100% | 0.9500 | 100% |
| RRF, 1,024 dimensions | 100% | 0.9486 | 97.14% |

Metrics cover the 35 answerable queries. All five absent queries return dense/
hybrid candidates; TF-IDF returns candidates for four. No answerability success
claim. At 512 dimensions, q16's correct document is ranked second. At 256,
q15 also ranks second; at 1,024, q06 also ranks second. Hybrid reduces q18's
ranking and, at 1,024 dimensions, loses its matching passage from the top five.
Per-category evidence and nonperfect queries are preserved in the
[machine-readable result](../tests/evaluation/results/qwen-cpu-20261010.json).

| CPU threads | Warm query median | Warm query p95 | Index 16 passages | Sampled peak RAM |
| --- | ---: | ---: | ---: | ---: |
| 2 | 0.707 s | 0.888 s | 15.73 s | 3.583 GiB |
| 4 | 0.324 s | 0.376 s | 8.09 s | 3.581 GiB |

OS process peak working set was about 3.64 GiB in both runs, slightly higher than
the 20 ms memory sampler. Exact values and each query timing are in the result.
Cached-file model initialization took 1.82/1.44 seconds; this excludes Python/
library import and hashes and is NOT a cold start because hash verification
reads the weights first. There was one warm pass of 40 short queries per setting.
Measured input lengths: passages 40–159 tokens, prompted queries 26–35. All fit
without truncation. Long-input memory and performance remain unmeasured.

Interpretation: 512 dimensions is a useful candidate for the next test, with half
the float payload of 1,024 (2,048 versus 4,096 bytes, excluding database/index
overhead). Do not finalize it using this tiny set. Identical scoring outcomes at
two and four threads were checked. Do not enable hybrid ranking solely because
it sounds better: this run's fixed RRF lowered ranking quality versus dense.

Checks: 112 worker + 34 evaluation + 4 UI tests pass, alongside lint, TypeScript,
formatting, frontend production build and pip consistency. Sandbox networking
blocked existing loopback tests; the complete rerun with loopback access passed.
No native inputs changed, so no new executable build was needed.

## Procedure

1. Prepare the existing fictional text-v1 corpus: 14 documents, 16 passages,
   40 queries. Keep relevance labels separate from inference inputs.
2. Download one immutable Qwen snapshot, record file sizes/SHA-256 hashes and
   verify upstream LFS hashes. Retain the model card with license metadata.
3. Use CPU-only PyTorch, float32, batch size one and a specified thread count.
   Load safetensors with remote code disabled. Run inference offline.
4. Tokenize exact prompted queries and plain passages with special tokens.
   Fail before inference if any input exceeds the explicit 2,048-token test cap.
   No silent truncation. This cap is smaller than Qwen's supported context.
5. Use the model card's last-token pooling and retrieval query instruction.
   Export 1,024 dimensions, plus 512/256 using supported prefix reduction and
   normalization. Each dimension has a separate embedding-space identity.
6. Score exact cosine rankings and TF-IDF/dense reciprocal rank fusion (k=60).
   Measure load time, first inference, passage indexing, warm query p50/p95 and
   process memory. Smaller vectors reduce storage, not model inference work.

## Storage and commands

Everything generated lives in `output/model-benchmark` inside this D: checkout.
The virtual environment, pip/Hugging Face/PyTorch/XDG caches and TEMP/TMP all use
D:. Scripts reject a checkout on another drive. Nothing is installed globally.
The already installed Python interpreter may reside on C:; the benchmark's
packages and model files do not. OS-managed pagefiles are outside this control.

```powershell
# Supply an installed Python 3.12 interpreter for initial environment creation.
./scripts/benchmark-cpu.ps1 -Action install -Python <python.exe>
./scripts/benchmark-cpu.ps1 -Action download
./scripts/benchmark-cpu.ps1 -Action run -Threads 2
```

Installation and download require network access. Run uses local model files
only, with Hugging Face and Transformers offline flags. Model download permits
only the fixed public Qwen repository, anonymous access, root configuration/
tokenizer files and safetensors, at most 4 GiB. Available disk headroom is checked.
At least 4 GiB available RAM is required before model loading. No cloud resource,
API key, personal document, database write or UI model progress is involved.

Artifacts: `qwen-download.json` (revision and hashes), `environment.txt`,
`qwen-2threads/measurement.json`, `vectors-{256,512,1024}.json`, and
`scores-{256,512,1024}/comparison.json`. Generated artifacts are ignored by Git;
commit the concise report and hashes, never model weights or the environment.

## Interpretation and remaining work

This is a tiny English development corpus, not a held-out quality test. Recall@5
asks whether the right documents appear in the first five unique results. MRR@5
rewards putting the first relevant document higher. Evidence recall checks the
actual matching passage. Five absent queries are reported separately; nearest
neighbors are not evidence that an answer exists. No abstention threshold is fitted.

Laptop timings, even with two threads, are not Cloud Run timings, vCPU limits or
a monthly bill. One warm pass is descriptive, not a stable service latency SLO.
Memory is process working-set evidence, not full container memory or billed RAM.
Quantization, concurrent requests, long inputs, cold cloud starts and real database
latency need separate tests before selecting a production configuration.

EmbeddingGemma is pending the user's license acceptance/access. SigLIP and OCR
need an approved image/scan corpus with category labels. Chat benchmarks remain
deferred until search works. None of these are implicitly complete after Qwen.

Sources: [Qwen model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B),
[Hugging Face cache controls](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables).
