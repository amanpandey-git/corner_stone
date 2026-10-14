# eval/questions.jsonl - how to write the labelled questions

One JSON object per line, 15-25 lines, **written from the slides, before looking at search results**:

```
{"question": "<a question a student would ask>", "file": "<exact file name in samples/>", "pages": [<page numbers>]}
```

- `pages` is always a list: the 1-based PDF page(s) that contain the answer. Use several when the
  answer spans slides. A question is a hit@5 if any listed page is covered by a top-5 chunk.
- Optional `"equivalent_pages": [..]`: pages holding a verbatim duplicate of the answer (`Unit 4` repeats its
  slides 2-26 as 27-51). A result covering any of them is a hit; they are not counted as multi-page.
- Do not reuse the three Step 5 questions (deadlock conditions / process vs thread / paging and
  external fragmentation); they are excluded from scoring if present.
- Vary the units; include some questions whose answer is on one slide and some on two.
- Check the file without scoring: `PYTHONPATH=src python eval/retrieval_eval.py --check`
  (rejects missing fields, files not in samples/, pages that do not exist, duplicates).
- Run the evaluation once: `PYTHONPATH=src python eval/retrieval_eval.py`
- Do not edit questions or chunking/ef_search after seeing the results and then re-report the new numbers
  as the result; if something changes, say so next to the number.
