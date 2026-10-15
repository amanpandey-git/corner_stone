"""Flashcards from the student's slides, each linked to its source slide (ARCHITECTURE.md 12.2).

Same pattern as the quiz: numbered slides in, JSON out, every card validated, invalid cards dropped with a reason.
A wrongly answered quiz question can also become a card (card_from_question).
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ValidationError, field_validator

from cornerstone import SearchFilters
from cornerstone.quiz import QuizQuestion, json_items, pick_slides, sources_block
from cornerstone.study_store import Card

CARDS_SYSTEM = """You make revision flashcards for a university student from slides of their own course notes.

Reply with JSON: {"cards": [{"front": "...", "back": "...", "source": 1}]}
Rules:
1. "front" is a short question or term; "back" is the answer in at most 2 sentences, using the slide's wording.
2. Each card covers one fact, definition or step stated on one numbered slide; "source" is that slide's number.
3. Use only the slides; no outside facts. Do not repeat a card.
Reply with the JSON object only."""


class CardDraft(BaseModel):
    front: str
    back: str
    source: int

    @field_validator("front", "back")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()


def _unit(store, doc_id: int) -> str | None:
    d = store.get_document(doc_id)
    return d.unit if d else None


def generate_flashcards(cfg: dict, store, provider, filters: SearchFilters | None = None, n: int = 10,
                        seed: int = 0, today: date | None = None) -> tuple[list[Card], list[str]]:
    """Up to n cards (one call) and the reasons for rejected ones. Cards are due today and not yet saved."""
    f = cfg["flashcards"]
    if not 1 <= n <= f["max_cards"]:
        raise ValueError(f"n must be 1..{f['max_cards']}, got {n}")
    today = today or date.today()
    sources = pick_slides(store, filters, cfg, seed)
    user = f"Slides:\n\n{sources_block(sources)}\n\nMake {n} flashcards."
    reply = provider.complete(CARDS_SYSTEM, user, f["max_tokens"], cfg["llm"]["temperature"], json_mode=True).text
    items = json_items(reply, "cards")
    if items is None:
        return [], ["reply was not JSON with a 'cards' list"]
    by_n = {s.n: s for s in sources}
    cards, rejected, seen = [], [], set()
    for i, item in enumerate(items, 1):
        try:
            d = CardDraft.model_validate(item)
        except ValidationError as e:
            rejected.append(f"card {i}: " + "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()))
            continue
        if d.source not in by_n:
            rejected.append(f"card {i}: source {d.source} is not one of the slides")
            continue
        key = " ".join(d.front.lower().split())
        if key in seen:
            rejected.append(f"card {i}: repeats an earlier card")
            continue
        seen.add(key)
        s = by_n[d.source]
        cards.append(Card(0, d.front, d.back, s.file_name, s.page_start, s.doc_id, s.chunk_id,
                          _unit(store, s.doc_id), today))
    return cards[:n], rejected


def card_from_question(q: QuizQuestion, today: date, unit: str | None = None) -> Card:
    """A quiz question the student got wrong, as a card: front = question, back = correct option + explanation."""
    m = q.mcq
    s = q.source
    return Card(0, m.question, f"{m.options[m.answer]}. {m.explanation}", s.file_name, s.page_start, s.doc_id,
                s.chunk_id, unit, today, origin="quiz")
