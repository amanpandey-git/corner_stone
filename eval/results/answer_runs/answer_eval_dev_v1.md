# Answer evaluation - split `dev` - Phase 2 v1 prompt, gate off

Generated 2026-10-15 by `eval/answer_eval.py --split dev --mode concise`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 38 (33 answerable, 5 unanswerable) |
| answered (not abstained) | 32 (32 checked by the judge, 0 not checkable) |
| **citation accuracy** | **95.3%** (41/43 citations supported) |
| **faithfulness** | **75.0%** (24/32 answers fully cited and supported) |
| cites a labelled page | 96.9% (31 answered answerable questions) |
| **abstention on unanswerable** | **5/5** |
| false abstention on answerable | 1/33 |
| **time to first token p50 / p95** | **829 ms / 1789 ms** (20 live answers; excludes 221 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | faithful | 0.840 | 1 | 0 | 0 | 0 | yes | 82 (cached) |
| 2 | yes | unfaithful | 0.863 | 1 | 1 | 0 | 0 | yes | 98 (cached) |
| 3 | yes | faithful | 0.876 | 2 | 0 | 0 | 0 | yes | 102 (cached) |
| 4 | yes | unfaithful | 0.826 | 1 | 0 | 1 | 0 | yes | 64 (cached) |
| 5 | yes | faithful | 0.908 | 2 | 0 | 0 | 0 | yes | 103 (cached) |
| 6 | yes | faithful | 0.788 | 1 | 0 | 0 | 0 | yes | 98 (cached) |
| 7 | yes | faithful | 0.842 | 1 | 0 | 0 | 0 | yes | 71 (cached) |
| 8 | yes | faithful | 0.772 | 1 | 0 | 0 | 0 | yes | 50 (cached) |
| 9 | yes | faithful | 0.784 | 2 | 0 | 0 | 0 | yes | 58 (cached) |
| 10 | yes | faithful | 0.805 | 1 | 0 | 0 | 0 | yes | 67 (cached) |
| 11 | yes | faithful | 0.792 | 1 | 0 | 0 | 0 | yes | 53 (cached) |
| 12 | yes | unfaithful | 0.825 | 1 | 0 | 1 | 0 | yes | 111 (cached) |
| 13 | yes | faithful | 0.846 | 1 | 0 | 0 | 0 | yes | 103 (cached) |
| 14 | yes | abstained (model) | 0.775 | 0 | - | 0 | 0 | - | 128 (cached) |
| 15 | yes | faithful | 0.898 | 2 | 0 | 0 | 0 | yes | 41 (cached) |
| 16 | yes | faithful | 0.838 | 1 | 0 | 0 | 0 | yes | 38 (cached) |
| 17 | yes | faithful | 0.869 | 1 | 0 | 0 | 0 | yes | 38 (cached) |
| 18 | yes | faithful | 0.680 | 1 | 0 | 0 | 0 | yes | 621 |
| 19 | yes | faithful | 0.836 | 3 | 0 | 0 | 0 | yes | 727 |
| 20 | yes | faithful | 0.784 | 1 | 0 | 0 | 0 | yes | 572 |
| 24 | yes | faithful | 0.867 | 3 | 0 | 0 | 0 | yes | 1301 |
| 30 | yes | unfaithful | 0.846 | 1 | 0 | 1 | 0 | yes | 837 |
| 36 | yes | faithful | 0.758 | 1 | 0 | 0 | 0 | yes | 881 |
| 42 | yes | faithful | 0.847 | 2 | 0 | 0 | 0 | yes | 572 |
| 48 | yes | unfaithful | 0.794 | 1 | 1 | 0 | 0 | yes | 872 |
| 66 | yes | faithful | 0.621 | 1 | 0 | 0 | 0 | yes | 981 |
| 68 | yes | faithful | 0.694 | 2 | 0 | 0 | 0 | yes | 798 |
| 70 | yes | faithful | 0.644 | 1 | 0 | 0 | 0 | no | 746 |
| 72 | yes | unfaithful | 0.569 | 1 | 0 | 1 | 0 | yes | 516 |
| 74 | yes | unfaithful | 0.617 | 1 | 0 | 1 | 0 | yes | 821 |
| 76 | yes | faithful | 0.707 | 1 | 0 | 0 | 0 | yes | 601 |
| 78 | yes | faithful | 0.721 | 1 | 0 | 0 | 0 | yes | 1002 |
| 80 | yes | unfaithful | 0.676 | 2 | 0 | 1 | 0 | yes | 771 |
| 61 | no | abstained (model) | 0.755 | 0 | - | 0 | 0 | - | 45 (cached) |
| 62 | no | abstained (model) | 0.727 | 0 | - | 0 | 0 | - | 1737 |
| 63 | no | abstained (model) | 0.566 | 0 | - | 0 | 0 | - | 1144 |
| 64 | no | abstained (model) | 0.803 | 0 | - | 0 | 0 | - | 2776 |
| 65 | no | abstained (model) | 0.642 | 0 | - | 0 | 0 | - | 1152 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.569, values 0.569, 0.617, 0.621, 0.644, 0.676, 0.680, 0.694, 0.707 ...
- unanswerable: 0.566, 0.642, 0.727, 0.755, 0.803
