import sys

import numpy as np

from conftest import ROOT

sys.path.insert(0, str(ROOT / "eval"))
import ann_vs_bruteforce as ev  # noqa: E402


def unit(n, d=32, seed=0):
    v = np.random.default_rng(seed).standard_normal((n, d)).astype(np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_exact_topk_matches_full_sort():
    v, q = unit(500), unit(1, seed=5)[0]
    expect = np.argsort(-(v @ q), kind="stable")[:10]
    assert list(ev.exact_topk(v, q, 10)) == list(expect)
    assert len(ev.exact_topk(v[:4], q, 10)) == 4          # k > n


def test_recall_arithmetic():
    exact = [np.arange(10)]
    assert ev.recall_at_k([np.arange(10)], exact) == 1.0
    assert ev.recall_at_k([np.arange(5, 15)], exact) == 0.5
    assert ev.recall_at_k([np.arange(100, 110)], exact) == 0.0


def test_sweep_on_small_data_is_near_exact():
    v, q = unit(300), unit(20, seed=9)
    h = ev.build_hnsw(v, 16, 200)

    def ann(qv, k, ef):
        h.hnsw.efSearch = max(ef, k)
        return h.search(qv.reshape(1, -1), k)[1][0]

    rows = ev.sweep(v, q, ann)
    assert [r["ef"] for r in rows] == [10, 50, 100]
    assert rows[-1]["recall"] >= 0.95
    assert rows[0]["recall"] <= rows[-1]["recall"] + 1e-9 or rows[0]["recall"] >= 0.9
    assert all(r["p50"] >= 0 and r["p95"] >= r["p50"] for r in rows)


def test_index_vectors_roundtrip_ids(cfg):
    from cornerstone.index.hnsw_index import HNSWIndex
    idx = HNSWIndex.from_config(cfg)
    v = unit(25, d=384)
    ids = np.arange(25) + 500
    idx.add(ids, v)
    got_ids, got_v = idx.vectors()
    assert list(got_ids) == list(ids) and np.allclose(got_v, v, atol=1e-6)
