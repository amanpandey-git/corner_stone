"""Command line interface. Step 2: `chunks` debug command. ingest/search/stats come in Step 5."""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import yaml

from cornerstone import CornerstoneError
from cornerstone.chunking import chunk_pages
from cornerstone.embeddings import load_token_counter
from cornerstone.ingest.loader import load_document

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None) -> dict:
    return yaml.safe_load((path or ROOT / "config.yaml").read_text(encoding="utf-8"))


def cmd_chunks(args: argparse.Namespace) -> int:
    """Print the chunks of one file so they can be inspected by eye."""
    cfg = load_config()
    path = Path(args.file)
    try:
        pages = load_document(path, cfg)
    except CornerstoneError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    count = load_token_counter(cfg)
    chunks = chunk_pages(pages, 0, path.name, cfg, count)
    flagged = [p for p in pages if p.status != "ok"]
    print(f"{path.name}: {len(pages)} pages, {len(flagged)} flagged, {len(chunks)} chunks")
    for p in flagged:
        print(f"  flagged page {p.page_no}: {p.status} - {p.reason}")
    for c in chunks:
        where = (f"p{c.page_start}" if c.page_start == c.page_end else f"p{c.page_start}-{c.page_end}") \
            if c.page_start is not None else f"para {c.para_start}-{c.para_end}"
        body = c.text.replace("\n", " / ")
        print(f"[{c.chunk_index:03d}] {where:<9} {c.token_count:>3} tok | {c.section_heading or '-'}")
        print(f"      {body if args.full else body[:160]}")
    if chunks:
        toks = [c.token_count for c in chunks]
        print(f"tokens: min {min(toks)}  median {int(statistics.median(toks))}  max {max(toks)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cornerstone")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chunks", help="print the chunks of one file (debug)")
    c.add_argument("file")
    c.add_argument("--full", action="store_true", help="print full chunk text")
    c.set_defaults(func=cmd_chunks)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
