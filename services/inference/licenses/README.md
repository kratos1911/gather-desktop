# Serving notice provenance

18 October 2026. tokenizers 0.23.3 upstream licence files are retained verbatim.
provenance.json records the resolved upstream tree, source URLs and SHA-256s.
The release tag contains root, Rust and Node binding LICENSE files and no file
named NOTICE/NOTICE.txt in the complete tree response. Including all three
licences conservatively preserves their text; it is not a native dependency audit.

scripts/inference_notices.py collects licence/notice/copying files from every
hash-locked wheel without extracting archive paths. Supplemental files must
match their recorded hashes. Staging fails on missing/changed wheels or notices.
The Dockerfile now copies third-party-notices.json into /app. Existing images
are unchanged until rebuilt. OS copyright files remain in the base filesystem.

Verified local staging: 47 wheels, 177 embedded notices and 3 upstream licence
supplements, 726876 bytes. This closes the missing upstream tokenizers licence
file gap. Bundled Rust/native dependency and model attribution review remain
open; filename discovery is not proof of all transitive licence obligations.

Sources: https://github.com/huggingface/tokenizers/tree/v0.23.3 and the immutable
URLs in tokenizers-0.23.3/provenance.json. No credentials or models downloaded.
