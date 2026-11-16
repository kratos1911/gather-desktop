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

## Hosted verification pending

After the compact route is approved and active, compare the same version with
reuse off and on, using the same synthetic corpus and query set. Report p50/p95
and failure counts for cache hits, warm cache misses, and cold startup separately.
Pair API receipts with the desktop submit-to-results measurements. Proposed p95
targets are 2 seconds for cache hits and 5 seconds for warm misses. Collect live
measurements before claiming either target. Cold model or API startup has its
own distribution. Set the reuse flag to `0` to restore the per-call helper.
