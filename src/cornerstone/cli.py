"""Command line interface: ingest, search, stats (+ chunks debug).

    python -m cornerstone.cli ingest <file|dir>
    python -m cornerstone.cli search "<query>" --k 5
    python -m cornerstone.cli stats
    python -m cornerstone.cli chunks <file> [--full]
Run with PYTHONPATH=src from the repo root.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from cornerstone import CornerstoneError, EmptyQuery
from cornerstone.chunking import chunk_pages
from cornerstone.embeddings import Embedder, load_token_counter
from cornerstone.index.hnsw_index import HNSWIndex
from cornerstone.index.metadata_store import MetadataStore
from cornerstone.ingest.loader import load_document
from cornerstone.pipeline import ingest_file
from cornerstone.search import search

ROOT = Path(__file__).resolve().parents[2]
INDEX_FILE = "hnsw.faiss"
DB_FILE = "cornerstone.sqlite"
SUPPORTED = {".pdf", ".docx"}


def load_config(path: Path | None = None) -> dict:
    return yaml.safe_load((Path(path) if path else ROOT / "config.yaml").read_text(encoding="utf-8"))


@dataclass
class Stack:
    store: MetadataStore
    index: HNSWIndex
    index_path: Path
    embedder: Embedder | None


def open_stack(cfg: dict, root: Path = ROOT, load_embedder: bool = True, assume_yes: bool = False) -> Stack:
    """Open (or create) store + index under paths.index_dir and verify they agree.

    Raises ModelMismatch if the index was built with other settings. Interrupted ingests found
    by check_sync are shown and discarded only after the user confirms (or --yes); anything
    else out of sync is reported with the way to rebuild. Nothing is repaired silently.
    """
    index_dir = Path(root) / cfg["paths"]["index_dir"]
    index_path = index_dir / INDEX_FILE
    store = MetadataStore(index_dir / DB_FILE)
    index = HNSWIndex.load(index_path, cfg) if index_path.is_file() else HNSWIndex.from_config(cfg)

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


def cmd_ingest(args, cfg) -> int:
    target = Path(args.path)
    files = sorted(f for f in target.iterdir() if f.suffix.lower() in SUPPORTED) if target.is_dir() else [target]
    if not files:
        print(f"no .pdf/.docx files found in {target}", file=sys.stderr)
        return 1
    st = open_stack(cfg, ROOT, assume_yes=args.yes)
    failed = 0
    for f in files:
        r = ingest_file(f, cfg, st.store, st.index, st.embedder, st.index_path,
                        progress=(lambda m: print("   " + m)) if args.verbose else None)
        line = f"[{r.status}] {r.file_name}"
        if r.status == "failed":
            failed += 1
            line += f" - {r.message}"
        elif r.status == "skipped_duplicate":
            line += f" - {r.message}"
        else:
            line += (f": {r.pages_total} pages, {r.pages_with_text} with text, {r.pages_flagged} flagged, "
                     f"{r.chunks_created} chunks, {r.seconds:.1f}s")
            if r.message:
                line += f" ({r.message})"
        print(line)
        for page_no, why in r.flagged_pages:
            print(f"      flagged page {page_no}: {why}")
    return 1 if failed else 0


def cmd_search(args, cfg) -> int:
    st = open_stack(cfg, ROOT, assume_yes=args.yes)
    try:
        results = search(args.query, args.k, cfg, st.store, st.index, st.embedder)
    except EmptyQuery as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
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
    size = st.index_path.stat().st_size if st.index_path.is_file() else 0
    m = st.index.manifest
    print(f"documents: {s['documents']} active, {s['documents_replaced']} replaced, "
          f"{s['documents_pending']} pending, {s['documents_abandoned']} abandoned")
    print(f"pages:     {s['pages_total']} total, {s['pages_with_text']} with text, {s['pages_flagged']} flagged")
    print(f"chunks:    {s['chunks_active']} active, {s['chunks_deleted']} soft-deleted, {s['chunks_pending']} pending")
    print(f"index:     {len(st.index)} vectors, dim {m.dimension}, {m.space}, {size / 1e6:.2f} MB on disk")
    print(f"model:     {m.model_name} @ {(m.model_revision or '-')[:8]}  (index created {m.created_at})")
    for p in s["flagged_pages"]:
        print(f"  flagged: {p['file_name']} page {p['page_no']}: {p['status']} - {p['reason']}")
    return 0


def cmd_chunks(args, cfg) -> int:
    """Print the chunks of one file so they can be inspected by eye."""
    path = Path(args.file)
    try:
        pages = load_document(path, cfg)
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
    p.add_argument("--yes", action="store_true")
    p = add("stats", cmd_stats, "show index and ingestion statistics")
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
