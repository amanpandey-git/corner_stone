"""PDF extraction with PyMuPDF: one Page per physical page, never dropped silently."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pymupdf

from cornerstone import CorruptFile, EmptyFile, Heading, Page, PasswordProtected

MAX_HEADING_CHARS = 150  # a "heading" longer than this is a paragraph in big print
MAX_HEADING_LEVELS = 3


def _page_lines(page: pymupdf.Page) -> tuple[list[tuple[str, float]], bool]:
    """Return ([(line_text, font_size)], has_image) for one page, in reading order.

    Blocks are separated by an empty-string entry so paragraphs stay visible in the text.
    """
    d = page.get_text("dict", sort=True)
    lines: list[tuple[str, float]] = []
    has_image = False
    for block in d["blocks"]:
        if block["type"] == 1:  # image block
            has_image = True
            continue
        block_lines = []
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in line["spans"]).strip()
            # size of the line = size of the span holding most characters
            size = max(spans, key=lambda s: len(s["text"]))["size"]
            block_lines.append((text, size))
        if block_lines:
            if lines:
                lines.append(("", 0.0))
            lines.extend(block_lines)
    if not has_image and page.get_images():
        has_image = True
    return lines, has_image


def extract_pdf(path: Path, cfg: dict) -> list[Page]:
    """Extract every page of a PDF into a Page with text, headings and a status.

    Raises EmptyFile, PasswordProtected, CorruptFile. A failure on a single page becomes
    Page(status="error") instead of aborting the whole file.
    """
    path = Path(path)
    if path.stat().st_size == 0:
        raise EmptyFile(f"{path.name} is empty (0 bytes)")
    ex = cfg["extraction"]
    try:
        doc = pymupdf.open(path)
    except Exception as e:  # pymupdf raises several types for broken files
        raise CorruptFile(f"{path.name}: cannot open PDF ({e})") from e
    with doc:
        if doc.needs_pass:
            raise PasswordProtected(f"{path.name} is password protected")
        if doc.page_count == 0:
            raise CorruptFile(f"{path.name}: PDF has no pages")

        # pass 1: lines per page, plus a document-wide font-size histogram
        raw: list[tuple[list[tuple[str, float]], bool] | Exception] = []
        size_chars: Counter = Counter()
        for page in doc:
            try:
                lines, has_image = _page_lines(page)
                raw.append((lines, has_image))
                for text, size in lines:
                    if text:
                        size_chars[round(size)] += len(text)
            except Exception as e:  # keep going; flagged below
                raw.append(e)

        # body text size = size carrying the most characters in the whole document
        body = size_chars.most_common(1)[0][0] if size_chars else 0
        threshold = body * ex["heading_size_ratio"]
        heading_sizes = sorted({s for s in size_chars if s >= threshold and body}, reverse=True)
        level_of = {s: min(i + 1, MAX_HEADING_LEVELS) for i, s in enumerate(heading_sizes)}

        # pass 2: build Page objects
        pages: list[Page] = []
        for i, item in enumerate(raw):
            page_no = i + 1
            if isinstance(item, Exception):
                pages.append(Page(page_no, status="error", reason=f"extraction failed: {item}"))
                continue
            lines, has_image = item
            text = "\n".join(t for t, _ in lines)
            headings = [
                Heading(t, level_of[round(s)], n)
                for n, (t, s) in enumerate(lines)
                if t and round(s) in level_of and len(t) <= MAX_HEADING_CHARS and any(c.isalpha() for c in t)
            ]
            n_chars = len(text.strip())
            if n_chars == 0 and not has_image:
                pages.append(Page(page_no, "", "empty", "blank page: no text and no images"))
            elif n_chars < ex["scan_min_chars"] and has_image:
                pages.append(Page(page_no, text, "needs_ocr",
                                  f"no usable text layer ({n_chars} chars) and page has an image: needs OCR",
                                  headings))
            else:
                pages.append(Page(page_no, text, "ok", None, headings))
        return pages
