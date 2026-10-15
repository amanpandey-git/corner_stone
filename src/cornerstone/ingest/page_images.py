"""Render one PNG per PDF page so a citation can show the slide itself (ARCHITECTURE.md 10.5).

Files: <paths.image_dir>/<doc_id>/p<NNN>.png. The path stored in SQLite (pages.image_path) is relative to
paths.image_dir, so the image folder can move with the index. One page is rendered at a time (bounded memory).
A page that fails to render gets no image and a warning; it never stops the ingest.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pymupdf


def image_root(cfg: dict) -> Path:
    return Path(cfg["paths"]["image_dir"])


def render_page_images(pdf_path: Path, doc_id: int, cfg: dict) -> tuple[dict[int, str], list[str]]:
    """({page_no: relative png path}, [warnings]). Returns ({}, []) when images.enabled is false."""
    if not cfg["images"]["enabled"]:
        return {}, []
    out_dir = image_root(cfg) / str(doc_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[int, str] = {}
    warnings: list[str] = []
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:  # the file was parsed a moment ago, so this is unexpected: report, do not crash
        return {}, [f"page images not rendered: cannot reopen PDF ({type(e).__name__}: {e})"]
    with doc:
        for i, page in enumerate(doc):
            rel = f"{doc_id}/p{i + 1:03d}.png"
            try:
                page.get_pixmap(dpi=cfg["images"]["dpi"]).save(image_root(cfg) / rel)
                paths[i + 1] = rel
            except Exception as e:
                warnings.append(f"page {i + 1}: image not rendered ({type(e).__name__}: {e})")
    return paths, warnings


def delete_page_images(doc_id: int, cfg: dict) -> None:
    """Remove a document's image folder (abandoned ingest, compaction). Missing folder is fine."""
    shutil.rmtree(image_root(cfg) / str(doc_id), ignore_errors=True)
