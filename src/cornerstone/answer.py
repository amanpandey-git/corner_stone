"""Grounded answers from the student's own slides, with [n] citations and abstention (ARCHITECTURE.md 11.2).

Three places can decide "Not in your notes.":
  1. retrieval gate  - nothing retrieved, or the best slide is too far from the question (no LLM call);
  2. the model       - the prompt tells it to reply NOT_IN_NOTES when the sources do not answer;
  3. no citations    - a reply with no valid [n] is not shown as an answer.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from cornerstone import EmptyQuery, LLMError, SearchFilters
from cornerstone.citations import NOT_IN_NOTES_TOKEN, Citation, check_citations, parse_citations, strip_invalid_refs
from cornerstone.search import search

MODES = ("concise", "detailed", "2-mark", "5-mark", "10-mark")
NOT_IN_NOTES = "Not in your notes."
_HOLD = len(NOT_IN_NOTES_TOKEN)   # streamed text is held back until it cannot be the abstention token

SYSTEM_PROMPT = """You are a study assistant for a university student preparing for exams. You answer ONLY from the numbered sources in the user message: slides from the student's own course notes.

Rules:
1. Use only information stated in the sources. Do not add facts from your own knowledge, even if you know them and even if the sources seem incomplete. Do not add your own conclusions, consequences or explanations that the sources do not state.
2. End EVERY sentence that states a fact with the number of the source that supports it in square brackets, like [1] or [2][3], even when several sentences in a row use the same source (repeat the number each time). A sentence without a citation counts as unsupported. Use plain square brackets only. Cite only numbers from the sources list.
3. If the sources do not contain the information needed to answer the question, reply with exactly NOT_IN_NOTES and nothing else. Do this also when the sources are only loosely related to the question.
4. If the sources answer only part of the question, answer that part with citations and add one sentence saying which part the notes do not cover.
5. Write in clear, simple English for a student. Do not mention "sources" or "slides" in the answer text; just cite them.

Answer format: {instruction}"""


@dataclass
class Source:
    n: int
    chunk_id: int
    doc_id: int
    file_name: str
    page_start: int | None
    page_end: int | None
    section: str | None
    text: str

    def label(self) -> str:
        """'Unit 3_Memory management, p.23' (or pp.9-10; DOCX: no page)."""
        stem = Path(self.file_name).stem
        if self.page_start is None:
            return stem
        if self.page_end and self.page_end != self.page_start:
            return f"{stem}, pp.{self.page_start}-{self.page_end}"
        return f"{stem}, p.{self.page_start}"


@dataclass
class Answer:
    question: str
    mode: str
    text: str
    abstained: bool
    abstain_reason: str | None              # retrieval | model | no_citations | None
    sources: list[Source]
    citations: list[Citation] = field(default_factory=list)
    uncited_sentences: list[str] = field(default_factory=list)
    invalid_refs: list[int] = field(default_factory=list)
    unsupported: list[int] | None = None     # indexes into citations; None = not checked
    provider: str = ""
    model: str = ""
    cached: bool = False
    ttft_ms: float | None = None
    total_ms: float = 0.0
    top_vector_score: float | None = None
    check_error: str | None = None           # why the judge could not check (then unsupported is None)
    queue_ms: float = 0.0                    # time waiting for the free-tier rate limiter (excluded from ttft_ms)

    def cited_sources(self) -> list[Source]:
        """Sources actually cited, in order of first citation."""
        seen: list[int] = []
        for c in self.citations:
            seen += [n for n in c.refs if n not in seen]
        by_n = {s.n: s for s in self.sources}
        return [by_n[n] for n in seen if n in by_n]


def build_prompt(question: str, sources: list[Source], mode: str, cfg: dict) -> tuple[str, str]:
    """(system, user). The user message lists the numbered sources, then the question."""
    if mode not in MODES:
        raise ValueError(f"unknown answer mode {mode!r}; choose one of {', '.join(MODES)}")
    system = SYSTEM_PROMPT.format(instruction=cfg["answer"]["modes"][mode]["instruction"])
    blocks = []
    for s in sources:
        head = f"[{s.n}] {s.label()}" + (f" - {s.section}" if s.section else "")
        blocks.append(f"{head}\n{s.text.strip()}")
    user = "Sources:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question.strip()}"
    return system, user


# gpt-oss writes citations as 【1】 or 【1†L3】 (lenticular brackets) instead of [1]
_LENTICULAR = re.compile(r"【\s*(\d+(?:\s*[,\-–]\s*\d+)*)[^】]*】")


def normalise(text: str) -> str:
    """NFKC turns narrow no-break spaces and full-width brackets into plain characters; lenticular
    citation brackets become [n] so the parser sees them."""
    text = unicodedata.normalize("NFKC", text)
    return _LENTICULAR.sub(lambda m: f"[{m.group(1)}]", text).strip()


def _sources(results) -> list[Source]:
    return [Source(i, r.chunk.chunk_id, r.chunk.doc_id, r.chunk.file_name, r.chunk.page_start, r.chunk.page_end,
                   r.chunk.section_heading, r.chunk.text) for i, r in enumerate(results, 1)]


def finalise(question: str, mode: str, raw: str, sources: list[Source], **meta) -> Answer:
    """Turn the model's raw reply into an Answer: abstention checks, citation parsing, invalid refs removed."""
    text = normalise(raw)
    base = dict(question=question, mode=mode, sources=sources, **meta)
    if text.upper().startswith(NOT_IN_NOTES_TOKEN) or (NOT_IN_NOTES_TOKEN in text and "[" not in text):
        return Answer(text=NOT_IN_NOTES, abstained=True, abstain_reason="model", **base)
    citations, uncited, invalid = parse_citations(text, len(sources))
    if not citations:
        return Answer(text=NOT_IN_NOTES, abstained=True, abstain_reason="no_citations",
                      uncited_sentences=uncited, invalid_refs=invalid, **base)
    return Answer(text=strip_invalid_refs(text, len(sources)), abstained=False, abstain_reason=None,
                  citations=citations, uncited_sentences=uncited, invalid_refs=invalid, **base)


def stream_answer(question: str, mode: str, cfg: dict, store, index, embedder, provider,
                  filters: SearchFilters | None = None, reranker=None, judge=None,
                  check: bool | None = None) -> Iterator[str | Answer]:
    """Yield text deltas as the model writes, then the final Answer (always last; it is the source of truth).

    Nothing is streamed for an abstention. ``judge`` (a provider) is used when ``check`` is true
    (default: answer.check_citations) to mark unsupported citations.
    """
    if not question or not question.strip():
        raise EmptyQuery("question is empty or whitespace-only")
    if mode not in MODES:
        raise ValueError(f"unknown answer mode {mode!r}; choose one of {', '.join(MODES)}")
    a = cfg["answer"]
    t0 = time.perf_counter()
    results = search(question, a["k"], cfg, store, index, embedder, filters=filters, reranker=reranker)
    sources = _sources(results)
    top = max((r.scores.get("vector", r.score) for r in results), default=None)
    if not results or top < a["min_vector_score"]:
        yield Answer(question, mode, NOT_IN_NOTES, True, "retrieval", sources, top_vector_score=top,
                     total_ms=(time.perf_counter() - t0) * 1000)
        return

    system, user = build_prompt(question, sources, mode, cfg)
    parts: list[str] = []
    ttft = None
    queue_ms = 0.0
    released = False                        # becomes True once the reply cannot be NOT_IN_NOTES
    for delta in provider.stream(system, user, a["modes"][mode]["max_tokens"], cfg["llm"]["temperature"]):
        if ttft is None and delta:
            queue_ms = getattr(provider, "last_wait_s", 0.0) * 1000
            ttft = (time.perf_counter() - t0) * 1000 - queue_ms
        parts.append(delta)
        if released:
            yield delta
            continue
        so_far = "".join(parts).lstrip()
        if len(so_far) >= _HOLD and not so_far.upper().startswith(NOT_IN_NOTES_TOKEN):
            released = True
            yield so_far
    cached = bool(getattr(provider, "last_cached", False))
    ans = finalise(question, mode, "".join(parts), sources, provider=provider.name, model=provider.model,
                   cached=cached, ttft_ms=ttft, total_ms=(time.perf_counter() - t0) * 1000, top_vector_score=top,
                   queue_ms=queue_ms)
    if not released and not ans.abstained:
        yield ans.text                      # a reply shorter than the hold-back window
    if (a["check_citations"] if check is None else check) and not ans.abstained and judge is not None:
        texts = {s.n: s.text for s in sources}
        try:
            ans.unsupported = check_citations(ans.citations, texts, judge, cfg)
            if ans.unsupported is None:
                ans.check_error = "judge reply was not valid JSON (twice)"
        except LLMError as e:              # the answer stands; it is reported as "not checked", never as fine
            ans.check_error = f"{type(e).__name__}: {e}"

    yield ans


def answer(question: str, mode: str, cfg: dict, store, index, embedder, provider,
           filters: SearchFilters | None = None, reranker=None, judge=None, check: bool | None = None) -> Answer:
    """Non-streaming wrapper: the final Answer of stream_answer()."""
    final = None
    for item in stream_answer(question, mode, cfg, store, index, embedder, provider, filters, reranker, judge, check):
        if isinstance(item, Answer):
            final = item
    return final
