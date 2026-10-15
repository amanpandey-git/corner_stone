# Answer evaluation - split `dev` - Phase 2 prompt v3 (one fact per sentence, format example), gate off

Generated 2026-10-15 by `eval/answer_eval.py --split dev --mode concise`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 38 (33 answerable, 5 unanswerable) |
| answered (not abstained) | 32 (32 checked by the judge, 0 not checkable) |
| **citation accuracy** | **100.0%** (71/71 citations supported) |
| **faithfulness** | **87.5%** (28/32 answers fully cited and supported) |
| cites a labelled page | 96.9% (31 answered answerable questions) |
| **abstention on unanswerable** | **5/5** |
| false abstention on answerable | 1/33 |
| **time to first token p50 / p95** | **925 ms / 1937 ms** (38 live answers; excludes 547 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | unfaithful | 0.840 | 2 | 0 | 1 | 0 | yes | 928 |
| 2 | yes | faithful | 0.863 | 5 | 0 | 0 | 0 | yes | 1220 |
| 3 | yes | faithful | 0.876 | 3 | 0 | 0 | 0 | yes | 759 |
| 4 | yes | faithful | 0.826 | 2 | 0 | 0 | 0 | yes | 794 |
| 5 | yes | faithful | 0.908 | 2 | 0 | 0 | 0 | yes | 922 |
| 6 | yes | faithful | 0.788 | 2 | 0 | 0 | 0 | yes | 659 |
| 7 | yes | faithful | 0.842 | 1 | 0 | 0 | 0 | yes | 755 |
| 8 | yes | faithful | 0.772 | 3 | 0 | 0 | 0 | yes | 1357 |
| 9 | yes | faithful | 0.784 | 3 | 0 | 0 | 0 | yes | 1119 |
| 10 | yes | faithful | 0.805 | 1 | 0 | 0 | 0 | yes | 944 |
| 11 | yes | faithful | 0.792 | 2 | 0 | 0 | 0 | yes | 1112 |
| 12 | yes | faithful | 0.825 | 2 | 0 | 0 | 0 | yes | 499 |
| 13 | yes | faithful | 0.846 | 1 | 0 | 0 | 0 | yes | 754 |
| 14 | yes | abstained (model) | 0.775 | 0 | - | 0 | 0 | - | 473 |
| 15 | yes | faithful | 0.898 | 4 | 0 | 0 | 0 | yes | 1084 |
| 16 | yes | faithful | 0.838 | 3 | 0 | 0 | 0 | yes | 637 |
| 17 | yes | faithful | 0.869 | 3 | 0 | 0 | 0 | yes | 1139 |
| 18 | yes | unfaithful | 0.680 | 1 | 0 | 2 | 0 | yes | 820 |
| 19 | yes | faithful | 0.836 | 3 | 0 | 0 | 0 | yes | 599 |
| 20 | yes | faithful | 0.784 | 2 | 0 | 0 | 0 | yes | 1018 |
| 24 | yes | faithful | 0.867 | 3 | 0 | 0 | 0 | yes | 1967 |
| 30 | yes | faithful | 0.846 | 2 | 0 | 0 | 0 | yes | 1180 |
| 36 | yes | unfaithful | 0.758 | 1 | 0 | 1 | 0 | yes | 889 |
| 42 | yes | faithful | 0.847 | 2 | 0 | 0 | 0 | yes | 858 |
| 48 | yes | faithful | 0.794 | 2 | 0 | 0 | 0 | yes | 869 |
| 66 | yes | faithful | 0.621 | 1 | 0 | 0 | 0 | yes | 1924 |
| 68 | yes | faithful | 0.694 | 2 | 0 | 0 | 0 | yes | 1932 |
| 70 | yes | faithful | 0.644 | 3 | 0 | 0 | 0 | no | 3512 |
| 72 | yes | unfaithful | 0.569 | 1 | 0 | 1 | 0 | yes | 645 |
| 74 | yes | faithful | 0.617 | 2 | 0 | 0 | 0 | yes | 1006 |
| 76 | yes | faithful | 0.707 | 2 | 0 | 0 | 0 | yes | 648 |
| 78 | yes | faithful | 0.721 | 2 | 0 | 0 | 0 | yes | 1090 |
| 80 | yes | faithful | 0.676 | 3 | 0 | 0 | 0 | yes | 946 |
| 61 | no | abstained (model) | 0.755 | 0 | - | 0 | 0 | - | 1076 |
| 62 | no | abstained (model) | 0.727 | 0 | - | 0 | 0 | - | 895 |
| 63 | no | abstained (model) | 0.566 | 0 | - | 0 | 0 | - | 521 |
| 64 | no | abstained (model) | 0.803 | 0 | - | 0 | 0 | - | 1646 |
| 65 | no | abstained (model) | 0.642 | 0 | - | 0 | 0 | - | 853 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.569, values 0.569, 0.617, 0.621, 0.644, 0.676, 0.680, 0.694, 0.707 ...
- unanswerable: 0.566, 0.642, 0.727, 0.755, 0.803
