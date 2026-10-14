"""Cornerstone demo UI: upload, ingestion report, stats, search with sources.

A thin layer over the same functions the CLI uses (open_stack, ingest_file, search).
No retrieval or ingestion logic lives here.

    PYTHONPATH=src streamlit run app/streamlit_app.py
Set CORNERSTONE_CONFIG to use another config file (the tests do).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cornerstone import CornerstoneError, EmptyQuery  # noqa: E402
from cornerstone.cli import load_config, location, open_stack  # noqa: E402
from cornerstone.embeddings import Embedder  # noqa: E402
from cornerstone.pipeline import ingest_file  # noqa: E402
from cornerstone.search import search  # noqa: E402

st.set_page_config(page_title="Cornerstone", page_icon=None, layout="wide")


@st.cache_resource(show_spinner="Loading the embedding model...")
def get_embedder(config_path: str | None) -> Embedder:
    """Only the model is cached (slow to load). SQLite connections are bound to one thread and
    Streamlit runs each rerun in its own thread, so store and index are opened per run (cheap)."""
    return Embedder(load_config(Path(config_path) if config_path else None))


def main() -> None:
    st.title("Cornerstone")
    st.caption("Stage 1: extraction and indexing. Upload notes, then search them. No LLM answers yet.")
    config_path = os.environ.get("CORNERSTONE_CONFIG")
    cfg = load_config(Path(config_path) if config_path else None)
    try:
        stack = open_stack(cfg, ROOT, load_embedder=False)
    except CornerstoneError as e:
        st.error(f"Cannot open the index: {type(e).__name__}: {e}")
        st.stop()
    stack.embedder = get_embedder(config_path)
    try:
        render(cfg, stack)
    finally:
        stack.store.close()


def render(cfg: dict, stack) -> None:
    store, index = stack.store, stack.index

    # ---- sync problems are shown, never hidden; discarding needs a click
    problems = store.check_sync(set(index.all_ids().tolist()))
    if problems:
        st.warning("The index and database are out of sync:\n\n" + "\n".join(f"- {p}" for p in problems))
        pending = store.list_documents("pending")
        if pending and st.button(f"Discard {len(pending)} interrupted ingest(s)"):
            for d in pending:
                store.discard_pending(d.doc_id)
            st.rerun()

    # ---- sidebar: stats
    s = store.stats()
    with st.sidebar:
        st.header("Index")
        st.metric("Documents", s["documents"])
        st.metric("Chunks (searchable)", s["chunks_active"])
        st.metric("Pages with text / total", f"{s['pages_with_text']} / {s['pages_total']}")
        size = stack.index_path.stat().st_size / 1e6 if stack.index_path.is_file() else 0.0
        st.write(f"Vectors: {len(index)}  \nDimension: {index.dim}  \nOn disk: {size:.2f} MB")
        st.write(f"Soft-deleted chunks: {s['chunks_deleted']}  \nModel: `{index.manifest.model_name}`")
        if s["flagged_pages"]:
            with st.expander(f"{s['pages_flagged']} flagged page(s)"):
                st.dataframe(s["flagged_pages"], hide_index=True, use_container_width=True)

    tab_search, tab_upload = st.tabs(["Search", "Upload"])

    # ---- search
    with tab_search:
        with st.form("search"):
            query = st.text_input("Question", placeholder="e.g. What is a TLB?")
            k = st.slider("Results", 1, 10, cfg["search"]["default_k"])
            go = st.form_submit_button("Search")
        if go:
            try:
                results = search(query, k, cfg, store, index, stack.embedder)
            except EmptyQuery:
                st.error("Please type a question.")
                results = None
            if results is not None and not results:
                st.info("No results. The index is empty or nothing indexed matches.")
            for r in results or []:
                c = r.chunk
                st.markdown(f"**#{r.rank}  {c.file_name}**  ·  {location(c)}  ·  score {r.score:.3f}")
                st.caption(f"Section: {c.section_heading or '-'}")
                st.write(r.snippet)
                with st.expander("Full chunk"):
                    st.text(c.text)

    # ---- upload + ingestion report
    with tab_upload:
        files = st.file_uploader("PDF or DOCX files", type=["pdf", "docx"], accept_multiple_files=True)
        if files and st.button("Ingest"):
            raw_dir = ROOT / cfg["paths"]["raw_dir"]
            raw_dir.mkdir(parents=True, exist_ok=True)
            rows, flagged = [], []
            bar = st.progress(0.0)
            for i, f in enumerate(files):
                dest = raw_dir / Path(f.name).name
                dest.write_bytes(f.getbuffer())
                r = ingest_file(dest, cfg, store, index, stack.embedder, stack.index_path)
                rows.append({"file": r.file_name, "status": r.status, "pages": r.pages_total,
                             "with text": r.pages_with_text, "flagged": r.pages_flagged,
                             "chunks": r.chunks_created, "seconds": round(r.seconds, 1), "note": r.message})
                flagged += [{"file": r.file_name, "page": p, "reason": why} for p, why in r.flagged_pages]
                bar.progress((i + 1) / len(files))
            st.subheader("Ingestion report")
            st.dataframe(rows, hide_index=True, use_container_width=True)
            if flagged:
                st.warning("Some pages were not indexed as text:")
                st.dataframe(flagged, hide_index=True, use_container_width=True)
            st.caption("Sidebar statistics refresh on the next interaction.")


main()
