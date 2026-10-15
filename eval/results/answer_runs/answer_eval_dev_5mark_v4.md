# Answer evaluation - split `dev` - 5-mark sample, prompt v3 + cited intro/conclusion

Generated 2026-10-16 by `eval/answer_eval.py --split dev --mode 5-mark`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 10 (8 answerable, 2 unanswerable) |
| answered (not abstained) | 8 (8 checked by the judge, 0 not checkable) |
| **citation accuracy** | **90.6%** (48/53 citations supported) |
| **faithfulness** | **50.0%** (4/8 answers fully cited and supported) |
| cites a labelled page | 100.0% (8 answered answerable questions) |
| **abstention on unanswerable** | **2/2** |
| false abstention on answerable | 0/8 |
| **time to first token p50 / p95** | **981 ms / 2424 ms** (10 live answers; excludes 167 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | faithful | 0.840 | 7 | 0 | 0 | 0 | yes | 1435 |
| 2 | yes | unfaithful | 0.863 | 7 | 1 | 0 | 0 | yes | 1023 |
| 3 | yes | unfaithful | 0.876 | 7 | 1 | 0 | 0 | yes | 2478 |
| 4 | yes | unfaithful | 0.826 | 6 | 2 | 0 | 0 | yes | 939 |
| 5 | yes | faithful | 0.908 | 9 | 0 | 0 | 0 | yes | 751 |
| 6 | yes | faithful | 0.788 | 6 | 0 | 0 | 0 | yes | 820 |
| 7 | yes | faithful | 0.842 | 6 | 0 | 0 | 0 | yes | 727 |
| 8 | yes | unfaithful | 0.772 | 5 | 1 | 0 | 0 | yes | 2357 |
| 61 | no | abstained (model) | 0.755 | 0 | - | 0 | 0 | - | 568 |
| 62 | no | abstained (model) | 0.727 | 0 | - | 0 | 0 | - | 1084 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.772, values 0.772, 0.788, 0.826, 0.840, 0.842, 0.863, 0.876, 0.908 ...
- unanswerable: 0.727, 0.755
