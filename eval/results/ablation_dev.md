# Ablation on the dev split (Phase 1)

One row per change, measured with `eval/retrieval_eval.py --split dev` (33 answerable dev questions; full
per-question output in `eval/results/ablation_runs/`). Dev is for decisions; the test split is reported once at the
end of Phase 1. p95 = end-to-end search latency (query embedding + retrieval + SQLite, k = 10) on the i5-1135G7.

| # | change | commit | hit@5 | MRR | p95 ms | notes |
|---|---|---|---|---|---|---|
| 0 | v0.1 (Stage 1 code and index) | 5f470b8 | 0.879 (29/33) | 0.816 | 43 | misses: 14 (FCFS seek, Unit 4 duplicates), 48 (cross-file starvation), 68 (context switch cost), 70 (huge time slice) |
| 1 | schema v2 + version check + rebuild | ba788d4 | 0.879 (29/33) | 0.816 | 63 | storage change only; same 328 chunks, same ranks (latency difference is run-to-run noise) |
| 2 | near-duplicate pages removed at ingest | 942b8ec | 0.879 (29/33) | 0.818 | 56 | 24 pages not indexed (Unit 4: 23, Unit 1-2: 1); 308 chunks. 48: rank 10 -> 7; 14 still >10 (its chunk merges p.9-11 under a mis-detected heading: target of slide chunking) |
| 3 | page images at ingest | 6b1b3dc | 0.879 (29/33) | 0.818 | 83 | no ranking change (expected); 422 PNGs, 49 MB in data/images; ingest of all 7 PDFs ~63 s vs ~45 s |
| 4 | slide chunking + "file > section" header | 72926dc | **0.939 (31/33)** | **0.835** | 55 | 328 chunks (1 slide each; 6 near-empty slides joined the next page). Better: 6, 8, 14 (>10 -> 8), 30, 48, 68 (7 -> 1), 78; worse but still hits: 7 (1 -> 3), 10, 36, 72 (1 -> 2). Misses: 14, 70 |
| 5 (reference, not a pipeline change) | keyword search only (FTS5 BM25, `--retriever keyword`) | step 5 | 0.818 (27/33) | 0.767 | 1 | ranks better than vector on 7, 10, 14 (8 -> 6), 48 (4 -> 1); misses 1, 72, 74 that vector ranks 1-2: complementary, so worth fusing (RRF, next) |
