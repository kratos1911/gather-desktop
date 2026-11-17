# Library file previews and originals

Saved cards show two lines from a bounded excerpt included in the existing
paginated list. Search cards reuse their cited excerpt. Clicking either card
displays at most 240 characters already in memory. Opening that preview sends
zero HTTP requests and keeps the original, extracted text and model out of the
preview interaction. A replacement updates the card after it becomes the
published version. Unpublished items keep their processing state.

**Open original** fetches the exact owned version and verifies the returned
bytes against its SHA-256. The Windows client saves a uniquely named copy in
Downloads → Gather and launches the default app for its permitted file type.
The copy carries Windows' Internet zone marker. If a default viewer is
unavailable, Gather tells the user where to find the copy. The user manages
the local copy. **Read saved text** retains the existing in-app reader and
cited page, paragraph or OCR navigation.

The feature is configured with `GATHER_FILE_PREVIEWS=1` after applying
`202611170001_file_previews.sql`. Owned list pages and original reads use fresh
Auth and the same publication and deletion fences as the reader. Opening the
original takes one API request. The API calls Auth and then the original RPC.
The previous API continues to support the preview for existing search results
and the saved-text reader. That compatibility path uses its existing listing.

## Verified rollout on 17 November 2026

The update passed 84 frontend, 51 backend and 31 disposable PostgreSQL checks.
The backend suite also passed in the candidate image. Frontend build, lint,
typecheck and the connected Windows build passed. Wide card and narrow preview
renderings were checked using synthetic data.

Applied the reviewed Supabase migration and verified each function grants
execute to authenticated callers and denies anonymous callers. Cloud Run
revision `gather-library-pilot-preview-8f81438c` serves 100% of Gather traffic.
The previous `gather-library-pilot-evidence-70aedd16` revision is the rollback
target. The desktop shortcut opens the verified Windows candidate.

On Windows, pilot A previewed the existing synthetic `automatic-pilot.md`.
The visible card and dialog used the listing excerpt. Cloud logs show zero
requests during the preview, one explicit original fetch, and zero embeddings.
The original API request took 3.44 seconds in this run. Windows opened the
133-byte copy in VS Code. Its SHA-256 matched the original fixture and its
Internet zone marker was present. Safe evidence is under `output/file-previews/`.
