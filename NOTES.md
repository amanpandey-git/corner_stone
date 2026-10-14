# NOTES - decision + bug log

Format: `date | what | why / root cause | fix`

2026-10-15 | Decision: use faiss-cpu `IndexHNSWFlat` instead of hnswlib | `pip install hnswlib` fails on Windows/Python 3.12: no prebuilt wheel, needs a C++ compiler (VS Build Tools not installed, ~3-6 GB). faiss-cpu has a Windows wheel and the same HNSW algorithm (M, efConstruction, efSearch). | Index sits behind `index/hnsw_index.py`; the interface is backend-agnostic. Differences handled: no native delete (soft-delete via SQLite `deleted` flag + over-fetch), no manual resize (faiss grows itself). Cosine = inner product on L2-normalised vectors.
2026-10-15 | Decision: Python 3.12.10 venv (not system 3.14.0) | torch / sentence-transformers wheels for 3.14 are not reliable on Windows. | `.venv` built with `py -3.12`.
2026-10-15 | Decision: dataclasses and exceptions live in `src/cornerstone/__init__.py` | The repo layout in CLAUDE.md Section III is fixed, and has no `models.py`. | Keeps the layout unchanged.
2026-10-15 | Decision: repo stays public | User's choice. | Never commit uploaded documents or indexes (`data/` is gitignored). `samples/` PDFs are course notes already in the repo.
