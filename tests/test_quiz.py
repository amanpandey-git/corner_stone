import copy
import json

import pytest

from cornerstone import SearchFilters
from cornerstone.embeddings import Embedder
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.llm import FakeProvider
from cornerstone.pipeline import ingest_file
from cornerstone.quiz import MCQ, generate_quiz, json_items, pick_slides


@pytest.fixture(scope="module")
def store(cfg, small_pdf, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("quiz_idx")
    s = MetadataStore(tmp / "m.sqlite")
    ingest_file(small_pdf, cfg, s, HNSWIndex.from_config(cfg), Embedder(cfg), tmp / "h.faiss")
    yield s
    s.close()


def item(q="What does a domain define?", options=("A set of access rights", "A disk", "A thread", "A port"),
         answer=0, source=1):
    return {"question": q, "options": list(options), "answer": answer, "explanation": "Slide says so.",
            "source": source}


def reply(*items):
    return json.dumps({"questions": list(items)})


def test_pick_slides_spread_numbered_and_filtered(cfg, store):
    s = pick_slides(store, None, cfg, seed=1)
    assert 1 <= len(s) <= cfg["quiz"]["max_sources"] and [x.n for x in s] == list(range(1, len(s) + 1))
    pages = [x.page_start for x in s]
    assert pages == sorted(pages) and len(set(pages)) == len(pages)
    assert pick_slides(store, None, cfg, seed=1) == s                      # deterministic
    with pytest.raises(ValueError, match="no slides"):
        pick_slides(store, SearchFilters(units=["Unit 9"]), cfg)


def test_valid_quiz_in_one_call_with_sources(cfg, store):
    fake = FakeProvider([reply(item(), item(q="What is a capability list?", source=2))])
    quiz = generate_quiz(cfg, store, fake, n=2)
    assert len(quiz.questions) == 2 and quiz.attempts == 1 and quiz.generated == 2 and not quiz.rejected
    q2 = quiz.questions[1]
    assert q2.source.n == 2 and q2.source.file_name.startswith("Unit 5")
    assert "Slides:" in fake.calls[0][1] and "Write 2 questions." in fake.calls[0][1]


def test_bad_items_rejected_with_reasons_then_one_top_up(cfg, store):
    bad = [item(options=("a", "b", "c")), item(options=("a", "A", "b", "c")), item(answer=4), item(source=99),
           item(options=("x", "y", "z", "All of the above"))]
    fake = FakeProvider([reply(item(), *bad), reply(item(q="What is an access matrix?"))])
    quiz = generate_quiz(cfg, store, fake, n=2)
    assert len(quiz.questions) == 2 and quiz.attempts == 2 and quiz.generated == 7
    reasons = " | ".join(quiz.rejected)
    for word in ("4 options", "not distinct", "answer index 4", "source 99", "of the above"):
        assert word in reasons
    assert "Do not repeat" in fake.calls[1][1] and "Write 1 questions." in fake.calls[1][1]


def test_invalid_json_twice_gives_partial_quiz_and_stops(cfg, store):
    fake = FakeProvider(["not json at all", "still not json"])
    quiz = generate_quiz(cfg, store, fake, n=3)
    assert quiz.questions == [] and quiz.attempts == cfg["quiz"]["max_attempts"] == len(fake.calls)
    assert all("not JSON" in r for r in quiz.rejected)


def test_repeated_question_is_rejected(cfg, store):
    quiz = generate_quiz(cfg, store, FakeProvider([reply(item(), item())]), n=2)
    assert len(quiz.questions) == 1 and "repeats" in quiz.rejected[0]


def test_n_bounds_and_json_items(cfg, store):
    for n in (0, cfg["quiz"]["max_questions"] + 1):
        with pytest.raises(ValueError):
            generate_quiz(cfg, store, FakeProvider(["{}"]), n=n)
    assert json_items('Here: ```json\n{"questions": [1]}\n```', "questions") == [1]
    assert json_items('{"questions": "x"}', "questions") is None
    assert MCQ.model_validate(item()).options[0] == "A set of access rights"
