# eval/questions.jsonl - how the labelled questions are written

One JSON object per line, **written from the slides' extracted text, before looking at search results**.
Every line has `id` (unique int) and `split` (`dev` or `test`). Three shapes:

```
{"id": 1,  "split": "dev",  "question": "...", "file": "<exact file name in samples/>", "pages": [12]}
{"id": 46, "split": "test", "question": "...", "targets": [{"file": "A.pdf", "pages": [17]}, {"file": "B.pdf", "pages": [5]}]}
{"id": 51, "split": "test", "question": "...", "answerable": false, "note": "why the notes do not answer it"}
```

- `pages` is always a list: the 1-based PDF page(s) containing the answer; several when the answer spans slides.
- Optional `"equivalent_pages": [..]` (top level or per target): pages holding a verbatim duplicate of the answer
  (`Unit 4` repeats its slides 2-26 as 27-51). A result covering any of them is a hit; not counted as multi-page.
- `targets` = cross-file question (>= 2 different files). hit@5 if any labelled page of any target is in the top 5;
  "all files in top 5" is reported separately.
- `answerable: false` = the notes do not answer it (abstention set, scored in Phase 2). No file/pages allowed.
- Do not reuse the three Step 5 questions (deadlock conditions / process vs thread / paging and external
  fragmentation); they are excluded from scoring if present.
- Evidence (answering phrase per page, absent terms for unanswerable ones): `eval/evidence.md`.

## Split rule (fixed 2026-10-15, before any Stage 2 run)
- **ids 1-20** (the Stage 1 questions): **dev**. Their v0.1 results were seen and the Q14 miss shaped the Phase 1
  design, so they cannot be an unbiased test.
- **ids 21-50** (new answerable, written grouped by file, cross-file last): **test**, except every 6th id
  (24, 30, 36, 42, 48) which goes to **dev**. Result: 25 answerable dev, 25 answerable test.
- **ids 51-60** (unanswerable): **test** (the "8 of 10" target). **ids 61-65** (5 extra unanswerable): **dev**, so the
  abstention prompt/threshold can be tuned without touching the test set.
- Tune only on dev. Test is run at the baseline, end of Phase 1, the Phase 2 answer evaluation and the final report.

## Commands
- Check only: `PYTHONPATH=src python eval/retrieval_eval.py --check`
- Evaluate a split: `PYTHONPATH=src python eval/retrieval_eval.py --split dev`
  (writes `eval/results/retrieval_eval_<split>.md`; `--out` and `--label` override; the Stage 1 file
  `eval/results/retrieval_eval.md` is never overwritten)
- Do not edit questions or the pipeline after seeing test results and re-report the new numbers as the result; if
  something changes, say so next to the number.
