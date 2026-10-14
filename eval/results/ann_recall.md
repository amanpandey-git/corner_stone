# ANN vs brute force - recall@10 and latency

Generated 2026-10-15 by `eval/ann_vs_bruteforce.py`. Nothing tuned: ef_search values are
the fixed sweep 10 / 50 / 100; M=16, ef_construction=200 from config.yaml.
Exact search = numpy `vectors @ query` + top-10. Recall@10 = |ANN ∩ exact| / 10, mean over queries.
CPU only, single query per call.

## A. Real index (328 vectors, dim 384, 191 queries = distinct chunk section headings)

Searched through the saved index itself (`HNSWIndex.search`), compared with numpy exact search on its own vectors.

| ef_search | recall@10 | HNSW p50 (ms) | HNSW p95 (ms) | exact p50 (ms) | exact p95 (ms) |
|---|---|---|---|---|---|
| 10 | 0.952 | 0.046 | 0.070 | 0.026 | 0.032 |
| 50 (default) | 0.995 | 0.071 | 0.085 | 0.026 | 0.032 |
| 100 | 0.996 | 0.105 | 0.171 | 0.026 | 0.032 |

Queries are the section headings of the indexed chunks, embedded with the bge query prefix. They are
**not** the labelled evaluation questions.

## B. Synthetic scale check (10000 vectors, 200 queries)

Vectors are real chunk vectors perturbed with Gaussian noise and renormalised (**synthetic**: it shows how
HNSW behaves on a graph 30x bigger; it is not a retrieval-quality result). Build time 0.8 s.

| ef_search | recall@10 | HNSW p50 (ms) | HNSW p95 (ms) | exact p50 (ms) | exact p95 (ms) |
|---|---|---|---|---|---|
| 10 | 0.975 | 0.054 | 0.243 | 0.823 | 1.380 |
| 50 (default) | 1.000 | 0.113 | 0.180 | 0.823 | 1.380 |
| 100 | 1.000 | 0.337 | 0.561 | 0.823 | 1.380 |

## Reading the numbers
- Target from CLAUDE.md: recall@10 >= 0.95 at the default ef_search (50):
  real index **0.995**,
  synthetic **1.000**.
- With only 328 vectors an exhaustive scan is as fast as the graph, and HNSW explores most of the graph,
  so recall near 1.0 is expected there; the synthetic run is the more informative check of the algorithm.
- Latency grows with ef_search; recall rises with it. That trade-off is what ef_search controls.
