# PROGRESS - session log (append only below the Morning report)

## Morning report (kept current; overwritten each update - the log below stays append-only)
Updated: 2026-10-16. Branch stage-2, 274 tests; GitHub Actions green (pytest + new web lint/build job). Everything in scope is built, including the Next.js web app.
- **Retrieval (test, once):** hit@5 **0.939** (31/33) vs v0.1 0.879; MRR 0.856; p95 47 ms. Target met.
- **Answers (test, once, concise, 43 questions):** citation accuracy **100%** (75/75), faithfulness **96.9%** (31/32), "Not in your notes." **10/10**, first token p50 **0.88 s**. All four answer targets met (LLM-judged).
- **5-mark test sample:** faithfulness **12.5% (1/8), target not met** (uncited intro/conclusion). Fixed after the test, declared in NOTES + report; dev 5-mark sample 12.5% -> 50% -> 100% (last run partial, 6/8).
- **Quiz:** 25/25 valid; 24/25 answers supported by their slide.
- **Web app (new, `web/`):** Next.js 16.4.1 + TypeScript + Tailwind 4, Node 24.20.0. Documents (upload, live ingestion status, list, delete), Ask (streamed answer, 5 modes, unit filter, clickable [n] -> slide image), Quiz (cited source, wrong answer -> flashcard), Flashcards (due cards, Again/Hard/Good/Easy via SM-2 in the API, generate). API has CORS for localhost:3000. Run: README "Web app (two terminals)". Streamlit still starts (fallback).
- **Checked live:** API health + CORS header, /ask/stream through the real API (1 Groq call, 2-mark "What is a TLB?", cited Unit 3 p.43, image served), all 5 pages return 200, lint + production build clean. **Not checked in a browser by me** (no browser tool connected): clicking through the pages is item 1 below. Quiz/flashcard generation not called live (Groq quota; API routes covered by tests).
- **Docs:** README (Stage 2 + web app run commands), docs/evaluation-report.md, docs/demo-script.md, VIVA.md (incl. web app questions).

### What I need to do
1. Browser click-through (5 min): run the two terminals from the README, open http://localhost:3000. Documents shows 7 decks; Ask "What is a TLB?" mode 2-mark (cached now, no quota), click the blue 1 -> Unit 3 p.43 slide opens; Quiz Unit 4, answer one wrong, "Make flashcard"; Flashcards -> grade it. Tell me anything that looks wrong.
2. Decide the demo UI: web app if item 1 works (go/no-go on the morning of 24 Oct per CLAUDE.md), else Streamlit. Update docs/demo-script.md tab names if you go with the web app (I left it on Streamlit wording).
3. Spot-check eval/results/answer_spotcheck_test.md (20 test answers in full) and note any disagreement with the judge in NOTES.md.
4. Review the draft pull request https://github.com/amanpandey-git/corner_stone/pull/1 (stage-2 -> main). You merge and tag v0.2; I will not.
5. Optional: delete old index backups in data/ (index.v1.bak, index.v2.bak..bak4, ~4 MB); I do not delete data.
6. Demo day: warm the cache early (ask the demo questions once); run no evaluations that day (Groq daily cap).

## [2026-10-15] - Step 0: Setup, docs, version lock
### Done
- Repo cloned (amanpandey-git/corner_stone, public); `test/` moved to `samples/` via git mv (7 PDFs); folder layout + .gitignore created.
- Docs: CLAUDE.md, ARCHITECTURE.md (pipeline, schemas, SQLite, all contracts, config reasons, manifest, edge cases, Stage 2 hooks), NOTES.md, VIVA.md, README.md, docs/stage-1-plan.md, docs/future-scope.md, config.yaml, .env.example.
- Version lock: Python 3.12.10 `.venv`; torch 2.14.1+cpu, sentence-transformers 6.1.0, transformers 5.19.0, faiss-cpu 1.15.1, PyMuPDF 1.28.2, python-docx 1.2.0, numpy 2.5.4, pytest 9.1.1 pinned in requirements.txt.
- Embedding model BAAI/bge-small-en-v1.5 pinned at revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a.
- Decision: faiss IndexHNSWFlat instead of hnswlib (no Windows wheel, no C++ compiler). Logged in NOTES.md.
### In progress / partial
- Nothing. No feature code exists yet.
### Not started
- Steps 1-8.
### Known issues / TODO
- Streamlit 1.66.0 is installed in the venv but intentionally not in requirements.txt until Step 7.
- Model weights are not downloaded yet (Step 3).
- Samples are OS course notes; user must write 15-25 labelled questions (eval/questions.jsonl) before Step 6.
### Next atomic action
- Step 1: implement `extract_pdf()` in src/cornerstone/ingest/pdf_parser.py per ARCHITECTURE.md 4.1, with tests/test_pdf_parser.py on samples/. First inspect one sample PDF (text layer? headers/footers? scanned pages?) before writing code.

## [2026-10-15] - Step 1: Extraction & cleaning
### Done
- `extract_pdf()` in ingest/pdf_parser.py: one Page per page, headings by font size, needs_ocr/empty/error flags with reasons; raises EmptyFile/CorruptFile/PasswordProtected.
- `extract_docx()` in ingest/docx_parser.py: heading-delimited sections, paragraph ranges, page_no None, tables flattened.
- `clean_pages()`, `normalise_text()` in ingest/cleaner.py: header/footer + page-number removal, ligatures, PUA glyph removal, heading re-location.
- `load_document()` in ingest/loader.py: dispatch + clean.
- 20 tests passing (whole suite) (tests/test_pdf_parser.py, test_cleaner.py, test_docx_parser.py).
- Real samples: 7 PDFs = 422 pages, 4 pages flagged needs_ocr, 0 errors.
### In progress / partial
- None.
### Not started
- Steps 2-8.
### Known issues / TODO
- Slide decks with body font larger than titles (Unit 5 Part 2) get few headings detected; chunker must cope with no-heading pages.
- needs_ocr pages with a short caption lose that caption from the index (text is kept on the Page for Stage 2).
- Multi-column reading order is best-effort (PyMuPDF sort=True).
### Next atomic action
- Step 2: implement `chunk_pages()` in src/cornerstone/chunking.py per ARCHITECTURE.md 4.3 using a token counter; tests/test_chunking.py; `cli.py chunks <file>` debug command.

## [2026-10-15] - Step 2: Structure-aware chunking
### Done
- `chunk_pages()` in chunking.py: sections by heading, token windows with overlap, merge of fragments < 40 tokens, never truncates.
- `load_token_counter()` in embeddings.py (tokenizer only, bge revision pinned).
- `chunks <file>` debug command in cli.py (`PYTHONPATH=src python -m cornerstone.cli chunks <file> [--full]`).
- Cleaner upgraded: position-independent footer removal (>=40% of pages, <=80 chars); footer-only pages with images -> needs_ocr (Page.has_image).
- 30 tests passing (suite, ~12 s; tokenizer cached after first run).
- Real samples: 7 PDFs -> 328 chunks; all chunks 40..275 tokens (<= hard_max 480); flagged pages: 13 (12 needs_ocr diagram/image slides + footer-only; 0 errors).
### In progress / partial
- None.
### Not started
- Steps 3-8.
### Known issues / TODO
- One irregularly wrapped footer variant remains in Unit 3 (logged in NOTES.md).
- Median chunk is 50-90 tokens because slides are short; kept as one chunk per slide-section on purpose (precise page hits). Revisit only if Step 6 hit@5 is low, and say so honestly.
- Chunk text keeps visual line breaks as "\n"; harmless for embedding.
### Next atomic action
- Step 3: `Embedder` in embeddings.py (batching, normalisation, query prefix, cache) per ARCHITECTURE.md 4.4; download bge-small once (~130 MB); tests: dim 384, unit norm, related > unrelated.

## [2026-10-15] - Step 3: Embeddings
### Done
- `Embedder` in embeddings.py: bge-small-en-v1.5 (pinned revision), CPU, batch 32, L2-normalised float32 output; query prefix on queries only; `EmptyQuery` on blank query, `ValueError` on blank passage; long queries truncated to `max_query_chars`; `count_tokens()`.
- tests/test_embeddings.py: 8 tests (dim 384, unit norm, related > unrelated, prefix on queries only, batching == single, empty inputs, long query, token count).
- Measured on this laptop: model load ~16 s, ~13 chunks/s (89 chunks of Unit 1 Part 2 in 6.9 s). All 328 sample chunks ~25 s.
- 38 tests passing in total.
### In progress / partial
- None.
### Not started
- Steps 4-8.
### Known issues / TODO
- First run downloads ~130 MB to ~/.cache/huggingface (symlink warning on Windows is harmless).
- No on-disk embedding cache yet: re-ingesting a changed file re-embeds all of its chunks (fine at this scale; the SHA-256 dedup avoids re-embedding unchanged files).
### Next atomic action
- Step 4a: write `HNSWIndex` (faiss IndexIDMap + IndexHNSWFlat, add/search/save/load, ef = max(ef_search, k)) and `Manifest` in src/cornerstone/index/, with tests/test_index.py and tests/test_manifest.py; then `MetadataStore`, then `ingest_file()`.

## [2026-10-15] - Step 4a: HNSWIndex + Manifest
### Done
- `HNSWIndex` in index/hnsw_index.py: faiss IndexIDMap2(IndexHNSWFlat, METRIC_INNER_PRODUCT), add_with_ids (label = chunk_id), search (ef = max(ef_search, k), k clipped to size, empty index -> empty arrays), atomic save, load(path, cfg) with manifest check, all_ids().
- `Manifest`, `manifest_from_config`, `read/write_manifest`, `check_manifest` in index/manifest.py; manifest.json is written next to the index and checked on load (model name, revision, dimension, space, normalisation, index_version; missing or corrupt manifest also raises ModelMismatch).
- tests/test_index.py: 14 tests (add, incremental add, save/reload identical results, mismatch x5, missing/corrupt manifest, empty index, k > n, ef < k, bad inputs).
- 52 tests passing in total.
### In progress / partial
- None.
### Not started
- Step 4b: MetadataStore (SQLite). Step 4c: ingest_file() with hashing, dedup, replace. Steps 5-8.
### Known issues / TODO
- Soft-deleted vectors stay in the graph; a compaction/rebuild command is out of Stage 1 scope (stats should report the deleted count).
### Next atomic action
- Step 4b: implement `MetadataStore` in index/metadata_store.py per ARCHITECTURE.md 4.5/section 3 (documents, pages, chunks; find_by_hash, find_active_by_name, add_document -> chunk_ids, activate, mark_replaced, get_chunks, stats, check_sync) with tests/test_metadata_store.py.

## [2026-10-15] - Step 4b: MetadataStore (SQLite)
### Done
- `MetadataStore` in index/metadata_store.py: tables documents/pages/chunks; `chunks.status` (pending/active/deleted) is the single soft-delete source; AUTOINCREMENT ids; unique index = one active version per file name.
- `add_document` (one transaction, returns chunk_ids), `activate(doc_id, replaces=)` (atomic swap), `mark_replaced`, `discard_pending`, `find_by_hash`, `find_active_by_name`, `get_document`, `list_documents`, `get_chunks` (active only), `active_chunk_ids`, `stats`, `check_sync`.
- `Document` dataclass added to cornerstone/__init__.py.
- tests/test_metadata_store.py: 9 tests (round trip, find by hash/name, replace, crash -> pending, rollback on failed write, sync mismatch both ways, stats/flagged pages, one-active-per-name).
- 61 tests passing in total.
### In progress / partial
- None.
### Not started
- Step 4c: pipeline.ingest_file() (hash, dedup, replace, batching, progress, IngestReport). Steps 5-8.
### Known issues / TODO
- Chunk.deleted is derived from status; code must never set chunk status directly outside the store.
- Pages table stores status/reason/size only; page text lives in chunks.
### Next atomic action
- Step 4c: write `IngestReport` dataclass and `ingest_file()` in pipeline.py per ARCHITECTURE.md 4.6, plus `open_stack(cfg)` helper? (decide in contract first), with tests/test_pipeline.py: ingest sample PDF, duplicate skipped, changed content replaced, bad files -> failed report, crash simulation -> pending detected.

## [2026-10-15] - Step 4c: ingest_file() (Step 4 complete)
### Done
- `ingest_file()` and `file_sha256()` in pipeline.py: hash -> dedup -> replace -> parse -> chunk -> batched embed -> pending rows -> index add+save -> activate(replaces=). Bad files return a failed IngestReport before any row is written. Ordinary failure after add_document cleans itself up; a hard crash leaves a pending document.
- `IngestReport` dataclass (cornerstone/__init__.py).
- tests/test_pipeline.py: 11 tests (sample PDF, duplicate incl. renamed copy, replace, 4 bad-file kinds, missing file, crash -> pending/check_sync/discard_pending/re-ingest, ordinary failure cleanup, all-flagged document).
- All 7 sample PDFs ingested: 422 pages, 409 text, 13 flagged, 328 chunks, 38.7 s; index 0.55 MB; sync OK; second run all skipped. Table saved to eval/results/ingest_report.md.
- 72 tests passing in total.
### In progress / partial
- None.
### Not started
- Step 5 (search + CLI), 6, 7, 8.
### Known issues / TODO
- ingest_file() does not itself run check_sync; the CLI will do it on open and offer discard_pending / rebuild.
- No real DOCX in samples/; DOCX is covered by generated files.
### Next atomic action
- Step 5a: contract for `search()` already in ARCHITECTURE.md 4.7; implement search.py (over-fetch + filter via store.get_chunks, EmptyQuery, k<1, snippet) with tests/test_search.py; then cli.py ingest/search/stats with `open_stack(cfg)` loading or creating the index under data/index/.

## [2026-10-15] - Step 5: Search + CLI
### Done
- `search()` in search.py: query prefix, over-fetch 3k and widen, SQLite active filter, SearchResult(chunk, score, rank, snippet); EmptyQuery (also on empty index), k<1 ValueError, empty index / all-deleted -> [].
- `SearchResult` dataclass; `open_stack()` + commands `ingest <file|dir>`, `search "<q>" --k`, `stats`, `chunks` in cli.py. Sync problems are printed; interrupted ingests are discarded only on `y` / `--yes`.
- tests/test_search.py (6) and tests/test_cli.py (4): known questions -> expected file, replaced/deleted docs never appear, over-fetch behind deleted chunks, empty index, k too large, CLI round trip, failure exit codes, pending-ingest consent.
- Real index built from samples/ into data/index (gitignored). 3 real searches saved to eval/results/sample_searches.md.
- 82 tests passing in total.
### In progress / partial
- Awaiting user's check of the 3 searches against the slides.
### Not started
- Step 6 (verification), 7 (Streamlit), 8 (wrap-up).
### Known issues / TODO
- Repeated slide titles merge sections (page ranges up to 6 slides); some bullets become headings (NOTES.md). Not blocking.
- `open_stack` offers a rebuild only as instructions; no rebuild command in Stage 1.
- User must write eval/questions.jsonl (15-25 questions, expected file + page) before the Step 6 retrieval eval.
### Next atomic action
- Step 6a: write eval/ann_vs_bruteforce.py (HNSW vs numpy exact on the real index vectors, recall@10 at ef_search 10/50/100, latency p50/p95) and save to eval/results/. Needs vectors: reconstruct from the index (IndexIDMap2.reconstruct) or re-embed chunk texts; decide in the script header.

## [2026-10-15] - Step 6a: ANN vs brute force
### Done
- eval/ann_vs_bruteforce.py: exact numpy top-10 vs the saved HNSW index (HNSWIndex.search), recall@10 at ef_search 10/50/100, p50/p95 per-query latency; plus a labelled-synthetic 10,000-vector scale check. Queries = distinct section headings of indexed chunks (not the labelled questions). Nothing tuned.
- `HNSWIndex.vectors()` added (ids + matrix in insertion order).
- tests/test_eval_ann.py (4 tests). 86 tests passing in total.
- Results saved to eval/results/ann_recall.md. Real index (328 vectors, 191 queries): recall@10 = 0.952 / 0.995 / 0.996 at ef 10 / 50 / 100 -> target >= 0.95 at default 50 MET. Synthetic 10k: 0.975 / 1.000 / 1.000.
- Latency (index only, no query embedding): real p50 0.046 / 0.071 / 0.105 ms vs exact 0.026 ms; synthetic p50 0.054 / 0.113 / 0.337 ms vs exact 0.823 ms.
### In progress / partial
- None.
### Not started
- Step 6b: retrieval eval (hit@5, MRR) on eval/questions.jsonl; end-to-end search latency p50/p95 incl. query embedding; README results table. Steps 7, 8.
### Known issues / TODO
- HNSW is not faster than numpy at 328 vectors; stated honestly in the results file and VIVA.
- BLOCKED on user: eval/questions.jsonl (15-25 questions, each {"question", "file", "page"} from samples/, written without looking at search output).
### Next atomic action
- Step 6b: write eval/retrieval_eval.py (hit@5, MRR, per-question table, p50/p95 end-to-end latency) and a format check; run once questions.jsonl exists. Do not tune chunking/ef on it.

## [2026-10-15] - Step 6b: retrieval evaluation harness (waiting for questions.jsonl)
### Done
- eval/retrieval_eval.py: validates eval/questions.jsonl (invalid JSON, missing fields, "pages" not a non-empty int list, files not in samples/, pages outside 1..page_count, duplicates), then scores hit@5, MRR (top-10), pages-found for multi-page questions (separately), per-question table, misses list, end-to-end p50/p95 latency (query embedding + HNSW + SQLite). Excludes the 3 Step 5 questions and says so in eval/results/retrieval_eval.md. `--check` validates only.
- Scoring rule fixed before results: a result covers a page if file matches and the page lies in the chunk's page_start..page_end. Also flags questions whose page is needs_ocr (cannot be hit).
- eval/QUESTIONS_FORMAT.md: how to write the questions.
- tests/test_eval_retrieval.py (17 tests incl. every rejection case). 103 tests passing in total.
### In progress / partial
- The evaluation itself has NOT been run: eval/questions.jsonl does not exist yet.
### Not started
- Running the eval and README results table; Step 7 (Streamlit); Step 8 (wrap-up, tag v0.1-indexing).
### Known issues / TODO
- BLOCKED on user: eval/questions.jsonl (15-25 questions, format in eval/QUESTIONS_FORMAT.md).
- README results table still empty; fill in from eval/results/ann_recall.md, ingest_report.md, retrieval_eval.md in Step 8.
### Next atomic action
- When questions.jsonl exists: `PYTHONPATH=src python eval/retrieval_eval.py --check`, then run once, commit eval/results/retrieval_eval.md unchanged, report hit@5 / MRR / misses honestly. Meanwhile Step 7 (minimal Streamlit page) can start: it does not depend on the eval.

## [2026-10-15] - Step 6b: retrieval evaluation run (Step 6 complete)
### Done
- eval/questions.jsonl: 20 questions written from the extracted slide text; spread 3/4/3/3/2/3/2 over the 7 files; 3 two-consecutive-page questions (Unit 1-1 p.14-15, Unit 1-2 p.75-76, Unit 2 p.11-12); no cross-file questions; Step 5 questions not reused. eval/evidence.md has the exact phrase + page for each.
- Harness extended BEFORE the first run with optional `equivalent_pages` (Unit 4 PDF duplicates its slides 2-26 as 27-51); 19 harness tests.
- Format check passed (20 valid, 0 excluded). Evaluation run once, nothing tuned: hit@5 = 0.950 (19/20), MRR = 0.885, multi-page 5/6 labelled pages found, end-to-end latency p50 35 ms / p95 57 ms. Saved unchanged to eval/results/retrieval_eval.md.
- Targets from CLAUDE.md: ANN recall@10 >= 0.95 MET (0.995); hit@5 >= 0.8 MET (0.95). Zero silent failures: 409 text + 13 flagged = 422 pages.
- 105 tests passing.
### In progress / partial
- None.
### Not started
- Step 7 (Streamlit), Step 8 (README results, final wrap-up, tag v0.1-indexing).
### Known issues / TODO
- 1 miss (Q14, Unit 4 FCFS seek time): ranking miss, analysed in NOTES.md; duplicate slides within a PDF halve effective top-k; mis-detected body-line headings in large-font decks.
- 20 questions: one question = 5 points; wording is natural and shares some words with slide titles.
### Next atomic action
- Step 7: minimal Streamlit page app/streamlit_app.py (upload -> ingest report, stats, search with sources) as a thin layer over open_stack/ingest_file/search; add streamlit to requirements.txt at that point (version 1.66.0 already installed).

## [2026-10-15] - Step 8: Wrap-up (tag v0.1-indexing)
### Done
- README.md: what Stage 1 does, Mermaid architecture, Windows setup, usage, results tables (ingestion, ANN recall, retrieval) with caveats (one question = 5 points; Unit 4 duplicate miss; equivalent_pages added before the first run), known limitations (no cross-file questions, duplicates not removed at ingest, no OCR, DOCX only generated, English only, heading heuristics), Stage 2 roadmap.
- VIVA.md: 10 evaluation / project-level questions added under Step 8.
- Results untouched (eval/results/*). Tag v0.1-indexing created on this commit.
- 105 tests passing.
### In progress / partial
- None.
### Not started
- Step 7 (Streamlit demo): intentionally after the tag; not part of v0.1-indexing.
### Known issues / TODO
- See README "Known limitations".
### Next atomic action
- Step 7: app/streamlit_app.py as a thin UI over open_stack/ingest_file/search; add `streamlit==1.66.0` to requirements.txt; test the logic helpers, smoke-run the page once.

## [2026-10-15] - Step 7: Streamlit demo (after tag v0.1-indexing)
### Done
- app/streamlit_app.py: sidebar stats + flagged pages, Search tab (query, k, file/page/section/score, snippet, full chunk), Upload tab (PDF/DOCX -> ingest_file -> ingestion report + flagged pages). Sync problems shown; discard only via button. Embedder cached; store/index opened per run (thread-bound SQLite bug fixed, see NOTES.md).
- `cli.location()` made public for reuse. streamlit==1.66.0 pinned in requirements.txt.
- tests/test_app.py: 4 AppTest tests (render + stats, search with source, blank query, upload -> report -> duplicate). Headless server start checked (health ok, HTTP 200).
- README updated (usage, test count). 109 tests passing.
### In progress / partial
- None.
### Not started
- Nothing planned for Stage 1.
### Known issues / TODO
- The tag v0.1-indexing points at the commit before the UI; the UI is a later commit on main.
- Not tested in a real browser by the assistant (only AppTest + server health); please click through once before the demo.
- Sidebar stats refresh on the next interaction after an upload.
### Next atomic action
- User: run `streamlit run app\streamlit_app.py`, ingest samples/ through the UI once, and rehearse the demo; decide whether to move the tag (currently v0.1-indexing = README commit 92cba7b).

## [2026-10-15 02:52] - Snapshot (pause): Stage 1 complete, demo UI committed
### Done
- Steps 0-8 complete and pushed: ingestion (PDF/DOCX, needs_ocr flags), cleaner, chunker, bge-small embedder, faiss HNSW + manifest, SQLite store, ingest_file with dedup/replace/crash-safe order, search, CLI (ingest/search/stats/chunks), eval (ANN recall 0.995 @ ef 50; hit@5 0.95, MRR 0.885 on 20 questions; p50/p95 35/57 ms), README with caveats and limitations, VIVA, Streamlit demo (app/streamlit_app.py).
- Tag v0.1-indexing -> 92cba7b (README commit, before the UI). Later commits on main: 20bee32 (Streamlit UI), cf683b8 + 260ed29 (README: --server.fileWatcherType none and its reason).
- 109 tests passing at last full run (20bee32; README-only commits since).
### In progress / partial
- Nothing in progress. No uncommitted code changes.
- Demo UI has only been checked with Streamlit AppTest and a headless start (health ok, HTTP 200); not clicked through in a real browser.
### Not started
- Stage 2 (LLM answers with citations, reranking, BM25, OCR, near-duplicate collapsing) - out of scope for Stage 1.
### Known issues / TODO
- Unit 4 PDF repeats its own slides (27-51 = 2-26): duplicates not removed at ingest; one eval miss (FCFS seek time) is a ranking miss with that cause, not fixed on purpose (NOTES.md).
- Heading heuristic promotes body lines in large-font decks; repeated slide titles merge sections.
- DOCX verified only with generated files; no real DOCX in samples/.
- Tag v0.1-indexing does not include the UI; user decides whether to move it.
- Streamlit file watcher traces a missing torchvision import on Windows/Python 3.12 (harmless; run with --server.fileWatcherType none; torchvision deliberately not installed).
### Next atomic action
- User: run .\.venv\Scripts\python -m streamlit run app\streamlit_app.py --server.fileWatcherType none (with $env:PYTHONPATH="src"), ingest samples/ through the Upload tab, run one search, and report anything wrong; then decide whether to move tag v0.1-indexing to the latest main commit.

## [2026-10-15] - Session start check
### Done
- 109 tests passing (full run). Working tree clean, main = origin/main (6c267a7).
- Found tag v0.1-demo -> 6c267a7 (latest main, includes the Streamlit UI), already pushed; not recorded before. v0.1-indexing stays at 92cba7b. The open "move the tag?" question is resolved by this second tag.
### In progress / partial
- None.
### Not started
- Stage 2 (out of scope for Stage 1).
### Known issues / TODO
- Unchanged from the previous snapshot. Demo UI still not clicked through in a real browser.
### Next atomic action
- User: rehearse the demo in a real browser (streamlit run app\streamlit_app.py --server.fileWatcherType none, PYTHONPATH=src) and report anything wrong.
## [2026-10-15] - Stage 2 Phase 0: setup (steps 5-7)
### Done
- Verified (git): tag v0.1-demo -> 6c267a7 on origin; branch stage-1-stable -> 6c267a7 in worktree ../corner_stone_stable; stage-2 = main = 5c80d2b, on origin. 109 tests passed at session start.
- Step 5: CLAUDE.md Section II rewritten for Stage 2 (scope = Phases 1-6, not-building list, targets, eval rules, cut list, learning rule, protected items, overrides of V/XV/X); Stage 1 Section II archived at the end; Section III lists the Stage 2 top-level additions.
- Step 6: eval/questions.jsonl now 65 lines: 20 Stage 1 + 30 new answerable (4 multi-page, 5 cross-file) + 15 unanswerable; dev 25+5, test 25+10 (rule in eval/QUESTIONS_FORMAT.md). Harness extended (id/split/targets/answerable, --split/--label/--out), 13 new tests. Evidence for every new label in eval/evidence.md, script-verified; 10 marked for the user's spot check.
- Baseline (v0.1 code, test split, run once): hit@5 0.960 (24/25), MRR 0.912, p50/p95 43/110 ms -> eval/results/baseline_v0.1_test.md.
- Step 7: node v25.9.0 found (not LTS). .env.example has GROQ_API_KEY and GEMINI_API_KEY; .env is gitignored (verified with git check-ignore).
- ARCHITECTURE.md section 10: Phase 1 contracts (schema v2 + IndexVersionMismatch + rebuild, dedup at ingest, query-time collapse, slide chunking + context header, page images, FTS5 + RRF, reranker, filters, compaction, ablation protocol, config, edge cases).
- 122 tests passing.
### In progress / partial
- None. Waiting for the user's "go" for Phase 1.
### Not started
- Phases 1-6.
### Known issues / TODO
- Final evaluation date not given (placeholder in the brief).
- Node LTS decision (keep v25 or install Node 24 LTS) is the user's.
- User to spot-check 10 questions (evidence.md) and approve 15 vs 10 unanswerable and the reranker choice.
### Next atomic action
- Phase 1 step 1: schema v2 + IndexVersionMismatch + `cli rebuild` (ARCHITECTURE 10.1), with tests; then the dev ablation baseline row.

## [2026-10-15] - Stage 2 Phase 1 steps 1-2 (snapshot, stop)
### Done
- Eval: +16 paraphrased questions (ids 66-81, 8 dev / 8 test), no slide-title words (script-checked), phrases verified. Test baseline re-run once: v0.1 hit@5 0.879 (29/33), MRR 0.848 (5f470b8). Target now "hit@5 >= 0.90 and at most one test question worse than v0.1" (CLAUDE.md II).
- CLAUDE.md standing decisions: final evaluation 25 Oct, freeze 24 Oct; Node stays v25; 15 unanswerable kept; reranker conditional; Streamlit = guaranteed demo UI.
- Step 1 (ba788d4): schema v2 (SQLite user_version + manifest index_version), IndexVersionMismatch with the rebuild command, `cli rebuild` (old folder kept as *.v<N>.bak), new columns + FTS5 table in the same transaction, unit/source_path at ingest; fix: CLI closes SQLite connections.
- Step 2 (942b8ec): dedup.py (3-shingle Jaccard >= 0.95, digits kept, < 80 chars never), duplicates stored with duplicate_of, counted separately in report/stats/CLI/Streamlit. Unit 4: 23 duplicates; Unit 1-2: p.67 = p.66.
- Ablation (dev, eval/results/ablation_dev.md): row 0 v0.1 0.879 / 0.816; row 1 schema 0.879 / 0.816; row 2 dedup 0.879 / 0.818.
- Local data/index rebuilt (v2 + dedup, 308 chunks); older indexes kept at data/index.v1.bak and data/index.v2.bak (gitignored).
- 140 tests passing.
### In progress / partial
- None.
### Not started
- Phase 1 steps 3+ (page images, slide chunking + context header, FTS5 + RRF, collapse, filters, reranker, compaction, test run); Phases 2-6.
### Known issues / TODO
- Q14 (FCFS seek, dev) still a miss: chunk spans p.9-11 under a mis-detected heading -> slide chunking.
- p.67 of Unit 1-2 marked duplicate of p.66 (identical text; its image may differ).
- User: 10 spot-checks (evidence.md) after the 16 Oct evaluation; wrong labels reported before Phase 1 ends.
- User: create .env with GROQ_API_KEY / GEMINI_API_KEY before Phase 2 (planned 19 Oct).
- 10-day plan below is PROPOSED, awaiting approval.
### Proposed plan (awaiting approval)
- 16 Oct (Stage 1 evaluation day, light): page images; slide-aware chunking + context header (ablation rows).
- 17 Oct: FTS5 keyword search + RRF (user writes rrf_merge from given structure + tests), query-time collapse, filters (rows).
- 18 Oct: reranker (adopt only if dev gain and p95 < 1 s), compaction; test split once; close Phase 1.
- 19 Oct: LLM interface (Groq + Gemini, timeouts, retries, rate limits, cache), grounded [n] prompt + "not in your notes", answer modes, streaming in Streamlit.
- 20 Oct: citation parser (user writes) + citation check; answer-eval harness + LLM judge; prompt work on dev only.
- 21 Oct: answer eval on test (paced), 20 answers for spot check; quiz generator (Pydantic, retries, cited answers) + validity rate.
- 22 Oct: flashcards per unit + SM-2 (user writes core; first cut if late) + wrong answer -> flashcard; Streamlit ask (modes, citation opens slide), quiz, review pages.
- 23 Oct: FastAPI endpoints + TestClient tests + GitHub Actions; buffer.
- 24 Oct: FREEZE: README, evaluation report + ablation table, demo script, rehearsal, PR stage-2 -> main, tag v0.2. No features.
- 25 Oct: final evaluation.
- Cut now (proposed): Next.js app (Phase 4), quiz UI polish, neighbour expansion, follow-up rewriting (only if 23 Oct buffer allows), weak-topic tracking.
### Next atomic action
- After plan approval: Phase 1 step 3, page images (ARCHITECTURE 10.5): render_page_images + pages.image_path + tests.

## [2026-10-15] - Schedule approved (with changes)
### Done
- Plan approved: Next.js kept (4 pages), FastAPI after the answering core, Streamlit fallback; cuts: quiz UI polish, neighbour expansion, weak-topic tracking, follow-up rewriting; SM-2 first cut. CLAUDE.md Section II holds the table:

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

### In progress / partial
- None.
### Not started
- Phase 1 step 3 onward.
### Known issues / TODO
- User: Node 24 LTS by end of 21 Oct; .env keys by 18 Oct; spot-checks after 16 Oct.
### Next atomic action
- Phase 1 step 3: page images (ARCHITECTURE 10.5).
## [2026-10-15] - Phase 1 step 3: page images
### Done
- ingest/page_images.py (render_page_images, delete_page_images); store.set_page_images/get_page_image; pipeline renders after index save, before activate; failure handler deletes images; IngestReport.warnings; config paths.image_dir + images.*; load_config resolves relative paths. 4 new tests; 144 passing.
- Local index rebuilt (data/images: 422 PNGs, 49 MB). Dev row 3: 0.879 / 0.818 (no ranking change).
### In progress / partial
- None.
### Not started
- Step 4 slide chunking + context header; step 5 FTS5 keyword search; rrf_merge (user); collapse; filters; compaction.
### Known issues / TODO
- Images of documents discarded via the CLI prompt or replaced stay until compaction (by design, 10.9).
### Next atomic action
- Phase 1 step 4: slide-aware chunking + "file > section" context header (ARCHITECTURE 10.4).
## [2026-10-15] - Phase 1 step 4: slide-aware chunking + context header
### Done
- chunking.py: slide mode (slide_title, _slide_pieces, _merge_tiny_slides, context_header, embedding_text); DOCX keeps section mode; pipeline embeds header + text. Config: chunking.mode/slide_max_tokens/slide_min_tokens/slide_title_lines/slide_title_max_chars. 10 new tests; 154 passing.
- Local index rebuilt (328 chunks). Dev row 4: hit@5 0.939, MRR 0.835, p95 55 ms.
### In progress / partial
- None.
### Not started
- Step 5 FTS5 keyword search; rrf_merge (user writes; structure + tests from me); collapse; filters; compaction; reranker.
### Known issues / TODO
- Dev misses: 14 (FCFS seek time, rank 8), 70 (huge time slice -> FCFS, p.77).
### Next atomic action
- Phase 1 step 5: keyword_search over chunks_fts (ARCHITECTURE 10.6) with tests; dev row for keyword-only as a reference.
## [2026-10-15] - Phase 1 step 5: keyword search (FTS5)
### Done
- hybrid.py: fts_query, keyword_search (BM25, active only, doc/unit filters), rrf_merge STUB (author writes it). SearchFilters dataclass. tests/test_hybrid.py: 13 keyword tests pass, 5 rrf tests skip until rrf_merge exists. retrieval_eval: --config, --retriever keyword.
- Dev reference row 5 (keyword only): 0.818 / 0.767, 1 ms. 167 passed, 5 skipped.
### In progress / partial
- rrf_merge: waiting for the author (structure in its docstring, tests in tests/test_hybrid.py).
### Not started
- collapse_results; vector-side filters in search(); compaction; hybrid wiring in search() (after rrf_merge); reranker.
### Known issues / TODO
- None new.
### Next atomic action
- Query-time collapse of near-identical results (ARCHITECTURE 10.3): collapse_results in dedup.py + SearchResult.also_on/scores + tests.
## [2026-10-15] - Phase 1 step 6: query-time collapse
### Done
- dedup.collapse_results; SearchResult.scores / also_on; search() restructured into stages (vector candidates -> collapse -> k) with config retrieval.candidates/collapse and dedup.result_jaccard. 4 new tests; 171 passed, 5 skipped (rrf).
- Dev row 6: 0.939 / 0.835 (no change; safety net).
### In progress / partial
- rrf_merge: waiting for the author.
### Not started
- vector-side filters in search(); compaction; hybrid wiring (after rrf_merge); reranker.
### Known issues / TODO
- None new.
### Next atomic action
- Filters (ARCHITECTURE 10.8): search(..., filters=SearchFilters) applied on the vector side (over-fetch) + CLI --unit/--doc options + tests.
## [2026-10-15] - Phase 1 step 7: filters
### Done
- MetadataStore.allowed_doc_ids; search(..., filters) on the vector side; CLI search --unit/--file. 2 new tests; 173 passed, 5 skipped (rrf). Dev row 7 unchanged (regression check).
### In progress / partial
- rrf_merge: waiting for the author.
### Not started
- compaction; hybrid wiring (after rrf_merge); reranker.
### Known issues / TODO
- None new.
### Next atomic action
- Compaction (ARCHITECTURE 10.9): compact() + `cli compact [--yes]` + tests (nothing to compact; replaced doc removed; crash after swap).
## [2026-10-15] - Phase 1 step 8: compaction
### Done
- pipeline.compact (returns new index + report; refuses while pending), MetadataStore.purge_deleted (chunks, FTS 'delete', retired pages), images of retired docs removed, `cli compact [--yes]`. 5 new tests; 178 passed, 5 skipped (rrf). Dev row 8 unchanged.
### In progress / partial
- rrf_merge: waiting for the author (docstring structure in src/cornerstone/hybrid.py, tests in tests/test_hybrid.py).
### Not started
- Hybrid wiring in search() (retrieval.hybrid; needs rrf_merge); reranker ablation; Phase 1 test run (18 Oct).
### Known issues / TODO
- Dev misses: 14 (FCFS seek time, rank 8), 70 (huge time slice, Unit 1-2 p.77).
### Next atomic action
- Author writes rrf_merge (run: PYTHONPATH=src .venv\Scripts\python -m pytest tests/test_hybrid.py -q). Meanwhile: reranker module behind retrieval.rerank (ARCHITECTURE 10.7), off by default until the dev ablation decides.
## [2026-10-15] - Phase 1 step 9: RRF + hybrid search (stop for the night)
### Done
- rrf_merge implemented (assistant, at the user's request; learning rule updated in CLAUDE.md), 6 rrf tests incl. the worked example B, A, D, C. Hybrid wired into search() (_fuse: vector + FTS5 candidates, RRF, per-stage scores, filters on both sides); 2 new search tests. 186 tests passing, none skipped.
- Dev row 9 (hybrid): 0.848 / 0.791 vs 0.939 / 0.835 without -> retrieval.hybrid = false by default (code and switch kept). VIVA.md: rrf_merge line by line + the three questions.
- Current default pipeline: dedup at ingest, slide chunking + header, vector top 30, collapse, first k. Dev: hit@5 0.939, MRR 0.835, p95 ~50-80 ms.
### In progress / partial
- None.
### Not started
- Reranker (17 Oct, not tonight); Phase 1 test run (18 Oct); Phases 2-6.
### Known issues / TODO
- Hybrid off: equal-weight RRF hurt dev. Re-test on 17 Oct: reranker over vector-only vs fused candidates; possibly weighted RRF (dev only).
- Dev misses (default pipeline): 14 (FCFS seek time, rank 8), 70 (huge time slice, p.77).
- User: spot-checks after 16 Oct; .env keys by 18 Oct; Node 24 LTS by end of 21 Oct.
### Next atomic action
- 17 Oct: pin the reranker model revision (cross-encoder/ms-marco-MiniLM-L-6-v2) in config + ARCHITECTURE section 7, implement rerank.py (10.7), then dev rows: vector+rerank and hybrid+rerank.

## [2026-10-15] - Read-only sub-agents
### Done
- .claude/agents/reviewer.md and .claude/agents/eval-auditor.md (read-only; Read/Grep/Glob/Bash for read-only commands; model sonnet). CLAUDE.md Section XIIIb: reviewer once per phase end and before every test-set run; eval-auditor before every test-set run; not after every commit.
### In progress / partial
- None.
### Not started
- Unchanged (reranker 17 Oct).
### Known issues / TODO
- First real use: before the Phase 1 test run (18 Oct).
### Next atomic action
- 17 Oct: pin the reranker revision, implement rerank.py, dev rows vector+rerank and hybrid+rerank.
## [2026-10-15] - Review of tonight's work (5c80d2b..993ffd7)
### Done
- Reviewer run (Explore agent with .claude/agents/reviewer.md instructions; the named agent loads next session). 0 blockers, 3 should-fix, 3 notes; reviewer changed nothing (git status clean).
- Fixed: 10.11 switch states (b4838ca); missing config rows slide_title_max_chars / slide_min_tokens (ea0a2af); PROGRESS.md-per-commit lapse logged in NOTES (this commit). 186 tests passing.
### In progress / partial
- None.
### Not started
- Reranker (17 Oct), Phase 1 test run (18 Oct).
### Known issues / TODO
- Review notes for later: ARCHITECTURE 10 diagram shows hybrid/rerank as unconditional; add test_rerank and pin the reranker revision with rerank.py.
### Next atomic action
- 17 Oct: pin reranker revision, implement rerank.py (10.7) with test_rerank, dev rows vector+rerank and hybrid+rerank.
## [2026-10-15] - Phase 1 step 10: cross-encoder reranker (measured, not adopted)
### Done
- rerank.py: Reranker (CrossEncoder ms-marco-MiniLM-L-6-v2 @ 233902d2, CPU, max_length 512), load_reranker; RerankerUnavailable; search(..., reranker=) as the last stage behind retrieval.rerank (ValueError if on without a reranker); CLI search / Streamlit / retrieval_eval pass it. tests/test_rerank.py: 7 tests.
- Dev rows 10 (rerank) and 11 (hybrid + rerank): 0.939 / 0.817, p95 2858 / 6297 ms -> not adopted, retrieval.rerank: false.
### In progress / partial
- None.
### Not started
- Phase 1 close: reviewer + eval-auditor, then the Phase 1 test run (once); Phases 2-6.
### Known issues / TODO
- Dev misses (default): 14 (rank 8), 70 (>10).
### Next atomic action
- Reviewer over 5c80d2b..HEAD and eval-auditor, then the Phase 1 test-split run with the default config.
## [2026-10-15] - Phase 1 close
### Done
- Reviewer + eval-auditor (named agents): 0 blockers; should-fixes fixed in 948a7c7 (eval/configs/ variants, hashes in ablation table, 10.12 test names). Agents changed nothing.
- Test run #3 (once): hit@5 0.939 (31/33), MRR 0.856, p95 47 ms -> eval/results/phase1_test.md; logged in NOTES.md. Target met.
- Key check: Groq ok, Gemini ok.
### In progress / partial
- Phase 2 drafts (contract 11, llm.py, citations.py, tests) in the session scratch folder; not committed yet.
### Not started
- Phases 2-6.
### Known issues / TODO
- CI must cache the reranker/embedding models (reviewer note).
### Next atomic action
- Phase 2 step 1: ARCHITECTURE section 11 + llm.py (Groq, Gemini, Fake; cache, limiter, capped retries) + tests/test_llm.py; pin httpx.
## [2026-10-15] - Phase 2 step 1: LLM layer
### Done
- ARCHITECTURE section 11 (Phase 2 contracts: llm, answer, citations, answer evaluation, config, edge cases).
- llm.py: GroqProvider / GeminiProvider over httpx (timeouts, retries only on 429/5xx/timeout, max 2, long retry-after fails fast), RateLimiter (rpm + tpm sliding window), AnswerCache (SQLite, data/cache), FakeProvider, make_provider, load_env/get_key. LLMError family in __init__. Config llm.*; httpx==0.28.1 pinned. tests/test_llm.py: 16 tests (mock transport, no network).
- Live check via llm.py: Groq ok (first token 0.6 s), Gemini ok (2.5 s), cache hit on repeat.
### In progress / partial
- citations.py draft in scratch folder.
### Not started
- answer.py, citation check wiring, answer evaluation, Streamlit Ask.
### Known issues / TODO
- Groq output contains narrow no-break spaces (U+202F): normalise in answer.py.
### Next atomic action
- citations.py (parse_citations, strip_invalid_refs, check_citations) + tests/test_citations.py + VIVA line by line.
## [2026-10-15] - Phase 2 step 2: citation parser
### Done
- citations.py: parse_citations, split_sentences, strip_invalid_refs, check_citations (judge, one retry, None = unchecked), parse_judge_reply. tests/test_citations.py: 11 tests. VIVA: line by line.
### In progress / partial
- None.
### Not started
- answer.py, answer evaluation, Streamlit Ask.
### Known issues / TODO
- Rule-based sentence splitting ("e.g." splits); errs on the strict side.
### Next atomic action
- answer.py: build_prompt, answer(), stream_answer() with retrieval gate + modes + abstention, tests with FakeProvider.
## [2026-10-15] - Phase 2 step 3: grounded answers
### Done
- answer.py: Source/Answer, build_prompt (rules + mode + numbered sources), stream_answer (retrieval gate, hold-back of NOT_IN_NOTES, TTFT, final Answer last), answer(), finalise (model / no-citation abstention, invalid refs stripped, NFKC), optional judge check. Config answer.* (k 5, gate 0.0 = off until calibrated on dev, judge gemini, 5 modes). provider.last_cached. citations: gap sentences need no citation.
- cli ask (stream, sources + image paths, flags). Tests: test_answer.py 10, test_cli ask 1, test_citations +1.
- Live: least-privilege 2-mark -> cited [1] p.5, judge ok, first token 0.72 s. Observed (not tuned): a SSTF-vs-SCAN question abstained because the top 5 had no SSTF slide; prompt rule 4 (partial answers) to be tuned on dev with the answer evaluation.
### In progress / partial
- None.
### Not started
- eval/answer_eval.py, gate calibration, prompt work on dev, Streamlit Ask.
### Known issues / TODO
- Comparison questions often retrieve one side only (retrieval limit, k=5).
### Next atomic action
- eval/answer_eval.py (metrics per ARCHITECTURE 11.4, pacing, partial results) + tests; then the dev run.
## [2026-10-15] - Phase 2 harness + Streamlit Ask; Phase 5 step 1: SM-2 + study store
### Done
- eval/answer_eval.py (+ tests/test_eval_answer.py, 5 tests); judge outages mark answers "not checked" (Answer.check_error), 3 in a row stop the run.
- Streamlit Ask tab (stream, modes, unit filter, flags, slide images); test_app +2.
- Fixes logged in NOTES: lenticular citation brackets from gpt-oss; Gemini 503 stopping a run.
- Contracts for quiz/flashcards (ARCHITECTURE 12) and the API (13); fastapi 0.143.2, pydantic 2.14.1 installed + pinned.
- srs.sm2 (assistant-written, VIVA line by line), study_store.StudyStore + Card (data/study.sqlite). tests: test_srs 5, test_study_store 5.
### In progress / partial
- Dev answer evaluation v1 running in the background (eval/results/answer_runs/answer_eval_dev_v1.md).
### Not started
- quiz.py, flashcards.py, json_mode; API; CI.
### Known issues / TODO
- Gate threshold and prompt tuning wait for the dev v1 numbers.
### Next atomic action
- json_mode in llm.py + quiz.py (pick_slides, generate_quiz, pydantic validation, one top-up) + tests/test_quiz.py.
## [2026-10-15] - Phase 5 step 2 + Phase 3: quiz, flashcards, API, schema v3
### Done
- quiz.py (pick_slides, generate_quiz, MCQ pydantic, one top-up), flashcards.py (generate_flashcards, card_from_question); json_mode in providers. tests: test_quiz 6, test_flashcards 3, test_llm +1.
- Judge moved to Groq Qwen (Gemini free tier = 20 requests/day, measured); TTFT excludes rate-limit queueing.
- api.py (FastAPI): health, documents (upload -> background job, list, delete), search, ask, ask/stream (SSE), page image, quiz, flashcards (generate, from-quiz, due, review). tests/test_api.py 7 tests (TestClient + FakeProvider).
- Schema v3 (documents can be 'deleted'); local index rebuilt (old kept as data/index.v2.bak4); dev ranks identical (row 12).
- Dev answer eval v1: citation accuracy 95.3%, faithfulness 75.0%, abstention 5/5, false abstention 1/33, TTFT p50 829 ms. Gate stays off (scores overlap).
### In progress / partial
- Prompt work on dev for faithfulness (uncited sentences).
### Not started
- GitHub Actions CI; Streamlit quiz/review pages; answer evaluation on test (after prompt work + reviewer + auditor); Next.js (needs Node 24).
### Known issues / TODO
- Starlette TestClient deprecation warning (httpx); harmless.
### Next atomic action
- Inspect uncited sentences in dev v1 answers, adjust the prompt (dev only), run dev v2.
## [2026-10-16] - Phase 2 prompt work, CI, Streamlit learning tabs, quiz evaluation, pre-test reviews
### Done
- Prompt v2 (cite every sentence; d7c5a9a) and v3 (one fact per sentence, say only what a slide states, format example; 9fcd5d8), each measured on dev: faithfulness 75.0% -> 81.2% -> 87.5%, citation accuracy 95.3% -> 91.8% -> 100%. v3 chosen for test (NOTES).
- .github/workflows/tests.yml: pytest on every push, HF model cache; first runs green (269 then 272 tests).
- Streamlit Quiz + Flashcards tabs (0e2bc02); API edge-case tests (413, from-quiz 422, SSE error event); API locks each faiss read instead of whole requests (LockedIndex).
- eval/quiz_eval.py + result: 25/25 valid, 24/25 supported. docs/demo-script.md.
- Reviewer (9b9da41..e600306) and eval-auditor before the test answer run: 0 blockers each; findings fixed (ARCHITECTURE 11.4 wording, 5-mark sample defined; this PROGRESS entry + morning report). Neither agent changed a file.
### In progress / partial
- None.
### Not started
- Test-split answer evaluation (next, once); Next.js web app (Node 24 needed); README + evaluation report (Phase 6).
### Known issues / TODO
- Dev faithfulness 87.5% < 90% target (uncited sentences); reported as is.
### Next atomic action
- Run the test-split answer evaluation once: concise (all 43) + 5-mark sample (--limit 10); log in NOTES.md.
## [2026-10-16] - Phase 2 test checkpoint, 5-mark fix, Phase 6 docs
### Done
- Test answer evaluation run once (concise all 43 + 5-mark sample 10), logged in NOTES: concise targets met; 5-mark faithfulness 12.5%.
- Declared post-test fix of exam modes (c91c8f4, f5328eb) + stray-token cleanup; dev 5-mark v3/v4/v5 = 12.5% / 50% / 100% (v5 partial).
- Limiter estimate chars/3; Groq daily cap (200k tokens) found and recorded (config tpd, demo script).
- docs/evaluation-report.md + README rewritten for Stage 2; eval-auditor: 0 blockers, fixes applied (4701ce6).
### In progress / partial
- Dev 5-mark v5 run partial (6/8) until Groq's daily window frees.
### Not started
- Next.js web app (Node 24 LTS needed); PR stage-2 -> main (draft next).
### Known issues / TODO
- 5-mark fix not re-measured on test (no further test checkpoint before the final report).
### Next atomic action
- Prepare the draft PR stage-2 -> main (no merge, no tag).

## [2026-10-16] - Phase 4: Next.js web app
### Done
- ARCHITECTURE 14 (web contract) + `api.cors_origins` in config.yaml; CORSMiddleware in api.py; test_cors_allows_only_the_configured_web_origin (274 tests pass).
- web/: Next 16.4.1, React 19.3.0, Tailwind 4.3.3, TypeScript 5.9.3, exact pins + package-lock. lib/api.ts (typed calls, ApiError, SSE reader streamAsk), components Nav (health), SlideModal, CitedText, Notice.
- Pages: /documents (5dc0a57), /ask (ae53cf0), /quiz (6f44fcd), /review (3f02e18); one commit each, pushed.
- CI: `web` job (Node 24: npm ci, lint, build) in tests.yml (e2aed36), green on GitHub.
- README two-terminal run commands; VIVA Phase 4 questions.
### In progress / partial
- None.
### Not started
- Browser click-through by the user (no browser tool in this session). docs/demo-script.md still uses Streamlit tab names.
### Known issues / TODO
- One Groq call used for the live /ask/stream check. Quiz and flashcard generation not called live.
- Job status lives in API memory: restarting uvicorn loses in-progress job ids (documents already indexed stay).
### Next atomic action
- User: browser click-through (Morning report item 1); then decide web vs Streamlit for the demo.
