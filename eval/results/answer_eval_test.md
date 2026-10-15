# Answer evaluation - split `test` - Phase 2 test run (once), prompt v3, concise

Generated 2026-10-16 by `eval/answer_eval.py --split test --mode concise`. Answerer `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 43 (33 answerable, 10 unanswerable) |
| answered (not abstained) | 32 (32 checked by the judge, 0 not checkable) |
| **citation accuracy** | **100.0%** (75/75 citations supported) |
| **faithfulness** | **96.9%** (31/32 answers fully cited and supported) |
| cites a labelled page | 96.9% (31 answered answerable questions) |
| **abstention on unanswerable** | **10/10** |
| false abstention on answerable | 1/33 |
| **time to first token p50 / p95** | **884 ms / 2071 ms** (43 live answers; excludes 546 s spent queueing for the free-tier rate limit) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 21 | yes | faithful | 0.802 | 4 | 0 | 0 | 0 | yes | 1156 |
| 22 | yes | faithful | 0.820 | 3 | 0 | 0 | 0 | yes | 739 |
| 23 | yes | faithful | 0.845 | 2 | 0 | 0 | 0 | yes | 632 |
| 25 | yes | faithful | 0.860 | 1 | 0 | 0 | 0 | yes | 779 |
| 26 | yes | faithful | 0.806 | 1 | 0 | 0 | 0 | yes | 1038 |
| 27 | yes | faithful | 0.763 | 5 | 0 | 0 | 0 | yes | 936 |
| 28 | yes | faithful | 0.816 | 2 | 0 | 0 | 0 | yes | 701 |
| 29 | yes | faithful | 0.866 | 1 | 0 | 0 | 0 | yes | 1081 |
| 31 | yes | faithful | 0.833 | 4 | 0 | 0 | 0 | yes | 1314 |
| 32 | yes | faithful | 0.771 | 2 | 0 | 0 | 0 | yes | 607 |
| 33 | yes | faithful | 0.744 | 2 | 0 | 0 | 0 | yes | 612 |
| 34 | yes | faithful | 0.891 | 7 | 0 | 0 | 0 | yes | 612 |
| 35 | yes | faithful | 0.827 | 2 | 0 | 0 | 0 | yes | 783 |
| 37 | yes | faithful | 0.854 | 1 | 0 | 0 | 0 | yes | 715 |
| 38 | yes | faithful | 0.890 | 1 | 0 | 0 | 0 | yes | 592 |
| 39 | yes | faithful | 0.755 | 1 | 0 | 0 | 0 | yes | 1947 |
| 40 | yes | faithful | 0.780 | 2 | 0 | 0 | 0 | yes | 910 |
| 41 | yes | faithful | 0.810 | 4 | 0 | 0 | 0 | yes | 1218 |
| 43 | yes | faithful | 0.740 | 2 | 0 | 0 | 0 | yes | 429 |
| 44 | yes | faithful | 0.865 | 2 | 0 | 0 | 0 | yes | 1093 |
| 45 | yes | faithful | 0.820 | 3 | 0 | 0 | 0 | yes | 1621 |
| 46 | yes | faithful | 0.740 | 3 | 0 | 0 | 0 | yes | 975 |
| 47 | yes | faithful | 0.875 | 4 | 0 | 0 | 0 | yes | 745 |
| 49 | yes | faithful | 0.857 | 2 | 0 | 0 | 0 | yes | 844 |
| 50 | yes | faithful | 0.819 | 2 | 0 | 0 | 0 | yes | 1155 |
| 67 | yes | faithful | 0.673 | 2 | 0 | 0 | 0 | yes | 827 |
| 69 | yes | faithful | 0.698 | 1 | 0 | 0 | 0 | yes | 464 |
| 71 | yes | faithful | 0.662 | 2 | 0 | 0 | 0 | no | 1680 |
| 73 | yes | faithful | 0.734 | 2 | 0 | 0 | 0 | yes | 2075 |
| 75 | yes | unfaithful | 0.657 | 2 | 0 | 1 | 0 | yes | 766 |
| 77 | yes | faithful | 0.829 | 1 | 0 | 0 | 0 | yes | 884 |
| 79 | yes | faithful | 0.683 | 2 | 0 | 0 | 0 | yes | 651 |
| 81 | yes | abstained (model) | 0.629 | 0 | - | 0 | 0 | - | 898 |
| 51 | no | abstained (model) | 0.665 | 0 | - | 0 | 0 | - | 1417 |
| 52 | no | abstained (model) | 0.635 | 0 | - | 0 | 0 | - | 885 |
| 53 | no | abstained (model) | 0.723 | 0 | - | 0 | 0 | - | 579 |
| 54 | no | abstained (model) | 0.681 | 0 | - | 0 | 0 | - | 1114 |
| 55 | no | abstained (model) | 0.678 | 0 | - | 0 | 0 | - | 2043 |
| 56 | no | abstained (model) | 0.632 | 0 | - | 0 | 0 | - | 3464 |
| 57 | no | abstained (model) | 0.766 | 0 | - | 0 | 0 | - | 2478 |
| 58 | no | abstained (model) | 0.603 | 0 | - | 0 | 0 | - | 794 |
| 59 | no | abstained (model) | 0.670 | 0 | - | 0 | 0 | - | 688 |
| 60 | no | abstained (model) | 0.510 | 0 | - | 0 | 0 | - | 874 |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.629, values 0.629, 0.657, 0.662, 0.673, 0.683, 0.698, 0.734, 0.740 ...
- unanswerable: 0.510, 0.603, 0.632, 0.635, 0.665, 0.670, 0.678, 0.681, 0.723, 0.766
