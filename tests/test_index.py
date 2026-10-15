import copy
import json

import numpy as np
import pytest

from cornerstone import ModelMismatch
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.manifest import manifest_path_for

DIM = 384


def unit_vectors(n: int, seed: int = 0) -> np.ndarray:
    v = np.random.default_rng(seed).standard_normal((n, DIM)).astype(np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


@pytest.fixture
def filled(cfg):
    idx = HNSWIndex.from_config(cfg)
    vecs = unit_vectors(200)
    ids = np.arange(200) + 1000          # labels are chunk_ids, not positions
    idx.add(ids, vecs)
    return idx, ids, vecs


def test_add_and_search_returns_chunk_ids(filled):
    idx, ids, vecs = filled
    assert len(idx) == 200
    labels, scores = idx.search(vecs[17], k=5)
    assert labels[0] == 1017 and scores[0] == pytest.approx(1.0, abs=1e-4)
    assert len(labels) == 5 and np.all(np.diff(scores) <= 1e-6)   # best first


def test_incremental_add_does_not_rebuild(cfg, filled):
    idx, _, vecs = filled
    more = unit_vectors(50, seed=1)
    idx.add(np.arange(50) + 5000, more)
    assert len(idx) == 250
    assert idx.search(more[3], 1)[0][0] == 5003
    assert idx.search(vecs[3], 1)[0][0] == 1003            # old vectors still there


def test_save_reload_same_results_and_manifest_next_to_index(cfg, filled, tmp_path):
    idx, ids, vecs = filled
    path = tmp_path / "hnsw.faiss"
    idx.save(path)
    assert manifest_path_for(path).is_file()
    again = HNSWIndex.load(path, cfg)
    assert len(again) == 200
    for i in (0, 50, 199):
        a_l, a_s = idx.search(vecs[i], 10)
        b_l, b_s = again.search(vecs[i], 10)
        assert list(a_l) == list(b_l) and np.allclose(a_s, b_s)
    assert set(again.all_ids()) == set(ids)
    again.add([9999], unit_vectors(1, seed=9))              # still incremental after reload
    assert len(again) == 201


@pytest.mark.parametrize("path, value", [
    (("embedding", "model_name"), "sentence-transformers/all-MiniLM-L6-v2"),
    (("embedding", "model_revision"), "deadbeef"),
    (("embedding", "dimension"), 768),
    (("hnsw", "space"), "l2"),
    (("embedding", "normalize"), False),
])
def test_manifest_mismatch_raises(cfg, filled, tmp_path, path, value):
    idx, _, _ = filled
    f = tmp_path / "hnsw.faiss"
    idx.save(f)
    bad = copy.deepcopy(cfg)
    bad[path[0]][path[1]] = value
    with pytest.raises(ModelMismatch, match=path[1]):
        HNSWIndex.load(f, bad)


def test_missing_or_corrupt_manifest_raises(cfg, filled, tmp_path):
    idx, _, _ = filled
    f = tmp_path / "hnsw.faiss"
    idx.save(f)
    m = manifest_path_for(f)
    m.write_text("{not json", encoding="utf-8")
    with pytest.raises(ModelMismatch):
        HNSWIndex.load(f, cfg)
    m.unlink()
    with pytest.raises(ModelMismatch, match="manifest not found"):
        HNSWIndex.load(f, cfg)


def test_manifest_contents(cfg, filled, tmp_path):
    idx, _, _ = filled
    f = tmp_path / "hnsw.faiss"
    idx.save(f)
    m = json.loads(manifest_path_for(f).read_text(encoding="utf-8"))
    assert m["model_name"] == cfg["embedding"]["model_name"]
    assert m["dimension"] == 384 and m["space"] == "cosine" and m["normalized"] is True
    assert m["created_at"]


def test_empty_index_search_returns_nothing_and_roundtrips(cfg, tmp_path):
    idx = HNSWIndex.from_config(cfg)
    labels, scores = idx.search(unit_vectors(1)[0], k=5)
    assert len(labels) == 0 and len(scores) == 0 and len(idx) == 0
    f = tmp_path / "empty.faiss"
    idx.save(f)
    assert len(HNSWIndex.load(f, cfg)) == 0


def test_k_larger_than_index_returns_what_exists(cfg):
    idx = HNSWIndex.from_config(cfg)
    idx.add([1, 2, 3], unit_vectors(3))
    labels, _ = idx.search(unit_vectors(1, seed=4)[0], k=10)
    assert sorted(labels) == [1, 2, 3]


def test_ef_search_below_k_still_returns_k(filled):
    idx, _, vecs = filled
    labels, _ = idx.search(vecs[0], k=50, ef_search=10)
    assert len(labels) == 50


def test_bad_inputs_rejected(cfg, filled):
    idx, ids, vecs = filled
    with pytest.raises(ValueError, match="already in the index"):
        idx.add([ids[0]], unit_vectors(1, seed=7))
    with pytest.raises(ValueError, match="unique"):
        idx.add([1, 1], unit_vectors(2, seed=8))
    with pytest.raises(ValueError, match="shape"):
        idx.add([77], np.ones((1, 10), dtype=np.float32))
    with pytest.raises(ValueError, match="normalised"):
        idx.add([78], unit_vectors(1, seed=2) * 3)
    with pytest.raises(ValueError, match="dimension"):
        idx.search(np.ones(10, dtype=np.float32), 3)
    with pytest.raises(ValueError, match="k must"):
        idx.search(vecs[0], 0)


def test_old_index_version_raises_index_version_mismatch(cfg, filled, tmp_path):
    from cornerstone import IndexVersionMismatch
    idx, _, _ = filled
    f = tmp_path / "hnsw.faiss"
    idx.save(f)
    m = manifest_path_for(f)
    data = json.loads(m.read_text(encoding="utf-8"))
    assert data["index_version"] == 2
    data["index_version"] = 1
    m.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(IndexVersionMismatch, match="schema 1.*cli rebuild"):
        HNSWIndex.load(f, cfg)
