"""DOCX extraction with python-docx.

DOCX has no fixed pages, so page_no is always None. Each heading starts a new Page
("section") that records its paragraph range instead.
"""
from __future__ import annotations

import re
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from cornerstone import CorruptFile, EmptyFile, Heading, Page, PasswordProtected

_OLE_MAGIC = b"\xd0\xcf\x11\xe0"  # encrypted .docx is an OLE container, not a zip


def _heading_level(par: Paragraph) -> int | None:
    """1.. for 'Heading N' / 'Title' styles, None for body text."""
    name = (par.style.name or "") if par.style is not None else ""
    if name == "Title":
        return 1
    m = re.fullmatch(r"Heading (\d+)", name)
    return int(m.group(1)) if m else None


def _blocks(document) -> list[tuple[str, int | None]]:
    """Body content in document order as (text, heading_level). Tables become 'a | b' lines."""
    out: list[tuple[str, int | None]] = []
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            par = Paragraph(child, document)
            out.append((par.text.strip(), _heading_level(par)))
        elif tag == "tbl":
            for row in Table(child, document).rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                out.append((" | ".join(c for c in cells if c), None))
    return out


def extract_docx(path: Path, cfg: dict) -> list[Page]:
    """Split a DOCX into heading-delimited Pages (page_no=None, paragraph ranges set).

    Raises EmptyFile, PasswordProtected, CorruptFile.
    """
    path = Path(path)
    if path.stat().st_size == 0:
        raise EmptyFile(f"{path.name} is empty (0 bytes)")
    with open(path, "rb") as fh:
        if fh.read(4) == _OLE_MAGIC:
            raise PasswordProtected(f"{path.name} is encrypted / password protected (or an old .doc)")
    try:
        document = docx.Document(str(path))
        blocks = _blocks(document)
    except Exception as e:  # python-docx raises BadZipFile, KeyError, ValueError...
        raise CorruptFile(f"{path.name}: cannot read DOCX ({e})") from e

    sections: list[list[tuple[int, str, int | None]]] = []  # (para_index, text, level)
    for i, (text, level) in enumerate(blocks):
        if level is not None or not sections:
            sections.append([])
        if text:
            sections[-1].append((i, text, level))

    pages: list[Page] = []
    for sec in sections:
        if not sec:
            continue
        lines = [t for _, t, _ in sec]
        headings = [Heading(t, lvl, n) for n, (_, t, lvl) in enumerate(sec) if lvl is not None]
        pages.append(Page(page_no=None, text="\n".join(lines), status="ok", headings=headings,
                          para_start=sec[0][0], para_end=sec[-1][0]))
    if not pages:
        pages.append(Page(page_no=None, status="empty", reason="document contains no text",
                          para_start=0, para_end=max(len(blocks) - 1, 0)))
    return pages
