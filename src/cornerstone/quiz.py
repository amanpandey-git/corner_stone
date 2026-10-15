"""Multiple-choice quizzes generated from the student's slides, each answer cited to its slide (ARCHITECTURE.md 12.1).

The model gets a numbered set of slides and must return JSON. Every question is validated with pydantic and
by hand-written rules (4 distinct options, a valid answer index, a source that exists); invalid questions are
dropped with a reason. If too few survive, one more call asks for the missing ones. Never more than
quiz.max_attempts calls.
"""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError, field_validator

from cornerstone import SearchFilters
from cornerstone.answer import Source, normalise

QUIZ_SYSTEM = """You write exam practice questions for a university student from slides of their own course notes.

Write multiple-choice questions as JSON: {"questions": [{"question": "...", "options": ["...", "...", "...", "..."], "answer": 0, "explanation": "...", "source": 1}]}
Rules:
1. Each question tests one fact that is stated on one numbered slide; "source" is that slide's number.
2. Exactly 4 options. Exactly one is correct according to that slide; "answer" is its index (0-3).
3. The 3 wrong options must be plausible to a student but clearly wrong according to the slide.
4. Never use "all of the above", "none of the above" or "both A and B".
5. "explanation" is one sentence saying why the answer is correct, using the slide's wording.
6. Use only the slides; no outside facts. Cover different slides; do not repeat a question.
Reply with the JSON object only."""


class MCQ(BaseModel):
    question: str
    options: list[str]
    answer: int
    explanation: str
    source: int

    @field_validator("question", "explanation")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("options")
    @classmethod
    def _four_distinct(cls, v: list[str]) -> list[str]:
        v = [o.strip() for o in v]
        if len(v) != 4:
            raise ValueError(f"needs exactly 4 options, got {len(v)}")
        if any(not o for o in v):
            raise ValueError("an option is empty")
        if len({" ".join(o.lower().split()) for o in v}) != 4:
            raise ValueError("options are not distinct")
        if any(re.search(r"\b(all|none) of the above\b", o, re.I) for o in v):
            raise ValueError("uses 'all/none of the above'")
        return v

    @field_validator("answer")
    @classmethod
    def _index(cls, v: int) -> int:
        if not 0 <= v <= 3:
            raise ValueError(f"answer index {v} is not 0..3")
        return v


@dataclass
class QuizQuestion:
    mcq: MCQ
    source: Source


@dataclass
class Quiz:
    questions: list[QuizQuestion]
    requested: int
    generated: int = 0                                # items the model returned, valid or not
    rejected: list[str] = field(default_factory=list)  # one reason per rejected item
    attempts: int = 0


def pick_slides(store, filters: SearchFilters | None, cfg: dict, seed: int = 0) -> list[Source]:
    """Up to quiz.max_sources slides with enough text, spread evenly through the selected documents."""
    q = cfg["quiz"]
    allowed = store.allowed_doc_ids(filters)
    chunks = [c for c in store.get_chunks(store.active_chunk_ids()).values()
              if (allowed is None or c.doc_id in allowed) and c.token_count >= q["min_tokens"]]
    if not chunks:
        raise ValueError(f"no slides with enough text match {filters or 'the index'}; ingest notes or widen the filter")
    chunks.sort(key=lambda c: (c.doc_id, c.page_start or 0, c.chunk_index))
    m = min(len(chunks), q["max_sources"])
    step = len(chunks) / m
    offset = random.Random(seed).random() * step
    picked = [chunks[min(int(offset + i * step), len(chunks) - 1)] for i in range(m)]
    return [Source(i, c.chunk_id, c.doc_id, c.file_name, c.page_start, c.page_end, c.section_heading, c.text)
            for i, c in enumerate(picked, 1)]


def sources_block(sources: list[Source]) -> str:
    return "\n\n".join(f"[{s.n}] {s.label()}" + (f" - {s.section}" if s.section else "") + f"\n{s.text.strip()}"
                       for s in sources)


def json_items(reply: str, key: str) -> list | None:
    """The list under `key` in the first JSON object of the reply; None if there is no such list."""
    m = re.search(r"\{.*\}", normalise(reply), re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    items = data.get(key) if isinstance(data, dict) else None
    return items if isinstance(items, list) else None


def _validate(items: list, sources: list[Source], seen: set[str], start: int) -> tuple[list[QuizQuestion], list[str]]:
    ok, bad = [], []
    by_n = {s.n: s for s in sources}
    for i, item in enumerate(items, start):
        try:
            mcq = MCQ.model_validate(item)
        except ValidationError as e:
            bad.append(f"item {i}: " + "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()))
            continue
        if mcq.source not in by_n:
            bad.append(f"item {i}: source {mcq.source} is not one of the slides")
            continue
        key = " ".join(mcq.question.lower().split())
        if key in seen:
            bad.append(f"item {i}: repeats an earlier question")
            continue
        seen.add(key)
        ok.append(QuizQuestion(mcq, by_n[mcq.source]))
    return ok, bad


def generate_quiz(cfg: dict, store, provider, filters: SearchFilters | None = None, n: int = 5,
                  seed: int = 0) -> Quiz:
    """n validated MCQs (fewer if the model keeps failing; the reasons are in Quiz.rejected)."""
    q = cfg["quiz"]
    if not 1 <= n <= q["max_questions"]:
        raise ValueError(f"n must be 1..{q['max_questions']}, got {n}")
    sources = pick_slides(store, filters, cfg, seed)
    quiz = Quiz([], requested=n)
    seen: set[str] = set()
    while len(quiz.questions) < n and quiz.attempts < q["max_attempts"]:
        missing = n - len(quiz.questions)
        user = f"Slides:\n\n{sources_block(sources)}\n\nWrite {missing} questions."
        if quiz.questions:
            done = "\n".join(f"- {x.mcq.question}" for x in quiz.questions)
            user += f" Do not repeat these questions:\n{done}"
        quiz.attempts += 1
        reply = provider.complete(QUIZ_SYSTEM, user, q["max_tokens"], cfg["llm"]["temperature"], json_mode=True).text
        items = json_items(reply, "questions")
        if items is None:
            quiz.rejected.append(f"attempt {quiz.attempts}: reply was not JSON with a 'questions' list")
            continue
        ok, bad = _validate(items, sources, seen, quiz.generated + 1)
        quiz.generated += len(items)
        quiz.questions += ok[:missing]
        quiz.rejected += bad
    return quiz
