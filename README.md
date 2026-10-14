# Cornerstone

An exam-prep study assistant. Students upload notes, textbooks and past papers (PDF, DOCX); the system extracts, cleans, chunks, embeds and indexes them so an LLM can later answer questions with citations and generate study material.

**Stage 1 (this repo, tag `v0.1-indexing`)**: extraction and indexing only, English documents. No LLM.

## Stage 1 scope
- PDF + DOCX ingestion with page / paragraph metadata; scanned pages flagged "needs OCR"
- Header/footer cleaning, structure-aware chunking
- Sentence embeddings (CPU) + HNSW index (faiss) + SQLite metadata store
- SHA-256 deduplication, replace-on-change
- CLI: `ingest`, `search`, `stats` (Streamlit demo page if time allows)
- Verification: HNSW vs brute-force recall, labelled retrieval set

See `ARCHITECTURE.md` for contracts, `docs/stage-1-plan.md` for the build order.

## Setup
_Filled in at Step 8._ Python 3.12, `python -m venv .venv`, `pip install -r requirements.txt`.

## Results
_Filled in at Step 6._

## Limitations
English only, no OCR, no tables/equations/images. See `ARCHITECTURE.md`.
