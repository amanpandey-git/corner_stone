import json
from datetime import date

import pytest

from cornerstone.embeddings import Embedder
from cornerstone.flashcards import card_from_question, generate_flashcards
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.llm import FakeProvider
from cornerstone.pipeline import ingest_file
from cornerstone.quiz import generate_quiz
from cornerstone.study_store import StudyStore

TODAY = date(2026, 10, 20)


@pytest.fixture(scope="module")
def store(cfg, small_pdf, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cards_idx")
    s = MetadataStore(tmp / "m.sqlite")
    ingest_file(small_pdf, cfg, s, HNSWIndex.from_config(cfg), Embedder(cfg), tmp / "h.faiss")
    yield s
    s.close()


def test_cards_are_linked_to_slides_and_validated(cfg, store, tmp_path):
    reply = json.dumps({"cards": [{"front": "Least privilege", "back": "Give only the rights needed.", "source": 1},
                                  {"front": "Domain", "back": "A set of access rights.", "source": 2},
                                  {"front": "", "back": "x", "source": 1},
                                  {"front": "Ghost", "back": "y", "source": 42},
                                  {"front": "least  privilege", "back": "dup", "source": 1}]})
    cards, rejected = generate_flashcards(cfg, store, FakeProvider([reply]), n=5, today=TODAY)
    assert [c.front for c in cards] == ["Least privilege", "Domain"]
    assert len(rejected) == 3 and "source 42" in rejected[1] and "repeats" in rejected[2]
    assert cards[0].file_name.startswith("Unit 5") and cards[0].page is not None and cards[0].unit == "Unit 5"
    ss = StudyStore(tmp_path / "s.sqlite")
    assert len(ss.add_cards(cards)) == 2 and len(ss.due(TODAY)) == 2


def test_not_json_and_bounds(cfg, store):
    assert generate_flashcards(cfg, store, FakeProvider(["nope"]), n=3) == ([], ["reply was not JSON with a 'cards' list"])
    with pytest.raises(ValueError):
        generate_flashcards(cfg, store, FakeProvider(["{}"]), n=0)


def test_wrong_quiz_answer_becomes_a_card(cfg, store):
    item = {"question": "What does a domain define?", "options": ["Access rights", "A disk", "A thread", "A port"],
            "answer": 0, "explanation": "A domain is a set of access rights.", "source": 1}
    q = generate_quiz(cfg, store, FakeProvider([json.dumps({"questions": [item]})]), n=1).questions[0]
    card = card_from_question(q, TODAY, unit="Unit 5")
    assert card.front == "What does a domain define?" and card.back.startswith("Access rights.")
    assert card.origin == "quiz" and card.page == q.source.page_start and card.due == TODAY
