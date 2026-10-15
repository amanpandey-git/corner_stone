"""Cornerstone: extraction, indexing and (Stage 2) a study assistant over the student's notes.

Shared data classes and exceptions live here (see ARCHITECTURE.md sections 2 and 4).
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Version of the on-disk format (SQLite user_version and manifest index_version). v0.1 = 1.
SCHEMA_VERSION = 3   # v3 (Stage 2 Phase 3): documents.status may be 'deleted'


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


class IndexVersionMismatch(ModelMismatch):
    """Index or database was written by another schema version (e.g. a v0.1 index); rebuild it."""


def rebuild_hint(found: int) -> str:
    """The message every IndexVersionMismatch carries: what was found and the exact command to fix it."""
    return (f"index was built with schema {found} ({'v0.1' if found == 1 else 'another version'}); "
            f"this code needs schema {SCHEMA_VERSION}. Rebuild: "
            f"python -m cornerstone.cli rebuild <your files or folder> --yes "
            f"(the old index folder is kept as <index_dir>.v{found}.bak)")


class IndexOutOfSync(CornerstoneError):
    """Index and SQLite store disagree (e.g. crash mid-ingest)."""


class EmptyQuery(CornerstoneError):
    """Query is empty or whitespace-only."""


class LLMError(CornerstoneError):
    """An LLM provider call failed (message has the provider, model, HTTP status and error type; never a key)."""


class LLMUnavailable(LLMError):
    """No API key, the key was refused, or the model does not exist."""


class LLMRateLimited(LLMError):
    """The provider's rate limit was hit and the retry cap (or a long retry-after) was reached."""


class LLMTimeout(LLMError):
    """The provider did not answer within llm.timeout_s, after the retry cap."""


class RerankerUnavailable(CornerstoneError):
    """The cross-encoder reranker model could not be loaded (offline, not cached, bad revision)."""


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
    duplicate_of: int | None = None  # page_no of an earlier page in the same document (status 'duplicate')
    image_path: str | None = None  # rendered PNG, relative to paths.image_dir


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
    unit: str | None = None  # e.g. "Unit 4", from the file name (retrieval.unit_pattern)
    source_path: str | None = None  # absolute path at ingest time


@dataclass
class IngestReport:
    """What happened to one file. status: indexed | replaced | skipped_duplicate | failed.

    flagged_pages lists (page_no, "status: reason") for pages not indexed because of a problem (needs_ocr,
    empty, error); duplicate_pages lists (page_no, duplicate_of) for near-copies of an earlier page.
    pages_with_text + pages_flagged + pages_duplicate == pages_total.
    """

    file_name: str
    status: str
    doc_id: int | None = None
    pages_total: int = 0
    pages_with_text: int = 0
    pages_flagged: int = 0
    flagged_pages: list[tuple[int | None, str]] = field(default_factory=list)
    chunks_created: int = 0
    pages_duplicate: int = 0
    duplicate_pages: list[tuple[int, int]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)  # e.g. a page image that could not be rendered
    seconds: float = 0.0
    message: str = ""


@dataclass
class SearchFilters:
    """Restrict search to some documents and/or units ("Unit 4"). None = no restriction on that field."""

    doc_ids: list[int] | None = None
    units: list[str] | None = None


@dataclass
class SearchResult:
    """One hit. ``chunk`` carries the full metadata so Stage 2 (LLM, reranker) needs no index access."""

    chunk: "Chunk"
    score: float  # score of the last stage that ran (cosine similarity -1..1 for vector-only search)
    rank: int  # 1-based
    snippet: str
    scores: dict[str, float] = field(default_factory=dict)  # per stage: vector, bm25, rrf, rerank
    also_on: list[tuple[str, int | None]] = field(default_factory=list)  # (file, page) of collapsed near-copies


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
    context_header: str | None = None  # "<file stem> > <section>", prepended to text before embedding
