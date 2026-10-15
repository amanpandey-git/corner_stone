# Answer evaluation - split `dev` - 5-mark sample, mode v5 (sourced intro, conclusion only if supported)

**PARTIAL RUN**: stopped after 6 questions: LLMRateLimited: groq openai/gpt-oss-120b: HTTP 429 tokens

Generated 2026-10-16 by `eval/answer_eval.py --split dev --mode 5-mark`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 6 (6 answerable, 0 unanswerable) |
| answered (not abstained) | 6 (6 checked by the judge, 0 not checkable) |
| **citation accuracy** | **100.0%** (29/29 citations supported) |
| **faithfulness** | **100.0%** (6/6 answers fully cited and supported) |
| cites a labelled page | 100.0% (6 answered answerable questions) |
| **abstention on unanswerable** | **0/0** |
| false abstention on answerable | 0/6 |
| **time to first token p50 / p95** | **828 ms / 1906 ms** (6 live answers; excludes 57 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | faithful | 0.840 | 5 | 0 | 0 | 0 | yes | 1689 |
| 2 | yes | faithful | 0.863 | 6 | 0 | 0 | 0 | yes | 734 |
| 3 | yes | faithful | 0.876 | 5 | 0 | 0 | 0 | yes | 748 |
| 4 | yes | faithful | 0.826 | 4 | 0 | 0 | 0 | yes | 908 |
| 5 | yes | faithful | 0.908 | 7 | 0 | 0 | 0 | yes | 641 |
| 6 | yes | faithful | 0.788 | 2 | 0 | 0 | 0 | yes | 1978 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.788, values 0.788, 0.826, 0.840, 0.863, 0.876, 0.908 ...
- unanswerable: 
