# Cornerstone Stage 2 - evaluation report (draft)

Every number below is copied from a result file in `eval/results/` (named in each table) and every test-split run is
logged in `NOTES.md`. Rules followed: tuning on the **dev** split only; the **test** split run once per checkpoint
(v0.1 baseline, end of Phase 1, Phase 2 answer evaluation), after a reviewer and an evaluation auditor; any change
made after seeing a test number is declared next to that number.

Corpus: 7 operating-systems slide decks (`samples/`, 422 pages). Questions: `eval/questions.jsonl`, 33 answerable +
5 unanswerable on dev, 33 answerable + 10 unanswerable on test (split rule in `eval/QUESTIONS_FORMAT.md`).
Hardware: Intel i5-1135G7, 8 GB RAM, CPU only.

## 1. Retrieval (Phase 1)

### 1.1 Test split (run once per checkpoint)

| metric | v0.1 baseline (`baseline_v0.1_test.md`) | Phase 1 (`phase1_test.md`) | target |
|---|---|---|---|
| hit@5 | 0.879 (29/33) | **0.939 (31/33)** | >= 0.90 |
| MRR (top 10) | 0.848 | **0.856** | - |
| v0.1 hits that became misses | - | **0** | <= 1 |
| multi-page questions: labelled pages in top 5 | 15/21 | 15/21 | - |
| cross-file questions with every file in top 5 | 2/5 | 3/5 | - |
| search latency p50 / p95 | 34 / 41 ms | 39 / 47 ms | p95 < 1 s |

Fixed by Phase 1: questions 41 (rank 7 -> 2) and 73 (6 -> 1). Still missed: 71 (thread cancellation) and 81
(cross-file FCFS CPU + disk).

### 1.2 Dev ablation (`ablation_dev.md`; one row per change, dev only)

| # | change | hit@5 | MRR | p95 ms | decision |
|---|---|---|---|---|---|
| 0 | v0.1 | 0.879 | 0.816 | 43 | baseline |
| 2 | near-duplicate pages removed at ingest | 0.879 | 0.818 | 56 | kept (24 copied slides no longer indexed) |
| 4 | one slide per chunk + "file > section" header | **0.939** | **0.835** | 55 | kept: the main gain |
| 5 | (reference) FTS5 keyword search alone | 0.818 | 0.767 | 1 | complementary misses -> try fusion |
| 6 | collapse near-identical results | 0.939 | 0.835 | 82 | kept as a safety net (no measured gain) |
| 9 | hybrid vector + keyword with RRF | 0.848 | 0.791 | 69 | **off**: hurt dev |
| 10 | cross-encoder reranker | 0.939 | 0.817 | 2858 | **off**: no gain, 2.9 s > 1 s |
| 11 | hybrid + reranker | 0.939 | 0.817 | 6297 | **off** |
| 12 | schema v3 rebuild (regression check) | 0.939 | 0.835 | 55 | identical ranks |

Two planned techniques (hybrid search, reranking) were built, tested and switched off because the measurements did
not support them; their code, tests and switches remain.

### 1.3 ANN quality (`ann_recall.md`, Stage 1)

HNSW recall@10 against exact search on the real index: 0.995 at the default ef_search = 50 (0.952 at 10).

## 2. Grounded answers (Phase 2)

Answerer `openai/gpt-oss-120b` (Groq), judge `qwen/qwen3.8-27b` (Groq, a different model family), k = 5 slides,
temperature 0. Definitions: ARCHITECTURE.md 11.4 and `eval/answer_eval.py`.

### 2.1 Test split (run once; `answer_eval_test.md`, `answer_eval_test_5mark.md`)

| metric | concise, all 43 questions | 5-mark sample (8 + 2) | target |
|---|---|---|---|
| citation accuracy | **100.0%** (75/75) | 96.6% (28/29) | >= 90% |
| faithfulness | **96.9%** (31/32) | 12.5% (1/8) | >= 90% |
| answer cites a labelled page | 96.9% | 100% | - |
| abstention on unanswerable | **10/10** | 2/2 | >= 8/10 |
| false abstention on answerable | 1/33 | 0/8 | - |
| time to first token p50 / p95 | **884 / 2071 ms** | 838 / 1173 ms | p50 < 3 s |

The concise mode meets every target. The 5-mark sample did not: 7 of 8 answers had an uncited one-sentence
introduction and conclusion, which the 5-mark format asked for. **Declared change after this test result:** the
exam-mode instructions now require a sourced introduction and a conclusion only when a slide supports one; this
was measured on a dev 5-mark sample only (2.3). The test numbers above remain the reported Phase 2 numbers.

### 2.2 Dev prompt iterations (`answer_runs/answer_eval_dev_v1..v3.md`, concise)

| prompt | change | citation accuracy | faithfulness | abstention | first token p50 |
|---|---|---|---|---|---|
| v1 | rules + numbered sources | 95.3% | 75.0% | 5/5 | 829 ms |
| v2 | cite every sentence, no unstated conclusions | 91.8% | 81.2% | 5/5 | 886 ms |
| v3 | one fact per sentence, say only what a slide states, format example | **100.0%** | **87.5%** | 5/5 | 925 ms |

v3 was chosen for the test run. The retrieval-score gate for abstention was not used: on dev the best-slide scores
of unanswerable questions (0.57-0.80) overlap those of answerable ones (from 0.57).

### 2.3 Dev 5-mark sample after the declared change (`answer_runs/answer_eval_dev_5mark_v3..v5.md`)

| mode instructions | citation accuracy | faithfulness |
|---|---|---|
| v3 (as tested) | 93.8% | 12.5% (1/8) |
| v4: cite introduction and conclusion | 90.6% | 50.0% (4/8) |
| v5: sourced introduction, conclusion only if supported | 100% (29/29) | 100% (6/6, PARTIAL: Groq's 200k tokens/day free-tier cap stopped the run after 6 of 8) |

## 3. Quiz (Phase 5; `quiz_eval.md`, one run, nothing tuned)

| metric | value | target |
|---|---|---|
| valid questions (schema + rules) | **100% (25/25)**, one model call per unit | >= 95% |
| correct answer supported by its cited slide (judge) | 96% (24/25) | - |

## 4. Limits of this evaluation

- The questions were written by the assistant at the user's request and checked against the slides
  (`eval/evidence.md`); a student-written set would be harder.
- One corpus (operating systems slides), 33 + 33 answerable questions: one question is about 3 points of hit@5.
- The citation judge is a language model; 20 answers per run are kept in full for the user's manual spot check
  (`answer_spotcheck_*.md`).
- Free-tier limits shape the runs: Groq allows 8000 tokens/minute and 200k tokens/day for the answer model; time to
  first token excludes the evaluation's own rate-limit queueing (reported next to the number).
