# Answer evaluation - split `dev` - Phase 2 v1 prompt, gate off

**PARTIAL RUN**: stopped after 17 questions: judge failed 3 times in a row (LLMRateLimited: gemini gemini-3.5-flash: HTTP 429 RESOURCE_EXHAUSTED)

Generated 2026-10-15 by `eval/answer_eval.py --split dev --mode concise`. Answerer `openai/gpt-oss-120b`, judge `gemini-3.5-flash`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 17 (17 answerable, 0 unanswerable) |
| answered (not abstained) | 16 (11 checked by the judge, 5 not checkable) |
| **citation accuracy** | **92.3%** (12/13 citations supported) |
| **faithfulness** | **72.7%** (8/11 answers fully cited and supported) |
| cites a labelled page | 100.0% (16 answered answerable questions) |
| **abstention on unanswerable** | **0/0** |
| false abstention on answerable | 1/17 |
| **time to first token p50 / p95** | **845 ms / 46563 ms** (14 live answers) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | faithful | 0.840 | 1 | 0 | 0 | 0 | yes | 54 (cached) |
| 2 | yes | unfaithful | 0.863 | 1 | 1 | 0 | 0 | yes | 36 (cached) |
| 3 | yes | answered | 0.876 | 2 | - | 0 | 0 | yes | 38 (cached) |
| 4 | yes | unfaithful | 0.826 | 1 | 0 | 1 | 0 | yes | 704 |
| 5 | yes | faithful | 0.908 | 2 | 0 | 0 | 0 | yes | 736 |
| 6 | yes | faithful | 0.788 | 1 | 0 | 0 | 0 | yes | 836 |
| 7 | yes | answered | 0.842 | 1 | - | 0 | 0 | yes | 679 |
| 8 | yes | faithful | 0.772 | 1 | 0 | 0 | 0 | yes | 44571 |
| 9 | yes | faithful | 0.784 | 2 | 0 | 0 | 0 | yes | 701 |
| 10 | yes | faithful | 0.805 | 1 | 0 | 0 | 0 | yes | 708 |
| 11 | yes | faithful | 0.792 | 1 | 0 | 0 | 0 | yes | 2201 |
| 12 | yes | unfaithful | 0.825 | 1 | 0 | 1 | 0 | yes | 50262 |
| 13 | yes | faithful | 0.846 | 1 | 0 | 0 | 0 | yes | 1021 |
| 14 | yes | abstained (model) | 0.775 | 0 | - | 0 | 0 | - | 1611 |
| 15 | yes | answered | 0.898 | 2 | - | 0 | 0 | yes | 639 |
| 16 | yes | answered | 0.838 | 1 | - | 0 | 0 | yes | 40414 |
| 17 | yes | answered | 0.869 | 1 | - | 0 | 0 | yes | 854 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.772, values 0.772, 0.775, 0.784, 0.788, 0.792, 0.805, 0.825, 0.826 ...
- unanswerable: 
