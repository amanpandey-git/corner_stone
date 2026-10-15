"""Retrieval quality on labelled questions: hit@5, MRR, per-question table, end-to-end latency.

Input: eval/questions.jsonl, one JSON object per line. Three shapes (format: eval/QUESTIONS_FORMAT.md):
    {"id": 1, "split": "dev", "question": "What is ...?", "file": "Unit 3_Memory management.pdf", "pages": [23]}
    {"id": 46, "split": "test", "question": "...", "targets": [{"file": "A.pdf", "pages": [5]},
                                                              {"file": "B.pdf", "pages": [9]}]}   # cross-file
    {"id": 51, "split": "test", "question": "...", "answerable": false, "note": "why the notes lack it"}
"pages" is always a list (several pages when the answer spans slides). Optional
"equivalent_pages" (per target): pages holding a verbatim duplicate of the answer slide (Unit 4 repeats its
own slides 2-26 as 27-51); a result covering any of them counts as a hit, but they are not part of the
multi-page statistics. "id" and "split" are optional, but if one line has them, every line must.

Scoring (fixed before any results were seen; do not change after looking at them):
  * A result "covers" a page if it is from that target's file and the page lies inside the chunk's
    page range (page_start..page_end).
  * hit@5   : any labelled page (of any target) is covered by one of the top-5 results.
  * MRR     : 1 / rank of the first result (within top-10) covering any labelled page, else 0.
  * pages found (multi-page and cross-file questions, reported separately): labelled pages covered by the top 5.
  * cross-file all-files@5 (reported separately): every target file has a labelled page in the top 5.
  * Unanswerable questions (answerable: false) are not retrieval questions; they are counted and skipped
    here and scored in Phase 2 (abstention rate).
  * The three questions used by hand in Step 5 are excluded from scoring (listed in the output).
  * Nothing (chunking, ef_search, k) is tuned on the test split.

    PYTHONPATH=src python eval/retrieval_eval.py --check                    # validate only (no model needed)
    PYTHONPATH=src python eval/retrieval_eval.py --split dev                # evaluate the dev split
    PYTHONPATH=src python eval/retrieval_eval.py --split test --label "v0.1 baseline" --out eval/results/x.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

QUESTIONS = ROOT / "eval" / "questions.jsonl"
SAMPLES = ROOT / "samples"
RESULTS_DIR = ROOT / "eval" / "results"
SPLITS = ("dev", "test")
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


def _int_list(x) -> bool:
    return isinstance(x, list) and all(isinstance(p, int) and not isinstance(p, bool) for p in x)


# ------------------------------------------------------------------ validation
def validate_questions(path: Path, samples_dir: Path = SAMPLES) -> tuple[list[dict], list[str]]:
    """Return (questions, errors). Any error means the file must not be scored.

    Each returned question has: id, split, question, answerable, targets (list of
    {file, pages, equivalent_pages}); single-target questions also keep file/pages/equivalent_pages.
    Rejects: bad JSON, missing/empty fields, 'pages' not a non-empty list of ints, files that are not in
    samples/ (or not PDFs), pages outside 1..page_count, duplicate questions or ids, a bad split,
    cross-file questions with fewer than 2 distinct files, unanswerable questions that carry pages,
    and id/split present on some lines but not on others.
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

    def check_target(t, where: str) -> dict | None:
        if not isinstance(t, dict):
            errors.append(f"{where}: each target must be an object with 'file' and 'pages'")
            return None
        f, pages, eq = t.get("file"), t.get("pages"), t.get("equivalent_pages", [])
        if not isinstance(f, str) or not f.strip():
            errors.append(f"{where}: 'file' must be a non-empty string")
            return None
        if not _int_list(pages) or not pages:
            errors.append(f"{where}: 'pages' must be a non-empty list of integers (got {pages!r})")
            return None
        total = n_pages(f)
        if total is None:
            errors.append(f"{where}: file '{f}' not found in samples/ (or not a PDF)")
            return None
        if not _int_list(eq) or set(eq) & set(pages):
            errors.append(f"{where}: 'equivalent_pages' must be a list of integers not already in 'pages'")
            return None
        bad = [p for p in list(pages) + list(eq) if p < 1 or p > total]
        if bad:
            errors.append(f"{where}: page(s) {bad} do not exist in '{f}' (it has {total} pages)")
            return None
        return {"file": f, "pages": sorted(set(pages)), "equivalent_pages": sorted(set(eq))}

    seen: set[str] = set()
    seen_ids: set[int] = set()
    with_meta = without_meta = 0
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
        answerable = obj.get("answerable", True)
        if not isinstance(answerable, bool):
            errors.append(f"{where}: 'answerable' must be true or false")
            continue
        if answerable:
            required = ("question", "targets") if "targets" in obj else ("question", "file", "pages")
        else:
            required = ("question",)
        missing = [k for k in required if k not in obj]
        if missing:
            errors.append(f"{where}: missing field(s) {missing}")
            continue
        q = obj["question"]
        if not isinstance(q, str) or not q.strip():
            errors.append(f"{where}: 'question' must be a non-empty string")
            continue
        qid, split = obj.get("id"), obj.get("split")
        if "id" in obj or "split" in obj:
            with_meta += 1
            if not isinstance(qid, int) or isinstance(qid, bool) or qid in seen_ids:
                errors.append(f"{where}: 'id' must be a unique integer (got {qid!r})")
                continue
            if split not in SPLITS:
                errors.append(f"{where}: 'split' must be one of {SPLITS} (got {split!r})")
                continue
            seen_ids.add(qid)
        else:
            without_meta += 1

        if not answerable:
            if any(k in obj for k in ("file", "pages", "targets", "equivalent_pages")):
                errors.append(f"{where}: an unanswerable question must not have file/pages/targets")
                continue
            targets: list[dict] = []
        elif "targets" in obj:
            raw_t = obj["targets"]
            if any(k in obj for k in ("file", "pages", "equivalent_pages")):
                errors.append(f"{where}: use either 'targets' or 'file'/'pages', not both")
                continue
            if not isinstance(raw_t, list) or len(raw_t) < 2:
                errors.append(f"{where}: 'targets' must be a list of at least 2 targets (cross-file)")
                continue
            targets = [check_target(t, f"{where} target {i + 1}") for i, t in enumerate(raw_t)]
            if any(t is None for t in targets):
                continue
            if len({t["file"] for t in targets}) != len(targets):
                errors.append(f"{where}: cross-file targets must name different files")
                continue
        else:
            t = check_target(obj, where)
            if t is None:
                continue
            targets = [t]

        key = _norm(q)
        if key in seen:
            errors.append(f"{where}: duplicate question")
            continue
        seen.add(key)
        item = {"id": qid, "split": split, "question": q.strip(), "answerable": answerable,
                "targets": targets, "note": obj.get("note", "")}
        if len(targets) == 1:
            item.update(targets[0])
        questions.append(item)
    if with_meta and without_meta:
        errors.append(f"'id'/'split' present on {with_meta} line(s) but missing on {without_meta}")
    if not questions and not errors:
        errors.append("no questions found")
    return questions, errors


# ------------------------------------------------------------------ scoring
def covers(chunk, file: str, page: int) -> bool:
    return (chunk.file_name == file and chunk.page_start is not None
            and chunk.page_start <= page <= chunk.page_end)


def score_targets(results: list, targets: list[dict]) -> dict:
    """hit@5, reciprocal rank (top 10), pages found (top 5) and files found (top 5) for one question.

    Rank/hit use each target's ``pages`` plus ``equivalent_pages`` (verbatim duplicates);
    pages_found uses ``pages`` only and lists (file, page) pairs.
    """
    accept = [(t["file"], p) for t in targets for p in list(t["pages"]) + list(t.get("equivalent_pages", []))]
    rank = next((i + 1 for i, r in enumerate(results[:MRR_K])
                 if any(covers(r.chunk, f, p) for f, p in accept)), None)
    found = [(t["file"], p) for t in targets for p in t["pages"]
             if any(covers(r.chunk, t["file"], p) for r in results[:HIT_K])]
    files_found = sorted({f for f, _ in found} | {
        t["file"] for t in targets for p in t.get("equivalent_pages", [])
        if any(covers(r.chunk, t["file"], p) for r in results[:HIT_K])})
    return {"rank": rank, "hit": rank is not None and rank <= HIT_K,
            "rr": 1.0 / rank if rank else 0.0, "pages_found": found, "files_found": files_found}


def score_question(results: list, file: str, pages: list[int], equivalent_pages: list[int] = ()) -> dict:
    """Single-file wrapper of score_targets (pages_found as plain page numbers)."""
    s = score_targets(results, [{"file": file, "pages": pages, "equivalent_pages": list(equivalent_pages)}])
    return {"rank": s["rank"], "hit": s["hit"], "rr": s["rr"], "pages_found": [p for _, p in s["pages_found"]]}


def summarise(rows: list[dict]) -> dict:
    """rows need hit, rr, pages (all labelled pages) and pages_found; cross-file rows also n_files/files_found."""
    n = len(rows)
    multi = [r for r in rows if len(r["pages"]) > 1]
    cross = [r for r in rows if r.get("n_files", 1) > 1]
    return {
        "n": n,
        "hit_at_5": sum(r["hit"] for r in rows) / n if n else float("nan"),
        "mrr": sum(r["rr"] for r in rows) / n if n else float("nan"),
        "multi_n": len(multi),
        "multi_pages_found": sum(len(r["pages_found"]) for r in multi),
        "multi_pages_total": sum(len(r["pages"]) for r in multi),
        "cross_n": len(cross),
        "cross_all_files": sum(len(r["files_found"]) == r["n_files"] for r in cross),
    }


def describe(questions: list[dict]) -> str:
    ans = [q for q in questions if q["answerable"]]
    multi = [q for q in ans if sum(len(t["pages"]) for t in q["targets"]) > 1]
    cross = [q for q in ans if len(q["targets"]) > 1]
    return (f"{len(questions)} questions: {len(ans)} answerable ({len(multi)} multi-page, {len(cross)} cross-file), "
            f"{len(questions) - len(ans)} unanswerable")


# ------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate questions.jsonl and exit")
    ap.add_argument("--questions", default=str(QUESTIONS))
    ap.add_argument("--split", choices=("all",) + SPLITS, default="all")
    ap.add_argument("--label", default="", help="what is being measured, e.g. 'v0.1 baseline'")
    ap.add_argument("--out", default=None, help="result file (default eval/results/retrieval_eval_<split>.md)")
    ap.add_argument("--config", default=str(ROOT / "config.yaml"), help="config variant (ablations)")
    ap.add_argument("--retriever", choices=("search", "keyword"), default="search",
                    help="search = the real search(); keyword = FTS5 only (reference row)")
    args = ap.parse_args(argv)

    questions, errors = validate_questions(Path(args.questions))
    if errors:
        print(f"{args.questions}: {len(errors)} problem(s), nothing scored:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"all: {describe(questions)}")
    for s in SPLITS:
        part = [q for q in questions if q["split"] == s]
        if part:
            print(f"{s}: {describe(part)}")
    if args.split != "all":
        if any(q["split"] is None for q in questions):
            print("error: --split needs 'id' and 'split' on every line", file=sys.stderr)
            return 1
        questions = [q for q in questions if q["split"] == args.split]
    unanswerable = [q for q in questions if not q["answerable"]]
    questions = [q for q in questions if q["answerable"]]
    excluded_keys = {_norm(q) for q in STEP5_QUESTIONS}
    excluded = [q for q in questions if _norm(q["question"]) in excluded_keys]
    scored = [q for q in questions if _norm(q["question"]) not in excluded_keys]
    print(f"split {args.split}: {len(scored)} to score; {len(excluded)} excluded (Step 5 manual questions); "
          f"{len(unanswerable)} unanswerable skipped (Phase 2 metric)")
    if args.check:
        return 0
    if len(scored) < 15:
        print(f"warning: only {len(scored)} scored questions; numbers are weak evidence", file=sys.stderr)
    if not scored:
        return 1

    import yaml
    from cornerstone.embeddings import Embedder
    from cornerstone.index.hnsw_index import HNSWIndex
    from cornerstone.index.metadata_store import MetadataStore
    from cornerstone.search import search

    from cornerstone import SearchResult
    from cornerstone.hybrid import keyword_search

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    def retrieve(q: str) -> list:
        if args.retriever == "search":
            return search(q, MRR_K, cfg, store, index, emb)
        hits = keyword_search(q, MRR_K, store)
        chunks = store.get_chunks([c for c, _ in hits])
        return [SearchResult(chunks[c], s, i + 1, "") for i, (c, s) in enumerate(hits)]
    index_dir = ROOT / cfg["paths"]["index_dir"]
    index = HNSWIndex.load(index_dir / "hnsw.faiss", cfg)
    store = MetadataStore(index_dir / "cornerstone.sqlite")
    emb = Embedder(cfg)
    indexed = {d.file_name for d in store.list_documents("active")}
    not_indexed = sorted({t["file"] for q in scored for t in q["targets"]} - indexed)
    if not_indexed:
        print(f"error: labelled files are not in the index: {not_indexed}. Run ingest first.", file=sys.stderr)
        return 1
    flagged = {(p["file_name"], p["page_no"]) for p in store.stats()["flagged_pages"]}

    retrieve("warm up")
    rows, lat = [], []
    for q in scored:
        t = time.perf_counter()
        res = retrieve(q["question"])
        lat.append((time.perf_counter() - t) * 1000)
        s = score_targets(res, q["targets"])
        top = res[0].chunk if res else None
        labelled = [(tg["file"], p) for tg in q["targets"] for p in tg["pages"]]
        rows.append({**q, **s, "pages": labelled, "n_files": len(q["targets"]),
                     "top": f"{top.file_name} p.{top.page_start}" + (f"-{top.page_end}" if top.page_end != top.page_start else "")
                            if top else "-",
                     "unindexable": [fp for fp in labelled if fp in flagged]})
    sm = summarise(rows)
    lat_p50, lat_p95 = float(np.percentile(lat, 50)), float(np.percentile(lat, 95))

    title = f"# Retrieval evaluation - split `{args.split}`" + (f" - {args.label}" if args.label else "")
    lines = [
        title, "",
        f"Generated {date.today().isoformat()} by `eval/retrieval_eval.py --split {args.split}`. Index: "
        f"{len(indexed)} documents, {len(index)} vectors, model `{cfg['embedding']['model_name']}`, "
        f"ef_search={cfg['hnsw']['ef_search']}, retriever `{args.retriever}`, config `{Path(args.config).name}`. "
        "Nothing was tuned on the test split.", "",
        "## Summary", "",
        "| metric | value |", "|---|---|",
        f"| scored questions | {sm['n']} |",
        f"| **hit@5** | **{sm['hit_at_5']:.3f}** ({sum(r['hit'] for r in rows)}/{sm['n']}) |",
        f"| **MRR** (top-10) | **{sm['mrr']:.3f}** |",
        f"| multi-page questions | {sm['multi_n']}: {sm['multi_pages_found']}/{sm['multi_pages_total']} labelled pages found in top 5 |",
        f"| cross-file questions | {sm['cross_n']}: {sm['cross_all_files']} with every file in top 5 |",
        f"| end-to-end search latency p50 / p95 | {lat_p50:.0f} ms / {lat_p95:.0f} ms (query embedding + HNSW + SQLite, k={MRR_K}) |",
        f"| unanswerable questions in split | {len(unanswerable)} (not scored here; Phase 2 abstention) |",
        "", "Definitions: a result covers a labelled page if it is from that target's file and the page lies inside "
        "the chunk's page range. hit@5 = any labelled page covered in the top 5. MRR = mean of 1/rank of the first "
        "covering result (top 10, else 0).", "",
        "## Excluded from scoring", "",
        "The three questions asked by hand in Step 5 (their results were shown to the author before evaluation):", "",
    ]
    lines += [f"- {q}" for q in STEP5_QUESTIONS]
    if excluded:
        lines += ["", f"{len(excluded)} of them were present in questions.jsonl and were left out."]
    lines += ["", "## Per question", "",
              "| id | question | expected | rank | hit@5 | top result |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        parts = []
        for tg in r["targets"]:
            e = f"{tg['file']} p.{','.join(map(str, tg['pages']))}"
            if tg["equivalent_pages"]:
                e += f" (duplicate on p.{','.join(map(str, tg['equivalent_pages']))})"
            parts.append(e)
        exp = " + ".join(parts)
        note = " (page flagged needs_ocr: not indexable)" if r["unindexable"] else ""
        if len(r["pages"]) > 1:
            note += f" [{len(r['pages_found'])}/{len(r['pages'])} pages in top 5]"
        if r["n_files"] > 1:
            note += f" [{len(r['files_found'])}/{r['n_files']} files in top 5]"
        lines.append(f"| {r['id'] if r['id'] is not None else i} | {r['question']} | {exp}{note} | "
                     f"{r['rank'] or '>10'} | {'yes' if r['hit'] else 'no'} | {r['top']} |")
    misses = [r for r in rows if not r["hit"]]
    lines += ["", f"## Misses ({len(misses)})", ""]
    lines += [f"- {r['question']} (expected {', '.join(f'{f} p.{p}' for f, p in r['pages'])}, got {r['top']})"
              for r in misses] or ["None."]
    out = "\n".join(lines) + "\n"
    out_file = Path(args.out) if args.out else RESULTS_DIR / f"retrieval_eval_{args.split}.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(out, encoding="utf-8")
    print(out)
    print(f"saved to {out_file}")
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
