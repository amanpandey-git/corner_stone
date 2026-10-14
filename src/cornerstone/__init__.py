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
class Document:
    """One ingested file version. status: pending -> active -> replaced (or abandoned)."""

    file_name: str
    sha256: str
    file_type: str  # "pdf" | "docx"
    doc_id: int = 0
    n_pages: int = 0
    n_pages_text: int = 0
    n_pages_flagged: int = 0
    n_chunks: int = 0
    status: str = "pending"
    ingested_at: str = ""


@dataclass
class IngestReport:
    """What happened to one file. status: indexed | replaced | skipped_duplicate | failed.

    flagged_pages lists (page_no, "status: reason") for every page that was not indexed as text.
    """

    file_name: str
    status: str
    doc_id: int | None = None
    pages_total: int = 0
    pages_with_text: int = 0
    pages_flagged: int = 0
    flagged_pages: list[tuple[int | None, str]] = field(default_factory=list)
    chunks_created: int = 0
    seconds: float = 0.0
    message: str = ""


@dataclass
class SearchResult:
    """One hit. ``chunk`` carries the full metadata so Stage 2 (LLM, reranker) needs no index access."""

    chunk: "Chunk"
    score: float  # cosine similarity, -1..1
    rank: int  # 1-based
    snippet: str


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
