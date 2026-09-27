# Retrieval development set: text v1

This is original fictional content authored for Gather. It is a development
fixture, not an independently labelled benchmark, production dataset or proof
of model accuracy. No model has run against it yet. There are 14 documents,
35 answerable questions and 5 deliberately absent-answer questions.

Topics: database notes, similar lamp/laptop receipts, competing project schedules,
train bookings, gardening, backups, sales versus stock figures, study notes and
a longer workshop handbook. Sources are TXT and raw Markdown; no PDF, Office,
OCR or photograph processing is tested here. Visual/OCR evaluation remains TASK-009.

## Run without downloads or cloud calls

From the repository root using Python 3.11+:

```powershell
python -m unittest discover -s tests/evaluation -v
python -m scripts.prepare_text_evaluation
python -m scripts.prepare_text_evaluation --output output/evaluation/text-v1
```

The last command optionally writes generated files under ignored `output/`:
- `index.json`: processed source passages, versions, hashes and source ranges.
- `queries.json`: question IDs and text only.
- `labels.json`: expected documents, exact evidence ranges and acceptable chunk IDs.

Do not expose labels to an embedding model, query rewriter or ranking adapter.
Only the offline scorer/reviewer should read them. The canonical JSON fingerprint
changes with sources, questions or labels; newline differences in the JSON file
itself do not change the fingerprint. Source text line endings are still data.
Pin this fingerprint, parser/chunker versions and model/provider revision in each
future run. Regenerate chunk labels after changing chunking, never reuse stale IDs.

## What the checker proves

Every evidence quote occurs exactly once in its source and is entirely present
in at least one chunk from the real TASK-004 processor. It records all containing
chunks to avoid penalizing overlap. Late-document evidence starts beyond the
first 1,024 characters. IDs and question text are unique. Absent questions have
empty labels and an authored rationale. These checks cannot establish that
human relevance judgements are correct; review labels before using results.

## Scoring protocol

For answerable questions, report **document Recall@5**: unique relevant documents
in the top five unique returned documents divided by all labelled relevant
documents, averaged across questions. Collapse repeated chunks from one document
before selecting five documents. Multiple-source questions require both sources
for full recall. Report **document MRR@5** using the first relevant document.

Report **evidence Recall@5** separately on the top five returned chunks: an
expected evidence span is found if any of its acceptable chunks appears; overlap
does not create extra positives. Average found-span fractions per question. A
correct file with the wrong passage must not pass the evidence metric. Report
each category, its sample count and each failure, not just an overall average.

Absent questions are excluded from recall/MRR denominators. A nearest-neighbour
index always returns something unless the application adds abstention. When
that exists, report the fraction of these five queries on which the system
incorrectly claims supporting evidence, alongside answerable coverage. Returning
a related laptop receipt is not proof that it contains a serial number.

Require one result entry for every query ID, with an empty list representing a
real no-result response. Missing IDs, unknown documents/chunks, mismatched corpus
hashes or duplicate result IDs invalidate the run rather than silently improving
the denominator. The offline scorer is implemented; model/provider integration
remains pending.

## Lexical baseline and saved runs

```powershell
python -m scripts.score_text_evaluation
python -m scripts.score_text_evaluation --run output/evaluation/text-v1/baseline/run.json --output output/evaluation/text-v1/rescored
```

The default writes `run.json` and `report.json` to ignored
`output/evaluation/text-v1/baseline`. Rankings contain all positive-score chunks
so document deduplication happens before top-five selection. The scorer treats
array order as rank; numeric scores are optional and never compared across runs.
Each hit has `document_id` and `chunk_id`. Every query needs an explicit result,
including `hits: []` for a completed request with no candidates. A failed request
must not be disguised as empty results; fix/retry the run before scoring.

Run metadata requires schema_version 1, corpus_version, corpus_sha256,
index_sha256 and a nonempty retriever identifier. The index fingerprint covers
processed text, chunk IDs/ranges and parser/chunker versions, preventing stale
rankings after processing changes even if corpus content has not changed.
An external adapter must use the same prepared index and metadata; include its
provider/model revision/configuration in its retriever identifier or additional
metadata. This is an offline developer utility, not an authenticated upload API.

`tfidf-cosine-v1` is a standard-library keyword comparator: Unicode casefold,
alphanumeric terms retaining internal hyphens, no stemming/stopword removal,
logarithmic term frequency `1 + ln(count)`, smoothed IDF
`1 + ln((1 + chunk_count)/(1 + document_frequency))`, L2 normalization and
cosine similarity. IDF is computed across chunks, not source files. Unknown
query terms are ignored; zero vectors yield no candidates. Ties break by source
ID then chunk ID. It receives no labels and has no corpus-specific synonyms or
tuned thresholds. This is neither semantic search nor Supabase full-text search.

Absent-query candidate counts are diagnostic, not an unsupported-answer rate:
the baseline makes no answer/support claim and implements no calibrated
abstention. That rate is explicitly null until an answerability layer exists.

See [the measured baseline](BASELINE.md) for results and limitations.

## Benchmark gate and limitations

Before hosted testing: choose provider/model revision and license, query/document
prompt templates, tokenizer limits, vector dimensions, budget and rate limits.
Record latency cold/warm separately, failed requests, billed usage and measured
cost. Do not claim the product's 10,000-chunk latency target from this tiny set.
Compare exact keywords with semantic/hybrid retrieval on the same frozen inputs.

These short sources make document-level retrieval easy; only one longer document
tests later passages. Add longer varied sources and independently reviewed unseen
questions before locking a model. Never tune on this set and call it a held-out
test. English-only questions do not validate multilingual claims. This set does
not test user isolation, chat faithfulness, deletion, native UI or cloud readiness.
