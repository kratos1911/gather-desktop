# Vector evaluation adapter

This offline adapter consumes saved embeddings. It does not generate embeddings,
download weights, contact an API, select a provider or enable semantic search in
the desktop. The only vectors exercised so far are explicitly synthetic unit
test numbers, not model output or an accuracy benchmark.

## Techniques

1. **Dense embeddings:** a future embedding model represents passages and queries
   as numeric vectors. Query/document prompting may differ, but both must belong
   to the same versioned embedding space. The model supplies meaning; this script
   does not manufacture it.
2. **L2 normalization and exact cosine search:** normalize vectors to length one
   and rank by their dot product. Every passage is examined for a simple reference
   result, without approximate-nearest-neighbour error. All scores, including
   zero/negative ones, remain candidates; no answerability threshold is invented.
3. **Reciprocal Rank Fusion:** add `1/(60 + rank)` from the TF-IDF and dense lists
   for each chunk, using equal weights. Rank starts at one. This combines ranks
   rather than incompatible raw scores. Constant 60 is fixed for this experiment,
   not tuned to gold labels. Production candidate depth remains a later decision.
4. **Controlled comparison:** score lexical, dense and fused rankings on identical
   frozen sources/questions with the existing Recall@5/MRR@5 scorer. Labels enter
   only scoring and run validation, not embedding or ranking decisions.

## Export contract

Root fields: `schema_version: 1`, `corpus_version`, `corpus_sha256`,
`index_sha256`, `provenance` (`model_export` or `synthetic_test`),
`embedding_space`, `documents`, `queries`.

`embedding_space` must include provider, model, revision, dimensions (1..4096),
query_template, document_template and tokenizer_revision. Use exact templates
or immutable template identifiers; say `identity` if no template applies.
Each document row contains document_id, chunk_id, vector, embedding_space and
`truncated: false`. Each query row has id, vector, embedding_space and the same
truncation declaration. Include every source chunk and every query exactly once.
Every row's embedding_space must equal the root configuration. A provider adapter
must actually verify tokenizer limits and processing settings before declaring
no truncation; this file validator cannot verify a producer's honesty.

Missing vectors, duplicate IDs, unknown/mismatched sources, zero/nonfinite vectors,
mixed models/revisions/prompts, changed index hashes and truncation are errors.
Do not silently replace failures with zero vectors or fabricated matches.
Changing output dimensions requires a fresh consistent export; dimensions alone
do not establish model compatibility. No automatic slicing of model output.

Run from repository root with a genuine export when available:

```powershell
python -m scripts.evaluate_vectors --vectors output/evaluation/provider-vectors.json
```

The CLI caps file input at 32 MiB, writes comparison.json under ignored
output/evaluation/text-v1/vectors and prints summaries with provenance.
It reads no credentials and performs no network calls. Keep exports out of Git.
All three rankings and reports, embedding configuration and provenance are saved
together. A `model_export` declaration is producer-supplied, not attested proof.

## Methodology and remaining work

First verify math and rejection paths with known vectors (current checkpoint).
Next select provider/model and budget, implement the producer with batching,
timeouts, token checks, usage accounting and safe errors, then export real vectors
and compare without altering labels. Record provider revision and costs alongside
the output. Preserve a failure rather than tuning the questions to fit a model.
Cloud hosting and model-quality evaluation remain deferred, not simulated as
completed. Broader unseen long-document queries remain a release requirement.
