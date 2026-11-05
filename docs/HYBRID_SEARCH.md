# Hybrid retrieval and search startup

5 November 2026. Migration17 and API00013-7zd are deployed with specific approval.
The rebuilt installed Windows app passed both selected live searches. Local
synthetic evidence and live measurements are separate below.

## Two observed failures

The first `cedar` request timed out at the existing 15-second model-operation
deadline. Logs show that its cold model request completed in 32.63 seconds.
The next request returned HTTP200 in 7.53 seconds but no visible match. The saved
image's published OCR region 3 contains “Cedar”. Raw candidate scores were not
captured, so the score floor alone was not established as the cause.

## Startup before one embedding

Trusted pilot composition now uses the existing automatic-startup function on a
query-vector cache miss, after Auth, metadata and query/token validation. It
permits up to three readiness GETs within one total 60-second deadline. Only
then can the existing provider send one embedding request, retaining its own
15-second deadline and shared three-attempt cap. No embedding retry or warm
instance setting is added. Empty libraries, cache hits and invalid/denied requests
do not prepare the model. Cancellation reaches the startup helper and inference.

Search's application allowance is 90 seconds: startup60 plus its previous30.
The client permits95 seconds for that route only; other operation limits remain.
The approved rollout changed the library Cloud Run request timeout30 to90.
The UI announces search preparation without claiming that a model is always
running. This remains a bounded wait, not an instant-search guarantee. Busy
admission remains single-flight; no new queue is introduced.

## Hybrid matching

The existing vector RPC and calibrated cosine gate remain unchanged. A new
authenticated RPC, search_published_keywords, uses PostgreSQL simple-config
full-text matching over the same owned, live published passages and pinned
model/revision/dimensions. It supports case-insensitive tokens and web-search
query syntax; it is not arbitrary substring search. No query-specific/file-specific
rule, model, extension, index or dependency is added.

The coordinator validates both candidate lists, applies the original relevance
gate to semantic hits, and merges accepted semantic/keyword ranks with reciprocal
rank fusion (RRF, constant60). Exact keyword matches are independent of cosine;
the returned similarity field stays the actual cosine, not a fabricated confidence.
Duplicates are merged and conflicting identities/content fail closed. Ranking
ties are deterministic. Current HTTP limit20 per branch/output remains; at most40
raw candidates fit within the existing100-candidate global ceiling. Existing
five-source, offset/hash/version/citation and context-byte limits remain.

SQL derives the owner from auth.uid(), never request data. Staging, deleted,
foreign, incompatible and superseded publications are excluded. Final exact-version
reads still handle deletion/replacement races; lexical text cannot bypass them.
This adds one bounded database read and does not establish large-library latency
or general retrieval accuracy. Full-text matching can still miss OCR errors.

## Evidence and delivery

- 88 focused backend checks pass on Windows and in the exact Linux image.
- 15 isolated SQL groups cover zero-cosine keyword retention, case/token behavior,
  bounds, ownership, hidden drafts/deletions, replacement and exact citations.
- 81 frontend checks, web build and private Windows executable build pass.
- All these fixtures/vectors are synthetic. No new inference or hosted mutation.
- Image2ad87ce89be798168683314f26e73d9de5281110e5e163cba2112005a805356d
  extends the reviewed40fcacab base with seven Python files only. Packages and
  existing unsuppressed OCR/base-image findings are unchanged. No fresh scan claim.
- Safe receipts and staging manifest: output/search-fixes/.

The SQL fixture initially retained an unpublished processing lease, then had an
ambiguous citation-test column; both harness errors were corrected. An older
token-timeout mock was isolated from unrelated claim parsing. Production guards
were not relaxed.

## Hosted and installed acceptance

Applied the reviewed SQL transaction in Gather's SQL Editor. The hosted check
confirmed function installed, authenticated execute allowed, anonymous denied.
Approved image2ad87ce8 and API timeout90 are live in Mumbai; CPU1/2GiB, min0/max1,
secrets/IAM, model, cache policy and INR500 allowance are unchanged. Installed
binary SHA256 is 67ea9a85ad2cb697971b3d1be3c5414accff69cb451955446e9f67073365d9eb.
Prior executable preserved on D:. A windowless old Gather process needed scoped
cleanup after the approved close; other apps/services were untouched.

Both explicit searches returned only synthetic-note.png with Cedar text and OCR
citations; the unrelated resume was excluded. No source was imported, changed or
deleted. Two real embeddings total, exactly one per search, no retries. Logs show
both readiness GETs completed before their embedding POSTs.

| Selected search | API total | Readiness | Embedding |
| --- | ---: | ---: | ---: |
| `cedar`, cold model | 42.52s | 31.58s | 0.62s |
| Descriptive archive request, warm model | 12.31s | 0.003s | 0.59s |

The native pending message was visually inspected. Cold startup no longer used
the embedding deadline in this run; it remains a real wait. These two different
queries do not establish a speed comparison, p95 or broad quality. Evidence:
live-acceptance.json, migration-verified.png, search-starting.png, cedar-result.png
and semantic-result.png under ignored output/search-fixes/.
