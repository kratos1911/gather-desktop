# Bounded search context

15 October 2026. Implemented in services/worker/search_context.py; evaluated with
saved, hash-verified Qwen vectors. No Docker, model calls, downloads or cloud work.
QUERY_SEARCH.md now connects it through an internal coordinator. Synthetic contract
checks pass; live coordinator API checks and desktop wiring remain pending.

## Policy and boundary

`source-neighbors-v1` accepts at most 100 ranked candidates and 100 source
snapshots. Keep the first hit from each source, at most five sources. Reserve
whole seed passages before expansion so earlier neighbors cannot consume later
sources' reserved space. Include at most one immediately preceding and one following
passage, only when their ranges touch or overlap. No second-hop expansion or gap
bridging. Slice the original text once, preserving Unicode-code-point offsets and
source/version/hash citations; overlapping characters appear once.

Each window is limited to 8 KiB UTF-8; all window text totals at most 32 KiB.
Whole neighbors or sources that do not fit are omitted with explicit reasons;
there is no silent clipping. Snapshots are limited to 64 KiB and 256 ordered
passages each. These are reader-context byte limits, not permission to send this
text to the embedding model or a future chat model without its own token check.

Validate every supplied hit and snapshot before returning anything, including
candidates beyond the selected five sources. Reject mixed owners, stale/unknown
versions/passages, duplicate source versions, deleted/unpublished sources, altered
source bytes, malformed Unicode, bad offsets and oversized inputs. Identity and
visibility metadata must come from a trusted, ownership-enforcing repository.
This function does not authenticate a client, implement RLS, or prevent a deletion
race by itself. Integration must fetch/check the active version and deletion state
at read time and enforce authorization before returning context.

## Replay evidence

Fixed policy chosen for known boundary failures; this is a development regression
replay, not blind evaluation. The model, prompts, chunks, labels and cosine ranking
are unchanged. Recompute rankings from saved vectors after checking their recorded
hash, identities, input order and index hashes. Labels are used only for scoring.

| Dataset | Answerable questions | Previous top-five passage union coverage | Assembled context coverage | Maximum output text |
| --- | ---: | ---: | ---: | ---: |
| text-v2 | 56 | 100% | 100% | 8,504 bytes |
| Boundary stress | 8 | 87.5% | 100% | 19,164 bytes |

All three split-condition questions now have their full evidence inside an output
window. Both late facts for boundary-08 are present in separate source windows.
No per-query coverage regressions occurred on these sets. This is more context
per result, not improved embedding accuracy or rank: historical/identifier ranking
weaknesses remain. The original strict passage recall remains 100%/50% respectively.
All ten absent questions still return context; no abstention is implemented.
With only two chunks per long stress source, immediate-neighbor expansion covers
the whole source. This does not establish coverage for arbitrarily long documents.

Nine focused tests pass: exact citations, overlap/gap behavior, one-hop boundary,
source diversity, Unicode/window/total budgets, seed reservation, all-candidate
validation, owner/version/deletion/hash rejection and malformed offsets. Frontend
production build passes; unchanged model/UI/native suites were not rerun.
Evidence: tests/evaluation/results/search-context-20261015.json.

```powershell
.\output\model-benchmark\venv\Scripts\python.exe -m unittest discover -s tests/worker -p test_search_context.py -v
.\output\model-benchmark\venv\Scripts\python.exe -m scripts.evaluate_search_context
```

Next: backend TXT/Markdown import/index/search/open/delete coordination, with
trusted repository snapshots and ownership/retry/deletion gates. Keep this policy
versioned; independent/larger-library validation remains necessary before release.
