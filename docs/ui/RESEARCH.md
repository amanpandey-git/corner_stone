# Synapse UI research (Phase 1)

Date: 2026-11-03. No application code was changed for this phase.

**How to read this file.** Values marked "measured" were read from the live page in real Edge through Playwright
(computed styles, not guesses). The raw data is in `captured/reference-sites-measured.json`. Claims from articles
are linked. Most design articles are agency or vendor blogs, so they are treated as direction, not proof.
Third-party screenshots were looked at but not committed, because this repo is public and they are not ours.

## 1. Result in five lines

1. All 12 sites measured use a sans-serif display face, and 9 of the 12 use Inter or Geist. A well-set serif
   display is the cheapest way to stop looking like every template.
2. All four study and note-taking products measured (NotebookLM, RemNote, Quizlet, Notion) use a blue accent. Your classmate uses purple. A
   highlighter yellow belongs to nobody in this set, and it means "this is the important bit" to any student.
3. The best citation pattern keeps the answer visible next to the source. Synapse's modal hides the answer.
4. The current app has few technical faults (1 axe violation) but no design at all. The problem is missing
   identity, missing states and hidden proof, not broken code.
5. Aceternity's licence forbids redistributing source files and this repo is public, so no Aceternity code is used.

## 2. Reference sites (measured)

| Site | Page background | Display type: font, size / line, weight, tracking | Accent or main button | Nav | LCP* |
|---|---|---|---|---|---|
| [linear.app](https://linear.app/) | `#08090A` | Inter Variable, 72/72, 510, -1.58 px; Berkeley Mono | one lime highlight | fixed, 73 px, blur | 4.2 s |
| [vercel.com](https://vercel.com/) | `#FAFAFA` | Geist, 64/64, 400, -3.84 px; Geist Mono | `#171717` pill, 40 px | sticky, 64 px | 1.0 s |
| [raycast.com](https://www.raycast.com/) | `#07080A` | Inter, 64/70, 600 | `#E6E6E6`, radius 8, 36 px | floating bar | 2.5 s |
| [notion.com](https://www.notion.com/) | `#FFFFFF` | NotionInter, 96/100, 600, -4.6 px; Lyon Text serif in quotes | `#0075DE`, radius 8, 38 px | 64 px | 1.1 s |
| [perplexity.ai](https://www.perplexity.ai/) | near-white, theme `#FCFCF9` | pplxSans, 26/39, 400 | dark pill | none: one search box | 4.7 s |
| [NotebookLM](https://notebook.google/) (the site now calls it Gemini Notebook) | `#FFFFFF` | Google Sans, 76/80, 500, -0.85 px | `#3186FF` text, `#1F1F1F` pill, 50 px | sticky, 80 px | 3.3 s |
| [RemNote](https://www.remnote.com/) | `#FFFFFF` | Inter Display, 40/50, 700, -1 px | `#4B69FF`, radius 6, 48 px | 84 px | 3.2 s |
| [Quizlet](https://quizlet.com/) | `#F6F7FB` | Hurme, 44/56, 700 | `#4255FF` pill, 48 px | sticky, 64 px | 6.2 s |

*One headless load from this laptop's connection, so treat it as a rough comparison only.

### What makes each look modern, and what Synapse takes from it

| Reference | What makes it look modern | Borrow | Avoid |
|---|---|---|---|
| **Linear** | Medium weight (510), not bold, with tight tracking. Near-black is tuned, with text in 4 grey steps. The product itself is the hero image. | Show the real product as the hero. Use a few precise text-colour steps. | The dark, near-monochrome look: it is the classmate's territory. |
| **Vercel** | Very tight tracking on regular weight. Nearly no colour. Hairline grid lines. | Hairline rules instead of heavy boxes. | Enterprise logo strip (Synapse has no such logos, and fakes are banned). |
| **Raycast** | The page reads as a long product screenshot. Keyboard hints are visible on screen. One large colour moment. | Visible `kbd` hints on real shortcuts. | Scroll length of 16,000 px; heavy imagery. |
| **Notion** | Very large type with a friendly inline accent. A serif used only for human quotes. Asymmetric cards, each showing a real UI. | Inline accent shape in the headline. Feature tiles that show real output, not icons. | Logo walls, testimonial portraits. |
| **Perplexity** | Answer first, evidence next, exploration last ([breakdown](https://www.925studios.co/blog/perplexity-design-breakdown)). The citation sits at the claim. | See section 3. | Three overlapping routes to the same sources, which a [teardown](https://aiuxplayground.com/teardowns/perplexity/citations) calls confusing. |
| **NotebookLM** | Three working panels: sources, chat, studio. Clicking a citation scrolls to the passage ([Google help](https://support.google.com/notebooklm/answer/14276569?hl=en)). | Show the source beside the answer. | Its gradient hero, which looks like every AI product. |
| **RemNote** | Study outputs are named immediately (flashcards, quizzes, summary, tracking). | Say the study outputs plainly and early. | "Trusted by 1,000,000+ students" style claims: Synapse has no user numbers. |
| **Quizlet** | Big, simple choices. Large 48 px buttons. | One decision per screen in Quiz and Flashcards; large targets. | Slow, ad-like weight. |

## 3. Citations: the core design decision

Sources: [AI UX Playground teardown](https://aiuxplayground.com/teardowns/perplexity/citations),
[925 Studios breakdown](https://www.925studios.co/blog/perplexity-design-breakdown),
[Google NotebookLM help](https://support.google.com/notebooklm/answer/14276569?hl=en),
[NotebookLM what's new](https://support.google.com/notebooklm/answer/14290935).

- **Perplexity:** chips at the end of each claim. A click opens a popover or a right-side panel, and the answer stays
  visible. A teardown notes that the panel narrows the answer on small screens and suggests a full-width sheet there.
- **NotebookLM:** numbered markers. Hover shows the quote; a click scrolls the source viewer to the passage.
- **Synapse has something neither has:** the source is the actual slide image, with the exact page.

**Decision.** Keep numbered chips at the claim. A click opens the slide **beside** the answer on desktop, with the
claim still readable, and as a bottom sheet on phones. One route to a source, not three. Show "5 slides searched, 2
cited", which also explains why chips can read 1 and 5 with no 2, 3 or 4. That gap looks like a bug today.

## 4. Component libraries and licences

Rule from the brief: free, open-source, licence allows this use, no paid templates. This repo is public, which
matters for the licences below.

| Source | Licence (checked) | Decision |
|---|---|---|
| [shadcn/ui](https://ui.shadcn.com/blocks) | MIT, (c) 2023 shadcn ([licence file](https://raw.githubusercontent.com/shadcn-ui/ui/main/LICENSE.md)) | Allowed. Component shapes and variant names followed. No Radix dependency needed. |
| [Magic UI](https://magicui.design/) free components | MIT, (c) Magic UI ([licence file](https://raw.githubusercontent.com/magicuidesign/magicui/main/LICENSE.md)) | Allowed. Nothing planned yet; its Pro templates are paid and excluded. |
| [Aceternity UI](https://ui.aceternity.com/) | [Licence page](https://ui.aceternity.com/licence): "You cannot re-distribute the Item as a stock image or its source files, regardless of modifications." It does not separate free from paid components. | **Not used**, even though the brief lists it: the brief also requires a licence that allows this use, and copying its source into a public repo looks like redistribution. Ideas only. |
| [shadcnblocks](https://www.shadcnblocks.com/) free blocks | [Terms](https://www.shadcnblocks.com/terms) allow "a public repository whose purpose is the End Product"; no republishing as a library | Allowed but not needed. Paid blocks excluded. |
| [Tailwind Plus](https://tailwindcss.com/plus) | Paid product ([licence](https://tailwindcss.com/plus/license)) | Excluded by the brief. |
| [Vercel templates](https://vercel.com/templates/next.js) | Varies by template | Reference only. Its Chatbot templates confirm the chat layout convention. |
| lucide-react 1.66.0 | ISC (npm registry) | **Used** for icons. |
| motion 14.9.0 | MIT (npm registry). [Stated size](https://motion.dev/docs/react-reduce-bundle-size): 43 KB full; just over 5 KB for `m`, plus 24 KB for `domAnimation` | **Not needed** so far: every planned animation works in CSS. |
| Fraunces, Atkinson Hyperlegible Next, JetBrains Mono | OFL-1.1 (`@fontsource-variable` package metadata) | **Used**, self-hosted. |

**Result:** the only new runtime dependency planned is `lucide-react`. Less copied code means less to defend in a viva.

## 5. 2026 trends: what to adopt

| Trend | Evidence | Decision for Synapse |
|---|---|---|
| Bento grid | Common, and now [criticised as derivative](https://design-styles.enlighten-media.net/pages/bento-ui/). Works only [when content has a natural hierarchy](https://www.saasframe.io/blog/designing-bento-grids-that-actually-work-a-2026-practical-guide); [equal tiles work against the page](https://www.buildmvpfast.com/blog/bento-grid-helps-vs-hurts-conversion-2026). | Use it, with unequal tiles. Cited answers gets the most space, and every tile shows real output, never an icon and a sentence. |
| Bold, large type | Named by [IONOS](https://www.ionos.com/digitalguide/websites/web-design/webdesign-trends/) and [Hostinger](https://www.hostinger.com/uk/tutorials/web-design-trends/). Measured display sizes above run 40 to 96 px. | Yes: up to 84 px, in a serif nobody else in this set uses. |
| Whitespace | The measured sites use tall sections and narrow text columns. | Yes. Today's landing is empty because of missing content, not because of designed space. |
| Dark theme designed on purpose | [Firebrand](https://www.firebrandagency.com/blog/web-design-trends-2026) lists dark mode; "on purpose" is the brief's own requirement. | Yes: warm "desk lamp" palette, not inverted. Slides are dimmed so they do not glare. |
| Muted base, one vivid accent | Confirmed by every site measured. | Yes: paper and ink plus highlighter. |
| Micro-interactions | [IONOS](https://www.ionos.com/digitalguide/websites/web-design/webdesign-trends/) | Only where they carry meaning: the highlight sweep on a cited sentence, the card flip. |
| Scroll reveals | `view()` works in [Chrome and Edge](https://developer.chrome.com/articles/scroll-driven-animations) and Safari 26. [Firefox stable may still need a flag](https://www.buildmvpfast.com/blog/css-scroll-driven-animations-replace-js-2026) (sources disagree, unverified). | CSS only, inside `@supports`. Content is visible without it. |
| Skeleton loading | Standard practice | Yes, shaped like the real content. |
| Command palette (Ctrl/Cmd+K) | Raycast and Magic UI show keyboard hints | Ctrl/Cmd+K focuses the question box as the brief asks. A full palette is not worth building for 4 pages. |

Flashcards: Anki has a preference named ["Show next review time above answer buttons"](https://docs.ankiweb.net/preferences.html),
and [forum users complain](https://forums.ankiweb.net/t/keyboard-ux-improvements/13471) that shortcuts are hard to
discover. So: intervals on the buttons, and shortcuts printed on the buttons too.

## 6. Three candidate directions

A warning that applies to all three: cream-and-serif is itself becoming a common AI-product look. A palette alone
gives no identity. What gives identity is structure taken from real study material, which is why A's value is in
the exam-paper layout, the highlighter behaviour and real slides, not the colour of the paper.

### A. Marginalia (recommended)
*"A well-annotated textbook, the night before the exam."*

- **Palette:** paper `#FAF6EC`, ink `#1F1B16`, highlighter `#FFD93D`, red-pen margin `#B3261E`. Dark: warm desk-lamp black `#15130F`.
- **Fonts:** Fraunces (display), Atkinson Hyperlegible Next (body), JetBrains Mono (page references, marks, numbers).
- **Why it fits:** a citation becomes a highlight, the slide opens in the margin, answer modes read like marks on an
  exam paper, results read like a marksheet, and the author section reads like a project title page.
- **Risk:** can look old-fashioned if overdone. Controlled with large type, sharp layout and very little ornament.

### B. Lecture Hall
*"Lights down, one bright board."*

- **Palette:** chalkboard green-black `#12201B`, chalk `#EEF2EA`, chalk yellow `#F4D35E`.
- **Fonts:** Bricolage Grotesque, Inter, Geist Mono.
- **Why it fits:** an obvious classroom metaphor, and dark-first looks striking in a demo room.
- **Risk:** closest to the classmate's dark SaaS look; white slide images glare on it; chalk easily turns into a
  gimmick; weak in light mode.

### C. Index Card
*"A Swiss textbook: exact and unfussy."*

- **Palette:** cool white `#FBFCFD`, graphite `#14171A`, vermilion `#E5401A`, faint graph-paper grid.
- **Fonts:** Schibsted Grotesk, Hanken Grotesk, IBM Plex Mono.
- **Why it fits:** very clean and fast; numbers look serious.
- **Risk:** competent but forgettable: close to Vercel and to many templates, so it says little about studying.

**Recommendation: A.** It is the only one where the design explains the product: every claim is marked up against
its source. It is also the furthest from the classmate's template and from all the sites measured.

## 7. The current app: concrete problems

**Method:** screenshots of all 5 pages at 1440 and 390 px in light and dark (`before/`), real states driven on the
live site (`before/state-*.png`), plus axe-core and layout checks on all pages (`captured/audit-before.json`). The
captures and checks used 4 Groq calls on the live site. The dark screenshots are byte-identical to the light ones, because the
app has no dark theme.

### Measured baseline

| Measure | Result |
|---|---|
| Landing LCP on the live site, 1440 px | 652 ms |
| Landing LCP on the live site, 390 px, CPU x4 + slow network | 820 ms |
| Landing transfer | JS 155 KB, CSS 5 KB, no web fonts |
| First visit to Ask until search is ready | **29.3 s** in a fresh browser (model 34 MB, plus 5.3 MB runtime) |
| Cited answer once ready | about 2.4 s (first words after 822 ms in that run) |
| Browser search self-check | top 5 match the Python model |
| Horizontal overflow, console errors | none on any page at either width |
| axe-core violations | 1 serious (Documents, 390 px) |
| Touch targets under 44 px at 390 px | 5 to 9 on every page; the checkbox is 13 x 13 px |

### Whole app
1. **No identity.** System font everywhere, every page title is 24 px, slate-and-black only.
2. **Every border is near-black.** Root cause: Tailwind 4's `border` defaults to the current text colour, and the
   code never sets a colour. So every card, input and table row looks harsh and equally loud.
3. **No dark theme** at all.
4. **Nav wraps to two rows on phones**, with 28 px targets, and shows developer data ("7 docs · 328 chunks").
5. **Nav polls `/api/demo/health` every 15 s**, for as long as any tab stays open.
6. **The proof is hidden.** No evaluation number, report link, GitHub link, author or guide appears anywhere.
7. **No footer, no skip link, no custom focus style.**
8. **Raw errors reach the user.** Seen today: `Groq openai/gpt-oss-120b: HTTP 401 invalid_request_error (key refused; check GROQ_API_KEY)`.

### Landing
9. No promise, no main action, no proof: one 24 px line and four small cards; about 400 characters in total.
10. About 60% of a 1440 px screen is empty.
11. **The first step is a dead end.** "1. Upload your notes" leads to a page saying uploads are off in the demo.
12. A visitor cannot see what an answer looks like without first waiting for the model.

### Ask
13. **The 29 s first load has no indicator.** It only says "Searching your notes...", so the page looks frozen, which
    is the worst possible moment in a live demo.
14. No starter questions, so the visitor has to invent one.
15. **The citation modal covers the answer**, so the claim and its slide can never be compared. This is the product's
    best moment. It also does not move or trap keyboard focus (read from the code).
16. Chips leave a gap before the full stop ("requests 5 ."), and chips read 5 and 1 with no explanation.
17. **"Not in your notes" looks like a footnote:** a small grey strip for the product's proudest behaviour, with no next step.
18. Modes appear as raw values (`concise`, `2-mark`) in a bare dropdown, with no idea of length.
19. Debug line shown to users: `groq openai/gpt-oss-120b · first words after 822 ms`.
20. Raw file names everywhere: `Unit 4_Storage management_ Disk Schduling`. (The typo is in the source PDF's name.)
21. Enter sends and Shift+Enter makes a new line, but nothing says so.

### Quiz
22. All questions appear at once in one long scroll, so there is no focus and no sense of progress.
23. Right and wrong differ by colour alone in the options (WCAG 1.4.1), and unchosen options fade to low contrast.
24. The score is a grey strip with no retry; the only option is to generate a new quiz, which uses quota.
25. No loading state beyond the button label. The question count is a free number box.

### Flashcards
26. Not a card: a form with a "Show answer" button.
27. No next-interval information, no keyboard shortcuts, and nothing saying cards live only in this browser.
28. Grammar: "1 cards in total". File name shows `.pdf` here but not in Ask.
29. The empty state is a single grey line, on what most first-time visitors will see.

### Documents
30. A 6-column table is the wrong shape at 390 px: it scrolls sideways, and the scroll area cannot be reached by
    keyboard (the axe violation).
31. "Flagged" and "Duplicates" are unexplained jargon, though "zero silent failures" is a real strength worth showing.
32. No totals and no sense of what the decks are; no slide thumbnails.

## 8. Facts found that the design must respect

These came from reading the code and the report, and each one changes the plan:

- **Answer metrics are for concise mode.** In the same report, the 5-mark test sample has citation accuracy 96.6% but
  faithfulness 12.5% (1/8), before a declared fix that was only re-measured partially on dev. The landing promotes
  exam modes, so the results section must say "concise mode" beside those numbers, and link to the report.
- **The numbers were not re-measured on the online demo.** They come from the Python system on a laptop (PROGRESS.md).
  The results section says so.
- **It is not really a chat.** Follow-up rewriting was cut, so each question is answered alone. A thread that implied
  memory would mislead, so the page says so.
- **SM-2 makes the interval buttons look alike.** A new card returns in 1 day on every grade. Later, Hard, Good and
  Easy show the same number, because the grade only affects later intervals. The buttons will show this honestly.
- **No answer cache online**, so a Groq rate limit can happen during a demo. The friendly error and the landing's
  recorded answer are the safety net.
- **Real progress needs a logic edit.** `web/lib/demo/client.ts` does not expose download progress. transformers.js
  4.3.1 does support it (`progress_callback`; `progress_total` confirmed in the file served by the CDN). See UI_PLAN.md section 10.
- **"Chunks" and "pages" differ:** 422 slide pages, 328 indexed chunks. Both are used, and labelled.

## 9. Other sources

Trend overviews: [IONOS](https://www.ionos.com/digitalguide/websites/web-design/webdesign-trends/),
[Hostinger](https://www.hostinger.com/uk/tutorials/web-design-trends/),
[Firebrand](https://www.firebrandagency.com/blog/web-design-trends-2026),
[Studio Meyer reality check](https://studiomeyer.io/en/blog/webdesign-trends-2026-reality-check).
Implementation: [Tailwind dark mode](https://tailwindcss.com/docs/dark-mode),
[Motion bundle size](https://motion.dev/docs/react-reduce-bundle-size),
[transformers.js progress guide (third-party)](https://instagit.com/huggingface/transformers.js/tracking-model-loading-progress-with-progress-callback-option).

**Not measured:** Aceternity (screenshot timed out) and Tailwind Plus (this browser was redirected to its login page).
Notes on those two rest on their public licence pages and search results only.
