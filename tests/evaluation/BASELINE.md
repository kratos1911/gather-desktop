# Keyword baseline: text-v1

Measured locally on 27 September 2026 using `python -m scripts.score_text_evaluation`.
Retriever: `tfidf-cosine-v1`; scorer: `retrieval-at5-v1`. No model, provider,
cloud storage or paid resource involved. This measures an offline development
comparator; it is not functionality connected to the desktop app.

Corpus SHA-256: `07836c70107491a5a44d7d00c7f50bb69802c62b871841537e74163a8fdf6a4c`

Processed index SHA-256: `704bacee8abd12fb09c2848f9484703963e112ee0b4365a8a6712e11539c6b7e`

| Category | Answerable queries | Document Recall@5 | Evidence Recall@5 | Document MRR@5 |
| --- | ---: | ---: | ---: | ---: |
| Paraphrase | 20 | 0.9500 | 0.9500 | 0.8167 |
| Exact | 6 | 1.0000 | 1.0000 | 1.0000 |
| Confusable | 4 | 1.0000 | 1.0000 | 0.8750 |
| Late document | 3 | 1.0000 | 1.0000 | 0.8333 |
| Multiple sources | 2 | 1.0000 | 1.0000 | 1.0000 |
| Overall | 35 | 0.9714 | 0.9714 | 0.8667 |

Recall missed one query: **q18**, "Find the packing advice for a walk exposed to
rain." Its expected evidence is in `travel`, code-point range `[152, 226)`:
"Pack a waterproof jacket because the walking route has no covered shelter."
The keyword baseline lacks morphological/synonym matching and does not retrieve
that evidence in its top five. Corpus and labels were not edited after this run.

Four of five absent-answer questions return candidates. These are related
documents, not verified supporting evidence; no model generated an answer and
no false-answer rate is claimed. All five are excluded from recall/MRR averages.

The corpus has just 14 sources and 16 chunks; nearly every document occupies
one chunk. Finding a document usually finds all its facts, which explains the
identical document/evidence recall here. This result exceeds the numerical
90% target on this easy development set only; it does not satisfy the product
release gate, prove semantic capability, or justify replacing embeddings.
Broader long-document and independently reviewed unseen queries remain needed.

No inference latency, 10,000-chunk latency, cloud cost, visual/OCR, multilingual,
user-isolation or chat-grounding benchmark was performed. Full per-query results
can be regenerated in the ignored output directory using the command above.
