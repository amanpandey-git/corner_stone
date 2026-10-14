"""SQLite metadata store: documents, pages, chunks.

chunks.chunk_id (INTEGER PRIMARY KEY AUTOINCREMENT) is the label used in the HNSW index.
chunks.status is the single source of truth for "can this vector be returned?":
    pending  - written, not yet confirmed (ingest in progress or interrupted)
    active   - searchable
    deleted  - soft-deleted (replaced or abandoned); the vector stays in the graph, filtered out here

Every multi-row write is one transaction, so a crash can never leave a half-written document.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from cornerstone import Chunk, Document, Page

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
    status          TEXT NOT NULL CHECK(status IN ('pending','active','replaced','abandoned')),
    ingested_at     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pages(
    page_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES documents(doc_id),
    page_no     INTEGER,
    para_start  INTEGER,
    para_end    INTEGER,
    status      TEXT NOT NULL,
    reason      TEXT,
    n_chars     INTEGER NOT NULL
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
    status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','active','deleted'))
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_docs_name ON documents(file_name);
CREATE INDEX IF NOT EXISTS idx_docs_sha ON documents(sha256);
-- at most one active version of a file name
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_name ON documents(file_name) WHERE status = 'active';
"""

_DOC_COLS = "doc_id, file_name, sha256, file_type, n_pages, n_pages_text, n_pages_flagged, n_chunks, status, ingested_at"
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
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

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
        with self.conn:  # commit on success, rollback on any exception
            cur = self.conn.execute(
                "INSERT INTO documents(file_name, sha256, file_type, n_pages, n_pages_text, n_pages_flagged,"
                " n_chunks, status, ingested_at) VALUES (?,?,?,?,?,?,?,'pending',?)",
                (doc.file_name, doc.sha256, doc.file_type, len(pages), ok, len(pages) - ok, len(chunks),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
            doc_id = cur.lastrowid
            self.conn.executemany(
                "INSERT INTO pages(doc_id, page_no, para_start, para_end, status, reason, n_chars)"
                " VALUES (?,?,?,?,?,?,?)",
                [(doc_id, p.page_no, p.para_start, p.para_end, p.status, p.reason, len(p.text)) for p in pages])
            chunk_ids = []
            for c in chunks:
                cur = self.conn.execute(
                    "INSERT INTO chunks(doc_id, page_start, page_end, para_start, para_end, section_heading,"
                    " chunk_index, token_count, text, status) VALUES (?,?,?,?,?,?,?,?,?,'pending')",
                    (doc_id, c.page_start, c.page_end, c.para_start, c.para_end, c.section_heading,
                     c.chunk_index, c.token_count, c.text))
                chunk_ids.append(cur.lastrowid)
        doc.doc_id, doc.status = doc_id, "pending"
        doc.n_pages, doc.n_pages_text, doc.n_pages_flagged, doc.n_chunks = len(pages), ok, len(pages) - ok, len(chunks)
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

    def mark_replaced(self, doc_id: int) -> None:
        """Retire a document: status 'replaced', all its chunks soft-deleted."""
        with self.conn:
            self._retire(doc_id)

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
                    para_start=r["para_start"], para_end=r["para_end"], deleted=False)
        return out

    def active_chunk_ids(self) -> list[int]:
        return [r[0] for r in self.conn.execute("SELECT chunk_id FROM chunks WHERE status='active' ORDER BY chunk_id")]

    def stats(self) -> dict:
        """Counts for the `stats` command and the ingestion report (active documents only for pages)."""
        q = self.conn.execute
        docs = dict(q("SELECT status, COUNT(*) FROM documents GROUP BY status").fetchall())
        chunks = dict(q("SELECT status, COUNT(*) FROM chunks GROUP BY status").fetchall())
        pg = q("SELECT COUNT(*), COALESCE(SUM(p.status='ok'),0) FROM pages p JOIN documents d USING(doc_id) "
               "WHERE d.status='active'").fetchone()
        flagged = [dict(r) for r in q(
            "SELECT d.file_name, p.page_no, p.status, p.reason FROM pages p JOIN documents d USING(doc_id) "
            "WHERE d.status='active' AND p.status!='ok' ORDER BY d.doc_id, p.page_id")]
        return {
            "documents": docs.get("active", 0), "documents_pending": docs.get("pending", 0),
            "documents_replaced": docs.get("replaced", 0), "documents_abandoned": docs.get("abandoned", 0),
            "chunks_active": chunks.get("active", 0), "chunks_pending": chunks.get("pending", 0),
            "chunks_deleted": chunks.get("deleted", 0),
            "pages_total": pg[0], "pages_with_text": pg[1], "pages_flagged": pg[0] - pg[1],
            "flagged_pages": flagged,
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
