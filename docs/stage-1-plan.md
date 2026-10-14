# Stage 1 plan (deadline 16 Oct 2026)

## Day 1
- [x] Step 0 - Setup: repo, .gitignore, folders, docs, venv, version lock, requirements.txt
- [x] Step 1 - Extraction: PDF + DOCX parsers, scanned-page detection, cleaner, tests on samples/
- [x] Step 2 - Chunking: structure-aware chunker, overlap + token limits, debug command, tests
- [x] Step 3 - Embeddings: batching, normalisation, prefixes, caching, tests

## Day 2
- [x] Step 4 - Index + store: HNSW save/load/grow/mark_deleted, SQLite, manifest, ingest_file() with dedup, tests
- [x] Step 5 - Search + CLI: search() -> SearchResult, CLI ingest/search/stats
- [ ] Step 6 - Verification: ANN vs brute-force (ef_search sweep), retrieval eval, README table
- [ ] Step 7 - Demo UI: minimal Streamlit page (only after 0-6 are green)
- [ ] Step 8 - Wrap-up: README, final PROGRESS.md, tag `v0.1-indexing`

Cut order if short on time: ef_search sweep, then Step 7. Never cut tests, brute-force check or snapshots.
