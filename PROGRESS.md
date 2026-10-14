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
- Real samples: 7 PDFs -> 328 chunks; all chunks 40..275 tokens (<= hard_max 480); flagged pages: 14 (all needs_ocr/diagram slides).
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
