import copy

import pytest

from cornerstone import Chunk, RerankerUnavailable, SearchResult
from cornerstone.embeddings import Embedder
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.pipeline import ingest_file
from cornerstone.rerank import Reranker, load_reranker
from cornerstone.search import search

from conftest import SAMPLES


@pytest.fixture(scope="module")
def reranker(cfg):
    return Reranker(cfg)


def result(cid: int, text: str, header: str | None = None, score: float = 0.5) -> SearchResult:
    c = Chunk(chunk_id=cid, doc_id=1, file_name="notes.pdf", text=text, chunk_index=cid, token_count=10,
              page_start=cid, page_end=cid, context_header=header)
    return SearchResult(c, score, cid, text, scores={"vector": score})


def test_relevant_passage_moves_to_the_top(reranker):
    res = [result(1, "Paging divides physical memory into fixed-size frames."),
           result(2, "The CPU scheduler picks the next process from the ready queue."),
           result(3, "A deadlock happens when each process in a set waits for a resource held by another.")]
    out = reranker.rerank("What is a deadlock?", res, 3)
    assert out[0].chunk.chunk_id == 3
    assert [r.rank for r in out] == [1, 2, 3]
    assert all(out[i].score >= out[i + 1].score for i in range(2))


def test_scores_keep_earlier_stages_and_input_is_not_mutated(reranker):
    res = [result(1, "Round robin gives each process a time quantum.", score=0.7),
           result(2, "SCAN moves the disk head like an elevator.", score=0.6)]
    before = copy.deepcopy(res)
    out = reranker.rerank("time quantum in round robin", res, 2)
    assert res == before
    assert out[0].scores["vector"] == 0.7 and out[0].scores["rerank"] == out[0].score


def test_top_k_cuts_and_empty_input(reranker):
    res = [result(i, f"slide {i} about disk scheduling") for i in range(1, 6)]
    assert len(reranker.rerank("disk", res, 2)) == 2
    assert reranker.rerank("disk", [], 5) == []
    with pytest.raises(ValueError):
        reranker.rerank("disk", res, 0)


def test_context_header_is_read(reranker):
    # identical body text: only the header says which one is about SSTF
    res = [result(1, "Worked example: total head movement.", header="Unit 4 > SCAN"),
           result(2, "Worked example: total head movement.", header="Unit 4 > SSTF shortest seek time first")]
    assert reranker.rerank("SSTF shortest seek time first example", res, 2)[0].chunk.chunk_id == 2


def test_unavailable_model_raises_named_error(cfg):
    bad = copy.deepcopy(cfg)
    bad["rerank"]["model_revision"] = "0" * 40
    with pytest.raises(RerankerUnavailable, match="ms-marco"):
        Reranker(bad)


def test_load_reranker_follows_the_switch(cfg):
    off = copy.deepcopy(cfg)
    off["retrieval"]["rerank"] = False
    assert load_reranker(off) is None


def test_search_with_rerank_on(cfg, reranker, tmp_path):
    on = copy.deepcopy(cfg)
    on["retrieval"]["rerank"] = True
    store = MetadataStore(tmp_path / "m.sqlite")
    index = HNSWIndex.from_config(on)
    emb = Embedder(on)
    ingest_file(SAMPLES / "Unit 5_Part 2_System Protection.pdf", on, store, index, emb, tmp_path / "h.faiss")
    with pytest.raises(ValueError, match="reranker"):
        search("access matrix", 5, on, store, index, emb)
    res = search("What is an access matrix?", 5, on, store, index, emb, reranker=reranker)
    assert len(res) == 5 and [r.rank for r in res] == [1, 2, 3, 4, 5]
    assert all({"vector", "rerank"} <= set(r.scores) for r in res)
    assert all(res[i].score >= res[i + 1].score for i in range(4))
    store.close()
