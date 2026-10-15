# Answer evaluation - split `test` - Phase 2 test run (once), prompt v3, 5-mark sample

Generated 2026-10-16 by `eval/answer_eval.py --split test --mode 5-mark`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 10 (8 answerable, 2 unanswerable) |
| answered (not abstained) | 8 (8 checked by the judge, 0 not checkable) |
| **citation accuracy** | **96.6%** (28/29 citations supported) |
| **faithfulness** | **12.5%** (1/8 answers fully cited and supported) |
| cites a labelled page | 100.0% (8 answered answerable questions) |
| **abstention on unanswerable** | **2/2** |
| false abstention on answerable | 0/8 |
| **time to first token p50 / p95** | **838 ms / 1173 ms** (10 live answers; excludes 169 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 21 | yes | unfaithful | 0.802 | 4 | 0 | 2 | 0 | yes | 849 |
| 22 | yes | unfaithful | 0.820 | 3 | 0 | 2 | 0 | yes | 969 |
| 23 | yes | unfaithful | 0.845 | 4 | 1 | 0 | 0 | yes | 573 |
| 25 | yes | faithful | 0.860 | 1 | 0 | 0 | 0 | yes | 1001 |
| 26 | yes | unfaithful | 0.806 | 4 | 0 | 2 | 0 | yes | 455 |
| 27 | yes | unfaithful | 0.763 | 5 | 0 | 2 | 0 | yes | 828 |
| 28 | yes | unfaithful | 0.816 | 4 | 0 | 2 | 0 | yes | 893 |
| 29 | yes | unfaithful | 0.866 | 4 | 0 | 2 | 0 | yes | 803 |
| 51 | no | abstained (model) | 0.665 | 0 | - | 0 | 0 | - | 1314 |
| 52 | no | abstained (model) | 0.635 | 0 | - | 0 | 0 | - | 675 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.763, values 0.763, 0.802, 0.806, 0.816, 0.820, 0.845, 0.860, 0.866 ...
- unanswerable: 0.635, 0.665
