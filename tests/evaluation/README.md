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

## Planned scoring protocol

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
the denominator. Scorer/provider integration is still to be implemented.

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
