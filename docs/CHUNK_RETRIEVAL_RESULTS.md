# Paired chunk-policy evaluation

15 October 2026. TASK-005 compares the legacy 1,024-character policy with the
prepared 512-token policy on the same patched Qwen CPU image. This changes
evaluation tooling only; production ingestion and existing indexes are unchanged.

## Results and decision

The predeclared text-v2 dense gate passes. All three metrics exceed 0.90 and none
falls more than 0.02 below the paired legacy policy. This does not make the
boundary problem solved or approve integration/release.

| Dataset / method | Policy | Document Recall@5 | MRR@5 | Strict evidence Recall@5 | Union evidence Recall@5 |
| --- | --- | ---: | ---: | ---: | ---: |
| text-v2 / dense | Legacy | 100% | 0.9613 | 99.11% | 99.11% |
| text-v2 / dense | Token512 | 100% | 0.9792 | 100% | 100% |
| text-v2 / TF-IDF | Legacy | 100% | 0.8836 | 92.86% | 92.86% |
| text-v2 / TF-IDF | Token512 | 100% | 0.8726 | 100% | 100% |
| text-v2 / RRF | Legacy | 100% | 0.9554 | 99.11% | 99.11% |
| text-v2 / RRF | Token512 | 100% | 0.9286 | 100% | 100% |
| Boundary / dense | Legacy | 100% | 0.7813 | 50% | 50% |
| Boundary / dense | Token512 | 100% | 0.8125 | 50% | 87.5% |
| Boundary / TF-IDF | Legacy | 100% | 0.9375 | 100% | 100% |
| Boundary / TF-IDF | Token512 | 100% | 1.0000 | 62.5% | 100% |
| Boundary / RRF | Legacy | 100% | 0.8542 | 93.75% | 93.75% |
| Boundary / RRF | Token512 | 100% | 1.0000 | 62.5% | 100% |

RRF remains a comparator: it helps this small stress set but lowers text-v2 MRR
versus dense. No fusion, prompt or overlap policy was changed after these results.
All eight text-v2 absent questions and both stress absent questions returned
candidates under every method. No abstention or answer-generation layer is tested.

### Review of dense query changes and remaining misses

On text-v2, maker-05 now retrieves both required evidence spans; game-03 and
game-04 move their relevant source from second to first. No dense metric regresses
per query. The two remaining nonperfect questions are festival-06 (historical
source still second behind current guidance) and stage-02 (exact WT-C22 source
still third). Both complete passages are in the top five. Other answerable
candidate queries have MRR=1 and strict evidence recall=1.

| Stress query | Candidate observation versus legacy |
| --- | --- |
| boundary-01 / boundary-02 | Same current source ranks first, but the shared condition spans two chunks. Strict recall drops from 1 to 0; union coverage is 1. |
| boundary-03 | Current closing-sheet passage recovered; source moves from second to first. |
| boundary-04 | Exact archived form passage recovered; source remains first. |
| boundary-05 | Archived guidance now outranks the requested current exception (first to second). Complete condition spans two chunks: strict recall drops from 1 to 0, union is 1. |
| boundary-06 | Requested archived source moves from second to first; evidence retained. |
| boundary-07 | Current inventory passage recovered, but archived guidance now ranks first (relevant source moves from first to second). |
| boundary-08 | Relevant sources are found, but neither late paperwork location is among the first five passages. Strict and union recall remain 0; MRR improves from 0.25 to 0.5. |

The boundary aggregate staying at 50% strict recall hides both recovered and lost
passages. Three deliberately split questions remain strict misses even when their
combined text is retrieved. boundary-08 is a distinct ranking/coverage failure.
These results justify testing bounded same-source context assembly and passage
diversity for multi-part searches next, before ingestion integration. Keep exact
source offsets/citations, ownership/version boundaries and resource caps; do not
silently merge unrelated sources or increase model input limits.

### Runtime and verification

All 178 requests completed without timeout/OOM in 284.98 s, including 13.78 s
startup. Individual requests took 0.637–6.972 s; mixed query/document median
1.037 s, nearest-rank p95 4.467 s. Peak cgroup memory was 4,290,404,352 bytes
(about 4.00 GiB), below 5 GiB. Inputs ranged from 28 to 512 prompted tokens.
These combined timings are not user-search latency, per-policy throughput or
cloud measurements. The temporary container exited zero and was removed.

44 evaluation tests, 26 inference tests and the frontend build pass. The new
tests verify unchanged legacy preparation, frozen-source/query/label rejection,
strict split misses, continuous same-source union coverage and retained outer
timeout evidence with owned-container cleanup. No runtime image or native assets
changed, so neither was rebuilt. Raw outputs remain on D:; reviewed evidence:
[chunk-retrieval-20261015.json](../tests/evaluation/results/chunk-retrieval-20261015.json).

Docker initially failed to start with an inaccessible internal sailor-ingest.sock.
With user approval, the failed app was closed and reopened through Explorer;
engine 29.7.2 recovered without deleting files or changing settings. A transient
clean-cache release and authorized closure of background Teams/WhatsApp freed
4.10 GiB host RAM. Chrome was left running. No individual API stop/update commands,
cloud resources or GitHub push were issued.

## Method

The frozen text-v2 set contains 40 fictional documents and 64 queries. Its complete
documents already fit in 512 tokens, so the candidate consolidates 64 old passages
into 40. It does not create smaller passages than the legacy policy on this set.
The token limit instead bounds model work relative to the earlier 2,048-token
serving budget. A separate six-document, ten-query fixture tests long documents,
current/archive confusion and conditions split across boundaries (24 versus ten
chunks). Three queries share two deliberately split conditional evidence spans.
They are diagnostic examples, not independent population samples.

Both layouts use the same pinned model, image, prompts, 512 dimensions and query
vectors. Exact duplicate role/text requests are evaluated once and reused. There
are 178 distinct requests, each at most 512 prompted tokens. The full experiment
has a 900-second outer deadline; each model request still has its 15-second limit.
CPU, 5 GiB container memory and 4 GiB host-availability guards are unchanged.

Strict evidence recall requires the entire unchanged quoted span inside a top-five
passage. Supplementary union coverage requires all characters of that span across
the top-five passages from the same source, without gaps. It does not generate an
answer or prove that the interface will assemble that context correctly.
Document recall deduplicates sources before selecting five results. Absent queries
are excluded from recall/MRR and their returned candidates are reported separately.

Protocol: [CHUNK_RETRIEVAL_PROTOCOL.md](../tests/evaluation/CHUNK_RETRIEVAL_PROTOCOL.md).
The fixtures, index hashes, protocol hash and request ordering were frozen before
inference. Labels never enter model requests. No threshold, quote or boundary is
tuned after viewing results. Historical v1/v2 exports are preserved.

## Reproduce locally

```powershell
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.evaluate_chunk_retrieval
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.check_inference_container --candidate --profile retrieval
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.evaluate_chunk_retrieval --score
```

Only repository-authored fictional sources enter the offline container. Weights,
prepared data and raw vectors stay under ignored D: output. The scorer checks
the frozen plan, pinned image and raw-output hash before accepting complete vectors.
Failed requests cannot become empty search results. Outer timeout evidence is
retained, and cleanup is limited to the uniquely owned test container.

These development results cannot establish real-user quality, cloud capacity,
abstention, multilingual retrieval or PDF/Office/OCR support. Image security and
licence review remain release gates; no deployment or GitHub push is implied.
