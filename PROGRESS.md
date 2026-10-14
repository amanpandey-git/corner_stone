# PROGRESS - session log (append only)

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
