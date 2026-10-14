"""Retrieval quality on labelled questions: hit@5, MRR, per-question table, end-to-end latency.

Input: eval/questions.jsonl, one JSON object per line:
    {"question": "What is ...?", "file": "Unit 3_Memory management.pdf", "pages": [23]}
"pages" is always a list (several pages when the answer spans slides).

Scoring (fixed before any results were seen; do not change after looking at them):
  * A result "covers" a page if it is from the labelled file and the page lies inside the chunk's
    page range (page_start..page_end).
  * hit@5   : any labelled page is covered by one of the top-5 results.
  * MRR     : 1 / rank of the first result (within top-10) covering any labelled page, else 0.
  * pages found (multi-page questions, reported separately): labelled pages covered by the top 5.
  * The three questions used by hand in Step 5 are excluded from scoring (listed in the output).
  * Nothing (chunking, ef_search, k) is tuned on these questions.

    PYTHONPATH=src python eval/retrieval_eval.py            # validate, then evaluate
    PYTHONPATH=src python eval/retrieval_eval.py --check    # validate only (no model needed)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

QUESTIONS = ROOT / "eval" / "questions.jsonl"
SAMPLES = ROOT / "samples"
RESULT_FILE = ROOT / "eval" / "results" / "retrieval_eval.md"
HIT_K = 5
MRR_K = 10

# asked by hand during Step 5 (and shown to the user), so they must not count as a result
STEP5_QUESTIONS = (
    "What are the four necessary conditions for deadlock?",
    "What is the difference between a process and a thread?",
    "How does paging avoid external fragmentation?",
)


def _norm(q: str) -> str:
    return " ".join(q.lower().split()).rstrip("?. ")


# ------------------------------------------------------------------ validation
def validate_questions(path: Path, samples_dir: Path = SAMPLES) -> tuple[list[dict], list[str]]:
    """Return (questions, errors). Any error means the file must not be scored.

    Rejects: bad JSON, missing/empty fields, 'pages' not a non-empty list of ints, files that
    are not in samples/ (or not PDFs), pages outside 1..page_count, duplicate questions.
    """
    errors: list[str] = []
    questions: list[dict] = []
    path = Path(path)
    if not path.is_file():
        return [], [f"{path} does not exist"]
    page_counts: dict[str, int | None] = {}

    def n_pages(name: str) -> int | None:
        if name not in page_counts:
            f = Path(samples_dir) / name
            if not f.is_file() or f.suffix.lower() != ".pdf":
                page_counts[name] = None
            else:
                import pymupdf
                with pymupdf.open(f) as d:
                    page_counts[name] = d.page_count
        return page_counts[name]

    seen: set[str] = set()
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        where = f"line {n}"
        try:
            obj = json.loads(raw)
        except ValueError as e:
            errors.append(f"{where}: invalid JSON ({e})")
            continue
        if not isinstance(obj, dict):
            errors.append(f"{where}: expected a JSON object")
            continue
        missing = [k for k in ("question", "file", "pages") if k not in obj]
        if missing:
            errors.append(f"{where}: missing field(s) {missing}")
            continue
        q, f, pages = obj["question"], obj["file"], obj["pages"]
        if not isinstance(q, str) or not q.strip():
            errors.append(f"{where}: 'question' must be a non-empty string")
            continue
        if not isinstance(f, str) or not f.strip():
            errors.append(f"{where}: 'file' must be a non-empty string")
            continue
        if (not isinstance(pages, list) or not pages
                or not all(isinstance(p, int) and not isinstance(p, bool) for p in pages)):
            errors.append(f"{where}: 'pages' must be a non-empty list of integers (got {pages!r})")
            continue
        total = n_pages(f)
        if total is None:
            errors.append(f"{where}: file '{f}' not found in samples/ (or not a PDF)")
            continue
        bad = [p for p in pages if p < 1 or p > total]
        if bad:
            errors.append(f"{where}: page(s) {bad} do not exist in '{f}' (it has {total} pages)")
            continue
        key = _norm(q)
        if key in seen:
            errors.append(f"{where}: duplicate question")
            continue
        seen.add(key)
        questions.append({"question": q.strip(), "file": f, "pages": sorted(set(pages))})
    if not questions and not errors:
        errors.append("no questions found")
    return questions, errors


# ------------------------------------------------------------------ scoring
def covers(chunk, file: str, page: int) -> bool:
    return (chunk.file_name == file and chunk.page_start is not None
            and chunk.page_start <= page <= chunk.page_end)


def score_question(results: list, file: str, pages: list[int]) -> dict:
    """hit@5, reciprocal rank (top 10) and pages found (top 5) for one question."""
    rank = next((i + 1 for i, r in enumerate(results[:MRR_K])
                 if any(covers(r.chunk, file, p) for p in pages)), None)
    found = [p for p in pages if any(covers(r.chunk, file, p) for r in results[:HIT_K])]
    return {"rank": rank, "hit": rank is not None and rank <= HIT_K,
            "rr": 1.0 / rank if rank else 0.0, "pages_found": found}


def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    multi = [r for r in rows if len(r["pages"]) > 1]
    return {
        "n": n,
        "hit_at_5": sum(r["hit"] for r in rows) / n if n else float("nan"),
        "mrr": sum(r["rr"] for r in rows) / n if n else float("nan"),
        "multi_n": len(multi),
        "multi_pages_found": sum(len(r["pages_found"]) for r in multi),
        "multi_pages_total": sum(len(r["pages"]) for r in multi),
    }


# ------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate questions.jsonl and exit")
    ap.add_argument("--questions", default=str(QUESTIONS))
    args = ap.parse_args(argv)

    questions, errors = validate_questions(Path(args.questions))
    if errors:
        print(f"{args.questions}: {len(errors)} problem(s), nothing scored:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    excluded_keys = {_norm(q) for q in STEP5_QUESTIONS}
    excluded = [q for q in questions if _norm(q["question"]) in excluded_keys]
    scored = [q for q in questions if _norm(q["question"]) not in excluded_keys]
    print(f"{len(questions)} questions valid; {len(excluded)} excluded (Step 5 manual questions); "
          f"{len(scored)} to score")
    if args.check:
        return 0
    if len(scored) < 15:
        print(f"warning: only {len(scored)} scored questions (plan: 15-25); numbers are weak evidence",
              file=sys.stderr)
    if not scored:
        return 1

    import yaml
    from cornerstone.embeddings import Embedder
    from cornerstone.index.hnsw_index import HNSWIndex
    from cornerstone.index.metadata_store import MetadataStore
    from cornerstone.search import search

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    index_dir = ROOT / cfg["paths"]["index_dir"]
    index = HNSWIndex.load(index_dir / "hnsw.faiss", cfg)
    store = MetadataStore(index_dir / "cornerstone.sqlite")
    emb = Embedder(cfg)
    indexed = {d.file_name for d in store.list_documents("active")}
    not_indexed = sorted({q["file"] for q in scored} - indexed)
    if not_indexed:
        print(f"error: labelled files are not in the index: {not_indexed}. Run ingest first.", file=sys.stderr)
        return 1
    flagged = {(p["file_name"], p["page_no"]) for p in store.stats()["flagged_pages"]}

    search("warm up", MRR_K, cfg, store, index, emb)
    rows, lat = [], []
    for q in scored:
        t = time.perf_counter()
        res = search(q["question"], MRR_K, cfg, store, index, emb)
        lat.append((time.perf_counter() - t) * 1000)
        s = score_question(res, q["file"], q["pages"])
        top = res[0].chunk if res else None
        rows.append({**q, **s,
                     "top": f"{top.file_name} p.{top.page_start}" + (f"-{top.page_end}" if top.page_end != top.page_start else "")
                            if top else "-",
                     "unindexable": [p for p in q["pages"] if (q["file"], p) in flagged]})
    sm = summarise(rows)
    lat_p50, lat_p95 = float(np.percentile(lat, 50)), float(np.percentile(lat, 95))

    lines = [
        "# Retrieval evaluation (labelled questions)", "",
        f"Generated {date.today().isoformat()} by `eval/retrieval_eval.py`. Index: {len(indexed)} documents, "
        f"{len(index)} vectors, model `{cfg['embedding']['model_name']}`, ef_search={cfg['hnsw']['ef_search']}. "
        "Nothing was tuned on these questions.", "",
        "## Summary", "",
        "| metric | value |", "|---|---|",
        f"| scored questions | {sm['n']} |",
        f"| **hit@5** | **{sm['hit_at_5']:.3f}** ({sum(r['hit'] for r in rows)}/{sm['n']}) |",
        f"| **MRR** (top-10) | **{sm['mrr']:.3f}** |",
        f"| multi-page questions | {sm['multi_n']}: {sm['multi_pages_found']}/{sm['multi_pages_total']} labelled pages found in top 5 |",
        f"| end-to-end search latency p50 / p95 | {lat_p50:.0f} ms / {lat_p95:.0f} ms (query embedding + HNSW + SQLite, k={MRR_K}) |",
        "", "Definitions: a result covers a labelled page if it is from the labelled file and the page lies inside "
        "the chunk's page range. hit@5 = any labelled page covered in the top 5. MRR = mean of 1/rank of the first "
        "covering result (top 10, else 0).", "",
        "## Excluded from scoring", "",
        "The three questions asked by hand in Step 5 (their results were shown to the author before evaluation):", "",
    ]
    lines += [f"- {q}" for q in STEP5_QUESTIONS]
    if excluded:
        lines += ["", f"{len(excluded)} of them were present in questions.jsonl and were left out."]
    lines += ["", "## Per question", "",
              "| # | question | expected | rank | hit@5 | top result |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        exp = f"{r['file']} p.{','.join(map(str, r['pages']))}"
        note = " (page flagged needs_ocr: not indexable)" if r["unindexable"] else ""
        if len(r["pages"]) > 1:
            note += f" [{len(r['pages_found'])}/{len(r['pages'])} pages in top 5]"
        lines.append(f"| {i} | {r['question']} | {exp}{note} | {r['rank'] or '>10'} | "
                     f"{'yes' if r['hit'] else 'no'} | {r['top']} |")
    misses = [r for r in rows if not r["hit"]]
    lines += ["", f"## Misses ({len(misses)})", ""]
    lines += [f"- {r['question']} (expected {r['file']} p.{r['pages']}, got {r['top']})" for r in misses] or ["None."]
    out = "\n".join(lines) + "\n"
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(out, encoding="utf-8")
    print(out)
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
