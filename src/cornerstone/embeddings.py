"""Embedding model wrapper: batching, L2 normalisation, query prefix (ARCHITECTURE.md 4.4)."""
from __future__ import annotations

from typing import Callable

import numpy as np

from cornerstone import EmptyQuery


class Embedder:
    """Sentence embedder (BAAI/bge-small-en-v1.5 by default), CPU only.

    - Passages are embedded as-is (no prefix).
    - Queries get the model's query prefix, because bge was trained so that a short question
      is matched to a longer passage with that instruction in front of the question.
    - Output vectors have unit length, so inner product == cosine similarity.
    """

    def __init__(self, cfg: dict) -> None:
        from sentence_transformers import SentenceTransformer

        e = cfg["embedding"]
        self.dim: int = e["dimension"]
        self.batch_size: int = e["batch_size"]
        self.query_prefix: str = e["query_prefix"]
        self.passage_prefix: str = e["passage_prefix"]
        self.max_query_chars: int = cfg["search"]["max_query_chars"]
        self.model = SentenceTransformer(e["model_name"], revision=e["model_revision"], device="cpu")
        self.model.max_seq_length = e["max_seq_length"]
        self.model.tokenizer.model_max_length = 10**9  # count_tokens() sees whole sections; chunker splits them
        actual = self.model.get_embedding_dimension()
        if actual != self.dim:
            raise ValueError(f"config says dimension {self.dim} but model produces {actual}")

    def _encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        vecs = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)
        return vecs.astype(np.float32, copy=False)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        """(n, dim) float32, L2-normalised. Raises ValueError on an empty/blank passage."""
        for i, t in enumerate(texts):
            if not t or not t.strip():
                raise ValueError(f"passage {i} is empty; refusing to embed an empty string")
        return self._encode([self.passage_prefix + t for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        """(dim,) float32, L2-normalised, with the query prefix. Raises EmptyQuery if blank."""
        if not text or not text.strip():
            raise EmptyQuery("query is empty or whitespace-only")
        text = text.strip()[: self.max_query_chars]
        return self._encode([self.query_prefix + text])[0]

    def count_tokens(self, text: str) -> int:
        """Number of model tokens in text (no special tokens)."""
        return len(self.model.tokenizer.encode(text, add_special_tokens=False))


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
