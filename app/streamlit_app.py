"""Cornerstone UI (fallback for the web app): ask with cited answers, search, upload, stats.

A thin layer over the same functions the CLI uses (open_stack, ingest_file, search, stream_answer).
No retrieval, answering or ingestion logic lives here.

    PYTHONPATH=src streamlit run app/streamlit_app.py
Set CORNERSTONE_CONFIG to use another config file (the tests do).
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cornerstone import CornerstoneError, EmptyQuery, LLMError, SearchFilters  # noqa: E402
from cornerstone import llm  # noqa: E402
from cornerstone.answer import MODES, Answer, stream_answer  # noqa: E402
from cornerstone.flashcards import card_from_question, generate_flashcards  # noqa: E402
from cornerstone.quiz import generate_quiz  # noqa: E402
from cornerstone.study_store import StudyStore  # noqa: E402
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


@st.cache_resource(show_spinner="Loading the reranker...")
def get_reranker(config_path: str | None):
    """Cross-encoder, cached like the embedder; None when retrieval.rerank is off."""
    from cornerstone.rerank import load_reranker

    return load_reranker(load_config(Path(config_path) if config_path else None))


def main() -> None:
    st.title("Cornerstone")
    st.caption("Exam answers from your own notes. Every claim cites the slide it came from.")
    config_path = os.environ.get("CORNERSTONE_CONFIG")
    cfg = load_config(Path(config_path) if config_path else None)
    try:
        stack = open_stack(cfg, ROOT, load_embedder=False)
    except CornerstoneError as e:
        st.error(f"Cannot open the index: {type(e).__name__}: {e}")
        st.stop()
    stack.embedder = get_embedder(config_path)
    stack.reranker = get_reranker(config_path)
    try:
        render(cfg, stack)
    finally:
        stack.store.close()


def show_answer(cfg: dict, stack, question: str, mode: str, filters, check: bool) -> None:
    """Stream the answer into one placeholder, then show the final text, flags and cited slides."""
    try:
        provider = llm.make_provider(cfg)
        judge = llm.make_provider(cfg, cfg["answer"]["judge_provider"]) if check else None
    except LLMError as e:
        st.error(f"The answer model is not available: {e}")
        return
    box = st.empty()
    shown, final = "", None
    try:
        for item in stream_answer(question, mode, cfg, stack.store, stack.index, stack.embedder, provider,
                                  filters=filters, reranker=stack.reranker, judge=judge, check=check):
            if isinstance(item, Answer):
                final = item
            else:
                shown += item
                box.markdown(shown + " ...")
    except EmptyQuery:
        box.empty()
        st.error("Please type a question.")
        return
    except LLMError as e:
        box.empty()
        st.error(f"The answer model failed: {e}")
        return
    if final.abstained:
        box.empty()
        why = {"retrieval": "nothing in your notes is close to this question",
               "model": "the closest slides do not answer it",
               "no_citations": "the model's answer could not be tied to any slide"}[final.abstain_reason]
        st.info(f"**{final.text}** ({why})")
        return
    box.markdown(final.text)
    if final.uncited_sentences:
        st.warning("Not backed by a citation: " + " | ".join(final.uncited_sentences))
    if final.invalid_refs:
        st.warning(f"Removed citations to sources that do not exist: {final.invalid_refs}")
    if final.unsupported:
        st.warning("The checker found these claims unsupported by their slide: "
                   + " | ".join(final.citations[i].sentence for i in final.unsupported))
    elif check and final.unsupported is None:
        st.caption("Citations could not be checked this time.")
    st.caption(f"{final.provider} {final.model} · first words after {final.ttft_ms or 0:.0f} ms"
               + (" · from cache" if final.cached else ""))
    st.subheader("Sources")
    for s in final.cited_sources():
        with st.expander(f"[{s.n}] {s.label()}" + (f" - {s.section}" if s.section else ""), expanded=s.n == 1):
            rel = stack.store.get_page_image(s.doc_id, s.page_start) if s.page_start is not None else None
            img = Path(cfg["paths"]["image_dir"]) / rel if rel else None
            if img is not None and img.is_file():
                st.image(str(img), use_container_width=True)
            st.text(s.text)


def show_slide(cfg: dict, stack, doc_id, page) -> None:
    rel = stack.store.get_page_image(doc_id, page) if doc_id is not None and page is not None else None
    img = Path(cfg["paths"]["image_dir"]) / rel if rel else None
    if img is not None and img.is_file():
        st.image(str(img), use_container_width=True)


def quiz_tab(cfg: dict, stack, study: StudyStore, units: list[str]) -> None:
    """Generate a cited MCQ quiz; after checking, wrong answers can become flashcards."""
    with st.form("quiz_form"):
        c1, c2 = st.columns([3, 1])
        chosen = c1.multiselect("Units", units, key="quiz_units")
        n = c2.number_input("Questions", 1, cfg["quiz"]["max_questions"], 5)
        make = st.form_submit_button("Make quiz")
    if make:
        try:
            filters = SearchFilters(units=chosen) if chosen else None
            with st.spinner("Writing questions from your slides..."):
                st.session_state["quiz_data"] = generate_quiz(cfg, stack.store, llm.make_provider(cfg), filters, n=int(n))
            st.session_state.pop("quiz_checked", None)
        except (ValueError, LLMError) as e:
            st.error(str(e))
            return
    quiz = st.session_state.get("quiz_data")
    if not quiz:
        st.caption("Pick a unit and make a quiz. Every answer is linked to the slide it comes from.")
        return
    if not quiz.questions:
        st.error("The model did not produce valid questions this time: " + "; ".join(quiz.rejected[:3]))
        return
    picks = []
    for i, q in enumerate(quiz.questions):
        st.markdown(f"**{i + 1}. {q.mcq.question}**")
        picks.append(st.radio("answer", q.mcq.options, index=None, key=f"q{i}", label_visibility="collapsed"))
    if st.button("Check answers"):
        st.session_state["quiz_checked"] = True
    if not st.session_state.get("quiz_checked"):
        return
    score = 0
    for i, (q, pick) in enumerate(zip(quiz.questions, picks)):
        right = q.mcq.options[q.mcq.answer]
        ok = pick == right
        score += ok
        (st.success if ok else st.error)(f"{i + 1}. {'Correct' if ok else 'Answer: ' + right} - {q.mcq.explanation}")
        with st.expander(f"Source: {q.source.label()}" + (f" - {q.source.section}" if q.source.section else "")):
            show_slide(cfg, stack, q.source.doc_id, q.source.page_start)
        if not ok and st.button("Make a flashcard of this", key=f"card{i}"):
            d = stack.store.get_document(q.source.doc_id)
            added = study.add_cards([card_from_question(q, date.today(), d.unit if d else None)])
            st.toast("Flashcard added" if added else "Already a flashcard")
    st.metric("Score", f"{score} / {len(quiz.questions)}")


GRADES = (("Again", 1), ("Hard", 3), ("Good", 4), ("Easy", 5))


def review_tab(cfg: dict, stack, study: StudyStore, units: list[str]) -> None:
    """Spaced-repetition review: show the front, reveal the back and slide, grade."""
    today = date.today()
    with st.expander("Make flashcards from a unit"):
        with st.form("cards_form"):
            chosen = st.multiselect("Units", units, key="card_units")
            n = st.number_input("Cards", 1, cfg["flashcards"]["max_cards"], 10)
            make = st.form_submit_button("Make flashcards")
        if make:
            try:
                with st.spinner("Writing flashcards from your slides..."):
                    cards, rejected = generate_flashcards(cfg, stack.store, llm.make_provider(cfg),
                                                          SearchFilters(units=chosen) if chosen else None, n=int(n))
                st.success(f"Added {len(study.add_cards(cards))} new card(s)."
                           + (f" {len(rejected)} rejected." if rejected else ""))
            except (ValueError, LLMError) as e:
                st.error(str(e))
    stats = study.stats(today)
    st.caption(f"{stats['due_today']} due today · {stats['cards']} cards · {stats['reviews']} reviews done")
    due = study.due(today, limit=1)
    if not due:
        st.info("Nothing due. Make cards from a unit, or turn wrong quiz answers into cards.")
        return
    card = due[0]
    st.markdown(f"### {card.front}")
    if st.button("Show answer", key=f"show{card.card_id}"):
        st.session_state["shown"] = card.card_id
    if st.session_state.get("shown") != card.card_id:
        return
    st.markdown(card.back)
    st.caption(f"{Path(card.file_name).stem}, p.{card.page}" if card.page else card.file_name)
    show_slide(cfg, stack, card.doc_id, card.page)
    for col, (label, grade) in zip(st.columns(len(GRADES)), GRADES):
        if col.button(label, key=f"g{card.card_id}{grade}"):
            nxt = study.review(card.card_id, grade, today)
            st.session_state.pop("shown", None)
            st.toast(f"Next review in {nxt.interval} day(s)")
            st.rerun()


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
        if s["duplicate_pages"]:
            with st.expander(f"{s['pages_duplicate']} duplicate page(s) (not indexed)"):
                st.dataframe(s["duplicate_pages"], hide_index=True, use_container_width=True)
        if s["flagged_pages"]:
            with st.expander(f"{s['pages_flagged']} flagged page(s)"):
                st.dataframe(s["flagged_pages"], hide_index=True, use_container_width=True)

    tab_ask, tab_quiz, tab_review, tab_search, tab_upload = st.tabs(["Ask", "Quiz", "Flashcards", "Search", "Upload"])
    units = sorted({d.unit for d in store.list_documents("active") if d.unit})
    study = StudyStore(Path(cfg["paths"]["study_db"]))
    with tab_quiz:
        quiz_tab(cfg, stack, study, units)
    with tab_review:
        review_tab(cfg, stack, study, units)

    # ---- ask: streamed answer, then cited slides with their images
    with tab_ask:
        with st.form("ask"):
            question = st.text_area("Your question", placeholder="e.g. Explain the SCAN disk scheduling algorithm")
            c1, c2, c3 = st.columns([2, 3, 2])
            mode = c1.selectbox("Answer type", MODES, index=0)
            chosen = c2.multiselect("Only these units", units)
            check = c3.checkbox("Check citations (slower)", value=cfg["answer"]["check_citations"])
            ask = st.form_submit_button("Ask")
        if ask:
            show_answer(cfg, stack, question, mode, SearchFilters(units=chosen) if chosen else None, check)

    # ---- search
    with tab_search:
        with st.form("search"):
            query = st.text_input("Question", placeholder="e.g. What is a TLB?")
            k = st.slider("Results", 1, 10, cfg["search"]["default_k"])
            go = st.form_submit_button("Search")
        if go:
            try:
                results = search(query, k, cfg, store, index, stack.embedder, reranker=stack.reranker)
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
                             "duplicate": r.pages_duplicate,
                             "chunks": r.chunks_created, "seconds": round(r.seconds, 1), "note": r.message})
                flagged += [{"file": r.file_name, "page": p, "reason": why} for p, why in r.flagged_pages]
                flagged += [{"file": r.file_name, "page": p, "reason": f"duplicate: near-copy of p.{orig}"}
                            for p, orig in r.duplicate_pages]
                bar.progress((i + 1) / len(files))
            st.subheader("Ingestion report")
            st.dataframe(rows, hide_index=True, use_container_width=True)
            if flagged:
                st.warning("Some pages were not indexed as text:")
                st.dataframe(flagged, hide_index=True, use_container_width=True)
            st.caption("Sidebar statistics refresh on the next interaction.")


main()
