# Search latency

`GATHER_SEARCH_TIMING=1` records total backend search time, success or failure,
route and cache outcome. Stage totals cover fresh Auth, database requests,
legacy full-source reads, tokenization, cache read/write, model readiness and
embedding. Numbers are elapsed milliseconds. Network stages include their
transport overhead. The receipt starts in the session handler and excludes
the API queue and response delivery. Unentered stages are absent. There are no
queries, account IDs, document details, tokens or exception messages in receipts.

The Windows Library keeps only its latest local User Timing entries, cleared
when the results view leaves. `gather-search-to-results` runs from submission
through the React commit. `gather-search-render` starts after response validation
and ends at the same commit, before paint. Entries stay in the webview.

`GATHER_SEARCH_HTTP_REUSE=1` allows the Auth and read-only search requests to
reuse an HTTP/1.1 connection to the fixed Supabase origin within a single
search. A disposable helper preserves the verified TLS, five-second per-call
deadline, cancellation and bounded JSON. Every new search verifies Auth again.
An idle connection may close before the next call. Failed calls are never
replayed. Both server flags default off and can be enabled independently.

## Local comparison

15 measured samples per mode following one warm-up per mode, alternating order
on the same Windows host. Auth, listing and preview ranking used the same
synthetic JSON over loopback HTTP. There was no TLS, Redis, SQL, cloud or model
work in this fixture. The p95 uses the nearest-rank sample.

| Mode | HTTP requests | TCP connections | p50 | p95 |
| --- | ---: | ---: | ---: | ---: |
| One helper and connection per call | 3 | 3 | 730 ms | 801 ms |
| Reuse within a search | 3 | 1 | 242 ms | 270 ms |

## Hosted verification on 16 November 2026

Applied `202611160001_search_previews.sql` in Gather Supabase. SQL readback
confirmed execute for authenticated sessions and denial for anonymous users.
Cloud Run rejected an unauthenticated compact search with HTTP 401 on both
revisions. The candidate image passed 75 focused backend tests in an isolated
container. Registry digest `sha256:7cc93f2e08f95586f54a515b526c7bbf45fd77c7ba70853255efaad83f2076e2`.

Both API revisions used the same image, preview route, cache and configuration.
Connection reuse was the only flag changed. The Windows timing client called
the live API sequentially as pilot B. The cached cohort used the same Cedar
query and the same published synthetic OCR note. Receipts pair HTTP response
time with content-free Cloud Run timing entries. Four embeddings succeeded,
all on observed cache misses. All 16 searches succeeded. An explicit Open
returned the same published version and exact cited substring.

| HTTP search measure | Baseline | Reuse enabled |
| --- | ---: | ---: |
| Cached p50, 6 per revision | 4.17 s | 2.52 s |
| Cached sample p95, 6 per revision | 5.23 s | 3.13 s |
| Median database time for cached searches | 2.19 s | 0.54 s |
| Warm misses | 6.75 s (1) | 4.89 and 5.77 s (2) |
| Observed model cold start | 36.63 s (1) | No paired sample |

The cold sample included 29.68 seconds of model readiness and matched one
Cloud Run model-instance startup. Warm misses used different Cedar phrasings.
The six-sample p95 is the sample maximum. The 2-second cached p95 target and
5-second warm-miss p95 target remain unmet in these samples. Hosted timings
end at HTTP response validation on the client and exclude desktop rendering.

`gather-library-pilot-sl-opt-7433154` serves 100% of traffic in Mumbai with
previews, stage timings, connection reuse and the existing cache enabled.
CPU 1, 2 GiB, min 0/max 1, API timeout, credentials and inference settings were
preserved. Route back to `gather-library-pilot-sl-base-7433154` to disable reuse
while keeping previews. Safe receipts are under `output/search-latency/`.
