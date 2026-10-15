# Answer evaluation - split `dev` - Phase 2 prompt v2 (cite every sentence), gate off

Generated 2026-10-15 by `eval/answer_eval.py --split dev --mode concise`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 38 (33 answerable, 5 unanswerable) |
| answered (not abstained) | 32 (32 checked by the judge, 0 not checkable) |
| **citation accuracy** | **91.8%** (45/49 citations supported) |
| **faithfulness** | **81.2%** (26/32 answers fully cited and supported) |
| cites a labelled page | 96.9% (31 answered answerable questions) |
| **abstention on unanswerable** | **5/5** |
| false abstention on answerable | 1/33 |
| **time to first token p50 / p95** | **886 ms / 1562 ms** (38 live answers; excludes 488 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | faithful | 0.840 | 1 | 0 | 0 | 0 | yes | 656 |
| 2 | yes | unfaithful | 0.863 | 1 | 1 | 0 | 0 | yes | 781 |
| 3 | yes | faithful | 0.876 | 2 | 0 | 0 | 0 | yes | 617 |
| 4 | yes | faithful | 0.826 | 2 | 0 | 0 | 0 | yes | 1060 |
| 5 | yes | faithful | 0.908 | 2 | 0 | 0 | 0 | yes | 825 |
| 6 | yes | faithful | 0.788 | 1 | 0 | 0 | 0 | yes | 911 |
| 7 | yes | faithful | 0.842 | 1 | 0 | 0 | 0 | yes | 1035 |
| 8 | yes | faithful | 0.772 | 3 | 0 | 0 | 0 | yes | 807 |
| 9 | yes | faithful | 0.784 | 2 | 0 | 0 | 0 | yes | 848 |
| 10 | yes | faithful | 0.805 | 1 | 0 | 0 | 0 | yes | 1333 |
| 11 | yes | faithful | 0.792 | 1 | 0 | 0 | 0 | yes | 1282 |
| 12 | yes | unfaithful | 0.825 | 2 | 1 | 0 | 0 | yes | 999 |
| 13 | yes | faithful | 0.846 | 1 | 0 | 0 | 0 | yes | 3683 |
| 14 | yes | abstained (model) | 0.775 | 0 | - | 0 | 0 | - | 770 |
| 15 | yes | faithful | 0.898 | 2 | 0 | 0 | 0 | yes | 694 |
| 16 | yes | faithful | 0.838 | 1 | 0 | 0 | 0 | yes | 754 |
| 17 | yes | faithful | 0.869 | 1 | 0 | 0 | 0 | yes | 875 |
| 18 | yes | unfaithful | 0.680 | 1 | 0 | 2 | 0 | yes | 2826 |
| 19 | yes | faithful | 0.836 | 3 | 0 | 0 | 0 | yes | 944 |
| 20 | yes | faithful | 0.784 | 1 | 0 | 0 | 0 | yes | 687 |
| 24 | yes | faithful | 0.867 | 3 | 0 | 0 | 0 | yes | 1125 |
| 30 | yes | faithful | 0.846 | 2 | 0 | 0 | 0 | yes | 746 |
| 36 | yes | faithful | 0.758 | 1 | 0 | 0 | 0 | yes | 1212 |
| 42 | yes | faithful | 0.847 | 2 | 0 | 0 | 0 | yes | 1111 |
| 48 | yes | unfaithful | 0.794 | 2 | 1 | 0 | 0 | yes | 753 |
| 66 | yes | faithful | 0.621 | 1 | 0 | 0 | 0 | yes | 831 |
| 68 | yes | faithful | 0.694 | 2 | 0 | 0 | 0 | yes | 1054 |
| 70 | yes | faithful | 0.644 | 1 | 0 | 0 | 0 | no | 469 |
| 72 | yes | unfaithful | 0.569 | 1 | 1 | 1 | 0 | yes | 933 |
| 74 | yes | faithful | 0.617 | 1 | 0 | 0 | 0 | yes | 1339 |
| 76 | yes | unfaithful | 0.707 | 1 | 0 | 1 | 0 | yes | 790 |
| 78 | yes | faithful | 0.721 | 1 | 0 | 0 | 0 | yes | 665 |
| 80 | yes | faithful | 0.676 | 2 | 0 | 0 | 0 | yes | 943 |
| 61 | no | abstained (model) | 0.755 | 0 | - | 0 | 0 | - | 897 |
| 62 | no | abstained (model) | 0.727 | 0 | - | 0 | 0 | - | 795 |
| 63 | no | abstained (model) | 0.566 | 0 | - | 0 | 0 | - | 1229 |
| 64 | no | abstained (model) | 0.803 | 0 | - | 0 | 0 | - | 1154 |
| 65 | no | abstained (model) | 0.642 | 0 | - | 0 | 0 | - | 773 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.569, values 0.569, 0.617, 0.621, 0.644, 0.676, 0.680, 0.694, 0.707 ...
- unanswerable: 0.566, 0.642, 0.727, 0.755, 0.803
