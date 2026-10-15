# Ablation on the dev split (Phase 1)

One row per change, measured with `eval/retrieval_eval.py --split dev` (33 answerable dev questions; full
per-question output in `eval/results/ablation_runs/`). Rows that switch a stage on were run with a config variant
kept in `eval/configs/` (`--config eval/configs/<name>.yaml`): row 9 `hybrid.yaml`, row 10 `rerank.yaml`, row 11
`hybrid_rerank.yaml`; each differs from config.yaml only in the named switches. Dev is for decisions; the test split is reported once at the
end of Phase 1. p95 = end-to-end search latency (query embedding + retrieval + SQLite, k = 10) on the i5-1135G7.

| # | change | commit | hit@5 | MRR | p95 ms | notes |
|---|---|---|---|---|---|---|
| 0 | v0.1 (Stage 1 code and index) | 5f470b8 | 0.879 (29/33) | 0.816 | 43 | misses: 14 (FCFS seek, Unit 4 duplicates), 48 (cross-file starvation), 68 (context switch cost), 70 (huge time slice) |
| 1 | schema v2 + version check + rebuild | ba788d4 | 0.879 (29/33) | 0.816 | 63 | storage change only; same 328 chunks, same ranks (latency difference is run-to-run noise) |
| 2 | near-duplicate pages removed at ingest | 942b8ec | 0.879 (29/33) | 0.818 | 56 | 24 pages not indexed (Unit 4: 23, Unit 1-2: 1); 308 chunks. 48: rank 10 -> 7; 14 still >10 (its chunk merges p.9-11 under a mis-detected heading: target of slide chunking) |
| 3 | page images at ingest | 6b1b3dc | 0.879 (29/33) | 0.818 | 83 | no ranking change (expected); 422 PNGs, 49 MB in data/images; ingest of all 7 PDFs ~63 s vs ~45 s |
| 4 | slide chunking + "file > section" header | 72926dc | **0.939 (31/33)** | **0.835** | 55 | 328 chunks (1 slide each; 6 near-empty slides joined the next page). Better: 6, 8, 14 (>10 -> 8), 30, 48, 68 (7 -> 1), 78; worse but still hits: 7 (1 -> 3), 10, 36, 72 (1 -> 2). Misses: 14, 70 |
| 5 (reference, not a pipeline change) | keyword search only (FTS5 BM25, `--retriever keyword`) | 2817a36 | 0.818 (27/33) | 0.767 | 1 | ranks better than vector on 7, 10, 14 (8 -> 6), 48 (4 -> 1); misses 1, 72, 74 that vector ranks 1-2: complementary, so worth fusing (RRF, next) |
| 6 | collapse near-identical results at query time (vector candidates 30 -> collapse -> k) | dfa1293 | 0.939 (31/33) | 0.835 | 82 | no rank changed: ingest dedup already removed the copies in this corpus. Kept on as a safety net (near-copies across uploaded files); costs fetching 30 candidates instead of k |
| 7 | document / unit filters (none applied in eval) | 2fb2052 | 0.939 (31/33) | 0.835 | 66 | regression check only: unfiltered ranking unchanged; filter behaviour is covered by tests |
| 8 | compaction command | 53d96ce | 0.939 (31/33) | 0.835 | 47 | regression check: local index was freshly rebuilt, nothing to compact (328 -> 328); behaviour covered by tests |
| 9 | hybrid: vector + FTS5 keyword, fused with RRF (k=60, 30 candidates each) | 96788a2 | 0.848 (28/33) | 0.791 | 69 | **worse -> switched off by default.** Better: 10 (2 -> 1), 14 (8 -> 6), 48 (4 -> 1); worse: 1 (1 -> 7), 8 (3 -> 5), 11 (1 -> 2), 72 (2 -> 9), 74 (1 -> 7), mostly questions keyword search misses entirely. Answer in top 10: 32/33 both ways (no recall gain). Revisit with the reranker on 17 Oct |
| 10 | cross-encoder rerank (ms-marco-MiniLM-L-6-v2) of the 30 collapsed vector candidates | bd39e9d | 0.939 (31/33) | 0.817 | 2858 | **not adopted (no hit@5 gain, MRR lower, p95 2.9 s > 1 s budget)** -> `retrieval.rerank: false`. Better: 7 (3 -> 2), 10, 14 (8 -> 6), 36, 48 (4 -> 1), 70 (>10 -> 4, a dev miss fixed); worse: 8 (3 -> 5), 11, 68, 72 (2 -> >10, new miss), 74, 80 (1 -> 3). p50 2.0 s: 30 pairs of up to ~450 tokens on 4 CPU cores |
| 11 | hybrid RRF + cross-encoder rerank | bd39e9d | 0.939 (31/33) | 0.817 | 6297 | identical ranks to row 10 (the reranker re-sorts the candidate pool, which hybrid barely changes); slower. Not adopted; hybrid stays off |
