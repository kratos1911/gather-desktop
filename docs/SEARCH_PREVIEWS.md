# Compact search responses

The new search route returns one excerpt per owned published version with the
exact citation and version ID. Full document text and original images load
through the existing reader only after Open.

The desktop selects `POST /v1/search-previews` after the authenticated library
listing advertises `search_previews_enabled`. Otherwise it uses `/v1/search`.
The compact response uses the `search-previews-v1` version tag and at most five
240-code-point excerpts. A failed compact request is reported without replay.

One Supabase function calls the existing semantic and keyword rankers in a
single database snapshot, clips the ranked passage text, and attaches only page,
paragraph, or OCR region numbers that overlap the clip. The worker retains the
semantic floor, rank fusion and source limit. Published-version and owner checks
apply on both Search and Open. Preview offsets refer to the exact substring.

In the tested compact path, Auth, library preflight, and the combined ranking
are three Supabase requests. The legacy hybrid path uses four plus one full
text read per chosen source and an additional read for each formatted source.
The total excerpt budget drops from 32 KiB to at most 4,800 UTF-8 bytes. These
are request and payload bounds. Hosted latency measurements remain pending.

The local API image and Windows build are verified with synthetic fixtures.
To activate the hosted path after approval, apply only
`202611160001_search_previews.sql`, deploy the reviewed API image with
`GATHER_SEARCH_PREVIEWS=1`, then use the updated Windows candidate. Disabling
the flag and refreshing the library returns the new desktop to the existing
route. The unactivated recruiter quota mode remains a separate rollout.
