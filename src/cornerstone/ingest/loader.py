"""Dispatch by file type, then clean."""
from __future__ import annotations

from pathlib import Path

from cornerstone import EmptyFile, Page, UnsupportedFileType
from cornerstone.ingest.cleaner import clean_pages
from cornerstone.ingest.docx_parser import extract_docx
from cornerstone.ingest.pdf_parser import extract_pdf

_PARSERS = {".pdf": extract_pdf, ".docx": extract_docx}


def load_document(path: Path, cfg: dict) -> list[Page]:
    """Parse a PDF or DOCX into cleaned Pages.

    Raises UnsupportedFileType, EmptyFile, CorruptFile, PasswordProtected.
    """
    path = Path(path)
    parser = _PARSERS.get(path.suffix.lower())
    if parser is None:
        raise UnsupportedFileType(f"{path.name}: '{path.suffix}' is not supported (use .pdf or .docx)")
    if not path.is_file():
        raise EmptyFile(f"{path.name}: file not found")
    return clean_pages(parser(path, cfg), cfg)
