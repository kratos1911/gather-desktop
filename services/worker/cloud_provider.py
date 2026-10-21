"""Trusted backend composition; tokenizer only, never model weights/downloads."""
import hashlib
import json
from pathlib import Path

from services.inference.runtime import MODEL, REVISION
from services.worker.service_clients import CloudInferenceClient


def pinned_token_counter(snapshot):
    """Read verified tokenizer bytes once, preventing verify/load file races."""
    manifest = json.loads((Path(__file__).parents[1] / 'inference/model-manifest.json').read_text())
    if (manifest['model'], manifest['revision']) != (MODEL, REVISION):
        raise ValueError('tokenizer_identity_mismatch')
    artifact = next(row for row in manifest['artifacts'] if row['file'] == 'tokenizer.json')
    path = Path(snapshot) / 'tokenizer.json'
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('invalid_tokenizer')
    with path.open('rb') as stream:
        raw = stream.read(artifact['bytes'] + 1)
    if len(raw) != artifact['bytes'] or hashlib.sha256(raw).hexdigest() != artifact['sha256']:
        raise ValueError('tokenizer_hash_mismatch')
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_str(raw.decode('utf-8'))
    return lambda text: len(tokenizer.encode(text, add_special_tokens=True).ids)


def cloud_provider(identity, snapshot, *, token_provider=None):
    """Same provider for ingestion and query; cloud metadata identity by default."""
    return CloudInferenceClient(identity, pinned_token_counter(snapshot), token_provider=token_provider)
