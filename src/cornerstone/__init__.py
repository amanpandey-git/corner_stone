"""Cornerstone Stage 1: extraction and indexing.

Shared data classes and exceptions live here (see ARCHITECTURE.md sections 2 and 4).
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------- exceptions
class CornerstoneError(Exception):
    """Base class for all expected, user-reportable errors."""


class UnsupportedFileType(CornerstoneError):
    """File extension is not .pdf or .docx."""


class EmptyFile(CornerstoneError):
    """File has zero bytes."""


class CorruptFile(CornerstoneError):
    """File could not be parsed."""


class PasswordProtected(CornerstoneError):
    """PDF is encrypted and needs a password."""


class ModelMismatch(CornerstoneError):
    """Index was built with a different model, dimension or space."""


class IndexOutOfSync(CornerstoneError):
    """Index and SQLite store disagree (e.g. crash mid-ingest)."""


class EmptyQuery(CornerstoneError):
    """Query is empty or whitespace-only."""


# ---------------------------------------------------------------- data
@dataclass
class Heading:
    """A heading found on a page. line_no indexes into ``page.text.split("\\n")``."""

    text: str
    level: int
    line_no: int


@dataclass
class Page:
    """One extraction unit: a PDF page, or a heading-delimited DOCX section.

    page_no is None for DOCX (never invented). status is ok | needs_ocr | empty | error;
    reason is always set when status != "ok".
    """

    page_no: int | None
    text: str = ""
    status: str = "ok"
    reason: str | None = None
    headings: list[Heading] = field(default_factory=list)
    para_start: int | None = None
    para_end: int | None = None
    page_id: int | None = None
    doc_id: int | None = None
    has_image: bool = False  # page contains an image/diagram (not extracted in Stage 1)


@dataclass
class Chunk:
    """A retrievable piece of text. chunk_id is the SQLite key and the index label.

    chunk_id is 0 until the metadata store assigns it. Location is page_start/page_end
    for PDF, para_start/para_end for DOCX (the other pair is None).
    """

    chunk_id: int
    doc_id: int
    file_name: str
    text: str
    chunk_index: int
    token_count: int
    section_heading: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    para_start: int | None = None
    para_end: int | None = None
    deleted: bool = False
