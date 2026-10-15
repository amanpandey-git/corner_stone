"""SQLite metadata store: documents, pages, chunks.

chunks.chunk_id (INTEGER PRIMARY KEY AUTOINCREMENT) is the label used in the HNSW index.
chunks.status is the single source of truth for "can this vector be returned?":
    pending  - written, not yet confirmed (ingest in progress or interrupted)
    active   - searchable
    deleted  - soft-deleted (replaced or abandoned); the vector stays in the graph, filtered out here

Every multi-row write is one transaction, so a crash can never leave a half-written document.

Schema version (PRAGMA user_version) must equal SCHEMA_VERSION; an older database (v0.1 = 0/1)
raises IndexVersionMismatch with the rebuild command instead of being migrated silently.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from cornerstone import SCHEMA_VERSION, Chunk, Document, IndexVersionMismatch, Page, SearchFilters, rebuild_hint

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents(
    doc_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name       TEXT NOT NULL,
    sha256          TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    n_pages         INTEGER NOT NULL DEFAULT 0,
    n_pages_text    INTEGER NOT NULL DEFAULT 0,
    n_pages_flagged INTEGER NOT NULL DEFAULT 0,
    n_chunks        INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL CHECK(status IN ('pending','active','replaced','abandoned','deleted')),
    ingested_at     TEXT NOT NULL,
    unit            TEXT,
    source_path     TEXT
);
CREATE TABLE IF NOT EXISTS pages(
    page_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES documents(doc_id),
    page_no     INTEGER,
    para_start  INTEGER,
    para_end    INTEGER,
    status      TEXT NOT NULL,
    reason      TEXT,
    n_chars     INTEGER NOT NULL,
    duplicate_of INTEGER,
    image_path  TEXT
);
CREATE TABLE IF NOT EXISTS chunks(
    chunk_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id          INTEGER NOT NULL REFERENCES documents(doc_id),
    page_start      INTEGER,
    page_end        INTEGER,
    para_start      INTEGER,
    para_end        INTEGER,
    section_heading TEXT,
    chunk_index     INTEGER NOT NULL,
    token_count     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','active','deleted')),
    context_header  TEXT
);
-- keyword index over chunk text (external content: rows are written next to the chunk rows, same transaction)
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, context_header, content='chunks', content_rowid='chunk_id', tokenize='porter unicode61');
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_docs_name ON documents(file_name);
CREATE INDEX IF NOT EXISTS idx_docs_sha ON documents(sha256);
CREATE INDEX IF NOT EXISTS idx_docs_unit ON documents(unit);
-- at most one active version of a file name
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_name ON documents(file_name) WHERE status = 'active';
"""

_DOC_COLS = ("doc_id, file_name, sha256, file_type, n_pages, n_pages_text, n_pages_flagged, n_chunks, status, "
             "ingested_at, unit, source_path")
_SQL_VARS = 500  # stay well under SQLite's variable limit


def _doc(row: sqlite3.Row) -> Document:
    return Document(**{k: row[k] for k in row.keys()})


class MetadataStore:
    def __init__(self, db_path: Path) -> None:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        fresh = self.conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='documents'"
                                  ).fetchone()[0] == 0
        if fresh:
            self.conn.executescript(_SCHEMA)
            self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            self.conn.commit()
        else:
            found = self.conn.execute("PRAGMA user_version").fetchone()[0] or 1   # v0.1 never set it
            if found != SCHEMA_VERSION:
                self.conn.close()
                raise IndexVersionMismatch(rebuild_hint(found))

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------ lookups
    def find_by_hash(self, sha256: str) -> Document | None:
        """The active document with this content hash, if any (pending/replaced do not count)."""
        row = self.conn.execute(f"SELECT {_DOC_COLS} FROM documents WHERE sha256=? AND status='active' "
                                "ORDER BY doc_id DESC LIMIT 1", (sha256,)).fetchone()
        return _doc(row) if row else None

    def find_active_by_name(self, file_name: str) -> Document | None:
        row = self.conn.execute(f"SELECT {_DOC_COLS} FROM documents WHERE file_name=? AND status='active'",
                                (file_name,)).fetchone()
        return _doc(row) if row else None

    def get_document(self, doc_id: int) -> Document | None:
        row = self.conn.execute(f"SELECT {_DOC_COLS} FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        return _doc(row) if row else None

    def list_documents(self, status: str = "active") -> list[Document]:
        rows = self.conn.execute(f"SELECT {_DOC_COLS} FROM documents WHERE status=? ORDER BY doc_id", (status,))
        return [_doc(r) for r in rows]

    # ------------------------------------------------------------ writes
    def add_document(self, doc: Document, pages: list[Page], chunks: list[Chunk]) -> list[int]:
        """Insert document + pages + chunks, all as 'pending', in ONE transaction.

        Returns the new chunk_ids in the order of ``chunks``; ``doc.doc_id`` is set. If anything
        fails nothing is written. Counts are computed here from ``pages``/``chunks``.
        """
        ok = sum(1 for p in pages if p.status == "ok")
        dup = sum(1 for p in pages if p.status == "duplicate")
        flagged = len(pages) - ok - dup
        with self.conn:  # commit on success, rollback on any exception
            cur = self.conn.execute(
                "INSERT INTO documents(file_name, sha256, file_type, n_pages, n_pages_text, n_pages_flagged,"
                " n_chunks, status, ingested_at, unit, source_path) VALUES (?,?,?,?,?,?,?,'pending',?,?,?)",
                (doc.file_name, doc.sha256, doc.file_type, len(pages), ok, flagged, len(chunks),
                 datetime.now(timezone.utc).isoformat(timespec="seconds"), doc.unit, doc.source_path))
            doc_id = cur.lastrowid
            self.conn.executemany(
                "INSERT INTO pages(doc_id, page_no, para_start, para_end, status, reason, n_chars, duplicate_of,"
                " image_path) VALUES (?,?,?,?,?,?,?,?,?)",
                [(doc_id, p.page_no, p.para_start, p.para_end, p.status, p.reason, len(p.text), p.duplicate_of,
                  p.image_path) for p in pages])
            chunk_ids = []
            for c in chunks:
                cur = self.conn.execute(
                    "INSERT INTO chunks(doc_id, page_start, page_end, para_start, para_end, section_heading,"
                    " chunk_index, token_count, text, status, context_header) VALUES (?,?,?,?,?,?,?,?,?,'pending',?)",
                    (doc_id, c.page_start, c.page_end, c.para_start, c.para_end, c.section_heading,
                     c.chunk_index, c.token_count, c.text, c.context_header))
                self.conn.execute("INSERT INTO chunks_fts(rowid, text, context_header) VALUES (?,?,?)",
                                  (cur.lastrowid, c.text, c.context_header))
                chunk_ids.append(cur.lastrowid)
        doc.doc_id, doc.status = doc_id, "pending"
        doc.n_pages, doc.n_pages_text, doc.n_pages_flagged, doc.n_chunks = len(pages), ok, flagged, len(chunks)
        return chunk_ids

    def activate(self, doc_id: int, replaces: int | None = None) -> None:
        """pending -> active for the document and its chunks, atomically.

        With ``replaces`` the old version is retired in the same transaction, so there is never
        a moment with two active versions (or none).
        """
        with self.conn:
            if replaces is not None:
                self._retire(replaces)
            cur = self.conn.execute("UPDATE documents SET status='active' WHERE doc_id=? AND status='pending'",
                                    (doc_id,))
            if cur.rowcount != 1:
                raise ValueError(f"document {doc_id} is not pending; cannot activate")
            self.conn.execute("UPDATE chunks SET status='active' WHERE doc_id=? AND status='pending'", (doc_id,))

    def set_page_images(self, doc_id: int, images: dict[int, str]) -> None:
        """Record rendered page images ({page_no: path relative to paths.image_dir}) in one transaction."""
        with self.conn:
            self.conn.executemany("UPDATE pages SET image_path=? WHERE doc_id=? AND page_no=?",
                                  [(path, doc_id, no) for no, path in images.items()])

    def get_page_image(self, doc_id: int, page_no: int) -> str | None:
        """Relative image path of one page, or None (no image, DOCX, unknown page)."""
        row = self.conn.execute("SELECT image_path FROM pages WHERE doc_id=? AND page_no=?",
                                (doc_id, page_no)).fetchone()
        return row[0] if row else None

    def mark_replaced(self, doc_id: int) -> None:
        """Retire a document: status 'replaced', all its chunks soft-deleted."""
        with self.conn:
            self._retire(doc_id)

    def delete_document(self, doc_id: int) -> None:
        """The student removed a document: status 'deleted', all its chunks soft-deleted, in one transaction.
        Its vectors stay in the graph (filtered out) until compaction. KeyError if it is not active."""
        with self.conn:
            cur = self.conn.execute("UPDATE documents SET status='deleted' WHERE doc_id=? AND status='active'",
                                    (doc_id,))
            if cur.rowcount != 1:
                raise KeyError(f"no active document with id {doc_id}")
            self.conn.execute("UPDATE chunks SET status='deleted' WHERE doc_id=?", (doc_id,))

    def discard_pending(self, doc_id: int) -> None:
        """Abandon an interrupted ingest: document 'abandoned', its chunks soft-deleted."""
        with self.conn:
            cur = self.conn.execute("UPDATE documents SET status='abandoned' WHERE doc_id=? AND status='pending'",
                                    (doc_id,))
            if cur.rowcount != 1:
                raise ValueError(f"document {doc_id} is not pending")
            self.conn.execute("UPDATE chunks SET status='deleted' WHERE doc_id=?", (doc_id,))

    def _retire(self, doc_id: int) -> None:
        cur = self.conn.execute("UPDATE documents SET status='replaced' WHERE doc_id=? AND status='active'",
                                (doc_id,))
        if cur.rowcount != 1:
            raise ValueError(f"document {doc_id} is not active; cannot replace")
        self.conn.execute("UPDATE chunks SET status='deleted' WHERE doc_id=?", (doc_id,))

    # ------------------------------------------------------------ reads for search / stats
    def get_chunks(self, chunk_ids: list[int]) -> dict[int, Chunk]:
        """Active chunks only (pending and deleted ones are silently absent from the result)."""
        out: dict[int, Chunk] = {}
        ids = [int(i) for i in chunk_ids]
        for i in range(0, len(ids), _SQL_VARS):
            part = ids[i:i + _SQL_VARS]
            q = ("SELECT c.*, d.file_name FROM chunks c JOIN documents d ON d.doc_id = c.doc_id "
                 f"WHERE c.status='active' AND c.chunk_id IN ({','.join('?' * len(part))})")
            for r in self.conn.execute(q, part):
                out[r["chunk_id"]] = Chunk(
                    chunk_id=r["chunk_id"], doc_id=r["doc_id"], file_name=r["file_name"], text=r["text"],
                    chunk_index=r["chunk_index"], token_count=r["token_count"],
                    section_heading=r["section_heading"], page_start=r["page_start"], page_end=r["page_end"],
                    para_start=r["para_start"], para_end=r["para_end"], deleted=False,
                    context_header=r["context_header"])
        return out

    def allowed_doc_ids(self, filters: SearchFilters | None) -> set[int] | None:
        """Active doc_ids matching the filters; None means "no restriction" (no filter given)."""
        if filters is None or (filters.doc_ids is None and filters.units is None):
            return None
        sql, args = "SELECT doc_id FROM documents WHERE status='active'", []
        if filters.doc_ids is not None:
            sql += f" AND doc_id IN ({','.join('?' * len(filters.doc_ids))})"
            args += list(filters.doc_ids)
        if filters.units is not None:
            sql += f" AND unit IN ({','.join('?' * len(filters.units))})"
            args += list(filters.units)
        return {r[0] for r in self.conn.execute(sql, args)}

    def purge_deleted(self) -> tuple[int, list[int]]:
        """Compaction, SQLite side (call only after the compacted index is saved). ONE transaction:
        remove 'deleted' chunk rows and their FTS rows, and the page rows of replaced/abandoned/deleted documents.
        Document rows stay (history). Returns (chunk rows removed, doc_ids whose pages were removed)."""
        with self.conn:
            rows = self.conn.execute("SELECT chunk_id, text, context_header FROM chunks WHERE status='deleted'"
                                     ).fetchall()
            # external-content FTS5 tables are cleaned with the special 'delete' command and the old values
            self.conn.executemany("INSERT INTO chunks_fts(chunks_fts, rowid, text, context_header) "
                                  "VALUES('delete', ?, ?, ?)", [tuple(r) for r in rows])
            self.conn.execute("DELETE FROM chunks WHERE status='deleted'")
            retired = [r[0] for r in self.conn.execute(
                "SELECT doc_id FROM documents WHERE status IN ('replaced','abandoned','deleted') "
                "AND doc_id IN (SELECT doc_id FROM pages)")]
            self.conn.executemany("DELETE FROM pages WHERE doc_id=?", [(d,) for d in retired])
        return len(rows), retired

    def active_chunk_ids(self) -> list[int]:
        return [r[0] for r in self.conn.execute("SELECT chunk_id FROM chunks WHERE status='active' ORDER BY chunk_id")]

    def stats(self) -> dict:
        """Counts for the `stats` command and the ingestion report (active documents only for pages)."""
        q = self.conn.execute
        docs = dict(q("SELECT status, COUNT(*) FROM documents GROUP BY status").fetchall())
        chunks = dict(q("SELECT status, COUNT(*) FROM chunks GROUP BY status").fetchall())
        pg = q("SELECT COUNT(*), COALESCE(SUM(p.status='ok'),0), COALESCE(SUM(p.status='duplicate'),0) "
               "FROM pages p JOIN documents d USING(doc_id) WHERE d.status='active'").fetchone()
        flagged = [dict(r) for r in q(
            "SELECT d.file_name, p.page_no, p.status, p.reason FROM pages p JOIN documents d USING(doc_id) "
            "WHERE d.status='active' AND p.status NOT IN ('ok','duplicate') ORDER BY d.doc_id, p.page_id")]
        duplicates = [dict(r) for r in q(
            "SELECT d.file_name, p.page_no, p.duplicate_of FROM pages p JOIN documents d USING(doc_id) "
            "WHERE d.status='active' AND p.status='duplicate' ORDER BY d.doc_id, p.page_id")]
        return {
            "documents": docs.get("active", 0), "documents_pending": docs.get("pending", 0),
            "documents_replaced": docs.get("replaced", 0), "documents_abandoned": docs.get("abandoned", 0),
            "documents_deleted": docs.get("deleted", 0),
            "chunks_active": chunks.get("active", 0), "chunks_pending": chunks.get("pending", 0),
            "chunks_deleted": chunks.get("deleted", 0),
            "pages_total": pg[0], "pages_with_text": pg[1], "pages_duplicate": pg[2],
            "pages_flagged": pg[0] - pg[1] - pg[2],
            "flagged_pages": flagged, "duplicate_pages": duplicates,
        }

    def check_sync(self, index_ids: set[int]) -> list[str]:
        """Compare SQLite with the labels stored in the index. [] means consistent.

        Reports: interrupted ingests (pending documents), vectors with no SQLite row, and active
        chunks whose vector is missing from the index.
        """
        index_ids = {int(i) for i in index_ids}
        problems: list[str] = []
        pending = self.list_documents("pending")
        if pending:
            names = ", ".join(f"{d.file_name} (doc {d.doc_id})" for d in pending)
            problems.append(f"{len(pending)} interrupted ingest(s) left pending: {names}")
        known = {r[0] for r in self.conn.execute("SELECT chunk_id FROM chunks")}
        orphans = index_ids - known
        if orphans:
            problems.append(f"{len(orphans)} vector(s) in the index have no row in SQLite "
                            f"(e.g. labels {sorted(orphans)[:5]})")
        active = {r[0] for r in self.conn.execute("SELECT chunk_id FROM chunks WHERE status='active'")}
        missing = active - index_ids
        if missing:
            problems.append(f"{len(missing)} active chunk(s) have no vector in the index "
                            f"(e.g. ids {sorted(missing)[:5]})")
        return problems
