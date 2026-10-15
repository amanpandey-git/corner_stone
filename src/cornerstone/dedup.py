"""Near-duplicate detection (ARCHITECTURE.md 10.2).

Some slide decks contain their own slides twice (the Unit 4 PDF repeats slides 2-26 as 27-51). Indexing both
copies wastes half of the top-k results on identical hits, so a later page that is a near-copy of an earlier
page in the same document is marked 'duplicate' and not indexed. Its page number and the page it copies are
recorded, so nothing disappears silently.

Similarity = Jaccard overlap of word 3-shingles: |A & B| / |A | B|, where A and B are the sets of
three-word sequences of each page. Digits are kept, so worked examples that differ only in their numbers
(FCFS / SSTF / SCAN seek-time slides) are not merged.
"""
from __future__ import annotations

import re
from dataclasses import replace

from cornerstone import Page, SearchResult

_WORD = re.compile(r"\w+")


def page_signature(text: str) -> set[str]:
    """Word 3-shingles of the lower-cased text; texts shorter than 3 words give one shingle of all words."""
    words = _WORD.findall(text.lower())
    if len(words) < 3:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}


def jaccard(a: set[str], b: set[str]) -> float:
    """|a & b| / |a | b|; two empty sets are not similar (0.0)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_duplicate_pages(pages: list[Page], cfg: dict) -> dict[int, int]:
    """{page_no: earlier page_no it duplicates} for pages of ONE document.

    Only 'ok' PDF pages (page_no set) with at least dedup.min_chars characters take part, on either side:
    short title/picture slides share their few words but differ in their images. A page is matched to the
    EARLIEST earlier original (never to another duplicate) whose Jaccard >= dedup.page_jaccard.
    """
    d = cfg["dedup"]
    min_chars, threshold = d["min_chars"], d["page_jaccard"]
    originals: list[tuple[int, set[str]]] = []   # (page_no, signature), in page order
    dups: dict[int, int] = {}
    for p in pages:
        if p.status != "ok" or p.page_no is None or len(p.text.strip()) < min_chars:
            continue
        sig = page_signature(p.text)
        match = next((no for no, s in originals if jaccard(sig, s) >= threshold), None)
        if match is None:
            originals.append((p.page_no, sig))
        else:
            dups[p.page_no] = match
    return dups


def mark_duplicates(pages: list[Page], cfg: dict) -> list[Page]:
    """Set status='duplicate', duplicate_of and a reason on near-duplicate pages (in place); returns pages."""
    dups = find_duplicate_pages(pages, cfg)
    for p in pages:
        if p.page_no in dups:
            p.status, p.duplicate_of = "duplicate", dups[p.page_no]
            p.reason = f"near-duplicate of p.{dups[p.page_no]}"
    return pages


def collapse_results(results: list[SearchResult], cfg: dict) -> list[SearchResult]:
    """Drop results whose text is a near-copy (Jaccard >= dedup.result_jaccard) of a higher-ranked kept
    result, across documents too (ARCHITECTURE.md 10.3). The kept result lists the dropped location in
    also_on as (file, page_start). Ranks are renumbered 1..n; the order is otherwise unchanged."""
    threshold = cfg["dedup"]["result_jaccard"]
    kept: list[tuple[SearchResult, set[str]]] = []
    for r in results:
        sig = page_signature(r.chunk.text)
        twin = next((k for k, s in kept if jaccard(sig, s) >= threshold), None)
        if twin is None:
            kept.append((replace(r, also_on=list(r.also_on)), sig))
        else:
            twin.also_on.append((r.chunk.file_name, r.chunk.page_start))
    return [replace(k, rank=i + 1) for i, (k, _) in enumerate(kept)]
