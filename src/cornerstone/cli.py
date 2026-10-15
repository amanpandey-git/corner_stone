"""Command line interface: ingest, search, stats (+ chunks debug).

    python -m cornerstone.cli ingest <file|dir>
    python -m cornerstone.cli search "<query>" --k 5
    python -m cornerstone.cli stats
    python -m cornerstone.cli chunks <file> [--full]
    python -m cornerstone.cli rebuild <file|dir>... [--yes]   # fresh index; old folder kept as *.v<N>.bak
Run with PYTHONPATH=src from the repo root.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from cornerstone import CornerstoneError, EmptyQuery, SearchFilters
from cornerstone.chunking import chunk_pages
from cornerstone.dedup import mark_duplicates
from cornerstone.embeddings import Embedder, load_token_counter
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.ingest.loader import load_document
from cornerstone.pipeline import compact, ingest_file
from cornerstone.search import search

ROOT = Path(__file__).resolve().parents[2]
INDEX_FILE = "hnsw.faiss"
DB_FILE = "cornerstone.sqlite"
SUPPORTED = {".pdf", ".docx"}


def load_config(path: Path | None = None) -> dict:
    """Read config.yaml; relative entries under `paths` are resolved against the repo root."""
    cfg = yaml.safe_load((Path(path) if path else ROOT / "config.yaml").read_text(encoding="utf-8"))
    cfg["paths"] = {k: str(ROOT / v) for k, v in cfg["paths"].items()}   # ROOT / absolute == absolute
    return cfg


@dataclass
class Stack:
    store: MetadataStore
    index: HNSWIndex
    index_path: Path
    embedder: Embedder | None

    def close(self) -> None:
        """Release the SQLite file (Windows cannot move a folder while a connection is open)."""
        self.store.close()


def open_stack(cfg: dict, root: Path = ROOT, load_embedder: bool = True, assume_yes: bool = False) -> Stack:
    """Open (or create) store + index under paths.index_dir and verify they agree.

    Raises ModelMismatch if the index was built with other settings. Interrupted ingests found
    by check_sync are shown and discarded only after the user confirms (or --yes); anything
    else out of sync is reported with the way to rebuild. Nothing is repaired silently.
    """
    index_dir = Path(root) / cfg["paths"]["index_dir"]
    index_path = index_dir / INDEX_FILE
    store = MetadataStore(index_dir / DB_FILE)
    try:
        index = HNSWIndex.load(index_path, cfg) if index_path.is_file() else HNSWIndex.from_config(cfg)
    except Exception:
        store.close()
        raise

    problems = store.check_sync(set(index.all_ids().tolist()))
    if problems:
        print("WARNING: index and database are out of sync:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        pending = store.list_documents("pending")
        if pending:
            ok = assume_yes
            if not ok and sys.stdin.isatty():
                ok = input(f"Discard {len(pending)} interrupted ingest(s) and re-ingest them later? [y/N] "
                           ).strip().lower() == "y"
            if ok:
                for d in pending:
                    store.discard_pending(d.doc_id)
                    print(f"  discarded interrupted ingest of {d.file_name} (doc {d.doc_id}); "
                          "ingest the file again", file=sys.stderr)
            else:
                print("  not discarded (answer y, or pass --yes, to clean up)", file=sys.stderr)
        if any("no row in SQLite" in p or "no vector in the index" in p for p in problems):
            print(f"  to rebuild: delete {index_dir} and ingest your files again", file=sys.stderr)
    return Stack(store, index, index_path, Embedder(cfg) if load_embedder else None)


# ------------------------------------------------------------------ commands
def location(c) -> str:
    if c.page_start is not None:
        return f"p.{c.page_start}" if c.page_start == c.page_end else f"pp.{c.page_start}-{c.page_end}"
    return f"paragraphs {c.para_start}-{c.para_end}"


def collect_files(targets: list[str]) -> list[Path]:
    """Files named directly, plus every .pdf/.docx inside named folders (sorted, not recursive)."""
    files: list[Path] = []
    for t in map(Path, targets):
        files += sorted(f for f in t.iterdir() if f.suffix.lower() in SUPPORTED) if t.is_dir() else [t]
    return files


def cmd_ingest(args, cfg) -> int:
    files = collect_files([args.path])
    if not files:
        print(f"no .pdf/.docx files found in {args.path}", file=sys.stderr)
        return 1
    st = open_stack(cfg, ROOT, assume_yes=args.yes)
    try:
        return ingest_files(files, cfg, st, args.verbose)
    finally:
        st.close()


def ingest_files(files: list[Path], cfg: dict, st: Stack, verbose: bool = False) -> int:
    """Ingest each file and print one report line per file; exit code 1 if any failed."""
    failed = 0
    for f in files:
        r = ingest_file(f, cfg, st.store, st.index, st.embedder, st.index_path,
                        progress=(lambda m: print("   " + m)) if verbose else None)
        line = f"[{r.status}] {r.file_name}"
        if r.status == "failed":
            failed += 1
            line += f" - {r.message}"
        elif r.status == "skipped_duplicate":
            line += f" - {r.message}"
        else:
            line += (f": {r.pages_total} pages, {r.pages_with_text} with text, {r.pages_flagged} flagged, "
                     f"{r.pages_duplicate} duplicate, {r.chunks_created} chunks, {r.seconds:.1f}s")
            if r.message:
                line += f" ({r.message})"
        print(line)
        for page_no, why in r.flagged_pages:
            print(f"      flagged page {page_no}: {why}")
        for w in r.warnings:
            print(f"      warning: {w}")
        if r.duplicate_pages:
            print("      duplicate pages (not indexed): "
                  + ", ".join(f"p.{p}=p.{orig}" for p, orig in r.duplicate_pages))
    return 1 if failed else 0


def stored_version(index_dir: Path) -> int | None:
    """Schema version of an existing index folder (SQLite user_version, else manifest); None if empty.

    Read directly, without MetadataStore, because the store refuses to open an old version.
    """
    db, manifest = index_dir / DB_FILE, index_dir / "manifest.json"
    if db.is_file():
        con = sqlite3.connect(db)
        try:
            return con.execute("PRAGMA user_version").fetchone()[0] or 1   # v0.1 never set it
        finally:
            con.close()
    if manifest.is_file():
        try:
            return int(json.loads(manifest.read_text(encoding="utf-8")).get("index_version", 1))
        except (ValueError, TypeError):
            return 1
    return None


def cmd_rebuild(args, cfg) -> int:
    """Move the current index folder aside (never delete it) and ingest the given files into a fresh one."""
    files = collect_files(args.paths)
    if not files:
        print(f"no .pdf/.docx files found in {', '.join(args.paths)}", file=sys.stderr)
        return 1
    index_dir = Path(ROOT) / cfg["paths"]["index_dir"]
    if index_dir.is_dir() and any(index_dir.iterdir()):
        found = stored_version(index_dir) or 1
        backup = index_dir.with_name(f"{index_dir.name}.v{found}.bak")
        n = 2
        while backup.exists():
            backup = index_dir.with_name(f"{index_dir.name}.v{found}.bak{n}")
            n += 1
        ok = args.yes
        if not ok and sys.stdin.isatty():
            ok = input(f"Move {index_dir} (schema {found}) to {backup.name} and re-ingest {len(files)} file(s)? "
                       "[y/N] ").strip().lower() == "y"
        if not ok:
            print("not rebuilt (answer y, or pass --yes)", file=sys.stderr)
            return 1
        index_dir.rename(backup)
        print(f"old index kept at {backup}")
    st = open_stack(cfg, ROOT, assume_yes=args.yes)
    try:
        return ingest_files(files, cfg, st, args.verbose)
    finally:
        st.close()


def cmd_compact(args, cfg) -> int:
    """Rebuild the index without soft-deleted vectors and purge their rows (asks first unless --yes)."""
    st = open_stack(cfg, ROOT, load_embedder=False, assume_yes=args.yes)
    try:
        ok = args.yes
        if not ok and sys.stdin.isatty():
            ok = input("Compact the index (rewrite it without deleted vectors)? [y/N] ").strip().lower() == "y"
        if not ok:
            print("not compacted (answer y, or pass --yes)", file=sys.stderr)
            return 1
        _, r = compact(cfg, st.store, st.index, st.index_path)
    finally:
        st.close()
    print(f"vectors: {r['vectors_before']} -> {r['vectors_after']}; index file: {r['bytes_before'] / 1e6:.2f} -> "
          f"{r['bytes_after'] / 1e6:.2f} MB; {r['chunk_rows_removed']} deleted chunk rows and "
          f"{r['documents_cleaned']} retired document(s) cleaned")
    return 0


def cmd_search(args, cfg) -> int:
    st = open_stack(cfg, ROOT, assume_yes=args.yes)
    filters = None
    if args.unit or args.file:
        doc_ids = None
        if args.file:
            docs = [st.store.find_active_by_name(f) for f in args.file]
            missing = [f for f, d in zip(args.file, docs) if d is None]
            if missing:
                print(f"warning: not indexed: {', '.join(missing)}", file=sys.stderr)
            doc_ids = [d.doc_id for d in docs if d is not None]
        filters = SearchFilters(doc_ids=doc_ids, units=args.unit)
    try:
        results = search(args.query, args.k, cfg, st.store, st.index, st.embedder, filters=filters)
    except EmptyQuery as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        st.close()
    if not results:
        print("no results (the index is empty, or nothing indexed matches)")
        return 0
    for r in results:
        c = r.chunk
        print(f"#{r.rank}  score {r.score:.3f}  {c.file_name}  {location(c)}")
        print(f"    section: {c.section_heading or '-'}")
        print(f"    {r.snippet}")
    return 0


def cmd_stats(args, cfg) -> int:
    st = open_stack(cfg, ROOT, load_embedder=False, assume_yes=args.yes)
    s = st.store.stats()
    st.close()
    size = st.index_path.stat().st_size if st.index_path.is_file() else 0
    m = st.index.manifest
    print(f"documents: {s['documents']} active, {s['documents_replaced']} replaced, "
          f"{s['documents_pending']} pending, {s['documents_abandoned']} abandoned")
    print(f"pages:     {s['pages_total']} total, {s['pages_with_text']} with text, {s['pages_flagged']} flagged, "
          f"{s['pages_duplicate']} duplicate")
    print(f"chunks:    {s['chunks_active']} active, {s['chunks_deleted']} soft-deleted, {s['chunks_pending']} pending")
    print(f"index:     {len(st.index)} vectors, dim {m.dimension}, {m.space}, {size / 1e6:.2f} MB on disk")
    print(f"model:     {m.model_name} @ {(m.model_revision or '-')[:8]}  (index created {m.created_at})")
    for p in s["flagged_pages"]:
        print(f"  flagged: {p['file_name']} page {p['page_no']}: {p['status']} - {p['reason']}")
    for p in s["duplicate_pages"]:
        print(f"  duplicate: {p['file_name']} page {p['page_no']} = page {p['duplicate_of']}")
    return 0


def cmd_chunks(args, cfg) -> int:
    """Print the chunks of one file so they can be inspected by eye."""
    path = Path(args.file)
    try:
        pages = mark_duplicates(load_document(path, cfg), cfg)
    except CornerstoneError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    chunks = chunk_pages(pages, 0, path.name, cfg, load_token_counter(cfg))
    flagged = [p for p in pages if p.status != "ok"]
    print(f"{path.name}: {len(pages)} pages, {len(flagged)} flagged, {len(chunks)} chunks")
    for p in flagged:
        print(f"  flagged page {p.page_no}: {p.status} - {p.reason}")
    for c in chunks:
        body = c.text.replace("\n", " / ")
        print(f"[{c.chunk_index:03d}] {location(c):<10} {c.token_count:>3} tok | {c.section_heading or '-'}")
        print(f"      {body if args.full else body[:160]}")
    if chunks:
        toks = [c.token_count for c in chunks]
        print(f"tokens: min {min(toks)}  median {int(statistics.median(toks))}  max {max(toks)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cornerstone")
    ap.add_argument("--config", help="path to config.yaml (default: repo config.yaml)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        p = sub.add_parser(name, help=help_)
        p.set_defaults(func=fn)
        return p

    p = add("ingest", cmd_ingest, "index a file or every .pdf/.docx in a folder")
    p.add_argument("path")
    p.add_argument("--yes", action="store_true", help="discard interrupted ingests without asking")
    p.add_argument("-v", "--verbose", action="store_true", help="show progress per file")
    p = add("search", cmd_search, "search the index")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=None, help="number of results (default from config)")
    p.add_argument("--unit", action="append", help='only this unit, e.g. --unit "Unit 4" (repeatable)')
    p.add_argument("--file", action="append", help="only this indexed file name (repeatable)")
    p.add_argument("--yes", action="store_true")
    p = add("stats", cmd_stats, "show index and ingestion statistics")
    p.add_argument("--yes", action="store_true")
    p = add("rebuild", cmd_rebuild, "build a fresh index from files (old index folder kept as *.v<N>.bak)")
    p.add_argument("paths", nargs="+")
    p.add_argument("--yes", action="store_true", help="do not ask before moving the old index aside")
    p.add_argument("-v", "--verbose", action="store_true")
    p = add("compact", cmd_compact, "rewrite the index without deleted vectors; purge their rows and images")
    p.add_argument("--yes", action="store_true")
    p = add("chunks", cmd_chunks, "print the chunks of one file (debug)")
    p.add_argument("file")
    p.add_argument("--full", action="store_true")

    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    if args.cmd == "search" and args.k is None:
        args.k = cfg["search"]["default_k"]
    try:
        return args.func(args, cfg)
    except CornerstoneError as e:
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
