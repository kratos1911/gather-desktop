# Native search trial acceptance

Point 4 of the compact search plan checks the Windows client against the active
private Gather API. It uses the production window and the existing two pilot
accounts.

## Fixed cases

| Case | Expected result |
| --- | --- |
| `NLP` against `gather-m4-nlp-synthetic.txt` | A bounded preview around the late keyword. Open shows the exact saved text. |
| `cedar` in pilot B | One compact result for the synthetic OCR note with its saved-region citation. |
| Archive-request paraphrases in pilot B | The same OCR note and exact saved version open. |
| `When do leatherback turtles come ashore to lay eggs?` | A successful empty result on pilot A’s nonempty library. |
| Repeat `NLP` after removal | The cached query vector does not restore the deleted source. |
| Indeterminate save and processing eligibility | Keep the original import ID for retry. A live, exhausted, deleted or foreign job never offers an eligible recovery. |

## Local evidence

99 focused backend checks, 83 frontend checks, typecheck, lint and both web and
connected Windows builds passed. A new compact-route regression checks that
two calls sharing a cached vector still read current rankings after deletion.
The real disposable PostgreSQL suites passed 41 assertions across ranking and
ownership, recovery readiness, and final cleanup. Those checks use synthetic
identities and vectors. They establish storage and UI contracts.

The exact connected Windows executable was rebuilt, copied and hash-checked
on D:. SHA-256 `9ad94eb0fc307dd72cc7901e8fb322d00ab9c689381270f94b8d5b3fe8476031`.
Native evidence applies to the current Windows PC.

## Compatible hosted evidence

Cloud Run still serves `gather-library-pilot-sl-opt-7433154` at 100%, with
compact previews and connection reuse. The existing Cedar and paraphrase
results on that revision and exact OCR-version read come from the point 3
comparison. See [hosted search latency](SEARCH_LATENCY.md).

## Windows and hosted results on 17 November 2026

The rebuilt client signed in as pilot A. Both source slots were in use, so the
operator explicitly approved a temporary third slot for the generated 580-byte
text file. The first save received HTTP 429 from the per-instance model-attempt
guard. A database check returned zero new source rows. The Windows client kept
the original import ID and used **Retry same import** after the API went idle.
Supabase showed the selected file published on its first processing attempt.
The native card hid Resume while processing. Local PostgreSQL tests separately
verified eligibility after lease expiry and denial for unauthorized,
active or exhausted jobs. Earlier live processing-retry evidence is in
[processing recovery](PROCESSING_RECOVERY.md).

The native `NLP` results showed one three-line card with visible Open and a
240-character excerpt at offsets 318–558. Open reported the exact published
version, and the full rendered text matched the original fixture after
normalizing line endings. The native sign-out returned to the sign-in screen
and cleared the Library controls and results.

The absent-topic result failed. The turtle question returned the retained
synthetic Markdown note even though the requested information was absent.
Gather completed the authorized cleanup of the new fixture through the owner
interface. Supabase confirmed the source, version, original, job and staged
passages were gone. The replay guard remained and pilot A's quota was restored
to two slots. A repeated `NLP` query was a logged cache hit and returned zero
results. Cloud Run confirmed three successful embeddings for import and the
two fresh queries. Safe receipts and the native preview are under
`output/search-acceptance/`.

## Original release gate

The absent-topic gate was open after the initial run. Hash-verified dense rankings for the
existing synthetic evaluation sets show a strongest absent-query score of
0.6803 and a weakest valid match score of 0.2697. A floor high enough to suppress
all ten saved absent cases would discard 42 of 73 expected source matches from
the dense candidate lists. This is an offline diagnostic of the score floor.
The next relevance check needs independent answerable and absent queries and
a policy that preserves valid paraphrases.

## Hosted corrective retest, 17 November 2026

The tested candidate drops semantic hits with neither a shared content term
nor a strong similarity score. The original turtle query returns empty in a
local replay with the pinned model and the original synthetic text. The saved
answerable-query evaluation retained 64 of 64 expected-source outcomes.
See [search relevance](SEARCH_RELEVANCE.md) for the rule and its quality limits.

After the approved rollout, the Windows client searched pilot A's existing
synthetic collection. The original turtle query showed “Nothing found this
time.” The Orchard backup paraphrase returned only `automatic-pilot.md`, with
“fourteen days” in the excerpt. Both compact requests returned HTTP 200 on
`gather-library-pilot-evidence-70aedd16`, which serves 100% of Gather traffic.
Cloud logs confirmed two successful embeddings. This clears the reported
off-topic acceptance failure. Topic-adjacent checks remain in TASK-005.
