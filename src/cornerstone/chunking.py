"""Chunking. Two modes (chunking.mode, ARCHITECTURE.md 4.3 and 10.4):

slide (PDF pages): one chunk per slide, so a citation points at exactly one page.
  slide -> title (a short heading in its first lines, else the previous slide's title)
  -> one piece, or windows inside the page if it is too long -> fragments merged into the next slide.
section (DOCX, or mode=section): Stage 1 behaviour.
  pages -> paragraph units tagged with a section heading -> sections
  -> sections over target_tokens are split into overlapping windows
  -> fragments under min_tokens are merged into a neighbour.
Both modes set a context header "<file stem> > <section>" that is embedded together with the text
(embedding_text), so a slide that only says "Advantages: ..." still carries what it is about.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cornerstone import Chunk, Page

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_BULLET_START = re.compile(r"^[\W\d]")   # bullets, arrows, numbers: body text, not a slide title


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


def context_header(file_name: str, section: str | None) -> str:
    """'Unit 4_Storage management.pdf', 'SCAN' -> 'Unit 4_Storage management > SCAN' (stem only if no section)."""
    stem = Path(file_name).stem
    return f"{stem} > {section}" if section else stem


def embedding_text(chunk: Chunk) -> str:
    """What is embedded (and later reranked): the context header line, then the chunk text."""
    return f"{chunk.context_header}\n{chunk.text}" if chunk.context_header else chunk.text


def slide_title(page: Page, c: dict) -> str | None:
    """The slide's title: its first heading if it sits in the first slide_title_lines lines, is at most
    slide_title_max_chars long and does not start like a bullet/number; else None (caller carries the
    previous title). Large-font decks mark body lines as headings; these rules keep them out."""
    for h in page.headings:
        if h.line_no >= c["slide_title_lines"]:
            break
        t = h.text.strip()
        if t and len(t) <= c["slide_title_max_chars"] and not _BULLET_START.match(t):
            return t
    return None


def _slide_pieces(pages: list[Page], file_name: str, c: dict, count: Callable[[str], int]) -> list[_Piece]:
    """One piece per ok slide; a slide too long for slide_max_tokens is windowed inside its page."""
    pieces: list[_Piece] = []
    title: str | None = None
    for page in pages:
        if page.status != "ok":
            continue
        title = slide_title(page, c) or title
        budget = c["slide_max_tokens"] - count(context_header(file_name, title))
        units = [u for _, u in _paragraph_units(page, title)]
        if not units:
            continue
        piece = _piece(units, title, count)
        if piece.tokens <= budget:
            pieces.append(piece)
        else:
            pieces.extend(_windows(units, title, {**c, "target_tokens": budget}, count))
    return pieces


def _merge_tiny_slides(pieces: list[_Piece], c: dict, count: Callable[[str], int]) -> list[_Piece]:
    """A near-empty slide (< slide_min_tokens, e.g. a lone title or a picture caption) joins the NEXT piece,
    but only if that piece starts on the very next page and the result stays within slide_max_tokens.
    Otherwise it stays a chunk of its own (its context header still says what it is). Never merges
    backwards, so a chunk's page range never jumps over removed or flagged pages."""
    out: list[_Piece] = []
    carry: _Piece | None = None
    for p in pieces:
        if carry is not None:
            if p.pages and carry.pages and p.pages[0] == carry.pages[-1] + 1:
                text = carry.text + "\n" + p.text
                if count(text) <= c["slide_max_tokens"]:
                    p = _Piece(text, count(text), p.heading or carry.heading, carry.pages + p.pages, None, None)
                else:
                    out.append(carry)
            else:
                out.append(carry)
            carry = None
        if p.tokens < c["slide_min_tokens"]:
            carry = p
        else:
            out.append(p)
    if carry is not None:
        out.append(carry)
    return out


def chunk_pages(pages: list[Page], doc_id: int, file_name: str, cfg: dict,
                count_tokens: Callable[[str], int]) -> list[Chunk]:
    """Turn cleaned pages into Chunks (chunk_id=0 until the store assigns real ids).

    Only pages with status "ok" are chunked. Nothing is truncated: long slides/sections are split
    into windows with overlap, over-long sentences are split by words. Slide mode is used for pages
    with page numbers (PDF) when chunking.mode == "slide"; DOCX always uses section mode.
    token_count counts embedding_text (header + text).
    """
    c = cfg["chunking"]
    if c["mode"] == "slide" and pages and all(p.page_no is not None for p in pages):
        merged = _merge_tiny_slides(_slide_pieces(pages, file_name, c, count_tokens), c, count_tokens)
        return _to_chunks(merged, doc_id, file_name, count_tokens)
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

    return _to_chunks(_merge_small(pieces, c, count_tokens), doc_id, file_name, count_tokens)


def _to_chunks(pieces: list[_Piece], doc_id: int, file_name: str, count: Callable[[str], int]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for i, p in enumerate(pieces):
        ch = Chunk(
            chunk_id=0, doc_id=doc_id, file_name=file_name,
            page_start=min(p.pages) if p.pages else None,
            page_end=max(p.pages) if p.pages else None,
            para_start=p.para_start, para_end=p.para_end,
            section_heading=p.heading, chunk_index=i,
            token_count=0, text=p.text, context_header=context_header(file_name, p.heading),
        )
        ch.token_count = count(embedding_text(ch))
        chunks.append(ch)
    return chunks
