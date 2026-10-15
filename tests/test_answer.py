import copy

import pytest

from cornerstone import EmptyQuery
from cornerstone.answer import (MODES, NOT_IN_NOTES, Answer, Source, answer, build_prompt, finalise,
                                stream_answer)
from cornerstone.embeddings import Embedder
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.llm import FakeProvider
from cornerstone.pipeline import ingest_file

QUESTION = "What is the principle of least privilege?"


@pytest.fixture(scope="module")
def stack(cfg, small_pdf, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("answer_idx")
    store = MetadataStore(tmp / "m.sqlite")
    index = HNSWIndex.from_config(cfg)
    emb = Embedder(cfg)
    ingest_file(small_pdf, cfg, store, index, emb, tmp / "h.faiss")
    yield store, index, emb
    store.close()


def src(n, text="Paging divides memory into frames.", page=3):
    return Source(n, n, 1, "Unit 3_Memory.pdf", page, page, "Paging", text)


def test_build_prompt_numbers_sources_and_mode(cfg):
    system, user = build_prompt("What is paging?", [src(1), src(2, page=4)], "5-mark", cfg)
    assert "NOT_IN_NOTES" in system and cfg["answer"]["modes"]["5-mark"]["instruction"] in system
    assert user.startswith("Sources:") and "[1] Unit 3_Memory, p.3 - Paging" in user and "[2] Unit 3_Memory, p.4" in user
    assert user.rstrip().endswith("Question: What is paging?")
    with pytest.raises(ValueError):
        build_prompt("q", [src(1)], "essay", cfg)


def test_every_mode_has_config(cfg):
    for m in MODES:
        assert cfg["answer"]["modes"][m]["max_tokens"] > 0 and cfg["answer"]["modes"][m]["instruction"]


def test_finalise_abstentions_and_cleanup():
    s = [src(1), src(2)]
    a = finalise("q", "concise", "NOT_IN_NOTES", s)
    assert a.abstained and a.abstain_reason == "model" and a.text == NOT_IN_NOTES
    a = finalise("q", "concise", "Paging is great and widely used in kernels.", s)
    assert a.abstained and a.abstain_reason == "no_citations" and a.uncited_sentences
    a = finalise("q", "concise", "Paging uses frames [1]. It avoids external fragmentation [5].", s)
    assert not a.abstained and a.text == "Paging uses frames [1]. It avoids external fragmentation."
    assert a.invalid_refs == [5] and a.uncited_sentences == ["It avoids external fragmentation."]
    assert [x.n for x in a.cited_sources()] == [1]


def test_answer_cites_and_streams(cfg, stack):
    store, index, emb = stack
    reply = "Least privilege gives each process only the rights it needs [1]. It limits damage from errors [2]."
    fake = FakeProvider([reply], chunk=5)
    items = list(stream_answer(QUESTION, "concise", cfg, store, index, emb, fake))
    final = items[-1]
    assert isinstance(final, Answer) and not final.abstained
    assert "".join(i for i in items[:-1]) == reply and len(items) > 3          # streamed in pieces
    assert [c.refs for c in final.citations] == [[1], [2]] and len(final.sources) == cfg["answer"]["k"]
    assert final.ttft_ms is not None and final.provider == "fake"
    system, user = fake.calls[0]
    assert QUESTION in user and "[1] Unit 5_Part 2_System Protection" in user


def test_model_abstention_streams_nothing(cfg, stack):
    store, index, emb = stack
    items = list(stream_answer("Who won the 2018 football world cup?", "concise", cfg, store, index, emb,
                               FakeProvider(["NOT_IN_NOTES"], chunk=3)))
    assert len(items) == 1 and items[0].abstained and items[0].abstain_reason == "model"


def test_short_reply_is_still_yielded(cfg, stack):
    store, index, emb = stack
    # shorter than the 12-character hold-back window: never released while streaming, yielded at the end
    items = list(stream_answer(QUESTION, "2-mark", cfg, store, index, emb, FakeProvider(["Yes [1]."])))
    assert items[0] == "Yes [1]." and len(items) == 2 and not items[-1].abstained


def test_retrieval_gate_skips_the_llm(cfg, stack):
    store, index, emb = stack
    gated = copy.deepcopy(cfg)
    gated["answer"]["min_vector_score"] = 0.99
    fake = FakeProvider(["should not be called [1]."])
    a = answer(QUESTION, "concise", gated, store, index, emb, fake)
    assert a.abstained and a.abstain_reason == "retrieval" and fake.calls == [] and a.top_vector_score < 0.99


def test_empty_index_abstains(cfg, tmp_path, stack):
    _, _, emb = stack
    store = MetadataStore(tmp_path / "e.sqlite")
    a = answer(QUESTION, "concise", cfg, store, HNSWIndex.from_config(cfg), emb, FakeProvider(["x [1]."]))
    assert a.abstained and a.abstain_reason == "retrieval" and a.sources == []
    store.close()


def test_bad_inputs(cfg, stack):
    store, index, emb = stack
    with pytest.raises(EmptyQuery):
        answer("  ", "concise", cfg, store, index, emb, FakeProvider(["x"]))
    with pytest.raises(ValueError):
        answer(QUESTION, "essay", cfg, store, index, emb, FakeProvider(["x"]))


def test_citation_check_with_judge(cfg, stack):
    store, index, emb = stack
    reply = "Least privilege gives minimal rights [1]. It was invented in 2020 [2]."
    judge = FakeProvider(['{"unsupported": [2]}'], name="judge")
    a = answer(QUESTION, "concise", cfg, store, index, emb, FakeProvider([reply]), judge=judge, check=True)
    assert a.unsupported == [1] and len(judge.calls) == 1
    a2 = answer(QUESTION, "concise", cfg, store, index, emb, FakeProvider([reply]), judge=judge, check=False)
    assert a2.unsupported is None
