"""Structure-aware chunking: sections first, then token windows with overlap.

Pipeline inside chunk_pages():
  pages -> paragraph units tagged with a section heading -> sections
  -> sections over target_tokens are split into overlapping windows
  -> fragments under min_tokens are merged into a neighbour.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from cornerstone import Chunk, Page

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass
class _Unit:
    """A paragraph (or sentence, or word group) with its location."""

    text: str
    page_no: int | None
    para_start: int | None
    para_end: int | None


@dataclass
class _Piece:
    """A chunk-to-be before final ids and token count are assigned."""

    text: str
    tokens: int
    heading: str | None
    pages: list[int]
    para_start: int | None
    para_end: int | None


def _paragraph_units(page: Page, heading: str | None) -> list[tuple[str | None, _Unit]]:
    """Split one page into (section_heading, unit) pairs.

    A heading line starts a new section and is kept as the first line of its text, so the
    heading words are embedded together with the content they introduce.
    """
    heading_lines = {h.line_no: h.text for h in page.headings}
    out: list[tuple[str | None, _Unit]] = []
    buf: list[str] = []

    def flush(h: str | None) -> None:
        if buf:
            out.append((h, _Unit(" ".join(buf), page.page_no, page.para_start, page.para_end)))
            buf.clear()

    for n, line in enumerate(page.text.split("\n")):
        if n in heading_lines:
            flush(heading)
            heading = heading_lines[n]
        if not line.strip():
            flush(heading)
            continue
        buf.append(line.strip())
        if n in heading_lines:  # a heading is its own paragraph unit
            flush(heading)
    flush(heading)
    return out


def _split_to_atoms(unit: _Unit, limit: int, count: Callable[[str], int]) -> list[_Unit]:
    """Break a unit larger than ``limit`` tokens: by sentence first, then by words."""
    if count(unit.text) <= limit:
        return [unit]
    atoms: list[_Unit] = []
    for sent in _SENTENCE_END.split(unit.text):
        if not sent.strip():
            continue
        if count(sent) <= limit:
            atoms.append(_Unit(sent, unit.page_no, unit.para_start, unit.para_end))
            continue
        words, cur = sent.split(), []
        for w in words:
            cur.append(w)
            if count(" ".join(cur)) > limit and len(cur) > 1:
                cur.pop()
                atoms.append(_Unit(" ".join(cur), unit.page_no, unit.para_start, unit.para_end))
                cur = [w]
        if cur:
            atoms.append(_Unit(" ".join(cur), unit.page_no, unit.para_start, unit.para_end))
    return atoms


def _piece(units: list[_Unit], heading: str | None, count: Callable[[str], int]) -> _Piece:
    text = "\n".join(u.text for u in units)
    pages = [u.page_no for u in units if u.page_no is not None]
    starts = [u.para_start for u in units if u.para_start is not None]
    ends = [u.para_end for u in units if u.para_end is not None]
    return _Piece(text, count(text), heading, pages,
                  min(starts) if starts else None, max(ends) if ends else None)


def _windows(units: list[_Unit], heading: str | None, c: dict, count: Callable[[str], int]) -> list[_Piece]:
    """Pack atoms into windows of about target_tokens, each window re-using the tail of the last."""
    target, overlap, hard = c["target_tokens"], c["overlap_tokens"], c["hard_max_tokens"]
    atoms = [a for u in units for a in _split_to_atoms(u, min(target, hard), count)]
    sizes = [count(a.text) for a in atoms]
    pieces: list[_Piece] = []
    start = 0
    must_reach = 1  # every window must consume at least one atom beyond the previous window
    while start < len(atoms):
        end, total = start, 0
        while end < len(atoms) and (end < must_reach or total + sizes[end] <= target):
            total += sizes[end]
            end += 1
        pieces.append(_piece(atoms[start:end], heading, count))
        if end >= len(atoms):
            break
        # step back from `end` while the repeated tail stays within the overlap budget
        back, kept = end, 0
        while back > start + 1 and kept + sizes[back - 1] <= overlap:
            back -= 1
            kept += sizes[back]
        must_reach = end + 1
        if back < end:
            start = back
            continue
        # the last atom alone is bigger than the overlap budget: repeat its last words instead
        last, tail = atoms[end - 1], []
        for w in reversed(last.text.split()):
            if count(" ".join([w] + tail)) > overlap:
                break
            tail.insert(0, w)
        if tail:
            atoms.insert(end, _Unit(" ".join(tail), last.page_no, last.para_start, last.para_end))
            sizes.insert(end, count(atoms[end].text))
            must_reach = end + 2  # the tail plus the next real atom
        start = end
    return pieces


def _merge_small(pieces: list[_Piece], c: dict, count: Callable[[str], int]) -> list[_Piece]:
    """Merge fragments under min_tokens into the next piece (or the previous if last)."""
    min_t, hard = c["min_tokens"], c["hard_max_tokens"]

    def join(a: _Piece, b: _Piece) -> _Piece:
        text = a.text + "\n" + b.text
        starts = [x for x in (a.para_start, b.para_start) if x is not None]
        ends = [x for x in (a.para_end, b.para_end) if x is not None]
        return _Piece(text, count(text), a.heading or b.heading, a.pages + b.pages,
                      min(starts) if starts else None, max(ends) if ends else None)

    out: list[_Piece] = []
    carry: _Piece | None = None
    for p in pieces:
        if carry is not None:
            merged = join(carry, p)
            if merged.tokens <= hard:
                p, carry = merged, None
            else:  # cannot merge forward without breaking the hard limit: keep both
                out.append(carry)
                carry = None
        if p.tokens < min_t:
            carry = p
        else:
            out.append(p)
    if carry is not None:
        if out and join(out[-1], carry).tokens <= hard:
            out[-1] = join(out[-1], carry)
        else:
            out.append(carry)
    return out


def chunk_pages(pages: list[Page], doc_id: int, file_name: str, cfg: dict,
                count_tokens: Callable[[str], int]) -> list[Chunk]:
    """Turn cleaned pages into Chunks (chunk_id=0 until the store assigns real ids).

    Only pages with status "ok" are chunked. Nothing is truncated: long sections are split
    into windows with overlap, over-long sentences are split by words.
    """
    c = cfg["chunking"]
    heading: str | None = None
    sections: list[tuple[str | None, list[_Unit]]] = []
    for page in pages:
        if page.status != "ok":
            continue
        for h, unit in _paragraph_units(page, heading):
            if not sections or sections[-1][0] != h:  # heading changed -> new section
                sections.append((h, []))
            sections[-1][1].append(unit)
            heading = h

    pieces: list[_Piece] = []
    for h, units in sections:
        total = count_tokens("\n".join(u.text for u in units))
        if total <= c["target_tokens"]:
            pieces.append(_piece(units, h, count_tokens))
        else:
            pieces.extend(_windows(units, h, c, count_tokens))

    chunks: list[Chunk] = []
    for i, p in enumerate(_merge_small(pieces, c, count_tokens)):
        chunks.append(Chunk(
            chunk_id=0, doc_id=doc_id, file_name=file_name,
            page_start=min(p.pages) if p.pages else None,
            page_end=max(p.pages) if p.pages else None,
            para_start=p.para_start, para_end=p.para_end,
            section_heading=p.heading, chunk_index=i,
            token_count=p.tokens, text=p.text,
        ))
    return chunks
