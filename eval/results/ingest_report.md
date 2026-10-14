# Ingestion report - samples/ (7 PDFs)

Measured 2026-10-15 on Intel i5-1135G7, 8 GB RAM, CPU only, bge-small-en-v1.5, fresh index.

| file | pages | with text | flagged | chunks | time (s) |
|---|---|---|---|---|---|
| Unit 1_Part 1_Introduction & OS Structure.pdf | 48 | 48 | 0 | 54 | 6.1 |
| Unit 1_Part 2_ Process management.pdf | 120 | 120 | 0 | 89 | 11.0 |
| Unit 2_Process Synchronization_Deadlock.pdf | 59 | 56 | 3 | 56 | 6.9 |
| Unit 3_Memory management.pdf | 55 | 48 | 7 | 41 | 5.6 |
| Unit 4_Storage management_ Disk Schduling.pdf | 51 | 51 | 0 | 38 | 4.2 |
| Unit 5_Part 1_File-system-interface.pdf | 61 | 60 | 1 | 32 | 2.9 |
| Unit 5_Part 2_System Protection.pdf | 28 | 26 | 2 | 18 | 2.0 |
| **total** | 422 | 409 | 13 | 328 | 38.7 |

- Flagged pages are all `needs_ocr` (diagram/image slides). 0 errors, 0 silently skipped: 409 + 13 = 422.
- Index file 0.55 MB, SQLite 0.25 MB. check_sync: OK. Second run: all 7 `skipped_duplicate`, vectors unchanged (328).
- Time includes text extraction, chunking and embedding; the model load (~16 s) is not included.