# Authenticated hosted text-flow pilot

Prepared 22 October 2026. The operator created pilot A/B Auth accounts and showed
both quotas as source_limit=2, used=0. Public project key was verified/saved under
ignored output, and public signup was disabled by the operator. This runner is
prepared and control-tested; a successful hosted document flow is NOT yet claimed.

## Run once

```powershell
.\scripts\python.ps1 -m scripts.check_hosted_flow --run
```

Uses the selected Sydney project only, encrypted backend credentials and two hidden
prompts for the existing test-user passwords. It obtains a short-lived Google caller
token with explicit personal account/Gather project flags. It never prints passwords,
session tokens, Google tokens or vectors. No Docker, downloaded weights, public signup,
email, IAM grant or deployment. Existing project Python has tokenizer and psycopg2;
the model-benchmark venv lacks psycopg2. Three pinned tokenizer counts match across
both runtimes, so the project launcher is used without installing dependencies.

Preflight verifies target/public key, stored credentials, closed signup and real Auth
identity for both test emails. One isolated startup/readiness request allows at most
60 seconds to observe a cold model container, within the existing 90-second model
startup guard. This is explicitly separate from unchanged 15-second inference and
five-second DB limits; Cloud Run's own timeout may still reject startup. No automatic
retry. A cold-start failure before admission creates no document.

## Actual test and evidence

1. Submit one fixed synthetic TXT through LibrarySession; repeat its request ID to
   confirm stable source/job/version identity. B cannot see the draft or delete it.
2. Existing coordinator uses the real bounded database driver, pinned tokenizer,
   cloud embeddings, private staging and atomic publication. It must publish ready.
3. Real query embedding -> actual hosted pgvector ranking -> exact-version source
   read. A sees the exact original; B cannot open or search it.
4. A deletes; reads/status/search must immediately hide the source.

Plan two model requests (one passage and one query); hard cap remains three through
the existing BoundedProvider. The two later ownership/deletion searches replay only
the identical real query response in memory, validated through the existing search
coordinator. This proves session/database isolation and visibility, not fresh model
calls for those replays or a general relevance benchmark. No synthetic vector fallback.

The worker wrapper stops before source reads/inference if the global claim returns
an unexpected job. Such a lease expires normally. Run in the dedicated pilot project
without another worker. This is supervised developer execution, not production dispatch.

Safe state is written before import to output/hosted-pilot/receipt.json. It records
request/source/job/version IDs, stages, request/replay counts and outcome only.
An existing receipt blocks reruns. Unacknowledged import marks cleanup outcome as
unknown; the request ID lets the operator investigate an uncertain DB commit. Failures
after acknowledged submission attempt an owner-authorized tombstone. No retry loop.

## Physical cleanup is a separate operator step

Deletion removes visibility and cancels late writes, but the restricted logins cannot
invoke the administrator cleanup finalizer. The receipt retains cleanup_pending=true.
After reviewing the receipt, run the exact source-specific finish_source_cleanup SQL
through the dashboard as administrator. Do not claim original bytes/passages were
removed until that succeeds. Preserve receipt history and clear/rearm it only after
reviewed cleanup; never rerun simply to get a passing result.

Seven new control tests plus six LibrarySession regressions pass (13 total), covering
matching query replay, cancellation, unexpected jobs, failure tombstones, uncertain
submission and startup token/deadline/no-retry behavior. Preview and required frontend
build pass. No real hosted/model test was run by the agent in this milestone because
the operator must provide the hidden user passwords locally. Remaining hosted execution,
physical cleanup, cold-start UX, HTTP application and desktop integration are explicit
gaps. User-deferred rotation of chat-exposed database passwords remains outstanding.
