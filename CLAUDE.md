# CORNERSTONE - PROJECT PILOT v1.0 (Stage 1: Extraction & Indexing)

Read this file, PROGRESS.md and ARCHITECTURE.md at the start of every session, run the tests, and tell the user in 3 lines where we are.

## 0. CONTEXT
- User: 3rd-year B.Tech CSE student. Knows Python, learning ML. Has not built a RAG system before.
- Project: an exam-prep study assistant. Students upload notes, textbooks and past papers (PDF, DOCX). Stage 1 handles English-language documents only. The system extracts and indexes them so that later an LLM can answer questions with citations and generate study material.
- Deadline: working demo of extraction + indexing for university evaluation, built in 2 days: 16 October 2026. The generative part is built next semester.
- User is on Claude Pro, so usage is limited. Work in small steps, keep replies compact, save state to files often (Section VIII).
- Code must run on: Windows 64-bit (x64), Intel Core i5-1135G7 (4 cores), 8 GB RAM (7.74 GB usable), Intel Iris Xe (no CUDA). CPU only, modest memory (batch embeddings, small model).
- Python: 3.12.10 in `.venv`.
- Repo: github.com/amanpandey-git/corner_stone (public). `samples/` holds 7 PDFs (the initial document set, moved from `test/` with git mv). They are exempt from the 5 MB rule.

## I. ROLE
You are the development pilot for this repo, not an autocomplete. You:
- Define contracts before code: no module is implemented before its interface and data schema are written in ARCHITECTURE.md.
- Prove correctness before adding features: each step is tested on samples/ before the next step starts.
- Lock versions before writing code that depends on them.
- Root-cause every bug. Never patch around a symptom.
- Keep state in files in the repo, never only in chat.
- Teach while building: the user must be able to explain every part in the viva.

## II. PROJECT LOCK (Stage 2: study assistant; Stage 1 text archived at the end of this file)
Product (decided): an exam-prep assistant for a student studying their own course slides. It answers only from their notes, every claim cites file and page, and the citation opens the slide image. When the notes don't contain the answer it says "not in your notes". Answers can be shaped as 2, 5 or 10-mark university answers. It also generates quizzes (MCQs with cited answers) and flashcards (with spaced repetition) per unit or per document. The demo leads with cited exam-style answers; the quiz + flashcard loop is the second act. Both are core scope.
Tie-breaker: when a decision is unclear, choose whatever makes citations, abstention and measured quality stronger.

In scope for Stage 2, built in this order (contracts in ARCHITECTURE.md before each phase's code):
1. Retrieval quality: near-duplicate page removal at ingest (record which page each skipped slide duplicates) + collapse of near-identical results at query time; slide-aware chunking (one slide per chunk where it fits, exact page numbers, a "file > section" context header prepended before embedding); page images (PyMuPDF PNG under data/); hybrid search (SQLite FTS5 + vector, merged with Reciprocal Rank Fusion; rank_bm25 only if FTS5 is missing); cross-encoder reranker on the top 30 (adopted only if the dev ablation shows a gain and p95 stays < 1 s; always switchable in config); filter by document and by unit; index compaction command; schema + index version bump (an old index fails loudly and offers a rebuild). After each change: an ablation row on the dev split (change, hit@5, MRR, p95 latency). Test split reported once, at the end of the phase.
2. Answering: provider-agnostic LLM interface with Groq and Gemini adapters chosen in config.yaml (timeouts, retries, rate-limit handling, answer cache); grounded prompt (answer only from retrieved chunks, numbered [n] citations mapped to file + page, "not in your notes" when evidence is insufficient); modes concise / detailed / 2-mark / 5-mark / 10-mark; follow-up rewriting from the last few turns; streaming; citation check (each cited chunk supports its sentence, unsupported claims flagged); answer evaluation on the test split (citation accuracy, faithfulness, abstention rate, time to first token) with an LLM judge + 20 answers listed for the user's manual spot check; runs paced for free-tier limits.
3. API: FastAPI endpoints for documents (upload with background ingestion + status, list, delete), search, ask (streaming), page image, quiz, flashcards, health. OpenAPI docs, TestClient tests, GitHub Actions running pytest on every push.
4. Frontend: Next.js + TypeScript in web/, Tailwind CSS only: upload + list with ingestion status, chat with streamed answers, clickable citations showing the slide image, answer-mode selector. Simple components; all logic stays in the API. The Streamlit page keeps working as a fallback.
5. Learning: quiz generator (MCQs from a document or unit, each correct answer cited to its slide, JSON validated with Pydantic, retried on failure); flashcards from a unit, each linked to its source slide, SM-2 spaced repetition stored in SQLite; a wrong quiz answer can become a flashcard; quiz and review pages in the app.
6. Polish: README, evaluation report with the ablation table, demo script (5-mark answer -> click citation -> slide; unrelated question -> "not in your notes"; quiz; flashcards), PR stage-2 -> main, tag v0.2.
Only if everything else is green: weak-topic tracking.

NOT building in Stage 2: OCR, PPTX/URL ingestion, table and diagram extraction, notebooks, accounts or multi-user, an external vector database, deployment, knowledge graph, audio, past-paper analysis. Still out: non-English documents. If reaching for any of these: stop, that is scope creep.

Targets (on the test split; report the real number either way): hit@5 >= 0.90 and no more than one test question worse than v0.1 (a v0.1 hit@5 that becomes a miss; v0.1 baseline 0.879 = 29/33, eval/results/baseline_v0.1_test.md); reranked search p95 < 1 s on this laptop; citation accuracy >= 90%; faithfulness >= 90%; >= 8 of the 10 test out-of-scope questions answered "not in your notes"; time to first token p50 < 3 s; >= 95% of quiz questions valid.

Evaluation rules: eval/questions.jsonl has a dev and a test split (rule in eval/QUESTIONS_FORMAT.md). Tune only on dev. The test split is run only at: the baseline (done), the end of Phase 1, the Phase 2 answer evaluation, and the final report; every test run is logged in NOTES.md, and nothing is changed because of a test result without saying so next to the number.

Cut (decided 2026-10-15): quiz UI polish, neighbour expansion, weak-topic tracking, follow-up rewriting. If behind: SM-2 is the first cut (keep plain flashcards). Next.js is kept (4 pages: Documents, Ask, Quiz, Flashcard review); the Streamlit page stays working as the fallback until the web app works end to end, and if the web app is not demoable on the morning of 24 Oct the demo runs on Streamlit. Never cut citations, abstention, the evaluation, the tests, or quiz + flashcard generation.

Schedule (approved 2026-10-15; tag v0.2 on 24 Oct; report and PPT written after):

| Day | Work | Notes |
|---|---|---|
| 15 Oct (night) | Phase 1: page images, slide chunking + context header, FTS5 keyword search, rrf_merge structure + tests (user writes it), collapse, filters, compaction | dev ablation row per change |
| 16 Oct (Stage 1 evaluation; light) | finish Phase 1 leftovers; user writes rrf_merge after the evaluation | spot-checks after the evaluation |
| 17 Oct | hybrid search wired with the user's rrf_merge; reranker ablation (adopt only if dev gain and p95 < 1 s) | |
| 18 Oct | Phase 1 test run (once), close Phase 1; start Phase 2: LLM interface (Groq + Gemini, timeouts, retries, rate limits, cache) | .env with both keys needed |
| 19 Oct | grounded [n] prompt + "not in your notes", answer modes, streaming; Streamlit Ask (fallback) | |
| 20 Oct | citation parser (user writes) + citation check; answer evaluation on dev (LLM judge); prompt work on dev only | |
| 21 Oct | answer evaluation on test (paced), 20 answers for spot check; quiz generator (Pydantic + retry, cited); FastAPI: documents, search, ask (streaming), page image, health | Node 24 LTS installed by end of day |
| 22 Oct | flashcards + SM-2 (user writes core; first cut) + wrong answer -> flashcard; FastAPI: quiz, flashcards; TestClient tests, GitHub Actions; Next.js scaffold + Documents page | Streamlit quiz/review fallback |
| 23 Oct | Next.js: Ask (streamed, mode selector, citations open slide image), Quiz, Flashcard review | |
| 24 Oct | morning go/no-go: Next.js demoable end to end, else demo on Streamlit; FREEZE: README, evaluation report + ablation table, demo script, rehearsal, PR stage-2 -> main, tag v0.2 | report/PPT written after |
| 25 Oct | final evaluation | |

Learning rule: for SM-2 and the citation parser, the user writes the core function: give the structure and tests, then review their code. (rrf_merge: written by the assistant at the user's request on 2026-10-15, explained line by line in VIVA.md.) Everything else: explain the key lines in VIVA.md.

Protected (never touch): ../corner_stone_stable (the Stage 1 evaluation demo), branch stage-1-stable, tags v0.1-*. Never commit .env, keys, data/, page images, model files or files over 5 MB; never print keys. Never uninstall already-installed packages. When the user says "freeze": stop, snapshot to PROGRESS.md, commit and push.

Stage 2 overrides: Section V "work on main" -> work on branch stage-2, PR to main at the end. Section XV build order -> the phases above. Section X metrics -> plus the Stage 2 targets above (new metrics only via ARCHITECTURE.md).

## III. REPO STRUCTURE (fixed - do not improvise another layout)
Stage 2 adds, at top level: `web/` (Next.js app), `.github/workflows/` (CI), `data/images/` (page PNGs, gitignored), and new modules under `src/cornerstone/` whose names are fixed in ARCHITECTURE.md before each phase.
```
corner_stone/
├── CLAUDE.md            # these rules; read at the start of every session
├── README.md            # what it is, setup, how to run, results, limitations
├── ARCHITECTURE.md      # source of truth: contracts, schemas, config, toolchain, decisions
├── PROGRESS.md          # session log (Section VIII)
├── NOTES.md             # decision + bug log: date | what | why / root cause | fix
├── VIVA.md              # likely examiner questions with short answers, per step
├── requirements.txt     # exact pinned versions
├── .gitignore
├── .env.example
├── config.yaml          # chunk size, overlap, model, HNSW params, paths (no magic numbers in code)
├── src/cornerstone/
│   ├── ingest/          # pdf_parser.py, docx_parser.py, cleaner.py, loader.py (dispatch by type)
│   ├── chunking.py
│   ├── embeddings.py
│   ├── index/           # hnsw_index.py, metadata_store.py (SQLite), manifest.py
│   ├── pipeline.py      # ingest_file(): hash -> parse -> clean -> chunk -> embed -> index -> store
│   ├── search.py
│   └── cli.py
├── app/streamlit_app.py # thin UI over the same functions; no logic in the UI
├── eval/                # questions.jsonl, ann_vs_bruteforce.py, retrieval_eval.py, results/
├── tests/               # pytest, one file per module, runs on samples/
├── samples/             # small test documents (committed)
├── data/                # raw/ and index/ - gitignored
└── docs/                # stage-1-plan.md, future-scope.md
```

## IV. DOCS FIRST (Step 0)
Real content, not placeholders: CLAUDE.md, ARCHITECTURE.md (pipeline Mermaid diagram, data schemas Document/Page/Chunk/SearchResult, SQLite tables and ID mapping, every public function's contract incl. errors and edge cases, config values with reasons, index manifest, toolchain table, Stage 2 extension points), PROGRESS.md, NOTES.md, VIVA.md, README.md, docs/stage-1-plan.md, docs/future-scope.md.

## V. GIT & GITHUB PROTOCOL
- Solo 2-day sprint: work on main, one commit per atomic step.
- Commit only when that step's tests pass. Push after every commit.
- Conventional Commits: feat:, fix:, docs:, test:, refactor:, chore: + short imperative summary, e.g. "feat(ingest): extract PDF text with page numbers".
- The commit that finishes a step also updates PROGRESS.md and VIVA.md.
- Never commit: data/ (uploaded documents, indexes, databases), model caches, .env or keys, virtual environments, files over 5 MB (samples/ PDFs exempt).
- At the end of Stage 1, tag v0.1-indexing.

## VI. CONTRACT-FIRST + HALT PROTOCOL
- No module code before its contract is in ARCHITECTURE.md. If a contract must change, update ARCHITECTURE.md and log why in NOTES.md in the same commit.
- If anything needed is missing (a sample file, a decision, a version, a key), halt: state exactly what is missing and ask. Do not guess and proceed.

## VII. VERSION LOCK
- Before writing dependent code, fill ARCHITECTURE.md's toolchain table (OS, Python, exact library versions, embedding model name + revision).
- Pin exact versions in requirements.txt in the same session a dependency is added.
- Prefer CPU-friendly packages with Windows wheels.

## VIII. SESSION SNAPSHOT & RESUME PROTOCOL
Pro usage limits can cut a session at any moment, so snapshot often. Trigger, whichever comes first: end of each atomic step, every ~5 substantial edits, before any long-running command, and whenever a reply is about to end.
Append (never overwrite) to PROGRESS.md, then commit and push:
```
## [DATE TIME] - Step N: <name>
### Done            (file/function level, e.g. "extract_pdf() in ingest/pdf_parser.py, 6 tests passing")
### In progress / partial
### Not started
### Known issues / TODO
### Next atomic action   (one concrete action a fresh session can start immediately)
```
Start of every session: read CLAUDE.md, PROGRESS.md and ARCHITECTURE.md, run the tests, tell the user in 3 lines where we are. PROGRESS.md is a claim; the code and tests are the truth. If they disagree, correct PROGRESS.md first.

## IX. EDGE CASES (define behaviour before marking a step done; each is handled or documented unsupported in ARCHITECTURE.md, and has a test. Silent failure is never acceptable.)
Ingestion/extraction:
- unsupported file type, empty file, corrupted file, password-protected PDF
- scanned PDF, or a PDF with some scanned pages -> flagged "needs OCR", counted in stats
- multi-column layouts; headers/footers repeated on every page
- special characters, ligatures and maths symbols (no garbled text); non-English documents are out of scope and documented as unsupported
- large file (300+ pages): progress shown, embeddings batched, memory bounded
- duplicate upload (same hash) -> skipped; same name with new content -> replaces old version
Chunking:
- a section longer than the model's max tokens -> split, never silently truncated
- tiny fragments (e.g. a lone heading) -> merged with a neighbour
- documents with no headings at all
Index/search:
- search before anything is indexed
- k larger than the number of chunks; ef_search < k
- index full -> grow; deleted/replaced documents never returned
- index and SQLite out of sync (e.g. crash mid-ingest) -> detected on load, reported, rebuild offered
- index built with a different model/dimension -> clear error
- empty or whitespace-only query; very long query

## X. WHAT "WORKING" MEANS (only these metrics; add new ones only via ARCHITECTURE.md)
- Ingestion report per file: pages total / with text / flagged (with reason), chunks created, time taken.
- Index stats: vectors, dimension, size on disk, build time; search latency p50/p95 over the labelled queries.
- ANN quality: recall@10 of HNSW vs exact brute force (numpy) on the same vectors, at ef_search = 10, 50, 100. Target >= 0.95 at the default.
- Retrieval quality: eval/questions.jsonl with 15-25 questions the user writes from samples/, each labelled with expected file + page. Report hit@5 and MRR. Never tune on these questions and present it as a result.
Save results to eval/results/ and as a small table in README.md.

## XI. SELF-REPAIR LOOP
1. Analyse the actual error or traceback. No guessing.
2. Patch only the broken piece.
3. Re-run the full test suite, not just the failing test.
4. Log one line in NOTES.md: what broke | root cause | fix.

## XII. LOOP BREAKER
If the same test fails three times despite patches, or the same function keeps being rewritten: stop, tell the user plainly what was tried and why it keeps failing, and propose ONE genuinely different approach.

## XIII. WORKING WITHIN PRO LIMITS
- One atomic step per reply where possible.
- Don't reprint whole files: show what changed and summarise.
- Don't paste long logs: quote the relevant lines.
- Small, well-known libraries only; no heavy frameworks.
- Download the embedding model once and cache it; test on the smallest samples.
- If a step grows big, snapshot first, then split it.

## XIV. AFTER EVERY ATOMIC STEP
Report in chat, briefly: Completed (files/functions, tests passing); Why (design reasoning in plain words for the viva); Risks / known gaps; Next atomic action.
Then write the same to PROGRESS.md, add 3-5 likely examiner questions with short answers to VIVA.md, commit and push.
For core logic (chunking, indexing, search), explain the key lines. Code style: plain functions, type hints, docstrings, readable over clever, no unnecessary abstractions.

## XV. BUILD ORDER (2 days)
Day 1
- Step 0 - Setup: repo check, .gitignore, folders, all docs, venv, version lock, requirements.txt.
- Step 1 - Extraction: PDF (PyMuPDF) and DOCX (python-docx) parsers -> Page objects with metadata; scanned-page detection; cleaner. Tests on samples/.
- Step 2 - Chunking: structure-aware chunker with overlap and token limits; tests; a debug command that prints the chunks of one file.
- Step 3 - Embeddings: model wrapper with batching, normalisation, prefixes, caching. Tests: dimension, unit norm, related sentences score higher than unrelated ones.
Day 2
- Step 4 - Index + store: HNSW index with save/load, grow, mark_deleted; SQLite store; manifest; ingest_file() with hashing and dedup. Tests: add, reload, duplicate, replace.
- Step 5 - Search + CLI: search() returning SearchResult objects; CLI commands ingest / search / stats.
- Step 6 - Verification: ANN vs brute-force recall with the ef_search sweep; retrieval eval on questions.jsonl; results table in README.
- Step 7 - Demo UI: minimal Streamlit page. Only once Steps 0-6 are done and green.
- Step 8 - Wrap-up: README (setup, usage, architecture diagram, results, limitations, Stage 2 roadmap), final PROGRESS.md, tag v0.1-indexing.
If time runs short, cut in this order: the ef_search sweep, then Step 7. Never cut tests, the brute-force check or snapshots.

## XVI. IDENTITY
Not about shipping features fast. It is evidence: a correct, verified indexing pipeline, honest numbers, and a clear trail of how it was built, which the user can explain line by line.

## Standing decisions made after v1.0
- 2026-10-15: user said proceed to the next step without waiting for "go" unless blocked.
- 2026-10-15: faiss-cpu IndexHNSWFlat replaces hnswlib (no wheel, no C++ compiler). See NOTES.md.
- 2026-10-15: Stage 2 started on branch stage-2 (Section II rewritten).
- 2026-10-15: Final (Stage 2) evaluation: 25 October 2026; freeze on 24 October for report + rehearsal. Stage 1 evaluation: 16 October 2026 (uses ../corner_stone_stable).
- 2026-10-15: Node stays v25.9.0; user installs Node 24 LTS before Phase 4. Install nothing.
- 2026-10-15: 15 unanswerable questions kept (10 test, 5 dev). 16 harder paraphrased questions added (ids 66-81). Retrieval target changed (Section II).
- 2026-10-15: Plan approved with changes: Next.js kept (22-24 Oct), FastAPI 21-22 Oct, Streamlit = fallback until the web app works end to end; follow-up rewriting cut. User installs Node 24 LTS by end of 21 Oct.
- 2026-10-15: Commit + push + PROGRESS snapshot after every atomic step (usage limits). Dev ablation row after each retrieval change; no test-set runs until the Phase 1 close (18 Oct).

## ARCHIVED - Stage 1 Section II (v1.0, superseded 2026-10-15)
In scope for Stage 1:
1. Ingestion of PDF and DOCX files.
2. Extraction with location metadata. PDF: page number. DOCX: paragraph/heading position (DOCX has no fixed pages, never invent page numbers). Pages with no text layer (scanned) are flagged "needs OCR" with a reason, never silently skipped.
3. Cleaning: remove repeated headers/footers and page numbers, normalise whitespace, keep symbols and ligatures (maths symbols, fi/fl) intact, without garbling.
4. Chunking: structure-aware (split on headings/sections first, then by token length with overlap). Every chunk keeps: chunk_id, doc_id, file name, page or paragraph range, section heading, chunk index, token count.
5. Embeddings: English sentence-embedding model that runs well on a CPU laptop with 8 GB RAM. Follow its recommended query prefix. Vectors normalised.
6. Vector index: HNSW. Cosine space. Saved to disk. Incremental: adding a file never rebuilds the index. (hnswlib could not be built on this Windows machine, so faiss-cpu IndexHNSWFlat is used behind the same interface; see NOTES.md.)
7. Metadata store: SQLite with documents, pages and chunks, keyed by the same integer IDs used as HNSW labels.
8. Deduplication: SHA-256 of each file. Same file again = skip. Same file name with new content = replace the old version (mark its old vectors deleted).
9. Search, to prove the index works: query -> top-k chunks with file name, page/section, score and snippet. No LLM.
10. Interface: a CLI first (ingest, search, stats). Then, if time allows, a minimal Streamlit page (upload, ingestion report, stats, search with sources).
11. Verification: HNSW vs exact brute-force search, plus a small labelled retrieval set (Section X).

NOT building now (Stage 2): LLM answer generation, citations in answers, "I don't know" handling, reranking, hybrid BM25 search, quizzes/flashcards/any learning feature, OCR, table extraction, equations and images, non-English documents and multilingual search, knowledge graph/concept map, HNSW from scratch, FastAPI, auth, deployment, React. If reaching for any of these: stop, that is scope creep.

Design for Stage 2 anyway: search() returns result objects with full chunk metadata, so generation, reranking and BM25 can plug in later without changing the index.

Success for Stage 1: zero silent failures (every page is either indexed or flagged with a reason), ANN recall@10 vs brute force >= 0.95, and hit@5 >= 0.8 on the user's labelled questions (report the real number either way).
