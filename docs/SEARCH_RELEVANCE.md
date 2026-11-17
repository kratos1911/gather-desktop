# Private search relevance filter

## Unrelated candidate filter, 17 November 2026

Hybrid search now checks for a shared content term in the candidate text or
title before applying the existing score floor and near-best band. It folds
case and compatibility forms, ignores common function words, and recognizes
basic plural endings. A cosine score of at least 0.65 retains a semantic-only
candidate without shared terms. The exact-keyword ranking branch still enters
fusion independently. The compact route evaluates its existing bounded preview;
the legacy hybrid route evaluates the ranked passage. Both return the original
saved text and citation offsets.

The pinned Qwen model reproduced the reported false match locally: the turtle
query scored 0.2477 against the synthetic Orchard note, just over the old 0.24
floor. In the same test it now returns an empty result. The second unrelated
case also returns empty. The Cedar and NLP exact queries and three paraphrases
retain their expected documents. The test used 11 local embeddings on four
synthetic sources and seven fixed queries. A hash-verified replay of the two
previous corpora kept expected top-five sources for all 64 answerable queries
using both full passages and simulated compact excerpts.

The ten topic-adjacent absent queries in those saved corpora still produce
candidates. They share subject terms with the sources or exceed the strong-score
threshold. The release evidence applies to queries whose topic is unrelated
to the retrieved file. See [native acceptance](SEARCH_ACCEPTANCE.md).

The candidate passed 107 focused checks on the local host and in its image.
The frontend build passed. Local receipts are under `output/search-evidence/`.

## Earlier score-only rollout

4 November 2026: local checks and approved hosted/native Cedar regression pass.
One real query embedding used; no document, database or resource-setting changes.

## Policy and boundaries

After Auth, one query embedding and owned ranking, validate every candidate.
Keep scores >= max(0.24, best score - 0.12), before source grouping/full reads.
Rejected same-source hits cannot reenter context. Preserve original ranks, scores,
ownership/version/citation checks, bounded neighbors, cancellation and limits.
Existing empty-results UI handles no accepted matches. No extra model call,
keyword requirement, client setting, DB migration or native asset change.
Policy qwen-cosine-window-v1 is bound to the pinned Qwen revision/512-D space;
changing that space fails closed until recalibration.

## Known-set calibration and verification

scripts/evaluate_relevance.py reuses hash-fenced real Qwen rankings/vectors and
frozen fictional labels. Text-v2 calibration preserves each expected source found
in top5: floor = lowest positive-source best score minus .02, rounded down to .01;
band = largest positive-source score gap plus .02, rounded up to .01. Result .24/.12.
A high absolute cutoff lost valid searches; a .08 band dropped maker-05's second
expected source and was rejected. No labels, model inputs or chunks were changed.

| Known set | Complete expected-source recovery before/after | Top5 candidates before/after | Context regressions |
| --- | --- | --- | --- |
| Text-v2, 56 answerable queries | 56/56 -> 56/56 | 320 -> 155 | 0 |
| Boundary, 8 answerable queries | 8/8 -> 8/8 | 50 -> 33 | 0 |

Candidate totals include absent queries. Assembled evidence remains covered on
both known sets. This is post-hoc calibration/regression, not blind held-out or
population accuracy. All ten topic-adjacent absent queries still return candidates:
weak-secondary suppression is not answerability proof. Future reranker/quality
work remains open. Cosine scores are not probabilities.

35 focused coordinator/profile/session checks pass locally and in packaged image
2e33313413ae31a0ae6c28767f6ae066410bc5243075767056e84d516d14aae3:
reject before reads, empty output, weak identifier/multi-source retention, rejected
same-source hits, candidate validation and space binding. These are synthetic;
cached replay separately verifies selected real model scores. Frontend build
passes; backend-only change requires no native rebuild. Runtime/packages/models
are unchanged, so OCR package review/open findings remain applicable.

Evidence: [saved replay](../tests/evaluation/results/search-relevance-20261104.json),
output/evaluation/relevance-v1/ and output/relevance-pilot/.

## Hosted acceptance

With explicit approval, uploaded/deployed the verified image to the existing
Gather API, revision gather-library-pilot-00009-mxp. CPU1/2GiB, min0/max1, env,
model, IAM/secrets and INR500 allowance stay unchanged. No migration or app
replacement. In the installed signed-in pilot B app, the original archive-request
query returned only synthetic-note.png with Cedar text/region citations; the
resume disappeared. No files were changed or deleted. One real embedding request.
The first manual readiness GET timed out during cold startup; the second passed
before search. No embedding request was repeated. Evidence: live-acceptance.json,
deployment.json and cedar-filtered.png under output/relevance-pilot/.
