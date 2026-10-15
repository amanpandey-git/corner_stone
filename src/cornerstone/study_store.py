"""Flashcards and their review history in their own SQLite file (ARCHITECTURE.md 12.2).

Kept apart from the index database on purpose: rebuilding or compacting the index must never wipe a student's
study progress. A card remembers the file name and page it came from, so its slide can be shown after a rebuild.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, fields
from datetime import date, datetime, timedelta
from pathlib import Path

from cornerstone.srs import sm2

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    card_id   INTEGER PRIMARY KEY,
    front     TEXT NOT NULL,
    back      TEXT NOT NULL,
    file_name TEXT NOT NULL,
    page      INTEGER,
    doc_id    INTEGER,
    chunk_id  INTEGER,
    unit      TEXT,
    due       TEXT NOT NULL,          -- ISO date
    ef        REAL NOT NULL DEFAULT 2.5,
    interval  INTEGER NOT NULL DEFAULT 0,
    reps      INTEGER NOT NULL DEFAULT 0,
    lapses    INTEGER NOT NULL DEFAULT 0,
    origin    TEXT NOT NULL DEFAULT 'generated',
    created   TEXT NOT NULL,
    UNIQUE (front, file_name, page)
);
CREATE TABLE IF NOT EXISTS reviews (
    review_id INTEGER PRIMARY KEY,
    card_id   INTEGER NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    reviewed  TEXT NOT NULL,          -- ISO date
    grade     INTEGER NOT NULL,
    interval  INTEGER NOT NULL,
    ef        REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS cards_due ON cards(due);
"""


@dataclass
class Card:
    card_id: int
    front: str
    back: str
    file_name: str
    page: int | None
    doc_id: int | None
    chunk_id: int | None
    unit: str | None
    due: date
    ef: float = 2.5
    interval: int = 0
    reps: int = 0
    lapses: int = 0
    origin: str = "generated"      # generated | quiz


_COLS = [f.name for f in fields(Card)]


def _card(row) -> Card:
    d = dict(zip(_COLS, row))
    d["due"] = date.fromisoformat(d["due"])
    return Card(**d)


class StudyStore:
    """Short-lived connections, so one StudyStore can be shared by Streamlit and FastAPI threads."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.execute("PRAGMA foreign_keys = ON")
        return c

    def _run(self, fn):
        c = self._conn()
        try:
            with c:
                return fn(c)
        finally:
            c.close()

    def add_cards(self, cards: list[Card]) -> list[int]:
        """Insert cards; a card with the same front, file and page as an existing one is skipped.
        Returns the ids of the cards actually added."""
        now = datetime.now().isoformat(timespec="seconds")

        def go(c):
            ids = []
            for k in cards:
                cur = c.execute(
                    "INSERT OR IGNORE INTO cards (front, back, file_name, page, doc_id, chunk_id, unit, due, ef, "
                    "interval, reps, lapses, origin, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (k.front.strip(), k.back.strip(), k.file_name, k.page, k.doc_id, k.chunk_id, k.unit,
                     k.due.isoformat(), k.ef, k.interval, k.reps, k.lapses, k.origin, now))
                if cur.rowcount:
                    ids.append(cur.lastrowid)
            return ids
        return self._run(go)

    def get(self, card_id: int) -> Card:
        row = self._run(lambda c: c.execute(f"SELECT {', '.join(_COLS)} FROM cards WHERE card_id=?",
                                            (card_id,)).fetchone())
        if row is None:
            raise KeyError(f"no flashcard with id {card_id}")
        return _card(row)

    def due(self, today: date, limit: int = 20, units: list[str] | None = None) -> list[Card]:
        """Cards due on or before today, the most overdue first."""
        sql = f"SELECT {', '.join(_COLS)} FROM cards WHERE due <= ?"
        args: list = [today.isoformat()]
        if units is not None:
            sql += f" AND unit IN ({', '.join('?' * len(units))})" if units else " AND 0"
            args += units
        sql += " ORDER BY due, card_id LIMIT ?"
        return [_card(r) for r in self._run(lambda c: c.execute(sql, (*args, limit)).fetchall())]

    def list_cards(self, units: list[str] | None = None) -> list[Card]:
        sql = f"SELECT {', '.join(_COLS)} FROM cards"
        args: list = []
        if units is not None:
            sql += f" WHERE unit IN ({', '.join('?' * len(units))})" if units else " WHERE 0"
            args = units
        return [_card(r) for r in self._run(lambda c: c.execute(sql + " ORDER BY card_id", args).fetchall())]

    def review(self, card_id: int, grade: int, today: date) -> Card:
        """Apply one SM-2 review and log it. KeyError for an unknown card, ValueError for a grade outside 0..5."""
        card = self.get(card_id)
        ef, interval, reps = sm2(card.ef, card.interval, card.reps, grade)   # ValueError before any write
        lapses = card.lapses + (1 if grade < 3 else 0)
        due = today + timedelta(days=interval)

        def go(c):
            c.execute("UPDATE cards SET ef=?, interval=?, reps=?, lapses=?, due=? WHERE card_id=?",
                      (ef, interval, reps, lapses, due.isoformat(), card_id))
            c.execute("INSERT INTO reviews (card_id, reviewed, grade, interval, ef) VALUES (?,?,?,?,?)",
                      (card_id, today.isoformat(), grade, interval, ef))
        self._run(go)
        return self.get(card_id)

    def delete_card(self, card_id: int) -> None:
        if not self._run(lambda c: c.execute("DELETE FROM cards WHERE card_id=?", (card_id,)).rowcount):
            raise KeyError(f"no flashcard with id {card_id}")

    def stats(self, today: date) -> dict:
        def go(c):
            total = c.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            due = c.execute("SELECT COUNT(*) FROM cards WHERE due <= ?", (today.isoformat(),)).fetchone()[0]
            reviews = c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            return {"cards": total, "due_today": due, "reviews": reviews}
        return self._run(go)
