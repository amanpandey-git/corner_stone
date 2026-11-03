# Synapse UI plan (Phase 2)

Status: **waiting for approval. No application code has been changed.** Research and evidence: `RESEARCH.md`.

## 1. Direction: Marginalia

*"A well-annotated textbook, the night before the exam."*

Four ideas carry the identity, and all of them come from real study material:

| Idea | Where it appears |
|---|---|
| **A citation is a highlight.** The chip is a yellow tab. Focusing it sweeps highlighter across the sentence it supports. | Ask, landing preview |
| **The source sits in the margin.** The slide opens beside the answer, the way a note sits beside text. | Ask, Quiz, Flashcards |
| **Marks, like an exam paper.** Modes read "2 marks", "5 marks". A thin red-pen rule runs down the page margin. | Ask, Quiz score |
| **Results are a marksheet; the author section is a title page.** | Landing |

### Not the classmate's template

The brief asks for some sections their template also has, so the *form* has to differ:

| Their template | Synapse |
|---|---|
| Generic dark purple | Warm paper and ink, highlighter yellow; a separate warm dark theme |
| Sticky nav | Quiet top bar on desktop; labelled bottom tabs in the app on phones |
| 4-step strip of cards | "How it works" set as a textbook **contents page**, with dot leaders and real numbers |
| Stats band | A **marksheet**: each result has its definition, scope and a tally of dots (31 of 33) |
| Equal feature cards | Unequal grid in which each tile shows real output from this demo |
| Developer card | A project **title page**: "Submitted by ... Under the guidance of ..." |
| Contact form | None. The brief bans forms that cannot send. A GitHub link instead. |

## 2. Design tokens

Defined as CSS variables, exposed to Tailwind 4 through `@theme`. Dark mode uses the class variant from the
[Tailwind docs](https://tailwindcss.com/docs/dark-mode): `@custom-variant dark (&:where(.dark, .dark *));`.

### Colour (contrast computed against WCAG, not estimated)

| Token | Light "Paper" | Dark "Desk lamp" | Use | Contrast, light / dark |
|---|---|---|---|---|
| `paper` | `#FAF6EC` | `#15130F` | page | - |
| `raised` | `#FFFDF7` | `#1F1C17` | cards, sheet | - |
| `sunk` | `#F1EBDC` | `#0F0E0B` | wells, composer | - |
| `ink` | `#1F1B16` | `#F4EFE3` | main text | 15.9 / 16.2 |
| `ink-2` | `#544D42` | `#C4BCAC` | secondary text | 7.7 / 9.8 |
| `ink-3` | `#6B6357` | `#A0978A` | captions (lowest on `sunk`: 5.0 / 6.7) | 5.5 / 6.4 |
| `rule` | `#E3DBC8` | `#2F2B24` | hairlines (decorative) | - |
| `rule-strong` | `#8F8675` | `#7C7466` | input borders (needs 3:1) | 3.3 / 4.0 |
| `marker` | `#FFD93D` | `#F2C230` | highlighter: **background only**, always with dark ink on it | 12.4 / 10.2 |
| `marker-soft` | `#FFF1B8` | `#3B3010` | highlighted sentence | 15.1 / 7.8 |
| `accent-ink` | `#7A5A00` | `#F2C230` | links and yellow-family text | 5.9 / 11.1 |
| `margin-pen` | `#B3261E` | `#F4978E` | the red margin rule | decorative |
| `correct` / `correct-bg` | `#1B6B3F` / `#E3F2E5` | `#7FD6A0` / `#14301F` | right answer | 5.6 / 8.2 |
| `wrong` / `wrong-bg` | `#B3261E` / `#FBE6E2` | `#F4978E` / `#3A1A16` | wrong answer | 5.5 / 7.2 |
| `warn` / `warn-bg` | `#8A5300` / `#FBEFD5` | `#EDB95E` / `#33260F` | rate limits, notices | 5.6 / 8.2 |

Every pair above passes AA. Dark mode is not an inversion: surfaces get lighter as they rise, drop shadows go away,
and slides are dimmed to 92% brightness on a paper-coloured frame so that white slides do not glare in a dark room.

### Type (self-hosted through `next/font/local`)

| Role | Font | File, latin | Loading |
|---|---|---|---|
| Display | Fraunces, optical size + weight | 65.7 KB | preload |
| Body | Atkinson Hyperlegible Next, weight (a typeface designed for legibility) | 33.2 KB | preload |
| Mono | JetBrains Mono, weight (page references, marks, numbers) | 39.5 KB | no preload |

`next/font/local` keeps today's property that the app **builds offline** (the layout's comment says this was on
purpose), because no download is needed at build time. All three are OFL-1.1; licence text goes in `web/app/fonts/`.

| Step | Size / line | Font and weight | Used for |
|---|---|---|---|
| `display` | clamp(44 to 84 px) / 1.02, -0.02em | Fraunces 600 | landing headline |
| `h1` | clamp(32 to 44 px) / 1.1, -0.015em | Fraunces 600 | page titles |
| `h2` | clamp(24 to 32 px) / 1.2 | Fraunces 600 | sections |
| `h3` | 20 px / 1.3 | Atkinson 700 | tiles, card titles |
| `lede` | 20 px / 1.5 | Atkinson 400 | intros |
| `body` | 17 px / 1.6 | Atkinson 400 | answers, text (max 68 characters a line) |
| `small` | 14 px / 1.5 | Atkinson 400 | captions |
| `mono` | 13 px / 1.4, `tabular-nums` | JetBrains 500 | "p.15", marks, chips |

### Scale

- **Spacing:** 4, 8, 12, 16, 24, 32, 48, 64, 96, 128 px. Landing sections use 96 to 128; app pages use 24 to 48.
- **Radius:** `sm` 6 (chips), `md` 10 (inputs, buttons), `lg` 16 (cards), `xl` 24 (hero sheet, slide panel).
- **Borders:** always a named colour, 1 px `rule`. This fixes the near-black borders at their cause. Inputs use `rule-strong`.
- **Shadows:** light mode has one soft `sheet` shadow, for floating items only. Dark mode has none, only a lighter surface and a 1 px top highlight.
- **Focus:** 2 px `ink` outline with 2 px offset on every interactive element (a yellow ring would fail on paper).
- **Icons:** lucide-react, 1.5 px stroke, 16 or 20 px, always with text or an `aria-label`.

### Motion

Short and purposeful: 120 ms for hover and press, 200 ms for highlight and panel fade, 320 ms for the card flip and
panel slide. Only `transform`, `opacity` and `background-size` animate. No parallax, no looping decoration, no
animation on page load apart from the hero answer. Scroll reveals are CSS-only inside `@supports (animation-timeline:
view())`, and content is always visible without them. **With `prefers-reduced-motion`, all of it is off**: the flip
becomes an instant swap and the hero shows the finished answer. No motion library is planned (it would add at least 29 KB).

## 3. Navigation and structure

Routes stay exactly as they are, so no link breaks: `/`, `/ask`, `/quiz`, `/review`, `/documents`.

- **Order:** Ask, Quiz, Flashcards, Documents. Ask comes first because the demo leads with it.
- **Desktop top bar:** Synapse wordmark, the 4 links, theme toggle, GitHub. The landing also has "Try the demo".
- **Phone:** top bar with wordmark and theme toggle; on app pages a **bottom tab bar** with 4 icon-and-label tabs of
  at least 56 px, which solves the wrapping nav and the small targets. The landing has no tab bar.
- **Status:** the developer text ("7 docs · 328 chunks") moves to a small footer indicator. It checks once on load and
  when the tab regains focus, instead of every 15 s. The `/api/demo/health` route itself does not change.
- **Footer:** one line about Synapse, Try the demo, Evaluation report, GitHub, author and guide.
- **Skip link** on every page: "Skip to content".

## 4. Pages

### a) Landing (`/`)

Sections, in order:

1. **Hero.** Headline from the brief, with "the slide they came from" highlighted in yellow. Main button "Try the demo",
   second link "See the results". Right side: a **real recorded answer** (`captured/real-answers.json`, SCAN question).
   It types in once, its chips are clickable and swap the real slides p.15 and p.17. Labelled "Recorded from this demo".
   It makes no Groq call and needs no model, so it works even if the quota runs out during the evaluation.
2. **How it works: a contents page.** Upload, Index, Ask, Revise with dot leaders and real numbers: 7 decks, 422 pages,
   328 chunks, 24 copied slides skipped. Upload carries the note "in the full app; this demo comes with the decks
   already indexed", which fixes today's dead-end first step.
3. **Features: unequal grid**, each showing real output:
   - **Cited answers** (largest): a sentence with its chip and slide thumbnail.
   - **Honest refusals:** the real "Not in your notes." for the real TCP question.
   - **Exam modes:** the 2, 5 and 10-mark selector with the word targets from the actual prompts (40-60, 150-250, 400-600 words; logged in PROGRESS.md, like the 34 MB and 29 s figures on the Ask page, so that the number rule holds).
   - **Quiz:** the real Rotational Latency question (`captured/real-quiz-sample.json`).
   - **Flashcards:** the card made from that wrong answer, with SM-2 explained in one line.
   - **Semantic search:** "searches by meaning, in your browser".
4. **Results: a marksheet.** Each row has: name, plain meaning, exact number, tally of dots. Rows: hit@5 0.939 (31/33), MRR 0.856,
   citation accuracy 100% (75/75, LLM-judged), faithfulness 96.9% (31/32), correct refusals 10/10, first token p50 884 ms, search p95 47 ms,
   quiz validity 25/25, tests 274. Below it, in normal text size: *"Answer metrics are for concise mode on the test split. Measured on the full
   system on a laptop; not re-measured on this online demo."* Link: "Read the evaluation report". Dots draw once, in CSS.
5. **Under the hood.** One line showing the path of a question: browser embeds it, finds slides, server asks Groq, answer streams back with citations. A short stack list.
6. **Title page.** Synapse. Submitted by Aman Pandey, B.Tech CSE, MITS Gwalior. Under the guidance of Dr. Manish Dixit. GitHub link.
7. **Footer.**

```
DESKTOP 1440
+------------------------------------------------------------------------------+
| Synapse          Ask  Quiz  Flashcards  Documents       (o) GH  [Try the demo]|
+------------------------------------------------------------------------------+
|!                                         +----------------------------------+|
|!  Ask your lecture slides.               | Q Explain the SCAN disk          ||
|!  Get answers with                       |   scheduling algorithm...        ||
|!  [the slide they came from].            |                                  ||
|!                                         | The SCAN algorithm moves the     ||
|!  An exam-prep assistant that answers    | disk head in one direction...[5] ||
|!  only from your notes, and says so      | It is easy to implement [1]...   ||
|!  when it can't.                         | +------------------------------+ ||
|!                                         | |  slide p.15 (real image)     | ||
|!  [ Try the demo ]   See the results ->  | +------------------------------+ ||
|!                                         | Recorded from this demo          ||
|!                                         +----------------------------------+|
+------------------------------------------------------------------------------+
|  How it works                                                                |
|  1  Upload ........................ 7 decks, 422 slide pages  (full app)      |
|  2  Index ......................... 328 chunks, 24 copied slides skipped      |
|  3  Ask ........................... every sentence cited to a slide           |
|  4  Revise ........................ quiz, then spaced flashcards              |
+------------------------------------------------------------------------------+
|  +--------------------------------+ +-----------------+ +-----------------+  |
|  | CITED ANSWERS                  | | HONEST REFUSALS | | EXAM MODES      |  |
|  | sentence with [1]  + thumbnail | | "Not in your    | | 2 | 5 | 10      |  |
|  |                                | |  notes."        | | marks           |  |
|  +--------------------------------+ +-----------------+ +-----------------+  |
|  +-----------------+ +-----------------+ +--------------------------------+  |
|  | QUIZ real MCQ   | | SEMANTIC SEARCH | | FLASHCARDS real card + SM-2    |  |
|  +-----------------+ +-----------------+ +--------------------------------+  |
+------------------------------------------------------------------------------+
|  Results                                     concise mode, test split        |
|  Finds the right slide    hit@5        0.939  31/33  ooooooooooooooooooooo.. |
|  Ranks it high            MRR          0.856                                 |
|  Citations are correct    accuracy      100%  75/75  ooooooooooooooooooooooo |
|  Sticks to the slides     faithfulness 96.9%  31/32  ooooooooooooooooooooo.  |
|  Refuses when unsure      refusals     10/10         oooooooooo              |
|  First words appear       p50          884 ms    Search p95   47 ms          |
|  Valid quiz questions     25/25                  Tests  274                  |
|  Measured on the full system on a laptop, not re-measured on this demo.      |
|  Read the evaluation report ->                                               |
+------------------------------------------------------------------------------+
|  Under the hood:  question > browser search > 5 slides > Groq > cited answer |
+------------------------------------------------------------------------------+
|                               S Y N A P S E                                  |
|      Submitted by  Aman Pandey, B.Tech CSE, MITS Gwalior                     |
|      Under the guidance of  Dr. Manish Dixit             GitHub ->           |
+------------------------------------------------------------------------------+
|  footer                                                                      |
+------------------------------------------------------------------------------+
  (! = red margin rule; [ ] around words = highlighter)

MOBILE 390
+----------------------------+
| Synapse               (o)  |
+----------------------------+
| Ask your lecture           |
| slides. Get answers        |
| with [the slide they       |
| came from].                |
| intro text                 |
| [     Try the demo      ]  |
| See the results ->         |
| +------------------------+ |
| | Q Explain SCAN...      | |
| | answer ... [5] ... [1] | |
| | slide p.15             | |
| +------------------------+ |
+----------------------------+
| How it works               |
| 1 Upload .......... 7 decks|
| 2 Index ...... 328 chunks  |
| 3 Ask ............ cited   |
| 4 Revise ... quiz + cards  |
+----------------------------+
| one column of tiles,       |
| Cited answers first        |
+----------------------------+
| Results: rows stack        |
| hit@5   0.939  31/33       |
| oooooooooooooooooo         |
| ...                        |
+----------------------------+
| Under the hood (vertical)  |
| Title page, footer         |
+----------------------------+
```

### b) Ask (`/ask`)

- **Layout:** answer column, with the composer pinned at the bottom. Modes as a labelled segmented control: Concise,
  Detailed, 2, 5 and 10 marks, each with a one-line hint. Unit filter and "Check citations" stay. `Ctrl/Cmd+K` focuses the
  box, with a printed `kbd` hint; "Enter to send, Shift+Enter for a new line" is shown too.
- **It looks like a chat, and says what it is:** earlier questions stay on the page, but a line reads *"Each question
  is answered on its own, from your slides."* Follow-ups do not use earlier context in this system.
- **Empty state:** four tested starter questions, including one that shows a refusal: "Explain the SCAN disk
  scheduling algorithm...", "What is paging in memory management?", "Explain the access matrix model of protection.",
  and "How does TCP congestion control work? (not in these notes)".
- **Streaming:** text appears live, with a caret. Chips appear in the stream but become clickable only when the final answer
  arrives. A status line shows "Searching slides", then "Writing".
- **Citation:** yellow mono chip, tight against the word so no gap comes before the full stop. Focus highlights its sentence.
  Click opens **SlidePanel** beside the answer: slide image, file, page, section, previous and next cited slide, Esc to close,
  focus returning to the chip. A quiet row reads "5 slides searched · 2 cited", and it expands to show the uncited ones.
- **"Not in your notes":** a proper state, not a footnote. Large display line with the **exact text from the answer**,
  the existing reason in plain words, an honest line ("Synapse would rather say so than guess"), and next steps: try another unit, or
  rephrase. Abstention logic is untouched: only its presentation changes.
- **Warnings stay visible:** uncited sentences, removed citations, unsupported claims. Honesty notices are restyled, never hidden.
- **Debug line:** moves into a small "Details" disclosure under each answer, in the same words.

```
DESKTOP 1440 (slide panel open)
+------------------------------------------------------------------------------+
| Synapse          [Ask]  Quiz  Flashcards  Documents                (o)  GH   |
+-----------------------------------------------+------------------------------+
|! Ask your notes                               | SLIDE                    [x] |
|! Each question is answered on its own.        | +--------------------------+ |
|!                                              | |                          | |
|!          Explain the SCAN disk scheduling... | |  SCAN Disk Scheduling    | |
|!                                              | |  Algorithm  (real image) | |
|! The SCAN algorithm moves the disk head in    | |                          | |
|! one direction, serving all pending requests  | +--------------------------+ |
|! until it reaches the end of the disk [5].    | Unit 4 Storage management    |
|! [It is easy to implement][1]. Requests do    | p.15 · SCAN Disk Scheduling  |
|! not have to wait in a queue [1].             |                              |
|!                                              | < prev cited    next cited > |
|! 5 slides searched · 2 cited            v     |                              |
|! Details                                v     |                              |
+-----------------------------------------------+                              |
| [Concise|Detailed|2|5|10 marks]  Unit:all  [ ] Check citations               |
| +-------------------------------------------------------------+ +----------+ |
| | Ask about your slides...                         Ctrl K     | |   Ask    | |
| +-------------------------------------------------------------+ +----------+ |
+------------------------------------------------------------------------------+

EMPTY STATE                             NOT IN YOUR NOTES
+-------------------------------------+ +-------------------------------------+
|  Ask your notes                     | |          How does TCP congestion... |
|  Answers come only from the 7       | |                                     |
|  decks, with the slide to prove it. | |  Not in your notes.                 |
|                                     | |  The closest slides do not answer   |
|  Try one:                           | |  it. Synapse would rather say so    |
|  ( Explain the SCAN disk...       ) | |  than guess.                        |
|  ( What is paging in memory...    ) | |                                     |
|  ( Explain the access matrix...   ) | |  ( Try a different unit )           |
|  ( How does TCP... not in notes   ) | |  ( See what is in the notes )       |
+-------------------------------------+ +-------------------------------------+

MOBILE 390 (answer)                     MOBILE 390 (slide open: bottom sheet)
+----------------------------+          +----------------------------+
| Synapse               (o)  |          | (answer dimmed behind)     |
+----------------------------+          +----------------------------+
|        Explain the SCAN... |          | ---- drag handle / [x]     |
| The SCAN algorithm moves   |          | +------------------------+ |
| the disk head ... [5]      |          | | slide image, full width| |
| It is easy to implement [1]|          | +------------------------+ |
| 5 searched · 2 cited    v  |          | Unit 4 Storage management  |
+----------------------------+          | p.15 · SCAN Disk Scheduling|
| Concise v  Unit v  [ ]Check|          | < prev          next >     |
| [ Ask about slides...  ][>]|          +----------------------------+
+----------------------------+
| Ask   Quiz   Cards   Docs  |
+----------------------------+
```

### c) Quiz (`/quiz`)

One question at a time, as the brief asks. Setup: unit and a 5 or 10 choice, which replaces the free number box. Then:
progress bar ("Question 2 of 5"), four large answer rows with A to D. After answering: a tick or cross **and** colour,
"Correct" or "Wrong: the answer is B" (colour never alone), the explanation, and the source slide right there. A wrong answer keeps
"Make flashcard". Keys: A to D or 1 to 4 to answer, Enter for next.

**Score screen:** large "4 / 5" in display type like a mark on a paper, a list of questions with a tick or cross and their source.
**Retry** clears the answers and repeats the same questions without a Groq call; "New quiz" generates another. "Review wrong answers as flashcards" adds them all.
When fewer questions pass validation than asked, the existing notice stays.

```
DESKTOP 1440                                         MOBILE 390
+----------------------------------------------+    +---------------------------+
| nav                                          |    | Synapse              (o)  |
+----------------------------------------------+    +---------------------------+
|! Quiz · Unit 4               Question 2 of 5 |    | Question 2 of 5           |
|! [=============>                           ] |    | [=====>                 ] |
|!                                             |    | What does 'Rotational     |
|! What does the term 'Rotational Latency'     |    | Latency' refer to?        |
|! refer to according to the slides?           |    | +-----------------------+ |
|!  +-----------------------------------------+|    | | A the disk arm...   x | |
|!  | A  The time taken by the disk arm...  x ||    | +-----------------------+ |
|!  +-----------------------------------------+|    | | B a sector to...    v | |
|!  | B  The time taken for a sector...     v ||    | +-----------------------+ |
|!  +-----------------------------------------+|    | | C ...                 | |
|!  | C  ...                                  ||    | | D ...                 | |
|!  | D  ...                                  ||    | +-----------------------+ |
|!  +-----------------------------------------+|    | Wrong: the answer is B.   |
|!  Wrong: the answer is B. explanation...     |    | explanation...            |
|!  +--------+ Unit 4, p.4  [ Make flashcard ] |    | [slide thumb] Unit 4, p.4 |
|!  | slide  |                      [ Next > ] |    | [Make flashcard] [Next >] |
+----------------------------------------------+    +---------------------------+
SCORE:    4 / 5    list with v / x    [ Retry ]  [ New quiz ]    | Ask Quiz Cards Docs |
```

### d) Flashcards (`/review`)

3D flip card, with the front on paper and the back ruled like a note card. Header: "**N due today**", from `stats.due_today`. A note: *"Your cards
are saved in this browser only."* Space flips; 1 to 4 grade, printed on the buttons. The source slide opens in SlidePanel.

Next-interval labels come from the existing `sm2()` in `lib/demo/core.ts`, called read-only with the current card, so there is **no logic
change and no invented number**. As `RESEARCH.md` section 8 explains, a new card shows "1 day" on all four buttons, and later Hard,
Good and Easy show the same number. A short line explains: "New cards come back tomorrow, whichever you pick; the gap grows after
that." Without the demo flag, grading still runs in the API.

Empty state: an illustration-free card, "No cards due", with "Generate 10 cards" (noting that it uses the AI quota) and a link to Quiz:
"Wrong quiz answers can become cards."

```
DESKTOP 1440                                         MOBILE 390
+----------------------------------------------+    +---------------------------+
| nav                                          |    | Synapse              (o)  |
+----------------------------------------------+    +---------------------------+
|! Flashcards          3 due today             |    | Flashcards    3 due today |
|! Unit: all     [Generate 10 cards]           |    | +-----------------------+ |
|!                                             |    | | UNIT 4 · FROM A QUIZ  | |
|!     +----------------------------------+    |    | | What does 'Rotational | |
|!     | UNIT 4 · FROM A QUIZ             |    |    | | Latency' refer to?    | |
|!     |                                  |    |    | | ...................   | |
|!     | What does 'Rotational Latency'   |    |    | | back: The time taken  | |
|!     | refer to?                        |    |    | | for a sector...       | |
|!     |            (Space to flip)       |    |    | | Unit 4, p.4           | |
|!     +----------------------------------+    |    | +-----------------------+ |
|!                                             |    | [Again ][Hard  ]          |
|!  [1 Again] [2 Hard] [3 Good] [4 Easy]       |    | [Good  ][Easy  ]          |
|!   1 day     1 day    1 day    1 day         |    | 1 day each (tomorrow)     |
|!  Saved in this browser only.                |    | Saved in this browser.    |
+----------------------------------------------+    | Ask Quiz Cards Docs       |
                                                    +---------------------------+
```

### e) Documents (`/documents`)

A summary line, "7 decks · 422 slide pages · 328 chunks", then 7 cards: first-page thumbnail (real and lazy-loaded, 4 to 16 KB each),
unit, name exactly as in the file, pages and chunks. Plain-language notes appear only where they apply: "23 repeated slides skipped",
"7 pages need OCR" (the real values from `docs.json`). Each card has "Ask this unit", which opens `/ask` with that unit selected. Demo notice:
"Read-only in this demo". **Upload, job status and delete stay intact without the demo flag**, restyled only.

```
DESKTOP 1440                                         MOBILE 390
+----------------------------------------------+    +---------------------------+
| nav                                          |    | Documents                 |
+----------------------------------------------+    | 7 decks · 422 pages       |
|! Documents                                   |    | Read-only in this demo    |
|! 7 decks · 422 slide pages · 328 chunks      |    | +-----------------------+ |
|! Read-only in this demo. Run it locally to   |    | | [thumb]  UNIT 1       | |
|! add your own notes.                         |    | | Introduction & OS...  | |
|! +------------+ +------------+ +------------+|    | | 48 pages · 47 chunks  | |
|! | [thumb]    | | [thumb]    | | [thumb]    ||    | | Ask this unit ->      | |
|! | UNIT 1     | | UNIT 1     | | UNIT 2     ||    | +-----------------------+ |
|! | Intro...   | | Process... | | Process... ||    | | [thumb]  UNIT 1       | |
|! | 48p · 47ch | | 120p ·100ch| | 59p · 53ch ||    | | ...                   | |
|! | Ask unit ->| | Ask unit ->| | Ask unit ->||    | +-----------------------+ |
|! +------------+ +------------+ +------------+|    | ...                       |
|! ... 4 more cards                            |    | Ask Quiz Cards Docs       |
+----------------------------------------------+    +---------------------------+
```

## 5. Shared components (`web/components/ui/`)

Button, Card, Badge, CitationChip, SlidePanel, Skeleton, EmptyState, ErrorState, Stat, as the brief lists, plus ThemeToggle, Kbd, Tally
and TabBar. `SlidePanel` replaces `SlideModal`: docked `aside` from 1024 px, native `<dialog>` sheet below that, which gives
focus trapping and Esc for free. Native elements are preferred, so no Radix is needed.

## 6. States everywhere

| State | Treatment |
|---|---|
| **First-visit warm-up** | Banner on Ask: "Preparing search in your browser. First visit downloads a 34 MB model; later visits are instant." Real progress bar, **if approved** (section 10). The question box stays usable: a question typed early waits and says so. |
| Loading: answer | Skeleton lines shaped like an answer, then streaming text |
| Loading: quiz, cards | Skeleton of question rows; "Writing your quiz..." |
| Loading: documents | 7 skeleton cards |
| Loading: slide | Fixed 16:9 frame (slides are 1100 x 619), so nothing jumps |
| Empty | Every page: one sentence on what goes here, one action |
| Rate limit | "The free AI quota is busy. Wait a minute and try again." with Try again. Amber, not red. |
| Connection | "Could not reach the demo. Check your connection and try again." |
| Model failed | "This browser could not download the search model. Try again, or use a different network." |
| Other | "Something went wrong. Try again." Real detail goes to `console.error` only. |

Errors are mapped in a new `web/lib/messages.ts`, which reads `ApiError.status` and the message and returns plain words. **No raw error text reaches the
page**, and `lib/api.ts` is unchanged. The local non-demo "API not reachable; start uvicorn" message stays, because a developer needs it.

## 7. Accessibility

- WCAG AA: all token pairs computed in section 2; checked again in the browser with axe on every page, dark and light.
- Visible focus everywhere; skip link; one `h1` per page; landmarks.
- Keyboard: full use of all pages, with Ctrl/Cmd+K, Space, 1-4, A-D, Enter and Esc. Single-key shortcuts act only when focus is not in a field or on a button, so Space never double-fires.
- Touch targets of at least 44 px (today's checkbox is 13 px).
- Colour is never the only signal: right and wrong also use an icon and a word.
- Slide alt text: `Slide: {file, page}, {section}`. In Ask, the slide's extracted text is also available to screen readers.
- Streaming answers use `aria-live="polite"` and announce when finished, not on every word.
- Native `<dialog>` handles focus; focus returns to the chip that opened the panel.

## 8. Performance budget

| Item | Today (live) | Budget |
|---|---|---|
| Landing LCP on Vercel | 652 ms desktop; 820 ms throttled | **under 2.5 s** on Lighthouse mobile |
| Landing JS | 155 KB | at most 185 KB |
| CSS | 5 KB | at most 20 KB |
| Fonts | none | 99 KB preloaded; mono 39.5 KB on demand |
| Hero slide | none | real WebP, 26 KB, lazy, reserved space; the headline text remains the LCP element |
| Model | loads on Ask only | **still Ask only**: landing never touches it |

The landing is a Server Component, with small client islands only for the hero preview and the theme toggle. Only one new runtime dependency.
Theme is set by an inline script in `<head>` to avoid a flash, as the Tailwind docs recommend. The stored key stays `localStorage.theme`, which the existing screenshot script already sets.

## 9. Build order

Times are working estimates and include lint, build, screenshots at both widths in both themes, and fixes. One commit per page; pushed each time so that the Preview URL stays current.

| Pri | Work | Estimate |
|---|---|---|
| **P0** | Tokens, fonts, shell (nav, tab bar, footer, theme toggle), shared components, plus a colour pass over the unredesigned pages so nothing breaks in dark mode | 40 min |
| **P0** | Landing | 40 min |
| **P0** | Ask (panel, states, friendly errors) | 40 min |
| **P1** | Quiz | 20 min |
| **P1** | Flashcards | 20 min |
| **P2** | Documents | 15 min |
| **P2** | Polish, Lighthouse on Preview, axe, PROGRESS, NOTES, VIVA, ARCHITECTURE 14 | 30 min |
| | **Total** | **about 3 h 25 min** |

**Safe stopping points.** `main` and the live site do not change until you merge. Each commit leaves the app working. If time runs out,
merging after P0 gives a new landing and Ask, while Quiz, Flashcards and Documents work in the new colours and shell.

**Proof at each step:** `npm run lint`, `npm run build`, self-check still matching, Ask, Quiz and Flashcards driven end to end in demo mode. The self-check needs the search model, and these flows use a little Groq quota.

## 10. What will and won't change

**Not touched:** `src/`, `web/lib/demo/core.ts`, `web/lib/demo/server.ts`, `web/app/api/demo/*`, `web/public/demo/*`, `web/lib/api.ts`, retrieval, embeddings, citation checking, the "Not in your notes" rule.

**Changed:** `web/app/layout.tsx`, `globals.css`, `page.tsx`, the 4 page files, `web/components/*`, new `web/components/ui/*`, `web/lib/messages.ts`, `web/app/fonts/*`, `web/package.json` and lock (`lucide-react`, exact pin), and the docs. ARCHITECTURE 14 gets updated first, as CLAUDE.md requires: the landing becomes a Server Component, and new components and error wording are listed.

**One decision needs you, because your rule says to ask.** A real progress bar needs a small edit in `web/lib/demo/client.ts`, which is a protected file:

```diff
+let onProgress: ((percent: number) => void) | null = null;
+export const watchModelLoad = (fn: typeof onProgress) => { onProgress = fn; };
 ...
-    return pipeline("feature-extraction", MODEL, { dtype: "q8" });
+    return pipeline("feature-extraction", MODEL, {
+      dtype: "q8",
+      progress_callback: (e) => { if (e.status === "progress_total") onProgress?.(e.progress); },
+    });
```

It changes no model, query, ranking or result: it only reports download progress, and the self-check would prove that. `progress_total` is confirmed in the 4.3.1 file the app already loads.

- **Option 1 (recommended): allow this edit.** A real percentage during the 29 s.
- **Option 2: no edit.** The banner names each step only as it finishes, read from the browser's resource timing. It is honest, but it shows no movement during the 34 MB file, which is the longest wait. No fake progress in either case.

## 11. Risks

| Risk | Handling |
|---|---|
| Vercel Preview lacks `NEXT_PUBLIC_DEMO` or `GROQ_API_KEY` | Pushing this docs-only commit tests it first. They are per-environment settings on Vercel. |
| Vercel protects Preview URLs with a login | Would block Lighthouse from outside. Lighthouse then runs on a local production build, and I will say so. |
| Groq rate limit during the evaluation | The online demo has no answer cache. Landing preview needs no Groq; friendly error otherwise. Avoid heavy testing just before. |
| First-time 29 s wait in front of examiners | Open `/ask` once on the evaluation laptop beforehand, so that the model is already cached. |
| Examiner opens the report and sees 5-mark faithfulness of 12.5% | The marksheet states "concise mode" and links there. Have the declared fix ready to explain. The report is also titled "(draft)", which you may want to change: I will not change it unasked. |
| Serif and cream looks old-fashioned | Large type, sharp grid, real slides; checked against screenshots at every step. |
| A merge goes wrong | Vercel can roll back to the previous deployment; exact steps come at the end of Phase 3. |

## 12. Questions for your approval

1. **Direction:** Marginalia (A)?
2. **The progress edit:** Option 1 or Option 2 (section 10)?
3. **What time is your evaluation?** This sets where to stop. Without an answer I build P0, P1, P2 in order and tell you at each safe point.
