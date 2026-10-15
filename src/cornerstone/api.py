"""HTTP API over the same functions the CLI and Streamlit use (ARCHITECTURE.md 13). No retrieval logic lives here.

    PYTHONPATH=src uvicorn cornerstone.api:app --port 8000      # docs at http://127.0.0.1:8000/docs

Threading: SQLite connections belong to one thread, so every request opens its own MetadataStore. The faiss index,
the embedder and the reranker are loaded once and shared; one lock serialises index writes (ingest, delete) with
each individual faiss read (LockedIndex), so a slow LLM answer never holds it. Uploaded files are ingested one at a time by a single background worker.
"""
from __future__ import annotations

import json
import queue
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from cornerstone import SCHEMA_VERSION, CornerstoneError, EmptyQuery, LLMError, SearchFilters
from cornerstone.answer import MODES, Answer, stream_answer
from cornerstone.cli import DB_FILE, INDEX_FILE, ROOT, load_config
from cornerstone.flashcards import generate_flashcards
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.llm import get_key, make_provider
from cornerstone.pipeline import ingest_file
from cornerstone.quiz import generate_quiz
from cornerstone.search import search
from cornerstone.study_store import Card, StudyStore

SUPPORTED = {".pdf", ".docx"}


# ------------------------------------------------------------------ request bodies
class AskBody(BaseModel):
    question: str
    mode: str = "concise"
    units: list[str] | None = None
    doc_ids: list[int] | None = None
    check: bool = False


class QuizBody(BaseModel):
    units: list[str] | None = None
    doc_ids: list[int] | None = None
    n: int = 5
    seed: int = 0


class CardsBody(BaseModel):
    units: list[str] | None = None
    doc_ids: list[int] | None = None
    n: int = 10
    seed: int = 0


class SourceRef(BaseModel):
    file_name: str
    page: int | None = None
    doc_id: int | None = None
    chunk_id: int | None = None


class FromQuizBody(BaseModel):
    question: str
    options: list[str]
    answer: int = Field(ge=0, le=3)
    explanation: str
    source: SourceRef


class ReviewBody(BaseModel):
    grade: int = Field(ge=0, le=5)


class LockedIndex:
    """Read-only view of the shared faiss index for search(): each call takes the lock only for itself.

    faiss must not search while an ingest is adding vectors. Locking every faiss call (not a whole request)
    means one student's answer streaming from the LLM never blocks another student's search or an upload.
    """

    def __init__(self, state) -> None:
        self._state = state

    def __len__(self) -> int:
        with self._state.lock:
            return len(self._state.index)

    def search(self, *args, **kwargs):
        with self._state.lock:
            return self._state.index.search(*args, **kwargs)

    def __getattr__(self, name):                 # dim, manifest, ... (read-only attributes)
        return getattr(self._state.index, name)


def _filters(units, doc_ids) -> SearchFilters | None:
    return SearchFilters(doc_ids=doc_ids, units=units) if (units or doc_ids) else None


# ------------------------------------------------------------------ app
def create_app(cfg: dict | None = None, provider_factory=make_provider, embedder=None, reranker=None) -> FastAPI:
    """Build the app. Tests pass a temp config, a FakeProvider factory and a shared embedder."""
    cfg = cfg or load_config()
    index_dir = Path(cfg["paths"]["index_dir"])
    index_path = index_dir / INDEX_FILE
    image_dir = Path(cfg["paths"]["image_dir"])
    raw_dir = Path(cfg["paths"]["raw_dir"])

    app = FastAPI(title="Cornerstone", version="0.2",
                  description="Exam answers, quizzes and flashcards from your own notes, every claim cited to a slide.")
    # the Next.js app runs on another port (another origin), so the browser needs CORS headers (ARCHITECTURE 14)
    app.add_middleware(CORSMiddleware, allow_origins=cfg["api"].get("cors_origins", []), allow_methods=["*"],
                       allow_headers=["*"])
    first = MetadataStore(index_dir / DB_FILE)      # creates the database (and checks its schema) once
    first.close()
    index = HNSWIndex.load(index_path, cfg) if index_path.is_file() else HNSWIndex.from_config(cfg)
    if embedder is None:
        from cornerstone.embeddings import Embedder
        embedder = Embedder(cfg)
    if reranker is None and cfg["retrieval"].get("rerank"):
        from cornerstone.rerank import Reranker
        reranker = Reranker(cfg)
    st = app.state
    st.index, st.lock, st.jobs = index, threading.Lock(), {}
    reader = LockedIndex(st)                     # what search()/stream_answer() see
    st.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ingest")
    study = StudyStore(Path(cfg["paths"]["study_db"]))

    @contextmanager
    def store_ctx() -> Iterator[MetadataStore]:
        s = MetadataStore(index_dir / DB_FILE)
        try:
            yield s
        finally:
            s.close()

    def image_url(store: MetadataStore, doc_id: int, page: int | None) -> str | None:
        if page is None or not store.get_page_image(doc_id, page):
            return None
        return f"/pages/{doc_id}/{page}/image"

    def provider(name: str | None = None):
        try:
            return provider_factory(cfg, name)
        except LLMError as e:
            raise HTTPException(503, str(e)) from e

    def answer_json(a: Answer, store: MetadataStore) -> dict:
        return {
            "question": a.question, "mode": a.mode, "text": a.text, "abstained": a.abstained,
            "abstain_reason": a.abstain_reason,
            "citations": [{"sentence": c.sentence, "refs": c.refs} for c in a.citations],
            "sources": [{"n": s.n, "file_name": s.file_name, "doc_id": s.doc_id, "page_start": s.page_start,
                         "page_end": s.page_end, "section": s.section, "label": s.label(), "text": s.text,
                         "cited": s.n in {n for c in a.citations for n in c.refs},
                         "image_url": image_url(store, s.doc_id, s.page_start)} for s in a.sources],
            "uncited_sentences": a.uncited_sentences, "invalid_refs": a.invalid_refs,
            "unsupported": a.unsupported, "check_error": a.check_error,
            "provider": a.provider, "model": a.model, "cached": a.cached, "ttft_ms": a.ttft_ms,
            "total_ms": a.total_ms,
        }

    def card_json(c: Card) -> dict:
        d = asdict(c)
        d["due"] = c.due.isoformat()
        return d

    # -------------------------------------------------------------- health + documents
    @app.get("/health")
    def health() -> dict:
        with store_ctx() as s:
            stats = s.stats()
        try:
            get_key(cfg["llm"]["provider"])
            key = True
        except CornerstoneError:
            key = False
        return {"status": "ok", "documents": stats["documents"], "chunks": stats["chunks_active"],
                "schema_version": SCHEMA_VERSION, "llm_provider": cfg["llm"]["provider"], "llm_key_present": key,
                "rerank": bool(cfg["retrieval"].get("rerank")), "hybrid": bool(cfg["retrieval"]["hybrid"])}

    @app.get("/documents")
    def documents() -> list[dict]:
        with store_ctx() as s:
            out = []
            for d in s.list_documents("active"):
                dup = s.conn.execute("SELECT COUNT(*) FROM pages WHERE doc_id=? AND status='duplicate'",
                                     (d.doc_id,)).fetchone()[0]
                out.append({"doc_id": d.doc_id, "file_name": d.file_name, "unit": d.unit, "pages_total": d.n_pages,
                            "pages_with_text": d.n_pages_text, "pages_flagged": d.n_pages_flagged,
                            "pages_duplicate": dup, "chunks": d.n_chunks, "status": d.status,
                            "ingested_at": d.ingested_at})
        return out

    def run_job(job_id: str, path: Path) -> None:
        job = st.jobs[job_id]
        job["state"] = "running"
        try:
            s = MetadataStore(index_dir / DB_FILE)
            try:
                with st.lock:
                    r = ingest_file(path, cfg, s, st.index, embedder, index_path)
            finally:
                s.close()
            rep = asdict(r)
            job.update(state="done" if r.status in ("indexed", "skipped_duplicate", "replaced") else "failed", report=rep)
        except Exception as e:                     # reported in the job, never silent
            job.update(state="failed", report={"message": f"{type(e).__name__}: {e}"})

    @app.post("/documents", status_code=202)
    async def upload(files: list[UploadFile] = File(...)) -> dict:
        limit = cfg["api"]["max_upload_mb"] * 1024 * 1024
        raw_dir.mkdir(parents=True, exist_ok=True)
        jobs = []
        for f in files:
            name = Path(f.filename or "").name
            if Path(name).suffix.lower() not in SUPPORTED:
                raise HTTPException(415, f"{name or 'file'}: only .pdf and .docx are supported")
            data = await f.read()
            if len(data) > limit:
                raise HTTPException(413, f"{name}: larger than {cfg['api']['max_upload_mb']} MB")
            dest = raw_dir / name
            dest.write_bytes(data)
            job_id = uuid.uuid4().hex[:12]
            st.jobs[job_id] = {"job_id": job_id, "file_name": name, "state": "queued", "report": None}
            st.worker.submit(run_job, job_id, dest)
            jobs.append({"job_id": job_id, "file_name": name})
        return {"jobs": jobs}

    @app.get("/documents/jobs/{job_id}")
    def job(job_id: str) -> dict:
        if job_id not in st.jobs:
            raise HTTPException(404, f"no job {job_id}")
        return st.jobs[job_id]

    @app.delete("/documents/{doc_id}", status_code=204)
    def delete(doc_id: int) -> Response:
        with st.lock, store_ctx() as s:
            try:
                s.delete_document(doc_id)
            except KeyError as e:
                raise HTTPException(404, str(e).strip("'\"")) from e
        return Response(status_code=204)

    # -------------------------------------------------------------- search + pages
    @app.get("/search")
    def search_route(q: str, k: int = Query(5, ge=1, le=50), unit: list[str] | None = Query(None),
                     doc_id: list[int] | None = Query(None)) -> list[dict]:
        with store_ctx() as s:
            try:
                res = search(q, k, cfg, s, reader, embedder, filters=_filters(unit, doc_id), reranker=reranker)
            except EmptyQuery as e:
                raise HTTPException(422, str(e)) from e
            return [{"rank": r.rank, "score": r.score, "scores": r.scores, "file_name": r.chunk.file_name,
                     "doc_id": r.chunk.doc_id, "chunk_id": r.chunk.chunk_id, "page_start": r.chunk.page_start,
                     "page_end": r.chunk.page_end, "section": r.chunk.section_heading, "snippet": r.snippet,
                     "image_url": image_url(s, r.chunk.doc_id, r.chunk.page_start), "also_on": r.also_on}
                    for r in res]

    @app.get("/pages/{doc_id}/{page_no}/image")
    def page_image(doc_id: int, page_no: int) -> FileResponse:
        with store_ctx() as s:
            rel = s.get_page_image(doc_id, page_no)
        path = (image_dir / rel).resolve() if rel else None
        if path is None or not path.is_file() or image_dir.resolve() not in path.parents:
            raise HTTPException(404, f"no image for document {doc_id} page {page_no}")
        return FileResponse(path, media_type="image/png")

    # -------------------------------------------------------------- answers
    def check_ask(body: AskBody) -> None:
        if not body.question.strip():
            raise HTTPException(422, "question is empty")
        if body.mode not in MODES:
            raise HTTPException(422, f"unknown mode {body.mode!r}; choose one of {', '.join(MODES)}")

    @app.post("/ask")
    def ask(body: AskBody) -> dict:
        check_ask(body)
        p = provider()
        judge = provider(cfg["answer"]["judge_provider"]) if body.check else None
        with store_ctx() as s:
            final = None
            try:
                for item in stream_answer(body.question, body.mode, cfg, s, reader, embedder, p,
                                          filters=_filters(body.units, body.doc_ids), reranker=reranker,
                                          judge=judge, check=body.check):
                    if isinstance(item, Answer):
                        final = item
            except LLMError as e:
                raise HTTPException(503, str(e)) from e
            return answer_json(final, s)

    @app.post("/ask/stream")
    def ask_stream(body: AskBody) -> StreamingResponse:
        check_ask(body)
        p = provider()
        judge = provider(cfg["answer"]["judge_provider"]) if body.check else None
        q: queue.Queue = queue.Queue()

        def produce() -> None:              # one thread owns the SQLite connection for the whole answer
            try:
                with store_ctx() as s:
                    for item in stream_answer(body.question, body.mode, cfg, s, reader, embedder, p,
                                              filters=_filters(body.units, body.doc_ids), reranker=reranker,
                                              judge=judge, check=body.check):
                        if isinstance(item, Answer):
                            q.put(("final", answer_json(item, s)))
                        else:
                            q.put(("delta", item))
            except CornerstoneError as e:
                q.put(("error", {"detail": str(e)}))
            finally:
                q.put(None)

        threading.Thread(target=produce, daemon=True).start()

        def events() -> Iterator[str]:
            while (msg := q.get()) is not None:
                kind, data = msg
                yield f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # -------------------------------------------------------------- quiz + flashcards
    @app.post("/quiz")
    def quiz(body: QuizBody) -> dict:
        p = provider()
        with store_ctx() as s:
            try:
                qz = generate_quiz(cfg, s, p, _filters(body.units, body.doc_ids), n=body.n, seed=body.seed)
            except ValueError as e:
                raise HTTPException(422, str(e)) from e
            except LLMError as e:
                raise HTTPException(503, str(e)) from e
            return {"requested": qz.requested, "generated": qz.generated, "attempts": qz.attempts,
                    "rejected": qz.rejected,
                    "questions": [{"question": x.mcq.question, "options": x.mcq.options, "answer": x.mcq.answer,
                                   "explanation": x.mcq.explanation,
                                   "source": {"n": x.source.n, "file_name": x.source.file_name,
                                              "page": x.source.page_start, "doc_id": x.source.doc_id,
                                              "chunk_id": x.source.chunk_id, "section": x.source.section,
                                              "label": x.source.label(),
                                              "image_url": image_url(s, x.source.doc_id, x.source.page_start)}}
                                  for x in qz.questions]}

    @app.post("/flashcards/generate")
    def cards_generate(body: CardsBody) -> dict:
        p = provider()
        with store_ctx() as s:
            try:
                cards, rejected = generate_flashcards(cfg, s, p, _filters(body.units, body.doc_ids), n=body.n,
                                                      seed=body.seed, today=date.today())
            except ValueError as e:
                raise HTTPException(422, str(e)) from e
            except LLMError as e:
                raise HTTPException(503, str(e)) from e
        ids = study.add_cards(cards)
        return {"created": [card_json(study.get(i)) for i in ids], "skipped_duplicates": len(cards) - len(ids),
                "rejected": rejected}

    @app.post("/flashcards/from-quiz")
    def cards_from_quiz(body: FromQuizBody) -> dict:
        if len(body.options) != 4:
            raise HTTPException(422, "a quiz question has exactly 4 options")
        unit = None
        if body.source.doc_id is not None:
            with store_ctx() as s:
                d = s.get_document(body.source.doc_id)
                unit = d.unit if d else None
        card = Card(0, body.question, f"{body.options[body.answer]}. {body.explanation}", body.source.file_name,
                    body.source.page, body.source.doc_id, body.source.chunk_id, unit, date.today(), origin="quiz")
        ids = study.add_cards([card])
        if not ids:
            existing = [c for c in study.list_cards() if c.front == body.question.strip()
                        and c.file_name == body.source.file_name and c.page == body.source.page]
            return {"card": card_json(existing[0]), "created": False}
        return {"card": card_json(study.get(ids[0])), "created": True}

    @app.get("/flashcards/due")
    def cards_due(limit: int = Query(20, ge=1, le=200), unit: list[str] | None = Query(None)) -> dict:
        today = date.today()
        cards = study.due(today, limit, unit)
        with store_ctx() as s:
            out = []
            for c in cards:
                d = card_json(c)
                d["image_url"] = image_url(s, c.doc_id, c.page) if c.doc_id is not None else None
                out.append(d)
        return {"today": today.isoformat(), "cards": out, "stats": study.stats(today)}

    @app.post("/flashcards/{card_id}/review")
    def cards_review(card_id: int, body: ReviewBody) -> dict:
        try:
            return card_json(study.review(card_id, body.grade, date.today()))
        except KeyError as e:
            raise HTTPException(404, f"no flashcard with id {card_id}") from e

    return app


def __getattr__(name: str):
    """`uvicorn cornerstone.api:app` builds the real app on first access (importing this module stays cheap)."""
    if name == "app":
        global app
        app = create_app()
        return app
    raise AttributeError(name)
