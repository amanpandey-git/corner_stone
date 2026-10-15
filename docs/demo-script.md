# Demo script (Stage 2, about 8 minutes)

Order fixed by CLAUDE.md: cited exam answer first, then abstention, then the quiz + flashcard loop. Runs on the
Next.js app if it is demoable on the morning of 24 Oct, otherwise on the Streamlit page (same backend functions).

## Before the demo (10 minutes earlier)

1. `git switch stage-2` and `.venv\Scripts\activate`.
2. `.env` holds `GROQ_API_KEY` (answers, quiz, judge). Check: `PYTHONPATH=src python -m cornerstone.cli ask "What is a TLB?" --mode 2-mark` prints a cited answer.
3. Index present: `PYTHONPATH=src python -m cornerstone.cli stats` shows 7 documents.
4. Start the UI:
   - Streamlit: `PYTHONPATH=src streamlit run app/streamlit_app.py`
   - or API + web app: `PYTHONPATH=src uvicorn cornerstone.api:app --port 8000`, then `npm run dev` in `web/`.
5. Warm the cache: ask the three demo questions once (answers are cached, so the live demo cannot hit a rate limit).
6. Fallback if the network fails: the cached answers still work for the exact demo questions; say so honestly.

## 1. The problem (30 s)

"Students revise from their own slides. A general chatbot answers from the internet, may be wrong for this
syllabus, and cannot show where a claim comes from. Cornerstone answers only from your notes, cites the slide
for every claim, and says 'not in your notes' when the notes do not cover it."

## 2. Upload and indexing (1 min)

- Documents tab: the 7 OS slide decks, pages, flagged pages (scanned/diagram-only, "needs OCR") and duplicate
  slides (Unit 4 repeats 23 of its own slides; they are detected and not indexed).
- Point: zero silent failures, every page is indexed, flagged with a reason, or marked duplicate.

## 3. A 5-mark answer with citations (2 min)

- Ask tab, mode **5-mark**: *"Explain the SCAN disk scheduling algorithm with its advantages and disadvantages."*
- Watch it stream. Point at the [n] after every sentence.
- Click a citation: the actual slide image opens (Unit 4, SCAN slide).
- Point: the answer is shaped for university marking (intro, points, conclusion) and every point is traceable.

## 4. Abstention (1 min)

- Ask: *"How does TCP congestion control work?"* (networking, not in these OS notes).
- Result: **Not in your notes.** with the reason.
- Point: on the test questions written to be out of scope, it abstained on N of 10 (fill in from
  eval/results/answer_eval_test.md).

## 5. Quiz (1.5 min)

- Quiz tab, Unit 4, 5 questions. Answer one deliberately wrong.
- Check answers: the correct answer is shown with its explanation and the source slide.
- Click "Make a flashcard of this" on the wrong one.

## 6. Flashcards with spaced repetition (1 min)

- Flashcards tab: the card from the quiz is due today. Show answer -> slide image -> grade **Good**:
  "next review in 1 day". Explain SM-2 in one sentence: cards you know come back after longer and longer gaps.

## 7. Evidence (1 min)

- Open `eval/results/` and the README results table: retrieval hit@5 0.879 (v0.1) -> 0.939 (Phase 1) on the
  test split, dev ablation table (what helped, what did not: hybrid and reranker were measured and switched off),
  answer evaluation (citation accuracy, faithfulness, abstention, time to first token).
- Point: every number was measured on a held-out test split that was run once per phase and logged.

## Likely questions during the demo

- *What if the slide is a diagram?* Diagram-only pages are flagged "needs OCR" and not indexed (OCR is out of scope).
- *Which model?* Groq `openai/gpt-oss-120b` for answers, `qwen/qwen3.8-27b` as an independent citation judge;
  provider is a config switch (Gemini adapter included).
- *What does it cost?* Free tiers only; answers are cached and calls are rate-limited in code.
