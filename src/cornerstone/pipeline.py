"""ingest_file(): hash -> dedup/replace -> parse -> clean -> mark duplicate pages -> chunk -> embed -> store -> index
-> activate."""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Callable

import numpy as np

from cornerstone import Document, IngestReport, ModelMismatch
from cornerstone.chunking import chunk_pages, embedding_text
from cornerstone.dedup import mark_duplicates
from cornerstone.embeddings import Embedder
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.ingest.loader import load_document
from cornerstone.ingest.page_images import delete_page_images, render_page_images

_READ_BLOCK = 1 << 20


def file_sha256(path: Path) -> str:
    """SHA-256 of the file bytes, read in 1 MB blocks (bounded memory)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(_READ_BLOCK):
            h.update(block)
    return h.hexdigest()


def unit_from_name(file_name: str, cfg: dict) -> str | None:
    """'Unit 4_Storage management.pdf' -> 'Unit 4' using retrieval.unit_pattern; None if no match."""
    m = re.search(cfg["retrieval"]["unit_pattern"], file_name)
    return f"Unit {int(m.group(1))}" if m else None


def _failed(name: str, t0: float, message: str) -> IngestReport:
    return IngestReport(file_name=name, status="failed", seconds=time.perf_counter() - t0, message=message)


def ingest_file(path: Path, cfg: dict, store: MetadataStore, index: HNSWIndex, embedder: Embedder,
                index_path: Path, progress: Callable[[str], None] | None = None) -> IngestReport:
    """Ingest one PDF/DOCX. Never raises for a bad *file*; returns a report instead.

    Write order (crash safety):
      1. add_document  -> SQLite rows, all 'pending'   (invisible to search)
      2. index.add + index.save                        (vectors durable on disk)
      3. activate      -> rows become 'active'         (now searchable; old version retired atomically)
    A crash between 1 and 3 leaves a pending document that check_sync reports.
    Raises ModelMismatch if the embedder does not match the index (a config error, not a file error).
    """
    say = progress or (lambda msg: None)
    t0 = time.perf_counter()
    path = Path(path)
    name = path.name
    if embedder.dim != index.dim:
        raise ModelMismatch(f"embedder produces {embedder.dim}-d vectors but the index holds {index.dim}-d")

    # 1. hash + dedup
    try:
        sha = file_sha256(path)
    except OSError as e:
        return _failed(name, t0, f"cannot read file: {e}")
    same = store.find_by_hash(sha)
    if same is not None:
        return IngestReport(file_name=name, status="skipped_duplicate", doc_id=same.doc_id,
                            pages_total=same.n_pages, pages_with_text=same.n_pages_text,
                            pages_flagged=same.n_pages_flagged, chunks_created=0,
                            seconds=time.perf_counter() - t0,
                            message=f"identical content already indexed as '{same.file_name}' (doc {same.doc_id})")
    old = store.find_active_by_name(name)  # same name, different content -> replace

    # 2. parse + clean (bad files stop here, before any row is written)
    say(f"{name}: extracting text")
    try:
        pages = load_document(path, cfg)
    except Exception as e:  # CornerstoneError subclasses, plus any parser surprise: report, never hide
        kind = type(e).__name__
        return _failed(name, t0, f"{kind}: {e}")

    # 3. near-duplicate pages (recorded, not indexed), then chunk + embed in batches
    mark_duplicates(pages, cfg)
    chunks = chunk_pages(pages, 0, name, cfg, embedder.count_tokens)
    say(f"{name}: {len(pages)} pages -> {len(chunks)} chunks; embedding")
    bs = cfg["embedding"]["batch_size"]
    parts = []
    for i in range(0, len(chunks), bs):
        parts.append(embedder.embed_passages([embedding_text(c) for c in chunks[i:i + bs]]))
        say(f"{name}: embedded {min(i + bs, len(chunks))}/{len(chunks)} chunks")
    vectors = np.vstack(parts) if parts else np.zeros((0, embedder.dim), dtype=np.float32)

    # 4. store as pending -> index add + save -> activate
    doc = Document(file_name=name, sha256=sha, file_type=path.suffix.lower().lstrip("."),
                   unit=unit_from_name(name, cfg), source_path=str(path.resolve()))
    chunk_ids = store.add_document(doc, pages, chunks)
    warnings: list[str] = []
    try:
        if chunk_ids:
            index.add(np.asarray(chunk_ids, dtype=np.int64), vectors)
            index.save(index_path)
        if doc.file_type == "pdf":
            say(f"{name}: rendering page images")
            images, warnings = render_page_images(path, doc.doc_id, cfg)
            store.set_page_images(doc.doc_id, images)
        store.activate(doc.doc_id, replaces=old.doc_id if old else None)
    except Exception:
        # ordinary failure (disk full, bad vectors): clean up and surface it.
        # A hard crash (process killed) skips this and leaves the document pending on purpose.
        store.discard_pending(doc.doc_id)
        delete_page_images(doc.doc_id, cfg)
        raise

    flagged = [(p.page_no, f"{p.status}: {p.reason}") for p in pages if p.status not in ("ok", "duplicate")]
    duplicates = [(p.page_no, p.duplicate_of) for p in pages if p.status == "duplicate"]
    msg = f"replaced previous version (doc {old.doc_id})" if old else ""
    if not chunk_ids:
        msg = (msg + "; " if msg else "") + "no indexable text found (all pages flagged)"
    return IngestReport(
        file_name=name, status="replaced" if old else "indexed", doc_id=doc.doc_id,
        pages_total=doc.n_pages, pages_with_text=doc.n_pages_text, pages_flagged=doc.n_pages_flagged,
        flagged_pages=flagged, chunks_created=len(chunk_ids), pages_duplicate=len(duplicates),
        duplicate_pages=duplicates, warnings=warnings, seconds=time.perf_counter() - t0, message=msg)
