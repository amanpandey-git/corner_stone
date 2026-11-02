"""Export the local index as static files for the online demo (web/public/demo/).

Run once from the repository root, after `python -m cornerstone.cli ingest samples`:

    .\\.venv\\Scripts\\python web\\scripts\\export_demo.py          (Windows)
    PYTHONPATH=src python web/scripts/export_demo.py             (macOS / Linux)

It writes, from the same index, prompts and config the evaluation used:
    chunks.json   every active chunk (text, file, page, section, unit), in vector order
    vectors.f32   the chunk vectors (float32, N x 384, little-endian), same order
    docs.json     the document list shown on the Documents page
    meta.json     prompts, answer modes and settings copied from the Python code and config.yaml,
                  plus a self-check: one query embedded by the real model and its top-5 chunk ids
    pages/        one compressed image per cited page (WebP, or JPEG if WebP is unavailable)
Nothing in the index is changed.
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from cornerstone import SCHEMA_VERSION  # noqa: E402
from cornerstone.answer import NOT_IN_NOTES, SYSTEM_PROMPT  # noqa: E402
from cornerstone.citations import JUDGE_SYSTEM  # noqa: E402
from cornerstone.cli import DB_FILE, INDEX_FILE, load_config  # noqa: E402
from cornerstone.flashcards import CARDS_SYSTEM  # noqa: E402
from cornerstone.index.hnsw_index import HNSWIndex  # noqa: E402
from cornerstone.index.metadata_store import MetadataStore  # noqa: E402
from cornerstone.quiz import QUIZ_SYSTEM  # noqa: E402

OUT = ROOT / "web" / "public" / "demo"
IMAGE_WIDTH = 1100        # slide images are ~1470 px wide at 110 dpi; 1100 keeps text readable
SELF_CHECK_QUERY = "What is paging in memory management?"


def compress(png: Path) -> tuple[bytes, str]:
    """Smaller copy of a page PNG: WebP (or JPEG), at most IMAGE_WIDTH wide."""
    try:
        from PIL import Image
    except ImportError:                       # PyMuPDF can still write JPEG
        import fitz
        pix = fitz.Pixmap(str(png))
        return pix.tobytes(output="jpeg", jpg_quality=70), "jpg"
    im = Image.open(png).convert("RGB")
    if im.width > IMAGE_WIDTH:
        im = im.resize((IMAGE_WIDTH, round(im.height * IMAGE_WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    try:
        im.save(buf, "WEBP", quality=72, method=6)
        return buf.getvalue(), "webp"
    except (OSError, KeyError):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True)
        return buf.getvalue(), "jpg"


def main() -> int:
    cfg = load_config()
    index_dir = Path(cfg["paths"]["index_dir"])
    image_dir = Path(cfg["paths"]["image_dir"])
    if not (index_dir / DB_FILE).is_file() or not (index_dir / INDEX_FILE).is_file():
        print(f"No index in {index_dir}. Build it first: python -m cornerstone.cli ingest samples", file=sys.stderr)
        return 1
    store = MetadataStore(index_dir / DB_FILE)
    index = HNSWIndex.load(index_dir / INDEX_FILE, cfg)

    # ---- documents (same fields as GET /documents)
    docs, units = [], {}
    for d in store.list_documents("active"):
        dup = store.conn.execute("SELECT COUNT(*) FROM pages WHERE doc_id=? AND status='duplicate'",
                                 (d.doc_id,)).fetchone()[0]
        docs.append({"doc_id": d.doc_id, "file_name": d.file_name, "unit": d.unit, "pages_total": d.n_pages,
                     "pages_with_text": d.n_pages_text, "pages_flagged": d.n_pages_flagged, "pages_duplicate": dup,
                     "chunks": d.n_chunks, "status": d.status, "ingested_at": d.ingested_at})
        units[d.doc_id] = d.unit

    # ---- chunks + vectors, same order
    ids, matrix = index.vectors()
    active = store.get_chunks(store.active_chunk_ids())
    keep = [i for i, cid in enumerate(ids.tolist()) if int(cid) in active]
    vectors = np.ascontiguousarray(matrix[keep], dtype="<f4")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pages").mkdir(exist_ok=True)

    chunks, images, total_bytes = [], {}, 0
    for row in keep:
        c = active[int(ids[row])]
        img = None
        if c.page_start is not None:
            key = (c.doc_id, c.page_start)
            if key not in images:
                rel = store.get_page_image(c.doc_id, c.page_start)
                src = (image_dir / rel) if rel else None
                images[key] = None
                if src is not None and src.is_file():
                    data, ext = compress(src)
                    name = f"pages/{c.doc_id}/{c.page_start}.{ext}"
                    (OUT / name).parent.mkdir(parents=True, exist_ok=True)
                    (OUT / name).write_bytes(data)
                    total_bytes += len(data)
                    images[key] = "/demo/" + name
            img = images[key]
        chunks.append({"id": c.chunk_id, "doc_id": c.doc_id, "file_name": c.file_name, "unit": units.get(c.doc_id),
                       "page_start": c.page_start, "page_end": c.page_end, "section": c.section_heading,
                       "chunk_index": c.chunk_index, "token_count": c.token_count, "text": c.text, "image": img})

    # ---- self-check: the real model's top-5 for one query (the web page compares its own search to this)
    from cornerstone.embeddings import Embedder
    q = Embedder(cfg).embed_query(SELF_CHECK_QUERY)
    top = np.argsort(-(vectors @ q))[:5]
    self_check = {"query": SELF_CHECK_QUERY, "top_ids": [chunks[i]["id"] for i in top],
                  "top_scores": [round(float((vectors @ q)[i]), 4) for i in top]}

    meta = {
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION,
        "n_chunks": len(chunks), "dim": int(vectors.shape[1]),
        "embedding": {"model_name": cfg["embedding"]["model_name"], "query_prefix": cfg["embedding"]["query_prefix"]},
        "prompts": {"answer_system": SYSTEM_PROMPT, "quiz_system": QUIZ_SYSTEM, "cards_system": CARDS_SYSTEM,
                    "judge_system": JUDGE_SYSTEM, "not_in_notes": NOT_IN_NOTES},
        "answer": cfg["answer"],
        "llm": {"temperature": cfg["llm"]["temperature"], "max_retries": cfg["llm"]["max_retries"],
                "backoff_s": cfg["llm"]["backoff_s"], "max_backoff_s": cfg["llm"]["max_backoff_s"],
                "groq": {"model": cfg["llm"]["groq"]["model"], "extra": cfg["llm"]["groq"].get("extra") or {}},
                "groq_judge": {"model": cfg["llm"]["groq_judge"]["model"],
                               "extra": cfg["llm"]["groq_judge"].get("extra") or {}}},
        "quiz": cfg["quiz"], "flashcards": cfg["flashcards"],
        "retrieval": {"candidates": cfg["retrieval"]["candidates"], "collapse": cfg["retrieval"]["collapse"]},
        "dedup": {"result_jaccard": cfg["dedup"]["result_jaccard"]},
        "search": {"max_query_chars": cfg["search"]["max_query_chars"], "snippet_chars": cfg["search"]["snippet_chars"]},
        "self_check": self_check,
    }

    (OUT / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    (OUT / "vectors.f32").write_bytes(vectors.tobytes())
    (OUT / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    store.close()

    print(f"Exported {len(docs)} documents, {len(chunks)} chunks ({vectors.shape[1]}-d vectors), "
          f"{sum(1 for v in images.values() if v)} page images ({total_bytes / 1e6:.1f} MB) to {OUT}")
    print(f"Self-check query: {SELF_CHECK_QUERY!r} -> top chunk ids {self_check['top_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
