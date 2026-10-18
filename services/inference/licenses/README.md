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

## Verified image update

Model attribution now includes the pinned model card (checked against the model
artifact manifest) and official Apache-2.0 text. Five supplements are packaged.
The tokenizers/tokenizers/LICENSE upstream entry is a relative symlink payload
(`../LICENSE`), retained as source evidence; the full root licence is also bundled.
Staging now requires the root tokenizers licence and both model files, so deleting
their provenance directories cannot silently yield a successful package.

notices-candidate contains the verified bundle; see
../../../tests/inference/results/notices-image-20261018.json. Its original nine
layers exactly match startup-candidate. Ten focused tests and frontend build
pass. No real model rerun or new security scan. Complete native dependency licence
coverage remains separate: in particular, upstream Rust dependency attribution
must be reconciled with the compiled tokenizers wheel rather than inferred from
its root Apache licence. OS copyright-file presence likewise is not legal clearance.
