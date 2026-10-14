"""Embedding model wrapper. Step 2 adds only the tokenizer-based token counter;
the Embedder class arrives in Step 3 (see ARCHITECTURE.md 4.4).
"""
from __future__ import annotations

from typing import Callable


def load_token_counter(cfg: dict) -> Callable[[str], int]:
    """Return count(text) -> number of model tokens (no special tokens).

    Loads only the tokenizer files (~1 MB), not the model weights, so chunking can be
    tested and debugged without the 130 MB model.
    """
    from transformers import AutoTokenizer

    e = cfg["embedding"]
    tok = AutoTokenizer.from_pretrained(e["model_name"], revision=e["model_revision"])
    tok.model_max_length = 10**9  # we split ourselves; silence the 512 warning

    def count(text: str) -> int:
        return len(tok.encode(text, add_special_tokens=False))

    return count
