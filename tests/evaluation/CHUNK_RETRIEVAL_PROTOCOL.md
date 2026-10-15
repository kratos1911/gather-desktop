# Paired chunk retrieval experiment

Declared on 15 October 2026 before this experiment's real model run. TASK-005
compares the existing character policy with the prepared token policy. It does
not modify ingestion, promote the image, deploy a service, or select a final
production model.

## Frozen inputs

Keep `text-v2.json` and its freeze unchanged: 40 fictional documents, 64 queries,
56 answerable and eight absent. On the pinned tokenizer, every complete v2
document fits within 512 tokens (maximum 487). Therefore the candidate produces
40 chunks versus 64 legacy chunks. This comparison tests consolidation of those
short documents, not splitting of long documents.

`chunk-boundaries-v1.json` is a separate original fictional diagnostic fixture:
four long documents in two current/archive pairs, two short distractors, eight
answerable questions and two absent questions. The long sources have 749–902
tokens. Their shared administrative prose deliberately makes them confusable.
The full fixture produces 24 legacy chunks and ten candidate chunks. The two
unrelated distractors keep six documents in the collection, so document Recall@5
is not automatically perfect.

Canonical stress corpus SHA-256:
`6e984a2895c0a942db993dc550f7e8f92f43d10ca69536d3228fae3e5ebd6bde`.

The two current-guide conditional quotes were deliberately positioned using the
pinned tokenizer and chunk ranges before inference. Each is fully present in a
legacy chunk and crosses a candidate boundary beyond its 64-character overlap.
This is a structural diagnostic, not blind evaluation. The quotes preserve the
exception and its limiting condition together; retrieving only a permissive
clause must not count as retrieving the complete supporting span. `boundary-01`
and `boundary-02` share one of those spans; `boundary-05` uses the other. Late
evidence, an exact identifier, archived guidance, a multiple-source question and
absent facts exercise other paths. The repeated conditions are not independent
samples and are not a population accuracy estimate.

Fixtures and labels are developer authored, not independently reviewed. No user
documents or live web content are included. Freeze content, questions and exact
quotes before inference. A correction after results requires a new fixture
version, documented reason and separate evidence; never overwrite results to
improve the reported score.

## Fixed comparison

- Both policies run on patched image
  `sha256:5d84bdf24729cacb20389734baee56fd49293eeb1bd2053d5eac1d0259c04f95`.
- Qwen3-Embedding-0.6B revision
  `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`, CPU float32, two threads,
  last-token pooling, first 512 dimensions and L2 normalization.
- Use the existing query instruction and unmodified document text. No prompt,
  rank-fusion, threshold, synonym or overlap tuning from these results.
- Legacy: `boundary-1024-overlap128-v1`. Candidate:
  `qwen-boundary-512-overlap64-v1`, at most 512 actual document tokens.
- One text per request. Keep the runtime's 15-second request deadline, resource
  limits, private offline container and 4 GiB host-availability guard unchanged.
- Generate query vectors once per corpus and use the same query vectors for
  both policies. Preserve distinct index fingerprints and all actual chunk
  vectors. Labels stay in the scorer, never in inference inputs.
- Report exact cosine as the primary method. The existing TF-IDF method is a
  diagnostic comparator on each policy's index. Historical v2 scores used a
  different host runtime; use this paired run for the policy comparison.

## Scoring and decision declared before inference

Use existing document Recall@5, document MRR@5 and strict evidence Recall@5.
Document ranking deduplicates sources before selecting five; evidence ranking
uses only the first five chunks. Rebind acceptable chunk IDs by full containment
of the original exact source span under each policy. An uncontained quote has
an empty acceptable list and remains an evidence miss; never shorten the quote,
drop the query, or mistake the correct document for the correct passage.

The primary v2 candidate must achieve all three metrics at least 0.90, with no
metric falling more than 0.02 below the paired legacy result. Report per-category
and per-query changes, including every regression and uncontained span. Passing
this gate is limited development evidence, not permission for deployment.

The stress fixture is diagnostic, not a gate to tune away. Its intentionally
split spans are expected to expose the strict metric's limitations. Report that
finding explicitly even when the supplementary coverage score is high.

Supplement strict evidence recall with coverage from the union of the top five
chunks' source intervals. Merge and clip intervals within the correct document;
overlap must not count twice, and an uncovered gap must remain a gap. Only a
fully covered original span counts as recovered supporting evidence. A chunk
from another source cannot cover it. The supplementary metric does not replace
strict recall, establish a coherent answer, or make a failing primary gate pass.

Absent questions remain outside recall/MRR denominators. Report candidate
returns without claiming abstention or answer correctness. A failed request or
incomplete export invalidates scoring rather than becoming an empty result.

## Evidence and limits

Record image/model/tokenizer and policy identities, corpus/index fingerprints,
raw-output hashes, token counts, request failures, startup and warm timings,
memory peak, ranks and every metric change. Save a compact reviewed report in
the repository; raw vectors stay in ignored D: output. Preserve failed runs.

This small synthetic experiment cannot establish real-user relevance, retrieval
at scale, multilingual quality, OCR, PDF/Office extraction, cloud latency,
authorization or release readiness. It compares isolated prepared text only.
If quality regresses, record the limitation and keep ingestion integration
gated rather than changing the metric or silently adjusting the corpus.
