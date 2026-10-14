"""ANN quality check: HNSW (faiss) vs exact brute-force search (numpy) on the same vectors.

Metric: recall@10 = |ANN top-10 ∩ exact top-10| / 10, averaged over queries, at
ef_search = 10, 50, 100. Latency: per-query p50/p95 of one search call (ms).

Two runs, both reported:
  A. REAL    - the vectors of the real index (data/index), queried with the section headings
               of the indexed chunks (natural short queries). NOT the labelled eval questions.
  B. SYNTHETIC scale check - 10,000 vectors made by perturbing real ones, so the graph is big
               enough for recall to be a meaningful number. Clearly labelled synthetic.

Nothing here is tuned: ef_search values are fixed by CLAUDE.md Section X.

    PYTHONPATH=src python eval/ann_vs_bruteforce.py
"""
from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

import faiss
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

K = 10
EF_VALUES = (10, 50, 100)
RESULT_FILE = ROOT / "eval" / "results" / "ann_recall.md"
SYNTH_N = 10_000
SYNTH_QUERIES = 200
MAX_REAL_QUERIES = 300


def exact_topk(vectors: np.ndarray, query: np.ndarray, k: int) -> np.ndarray:
    """Indices (row numbers) of the k highest inner products, exact, best first."""
    scores = vectors @ query
    k = min(k, len(scores))
    part = np.argpartition(-scores, k - 1)[:k]
    return part[np.argsort(-scores[part], kind="stable")]


def recall_at_k(ann_ids: list[np.ndarray], exact_ids: list[np.ndarray], k: int = K) -> float:
    """Mean fraction of the exact top-k that the ANN search also returned."""
    hits = [len(set(a[:k].tolist()) & set(e[:k].tolist())) / min(k, len(e)) for a, e in zip(ann_ids, exact_ids)]
    return float(np.mean(hits)) if hits else float("nan")


def build_hnsw(vectors: np.ndarray, M: int, ef_construction: int) -> faiss.IndexHNSWFlat:
    idx = faiss.IndexHNSWFlat(vectors.shape[1], M, faiss.METRIC_INNER_PRODUCT)
    idx.hnsw.efConstruction = ef_construction
    idx.add(np.ascontiguousarray(vectors, dtype=np.float32))
    return idx


def sweep(vectors: np.ndarray, queries: np.ndarray, ann_search, row_ids: np.ndarray | None = None) -> list[dict]:
    """Recall and latency of an ANN search vs exact, for every ef_search value.

    ann_search(query, k, ef) -> labels. When the ANN labels are not row numbers (the real index
    uses chunk ids), pass row_ids so exact results are mapped to the same label space.
    """
    exact = []
    t_exact = []
    for q in queries:
        t = time.perf_counter()
        rows_ = exact_topk(vectors, q, K)
        t_exact.append((time.perf_counter() - t) * 1000)
        exact.append(row_ids[rows_] if row_ids is not None else rows_)
    rows = []
    for ef in EF_VALUES:
        ann_search(queries[0], K, ef)  # warm-up
        got, t_ann = [], []
        for q in queries:
            t = time.perf_counter()
            lab = ann_search(q, K, ef)
            t_ann.append((time.perf_counter() - t) * 1000)
            got.append(np.asarray(lab))
        rows.append({
            "ef": ef, "recall": recall_at_k(got, exact),
            "p50": float(np.percentile(t_ann, 50)), "p95": float(np.percentile(t_ann, 95)),
            "exact_p50": float(np.percentile(t_exact, 50)), "exact_p95": float(np.percentile(t_exact, 95)),
        })
    return rows


def table(rows: list[dict], default_ef: int) -> str:
    out = ["| ef_search | recall@10 | HNSW p50 (ms) | HNSW p95 (ms) | exact p50 (ms) | exact p95 (ms) |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        mark = " (default)" if r["ef"] == default_ef else ""
        out.append(f"| {r['ef']}{mark} | {r['recall']:.3f} | {r['p50']:.3f} | {r['p95']:.3f} | "
                   f"{r['exact_p50']:.3f} | {r['exact_p95']:.3f} |")
    return "\n".join(out)


def synthetic_vectors(base: np.ndarray, n: int, seed: int = 0) -> np.ndarray:
    """n unit vectors: random real vectors plus Gaussian noise (keeps real cluster structure)."""
    rng = np.random.default_rng(seed)
    picks = base[rng.integers(0, len(base), n)]
    v = picks + 0.35 * rng.standard_normal(picks.shape).astype(np.float32) / np.sqrt(base.shape[1])
    return (v / np.linalg.norm(v, axis=1, keepdims=True)).astype(np.float32)


def main() -> int:
    import yaml
    from cornerstone.embeddings import Embedder
    from cornerstone.index.hnsw_index import HNSWIndex
    from cornerstone.index.metadata_store import MetadataStore

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    h = cfg["hnsw"]
    index_dir = ROOT / cfg["paths"]["index_dir"]
    index = HNSWIndex.load(index_dir / "hnsw.faiss", cfg)
    store = MetadataStore(index_dir / "cornerstone.sqlite")
    ids, vecs = index.vectors()
    if len(ids) == 0:
        print("index is empty: ingest documents first", file=sys.stderr)
        return 1

    # A. real vectors, queries = distinct section headings of active chunks
    chunks = store.get_chunks(store.active_chunk_ids())
    heads = sorted({c.section_heading.strip() for c in chunks.values()
                    if c.section_heading and len(c.section_heading.split()) >= 3})[:MAX_REAL_QUERIES]
    emb = Embedder(cfg)
    queries = np.vstack([emb.embed_query(t) for t in heads])
    # the saved index itself (HNSWIndex.search), not a rebuilt copy
    real_rows = sweep(vecs, queries, lambda q, k, ef: index.search(q, k, ef)[0], row_ids=ids)

    # B. synthetic scale check
    synth = synthetic_vectors(vecs, SYNTH_N)
    sq = synthetic_vectors(vecs, SYNTH_QUERIES, seed=1)
    t = time.perf_counter()
    synth_hnsw = build_hnsw(synth, h["M"], h["ef_construction"])
    build_s = time.perf_counter() - t
    def synth_search(q, k, ef):
        synth_hnsw.hnsw.efSearch = max(ef, k)
        return synth_hnsw.search(q.reshape(1, -1), k)[1][0]

    synth_rows = sweep(synth, sq, synth_search)

    md = f"""# ANN vs brute force - recall@10 and latency

Generated {date.today().isoformat()} by `eval/ann_vs_bruteforce.py`. Nothing tuned: ef_search values are
the fixed sweep 10 / 50 / 100; M={h['M']}, ef_construction={h['ef_construction']} from config.yaml.
Exact search = numpy `vectors @ query` + top-10. Recall@10 = |ANN ∩ exact| / 10, mean over queries.
CPU only, single query per call.

## A. Real index ({len(ids)} vectors, dim {vecs.shape[1]}, {len(queries)} queries = distinct chunk section headings)

Searched through the saved index itself (`HNSWIndex.search`), compared with numpy exact search on its own vectors.

{table(real_rows, h['ef_search'])}

Queries are the section headings of the indexed chunks, embedded with the bge query prefix. They are
**not** the labelled evaluation questions.

## B. Synthetic scale check ({SYNTH_N} vectors, {SYNTH_QUERIES} queries)

Vectors are real chunk vectors perturbed with Gaussian noise and renormalised (**synthetic**: it shows how
HNSW behaves on a graph 30x bigger; it is not a retrieval-quality result). Build time {build_s:.1f} s.

{table(synth_rows, h['ef_search'])}

## Reading the numbers
- Target from CLAUDE.md: recall@10 >= 0.95 at the default ef_search ({h['ef_search']}):
  real index **{next(r for r in real_rows if r['ef'] == h['ef_search'])['recall']:.3f}**,
  synthetic **{next(r for r in synth_rows if r['ef'] == h['ef_search'])['recall']:.3f}**.
- With only {len(ids)} vectors an exhaustive scan is as fast as the graph, and HNSW explores most of the graph,
  so recall near 1.0 is expected there; the synthetic run is the more informative check of the algorithm.
- Latency grows with ef_search; recall rises with it. That trade-off is what ef_search controls.
"""
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(md, encoding="utf-8")
    print(md)
    print(f"saved {RESULT_FILE}")
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
