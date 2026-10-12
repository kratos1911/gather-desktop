"""Load only an operator-supplied, verified local Qwen snapshot on CPU."""

import os
from pathlib import Path


class QwenEngine:
    def __init__(self, snapshot):
        snapshot = Path(snapshot)
        if not snapshot.is_absolute() or not snapshot.is_dir():
            raise ValueError("Local model directory required")
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                          HF_HUB_DISABLE_TELEMETRY="1", TOKENIZERS_PARALLELISM="false")
        import torch
        from transformers import AutoModel, AutoTokenizer
        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True,
                                                       trust_remote_code=False, padding_side="left")
        self.model = AutoModel.from_pretrained(str(snapshot), local_files_only=True,
                                              trust_remote_code=False, use_safetensors=True,
                                              dtype=torch.float32, attn_implementation="sdpa").cpu().eval()

    def count_tokens(self, text):
        return len(self.tokenizer(text, truncation=False, add_special_tokens=True)["input_ids"])

    def embed(self, text):
        tokens = self.tokenizer(text, return_tensors="pt", truncation=False)
        with self.torch.inference_mode():
            return self.model(**tokens, use_cache=False).last_hidden_state[0, -1].float().tolist()
