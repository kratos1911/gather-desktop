# Text-v2 challenge protocol

Frozen on 12 October 2026 before the first text-v2 model run. This is a new,
original fictional challenge set authored by the development assistant after
seeing v1 results. It is not blind, independently labelled, or representative of
all personal libraries. No personal files, websites or copyrighted source corpus
were imported. The JSON and exact quotes are the authoritative fixtures.

## Inventory and freeze

40 Markdown documents across eight domains: museum loans, fabrication, film
screenings, gaming, bicycle servicing, field observations, theatre and seeds.
Each domain includes a long current handbook, a related current process, an
explicitly archived process, a neighbouring activity and a distractor note.
These deliberately similar records test whether the requested subject and time
period matter. They are not parser benchmarks for Office files or web pages.

64 queries: 16 paraphrases, 16 confusable cases, 8 exact identifiers, 8 late
passages, 8 multiple-source questions and 8 absent-answer cases. The last eight
are excluded from recall/MRR. The current unchanged processor produces 64 chunks.
All eight late quotes start beyond character 2,300. Sources span 166–2,736
characters: this tests later passages, not maximum-length documents or load.

Canonical corpus SHA-256:
`d23f63392759b5db751f1a024468908d8d6b3832652ddbdb7234264c8eb4d25b`.
The loader enforces text-v2.freeze.json. No source, query or relevance label may
be adjusted after results to improve a score. Corrections require a new version,
a stated reason and a new evaluation. v1 and its outputs remain unchanged.

## Fixed experiment

- Reuse Qwen3-Embedding-0.6B revision
  `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` from the existing D: cache.
- CPU float32, four threads, one item per batch, same prompt/last-token pooling.
- Same 1,024-character chunker with 128-character overlap; exact tokenizer
  preflight must fit the 2,048-token test cap. Never truncate silently.
- Evaluate 256, 512 and 1,024 dimensions; normalize after prefix reduction.
- Same exact cosine, TF-IDF and equal-weight RRF k=60. No prompt, threshold,
  stopword, candidate-depth, synonym or fusion-weight tuning on this set.
- Labels stay in the scorer; inference receives only prepared index/query data.
- The prior 512-dimensional candidate is the primary check. Other dimensions
  and RRF are comparators, not an invitation to select on this set retrospectively.

## Decision criteria declared before inference

For advancing the 512-dimensional candidate to a bounded serving-container
experiment: document Recall@5 >=0.90, evidence Recall@5 >=0.90 and MRR@5 >=0.90
on the 56 answerable questions. Report each category and every nonperfect query.
These are development gates, not statistical confidence or a public accuracy claim.

If the candidate fails, report the cause and keep it unselected. Preserve the
original scores when testing a later change. If it passes, investigate failures
before using it in the first connected slice. Neither outcome establishes cloud
latency, multilingual support, user isolation, abstention or production readiness.
Do not enable RRF by default unless it demonstrates a useful quality tradeoff.

Record all eight absent cases returning candidates; no calibrated answerability
layer exists. A candidate result is not a claim that the requested fact is present.

## Run

```powershell
python -m unittest discover -s tests/evaluation -v
./scripts/benchmark-cpu.ps1 -Action run -Corpus text-v2 -Threads 4
```

The second command runs offline against the cached weights. v2 inputs/vectors/
reports are written to `output/model-benchmark/text-v2` on D:, separately from
v1. No new model download, cloud service or deployment is needed. Record hashes
of raw outputs plus a compact result report in the repository after review.
