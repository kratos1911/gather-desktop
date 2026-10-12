# Fresh text challenge: results and next step

12 October 2026, TASK-005. The previous 512-dimensional Qwen candidate passes
the development gate declared in [the frozen protocol](../tests/evaluation/TEXT_V2_PROTOCOL.md).
It can advance to a bounded CPU serving-container experiment. This does not
select a final production model or complete connected desktop search.

## What changed in the experiment

40 new fictional Markdown documents, 64 passages and 64 questions, covering eight
different domains. There are 56 answerable questions and eight absent-answer
questions. Eight long handbooks place labelled evidence beyond character 2,300;
related current, archived and neighbouring records compete in the same search.

The corpus and labels were fingerprinted before inference. Its loader rejects
changes. The model revision, query prompt, chunker, precision, 256/512/1,024
dimensions, cosine scorer and fixed RRF remained unchanged. This was one offline
four-thread CPU run using the existing D: weights; there was no new download.
The prior twelve raw v1 vector/comparison files still match their recorded hashes.

## Quality

| Method | Document Recall@5 | MRR@5 | Evidence Recall@5 |
| --- | ---: | ---: | ---: |
| TF-IDF | 100% | 0.8836 | 92.86% |
| Qwen 256 | 100% | 0.9702 | 97.32% |
| Qwen 512, primary candidate | 100% | 0.9613 | 99.11% |
| Qwen 1,024 | 100% | 0.9821 | 98.21% |
| RRF with 256 | 100% | 0.9464 | 96.43% |
| RRF with 512 | 100% | 0.9554 | 99.11% |
| RRF with 1,024 | 100% | 0.9286 | 98.21% |

Document recall deduplicates sources before taking five results. Evidence recall
uses the first five passages, so finding a file does not imply finding the right
excerpt. Scores average across answerable queries; 99.11% evidence recall is not
the percentage of perfectly answered questions. Search generates no answers here.
The 512 candidate meets each predeclared >=0.90 threshold. It has the best evidence
recall, while 1,024 has the best MRR; there is no universal winner on these metrics.

All eight absent questions return candidates for every method. No abstention or
answerability threshold is implemented. This is a known limitation, not a passed
no-answer test. The examples were authored by the development assistant after
v1, not independently labelled or blind. No real-user, multilingual or 10,000-chunk
performance claim follows from these results.

### Review of every nonperfect 512-dimensional dense query

| Query | Observed issue | Follow-up, not implemented here |
| --- | --- | --- |
| maker-05 | Both files appear, but the resin rescheduling passage is sixth; only one of two required evidence spans is in the first five. | Evaluate passage coverage for questions with multiple parts; preserve source identity and avoid filling results with redundant passages. |
| festival-06 | Current outdoor guidance ranks above the requested historical backup venue; historical source is second. | Test temporal wording and explicit current/archive metadata. |
| game-03 | Team substitute guidance outranks the requested solo rule; solo source is second. | Test entity qualification and closely related contradictory rules. |
| game-04 | An archived deadline ranks above the current rule; current source is second and correct evidence is in the first five. | Evaluate temporal metadata alongside query intent. |
| stage-02 | The exact WT-C22 code retrieves the right file third. | Evaluate explicit identifier matching; TF-IDF and 512 RRF put this source first, but fixed RRF loses MRR elsewhere. |

No labels, prompts or rankings were tuned after finding these cases. All other
answerable 512-dense queries have MRR=1 and evidence recall=1. Per-category
results and failures for every comparison are in the
[machine-readable evidence](../tests/evaluation/results/qwen-text-v2-20261012.json).
Keep fixed RRF as a comparator rather than enabling it by default: again it
lowers overall MRR versus dense retrieval at every dimension.

## Runtime and verification

Ryzen 7 4800H, Windows, CPU float32, four PyTorch threads, batch size one.
Median warm query: **0.329 seconds**; nearest-rank p95: **0.403 seconds**.
Indexing 64 passages: **39.73 seconds**. OS peak working set: **3.64 GiB**.
Actual tokens: passages 32–171; prompted queries 28–39. Nothing was truncated.
Cached-weight initialization: 1.44 seconds, excluding imports and earlier hash
reads. This is not a cold-start measurement, service load test or cloud estimate.

Commands verified:

```powershell
./output/model-benchmark/venv/Scripts/python.exe -m unittest discover -s tests/evaluation -v
./scripts/desktop.ps1 build
./scripts/benchmark-cpu.ps1 -Action run -Corpus text-v2 -Threads 4
```

39 evaluation tests and frontend production build pass; pip check passes.
The v1 lexical regression reproduces Recall@5 0.9714 and MRR@5 0.8667.
New tests cover frozen source/query/label edits, evidence positions, label
separation, disjoint fixtures, output separation and cross-corpus rejection.
Unchanged worker/UI suites were not rerun for this evaluation-only change.
No native inputs changed. Model files, venv, caches, inputs and raw results stay
under ignored `output/model-benchmark` on D:. No personal files or paid resources.

## Next implementation

Build the local CPU serving-container experiment using the pinned Qwen model and
512-dimensional candidate. Acceptance: explicit CPU/RAM/concurrency limits,
bounded token and request sizes, readiness only after model load, inference error
and timeout behavior, and observed container memory/startup/query timing. Keep it
local and private; verify Docker storage remains on D: before large image work.
Then choose cloud sizing from measurements and close auth/quota/security gates
before deployment. Track identifier, temporal and multiple-part retrieval work
as open quality issues for the connected search slice.

EmbeddingGemma still awaits license/access; image/OCR has a separate corpus gate;
chat remains deferred. User-approved real-world/independent relevance review is
still required before public quality claims.
