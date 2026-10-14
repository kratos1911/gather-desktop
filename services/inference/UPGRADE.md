# CPU dependency upgrade and token-aware chunks

14 October 2026. Candidate image:
`sha256:5d84bdf24729cacb20389734baee56fd49293eeb1bd2053d5eac1d0259c04f95`.
The previous cpu-local image is retained. Use `--candidate` with the verification
launcher to select cpu-patched; candidate evidence is written separately.

## Changes

- Torch 2.8.0+cpu -> 2.14.1+cpu, from the official CPU wheel index.
- Transformers 4.57.6 -> 5.19.0. Its downloaded wheel SHA-256 matches the
  [PyPI publisher checksum](https://pypi.org/project/transformers/5.19.0/):
  `afcd2dd5f603ed28c1e1fcb00a338ccbb4ef5f878ed289635df8b58187afb518`.
- 34 Linux distributions pinned with wheel hashes; installed dependency
  consistency passes. The Windows benchmark environment is unchanged.
- OpenSSL/libssl/provider pinned to Debian 3.5.7-1~deb13u3; PCRE2 to
  10.46-1~deb13u3. Build output confirms all four OS packages upgraded.
- Build context/wheels/model exports remain on D:. No credentials or personal
  files mounted, no modifications to existing API containers or Docker settings.

## Chunking contract

`services/inference/chunking.py` adds a server-side preparation function using
the pinned model's document token-count callback. Each slice is at most 512
tokens including special tokens and 8 KiB UTF-8. Send one slice per embedding
request. Prefer paragraph/line/space boundaries, with up to 64 characters overlap.
IDs include source hash, model revision, chunker version and exact source offsets.
Offsets use Unicode code points; text is sliced without decoding token fragments.
Every emitted slice is rechecked, and the slices cover the source without gaps.

Input is bounded to 64 KiB and output to 256 slices. Invalid tokenizer counts,
unrepresentable characters, oversized sources and all-whitespace slices fail
explicitly; no partial list or silent truncation is returned. The callback is
trusted server code, never provided by an end user. The algorithm finds a fitting
prefix; it does not assume token counts are strictly monotonic or claim maximal
packing. Existing parser chunks/index versions and runtime limits are unchanged.

This is a prepared ingestion component, not yet wired into the desktop/coordinator.
Changing published source chunks still needs explicit versioning/reindexing at
integration time. Retrieval quality on the new chunk boundaries is not yet proven.

## Verification gates

25 focused control/chunking/reporting tests pass on Windows and in the candidate
Linux image; frontend build passes. A six-case baseline embedding export is
available. The candidate comparison checks exact token counts, cosine >=0.99999,
maximum per-coordinate difference <=0.0001 and unchanged three-document rankings.
The chunk profile embeds five source slices individually and verifies their
actual model token counts remain <=512. These are synthetic compatibility and
latency checks, not full retrieval benchmarks or public deployment approval.

15 October real-model checkpoint: both profiles pass on the exact candidate image.
Six compatibility cases retain identical token counts and all three tested ranks;
minimum paired cosine 0.999999999996, maximum coordinate difference 4.33e-7.
Requests took 0.613–0.791 s; startup 18.348 s. Five chunks contain 495, 494, 380,
500 and 306 tokens, completing in 5.883, 4.569, 4.127, 4.591 and 3.053 s;
startup 14.374 s. Peak cgroup memory was 4,241,444,864 bytes for compatibility and
4,240,633,856 bytes for chunks (both about 3.95 GiB). Both exited zero without OOM.
All vectors passed finite, normalized, 512-dimensional checks. Test containers
were removed. Evidence: tests/inference/results/patched-{compatibility,comparison,
chunks}-20261015.json; raw synthetic vectors stay ignored.

The 4 GiB host guard, 15 s deadline and 5 GiB container ceiling were unchanged.
Approved one-time Linux clean-page-cache release was needed before each profile;
Windows reclaimed memory with a delay. No persistent Docker setting changes or
API stops. These shared-machine fixtures do not establish production capacity or
retrieval quality with new chunk boundaries. Next: evaluate that retrieval quality
before ingestion integration; keep promotion/security/licence gates open.

The 14 October rescan completed: 172 packages indexed; 28 findings across 13
vulnerable packages (1 high, 1 medium, 26 low), down from 56 (12 high). No Python
package findings remain in this scan. High zlib CVE-2026-85091 and medium tar
CVE-2025-45582 have no fixed version listed and remain open; no findings were
suppressed. Evidence: tests/inference/results/patched-image-scan-20261014.json.
The report completed despite a locked temporary-archive cleanup warning. No
Docker restart or cache deletion was performed. Deployment remains gated.
