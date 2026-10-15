"""Cross-encoder reranker over search candidates (ARCHITECTURE.md 10.7).

A bi-encoder (the embedder) scores query and passage separately and compares two vectors. A cross-encoder
reads the query and the passage together in one transformer pass, so it can see which words of the
question the passage actually answers. It is too slow to run on every chunk, so it only reorders the
~30 candidates that the fast retrievers already found.
"""
from __future__ import annotations

from dataclasses import replace

from cornerstone import RerankerUnavailable, SearchResult
from cornerstone.chunking import embedding_text


class Reranker:
    """Wraps sentence-transformers CrossEncoder (cross-encoder/ms-marco-MiniLM-L-6-v2 by default), CPU only."""

    def __init__(self, cfg: dict) -> None:
        r = cfg["rerank"]
        self.model_name: str = r["model_name"]
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(r["model_name"], revision=r["model_revision"], device="cpu",
                                      max_length=r["max_length"])
        except Exception as e:  # offline, not cached, unknown revision: never fall back silently
            raise RerankerUnavailable(
                f"reranker model {r['model_name']}@{r['model_revision'][:8]} could not be loaded ({e}). "
                "Connect once to download it, or set retrieval.rerank: false in config.yaml.") from e

    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        """Reorder results by cross-encoder score; return the best top_k with ranks 1..n.

        The query is the raw question (no bge prefix). Each passage is the context header + slide text,
        the same text that was embedded. ``score`` becomes the reranker score (a logit: higher = more
        relevant, not bounded); earlier stage scores stay in ``scores``. Ties keep the earlier order.
        """
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not results:
            return []
        logits = self.model.predict([(query.strip(), embedding_text(r.chunk)) for r in results],
                                    show_progress_bar=False)
        order = sorted(range(len(results)), key=lambda i: (-float(logits[i]), i))
        out = []
        for i in order[:top_k]:
            r = results[i]
            out.append(replace(r, score=float(logits[i]), rank=len(out) + 1,
                               scores={**r.scores, "rerank": float(logits[i])}))
        return out


def load_reranker(cfg: dict) -> Reranker | None:
    """The reranker search() needs under this config: a Reranker if retrieval.rerank is on, else None."""
    return Reranker(cfg) if cfg["retrieval"].get("rerank") else None
