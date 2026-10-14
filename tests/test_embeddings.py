import numpy as np
import pytest

from cornerstone import EmptyQuery
from cornerstone.embeddings import Embedder


@pytest.fixture(scope="module")
def emb(cfg):
    return Embedder(cfg)


PASSAGES = [
    "A deadlock occurs when a set of processes are blocked, each holding a resource and waiting for another.",
    "To bake sourdough bread, mix flour, water and salt, then let the dough ferment overnight.",
    "Paging divides physical memory into fixed-size frames and logical memory into pages.",
]


def test_dimension_and_dtype(emb):
    v = emb.embed_passages(PASSAGES)
    assert v.shape == (3, 384) and v.dtype == np.float32


def test_unit_norm(emb):
    v = emb.embed_passages(PASSAGES)
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-5)
    assert np.isclose(np.linalg.norm(emb.embed_query("what is paging?")), 1.0, atol=1e-5)


def test_query_prefers_related_passage(emb):
    p = emb.embed_passages(PASSAGES)
    q = emb.embed_query("What is a deadlock in an operating system?")
    scores = p @ q
    assert scores[0] > scores[1] and scores[0] > scores[2]
    q2 = emb.embed_query("How does memory paging work?")
    assert int(np.argmax(p @ q2)) == 2


def test_query_prefix_applied_to_queries_only(emb):
    text = "What is a deadlock?"
    plain = emb.embed_passages([text])[0]
    query = emb.embed_query(text)
    assert not np.allclose(plain, query, atol=1e-4)           # prefix changes the vector
    with_prefix = emb.embed_passages([emb.query_prefix + text])[0]
    assert np.allclose(query, with_prefix, atol=1e-5)          # and it is exactly the prefix
    assert emb.passage_prefix == ""


def test_batching_matches_single_encoding(emb):
    texts = [f"Process number {i} waits for resource {i * 7} in the ready queue." for i in range(70)]
    batch = emb.embed_passages(texts)
    assert batch.shape == (70, 384)
    assert np.allclose(batch[13], emb.embed_passages([texts[13]])[0], atol=1e-4)


def test_empty_inputs(emb):
    assert emb.embed_passages([]).shape == (0, 384)
    for bad in ("", "   ", "\n\t"):
        with pytest.raises(EmptyQuery):
            emb.embed_query(bad)
    with pytest.raises(ValueError, match="empty"):
        emb.embed_passages(["fine text", " "])


def test_very_long_query_is_truncated_not_fatal(emb, cfg):
    v = emb.embed_query("deadlock " * 5000)
    assert v.shape == (384,)


def test_count_tokens(emb):
    assert emb.count_tokens("deadlock") >= 1
    assert emb.count_tokens("a b c d e f") == 6
