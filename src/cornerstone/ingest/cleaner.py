"""Cleaning: strip repeated headers/footers and page numbers, normalise whitespace.

Symbols are kept: we use NFC (not NFKC), so maths symbols (≤ ∑ ∈ →) survive.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import replace

from cornerstone import Heading, Page

# ligature code points -> plain letters (the visible text is identical, search works)
_LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi",
    "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
}
_INVISIBLE = dict.fromkeys(map(ord, "​‌‍⁠﻿­"))
_PAGE_NUM = re.compile(r"^\s*(page\s+)?\d{1,4}(\s*(of|/)\s*\d{1,4})?\s*$", re.IGNORECASE)
_HYPHEN_BREAK = re.compile(r"(\w)-\n([a-z])")


def normalise_text(text: str) -> str:
    """NFC, ligatures expanded, invisible chars removed, whitespace collapsed. Idempotent."""
    text = unicodedata.normalize("NFC", text)
    for lig, plain in _LIGATURES.items():
        text = text.replace(lig, plain)
    text = text.translate(_INVISIBLE).replace("\xa0", " ").replace("\r", "")
    # private-use glyphs (Wingdings/Symbol bullets) have no meaning outside their font
    text = re.sub("[-]", "", text)
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _key(line: str) -> str:
    """Comparison key: digits and punctuation ignored, so 'MITS-DU' == 'MITS DU', 'Page 3' == 'Page 4'."""
    return re.sub(r"[\W_]+", " ", re.sub(r"\d+", "#", line.lower())).strip()


def _edge_indices(lines: list[str], n: int) -> set[int]:
    """Indices of the first n and last n non-blank lines (where headers/footers live)."""
    idx = [i for i, ln in enumerate(lines) if ln.strip()]
    return set(idx[:n]) | set(idx[-n:])


def _relocate_headings(headings: list[Heading], text: str) -> list[Heading]:
    """Find each heading's line again after lines were removed or merged. Drop it if gone."""
    lines = text.split("\n")
    out, cursor = [], 0
    for h in headings:
        want = re.sub(r"[ \t]+", " ", h.text).strip()
        for i in range(cursor, len(lines)):
            if lines[i] == want:
                out.append(Heading(want, h.level, i))
                cursor = i + 1
                break
    return out


def clean_pages(pages: list[Page], cfg: dict) -> list[Page]:
    """Return cleaned copies of pages. Never drops a page; may change status to empty."""
    ex = cfg["extraction"]
    n_edge = ex["header_footer_lines"]
    paged = [p for p in pages if p.page_no is not None and p.text.strip()]

    # repeated edge lines: count the pages on which each key appears in an edge position
    repeated: set[str] = set()
    if len(paged) >= 3:
        counts: Counter = Counter()
        for p in paged:
            lines = p.text.split("\n")
            keys = {_key(lines[i]) for i in _edge_indices(lines, n_edge)}
            counts.update(k for k in keys if k)
        need = ex["header_footer_min_frac"] * len(paged)
        repeated = {k for k, c in counts.items() if c >= need}

    cleaned: list[Page] = []
    for p in pages:
        if not p.text.strip():
            cleaned.append(replace(p))
            continue
        lines = p.text.split("\n")
        drop = set()
        if p.page_no is not None:  # DOCX sections have no running headers in body text
            for i in _edge_indices(lines, n_edge):
                if _PAGE_NUM.match(lines[i]) or _key(lines[i]) in repeated:
                    drop.add(i)
        text = normalise_text("\n".join(ln for i, ln in enumerate(lines) if i not in drop))
        status, reason = p.status, p.reason
        if status == "ok" and not text:
            status, reason = "empty", "only header/footer/page-number text; nothing left after cleaning"
        cleaned.append(replace(p, text=text, status=status, reason=reason,
                               headings=_relocate_headings(p.headings, text)))
    return cleaned
