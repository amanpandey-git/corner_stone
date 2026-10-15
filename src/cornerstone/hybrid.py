"""Keyword search (SQLite FTS5, BM25) and Reciprocal Rank Fusion (ARCHITECTURE.md 10.6).

Vector search finds slides that MEAN the same as the question; keyword search finds slides that
contain the exact rare words ("C-LOOK", "setuid", "642"). RRF merges the two ranked lists using only
ranks, so the two very different score scales never have to be compared.
"""
from __future__ import annotations

import re

from cornerstone import SearchFilters
from cornerstone.index.metadata_store import MetadataStore

_TOKEN = re.compile(r"\w+")
# Question words that match almost every slide; BM25 would down-weight them anyway, removing them keeps
# the FTS query short. A fixed list, not tuned on the evaluation questions.
_STOPWORDS = frozenset("""a an and are as at be by can do does for from how in is it its of on or so than that the
their them these this to was were what when where which who why will with""".split())


def fts_query(query: str) -> str:
    """Build a safe FTS5 query: each word token double-quoted, joined with OR; '' if there are none.

    Quoting every token means FTS5 operators or punctuation in a question (AND, NEAR, *, ", -) are
    treated as plain words and can never raise a syntax error.
    """
    seen: list[str] = []
    for t in _TOKEN.findall(query.lower()):
        if t not in _STOPWORDS and t not in seen:
            seen.append(t)
    return " OR ".join(f'"{t}"' for t in seen)


def keyword_search(query: str, k: int, store: MetadataStore,
                   filters: SearchFilters | None = None) -> list[tuple[int, float]]:
    """[(chunk_id, score)] best first, active chunks only; score = -bm25 (higher is better).

    Empty/stopword-only query -> []. Filters restrict to doc_ids and/or units (both may be given).
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    q = fts_query(query)
    if not q:
        return []
    sql = ("SELECT c.chunk_id, -bm25(chunks_fts) AS score FROM chunks_fts "
           "JOIN chunks c ON c.chunk_id = chunks_fts.rowid JOIN documents d ON d.doc_id = c.doc_id "
           "WHERE chunks_fts MATCH ? AND c.status = 'active'")
    args: list = [q]
    if filters and filters.doc_ids is not None:
        sql += f" AND d.doc_id IN ({','.join('?' * len(filters.doc_ids))})"
        args += list(filters.doc_ids)
    if filters and filters.units is not None:
        sql += f" AND d.unit IN ({','.join('?' * len(filters.units))})"
        args += list(filters.units)
    sql += " ORDER BY bm25(chunks_fts) LIMIT ?"
    args.append(k)
    return [(int(r[0]), float(r[1])) for r in store.conn.execute(sql, args)]


def rrf_merge(rankings: list[list[int]], k_rrf: int = 60) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: merge several ranked lists of chunk_ids into one, using ranks only.

    rankings: ranked lists, best first, each id at most once per list (e.g. [vector_ids, keyword_ids]).
    Returns [(chunk_id, score)] sorted best first, where

        score(d) = sum over the rankings that contain d of  1 / (k_rrf + rank_of_d_in_that_ranking)

    with rank starting at 1. Ties: better best-single-rank first, then smaller chunk_id (deterministic).
    An empty input (or only empty lists) returns [].
    """
    scores: dict[int, float] = {}
    best: dict[int, int] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k_rrf + rank)
            best[cid] = min(best.get(cid, rank), rank)
    return sorted(scores.items(), key=lambda item: (-item[1], best[item[0]], item[0]))
