# Answer evaluation - split `dev` - Phase 2 v1 prompt, gate off

**PARTIAL RUN**: stopped after 2 questions: LLMError: gemini gemini-3.5-flash: HTTP 503 UNAVAILABLE

Generated 2026-10-15 by `eval/answer_eval.py --split dev --mode concise`. Answerer `openai/gpt-oss-120b`, judge `gemini-3.5-flash`, k=5, retrieval gate min_vector_score=0.0, config `config.yaml`.

| metric | value |
|---|---|
| questions | 2 (2 answerable, 0 unanswerable) |
| answered (not abstained) | 2 (2 checked by the judge, 0 not checkable) |
| **citation accuracy** | **50.0%** (1/2 citations supported) |
| **faithfulness** | **50.0%** (1/2 answers fully cited and supported) |
| cites a labelled page | 100.0% (2 answered answerable questions) |
| **abstention on unanswerable** | **0/0** |
| false abstention on answerable | 0/2 |
| **time to first token p50 / p95** | **- ms / - ms** (0 live answers) |

## Per question

| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | yes | faithful | 0.840 | 1 | 0 | 0 | 0 | yes | 41 (cached) |
| 2 | yes | unfaithful | 0.863 | 1 | 1 | 0 | 0 | yes | 42 (cached) |

## Top vector score (for the retrieval gate; choose on dev only)

- answerable: min 0.840, values 0.840, 0.863 ...
- unanswerable: 
