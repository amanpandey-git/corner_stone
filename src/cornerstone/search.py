"""Query -> top-k active chunks with full metadata. No LLM.

Stages (ARCHITECTURE.md 10.8), each switched in config `retrieval.*`:
  vector candidates -> [collapse near-identical results] -> first k.
With every switch off this is exactly the Stage 1 search (the ablation baseline).
"""
from __future__ import annotations

from dataclasses import replace

from cornerstone import SearchFilters, SearchResult
from cornerstone.dedup import collapse_results
from cornerstone.embeddings import Embedder
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore

_OVERFETCH = 3  # first look at 3k candidates, doubling while soft-deleted ones crowd out live ones


def _snippet(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[:limit].rstrip() + "..."


def search(query: str, k: int, cfg: dict, store: MetadataStore, index: HNSWIndex, embedder: Embedder,
           ef_search: int | None = None, filters: SearchFilters | None = None) -> list[SearchResult]:
    """Return up to k results, best first. Deleted/replaced/pending chunks never appear.

    Raises EmptyQuery for a blank query (checked even when the index is empty) and ValueError
    for k < 1. An empty index, or one whose hits are all deleted, returns []. ``filters`` restricts
    results to some documents and/or units; a filter that matches no active document returns [].
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    q = embedder.embed_query(query)            # raises EmptyQuery
    n = len(index)
    if n == 0:
        return []
    allowed = store.allowed_doc_ids(filters)
    if allowed is not None and not allowed:
        return []
    r = cfg["retrieval"]
    staged = r["collapse"]
    want = max(k, r["candidates"]) if staged else k   # later stages need more than k candidates
    results = _vector_candidates(q, want, cfg, store, index, ef_search, allowed)
    if r["collapse"]:
        results = collapse_results(results, cfg)
    return [replace(x, rank=i + 1) for i, x in enumerate(results[:k])]


def _vector_candidates(q, k: int, cfg: dict, store: MetadataStore, index: HNSWIndex,
                       ef_search: int | None, allowed: set[int] | None = None) -> list[SearchResult]:
    """Up to k live (active) chunks nearest to the query vector, best first, from allowed docs only."""
    n = len(index)

    # HNSW cannot delete, so some of the nearest vectors may belong to retired chunks.
    # Fetch more than k, keep only active ones (SQLite decides), widen until k are found or
    # the whole index has been looked at.
    fetch = min(k * _OVERFETCH, n)
    while True:
        labels, scores = index.search(q, fetch, ef_search)
        live = store.get_chunks(labels.tolist())
        hits = [(int(lab), float(s)) for lab, s in zip(labels, scores)
                if int(lab) in live and (allowed is None or live[int(lab)].doc_id in allowed)]
        if len(hits) >= k or fetch >= n:
            break
        fetch = min(fetch * 2, n)

    limit = cfg["search"]["snippet_chars"]
    return [SearchResult(chunk=live[lab], score=s, rank=i + 1, snippet=_snippet(live[lab].text, limit),
                         scores={"vector": s})
            for i, (lab, s) in enumerate(hits[:k])]
