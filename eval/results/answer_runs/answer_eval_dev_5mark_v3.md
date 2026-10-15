# Answer evaluation - split `dev` - 5-mark sample, prompt v3 (baseline before mode fix)

Generated 2026-10-16 by `eval/answer_eval.py --split dev --mode 5-mark`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 10 (8 answerable, 2 unanswerable) |
| answered (not abstained) | 8 (8 checked by the judge, 0 not checkable) |
| **citation accuracy** | **93.8%** (30/32 citations supported) |
| **faithfulness** | **12.5%** (1/8 answers fully cited and supported) |
| cites a labelled page | 100.0% (8 answered answerable questions) |
| **abstention on unanswerable** | **2/2** |
| false abstention on answerable | 0/8 |
| **time to first token p50 / p95** | **975 ms / 2876 ms** (10 live answers; excludes 166 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | unfaithful | 0.840 | 4 | 0 | 2 | 0 | yes | 3689 |
| 2 | yes | unfaithful | 0.863 | 5 | 0 | 2 | 0 | yes | 731 |
| 3 | yes | unfaithful | 0.876 | 6 | 2 | 2 | 0 | yes | 1882 |
| 4 | yes | unfaithful | 0.826 | 4 | 0 | 2 | 0 | yes | 550 |
| 5 | yes | unfaithful | 0.908 | 6 | 0 | 2 | 0 | yes | 1258 |
| 6 | yes | unfaithful | 0.788 | 3 | 0 | 2 | 0 | yes | 1012 |
| 7 | yes | faithful | 0.842 | 1 | 0 | 0 | 0 | yes | 707 |
| 8 | yes | unfaithful | 0.772 | 3 | 0 | 2 | 0 | yes | 744 |
| 61 | no | abstained (model) | 0.755 | 0 | - | 0 | 0 | - | 1214 |
| 62 | no | abstained (model) | 0.727 | 0 | - | 0 | 0 | - | 939 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.772, values 0.772, 0.788, 0.826, 0.840, 0.842, 0.863, 0.876, 0.908 ...
- unanswerable: 0.727, 0.755
