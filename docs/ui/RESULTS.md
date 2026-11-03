# Synapse UI redesign: results (Phase 3)

Branch `ui-redesign`, not merged. `main` and the live site are unchanged until you merge. Plan: `UI_PLAN.md`.

## Before and after

| Page | Before | After | What changed |
|---|---|---|---|
| Landing | [1440](before/landing-1440-light.png), [390](before/landing-390-light.png) | [1440](after/landing-1440-light.png), [dark](after/landing-1440-dark.png), [390](after/landing-390-light.png) | Headline and main action; real recorded answer with working citations; contents page; unequal feature tiles with real output; marksheet; title page |
| Ask | [empty](before/ask-1440-light.png), [answer](before/state-ask-answer-1440-light.png), [refusal](before/state-ask-not-in-notes-1440-light.png) | [empty](after/state-ask-empty-1440-light.png), [real answer](after/state-ask-real-answer-1440-light.png), [refusal](after/state-ask-not-in-notes-1440-dark.png), [phone sheet](after/state-ask-sheet-390-dark.png) | Slide beside the answer; real download percent; starter questions; exam-mark modes; proper refusal state; friendly errors; bullets and bold in long answers |
| Quiz | [setup](before/quiz-1440-light.png), [questions](before/state-quiz-feedback-1440-light.png) | [question](after/state-quiz-feedback-1440-light.png), [score](after/state-quiz-score-1440-dark.png), [phone](after/state-quiz-feedback-390-dark.png) | One question at a time; progress bar; tick or cross as well as colour; slide beside the feedback; marked score; retry with no AI call; keyboard |
| Flashcards | [front](before/state-flashcards-front-1440-light.png), [back](before/state-flashcards-back-1440-light.png) | [front](after/state-flashcards-front-1440-light.png), [back](after/state-flashcards-back-390-light.png), [empty](after/state-flashcards-empty-1440-dark.png) | 3D flip; real next-interval labels; due-today count; Space and 1-4; note that cards stay in this browser |
| Documents | [1440](before/documents-1440-light.png), [390](before/documents-390-light.png) | [1440](after/documents-1440-light.png), [dark](after/documents-1440-dark.png), [390](after/documents-390-dark.png) | Deck cards with real thumbnails instead of a sideways-scrolling table; plain words for repeated and flagged pages; Ask this unit |

The app now has a designed dark theme, a phone tab bar and a footer on every page.

## Checks on the final code

| Check | Result |
|---|---|
| `npm run lint`, `npm run build` | Pass |
| Ask, recorded answers | 44 of 44 |
| Quiz and Flashcards, recorded answers | 72 of 72 |
| Fresh browser: real progress, self-check, no stale banner | 4 of 4; ready in 19-28 s, second visit about 1.5 s |
| Browser self-check | Top 5 match the Python model |
| axe-core: 50 states, 2 widths, 2 themes | No violations (`captured/audit-after.json`) |
| Real Groq check | Streaming, cited answer, real slide, quiz and flashcard all worked |

Quiz, Flashcards and axe last ran just before a one-line CSS change to the streaming caret; lint, build and Ask ran after it.

**Groq use:** 3 requests in Phase 3. The first attempt stopped early because of a fault in my test; the real refusal was skipped to stay within the 3 planned.

### Lighthouse: local production build, not the Preview

The Preview sits behind a Vercel login, so as agreed this ran on `next start`. A local network flatters LCP, so treat those numbers as a best case. Raw results: `captured/lighthouse-local.json`.

| Page | Performance | Accessibility | Best practices | LCP | Layout shift |
|---|---|---|---|---|---|
| Landing, phone | 100 | 100 | 100 | 0.8 s | 0 |
| Landing, desktop | 100 | 100 | 100 | 0.2 s | 0 |
| Ask, phone | **70** | 100 | **81** | 0.8 s | 0 |
| Quiz, phone | 99 | 100 | 100 | 0.8 s | 0 |
| Flashcards, phone | 94 | 100 | 100 | 2.8 s | 0.065 |
| Documents, phone | 91 | 100 | 100 | 3.4 s | 0 |

Landing is within budget: JS 157 KB (budget 185), CSS 8 KB (budget 20).

**Ask's two scores below 90 were not fixed, because both come from the search model:**
- Performance 70: the model loads on the page's main thread, blocking for about 4.5 s under Lighthouse's phone throttling. Moving it to a worker would change `web/lib/demo/client.ts`, which is outside presentation.
- Best practices 81: a deprecated API inside the third-party model runtime's worker.

## Left undone

- Lighthouse on the Vercel Preview itself (behind the login).
- A real refusal on the new UI. Its display was tested with a real recorded refusal, and the logic did not change.
- `prefers-reduced-motion` and scroll reveals were checked by automated runs only, not by eye in a real scroll.

## Known, not changed

- **A generated quiz can be wrong.** In the real check, a question on Unit 1 Part 1 p.43 marked "System call" as correct, while the slide says the transition is "context switching". This is the model, not the UI; the report measures it at 24 of 25 supported.
- **SM-2 labels look alike:** a new card shows 1 day on all four buttons, later Hard, Good and Easy match. This is correct SM-2.
- **Slashed zero:** the approved body font draws zero with a slash and has no plain alternative.
- **File name typo:** "Schduling" is in the source PDF's name, and the data is protected.
- **`docs/evaluation-report.md`** is still titled "(draft)".

## Merge steps

1. **Check the Preview while logged in to Vercel.** Open <https://corner-stone-git-ui-redesign-maverick-1081.vercel.app/api/demo/health>. It should show `"llm_key_present":true`. Then look through the pages. Asking questions there may use your quota.
2. **Open the pull request:** <https://github.com/amanpandey-git/corner_stone/compare/main...ui-redesign>, press **Create pull request**, wait for the checks, then **Merge pull request**.
3. **Vercel deploys `main`** by itself. Wait for it to show **Ready**, then open <https://corner-stone-alpha.vercel.app>.
4. **On the evaluation laptop,** open `/ask` once beforehand, so the 34 MB model is already in the browser.
5. **If anything is wrong after merging:** in Vercel, open **Deployments**, choose the previous one, and use **Instant Rollback**. The code can then be reverted on GitHub with the **Revert** button on the pull request.
