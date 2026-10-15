"""Quiz quality: share of valid questions and of correct answers supported by their cited slide.

Definitions (ARCHITECTURE.md 12.1; fixed before the first run):
  * valid      = questions that pass validation (pydantic + rules) / items the model returned.
  * supported  = valid questions whose "question + correct option" the judge finds stated by the cited slide /
                 valid questions the judge could check.
One quiz of --n questions per unit found in the index (seed 0), so the run is reproducible and cached.

    PYTHONPATH=src python eval/quiz_eval.py            # writes eval/results/quiz_eval.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", default=str(ROOT / "eval" / "results" / "quiz_eval.md"))
    args = ap.parse_args(argv)

    from cornerstone import LLMError, SearchFilters
    from cornerstone.citations import Citation, check_citations
    from cornerstone.cli import load_config, open_stack
    from cornerstone.llm import make_provider
    from cornerstone.quiz import generate_quiz

    cfg = load_config()
    gen, judge = make_provider(cfg), make_provider(cfg, cfg["answer"]["judge_provider"])
    st = open_stack(cfg, ROOT, load_embedder=False)
    rows, lines = [], []
    try:
        units = sorted({d.unit for d in st.store.list_documents("active") if d.unit})
        for unit in units:
            try:
                quiz = generate_quiz(cfg, st.store, gen, SearchFilters(units=[unit]), n=args.n, seed=0)
            except LLMError as e:
                print(f"{unit}: stopped ({type(e).__name__}: {e})", file=sys.stderr)
                break
            cits = [Citation(f"{q.mcq.question} Answer: {q.mcq.options[q.mcq.answer]}.", [1]) for q in quiz.questions]
            bad = []
            for c, q in zip(cits, quiz.questions):        # one judge call per question: each cites its own slide
                try:
                    r = check_citations([c], {1: q.source.text}, judge, cfg)
                except LLMError:
                    r = None
                bad.append(None if r is None else bool(r))
            row = {"unit": unit, "generated": quiz.generated, "valid": len(quiz.questions), "attempts": quiz.attempts,
                   "checked": sum(b is not None for b in bad), "unsupported": sum(bool(b) for b in bad),
                   "rejected": quiz.rejected}
            rows.append(row)
            print(f"{unit}: {row['valid']}/{row['generated']} valid, {row['unsupported']} unsupported, "
                  f"{row['attempts']} call(s)", flush=True)
            for q, b in zip(quiz.questions, bad):
                mark = "not checked" if b is None else ("UNSUPPORTED" if b else "supported")
                lines.append(f"- {unit} | {q.mcq.question} -> **{q.mcq.options[q.mcq.answer]}** "
                             f"({q.source.label()}; judge: {mark})")
    finally:
        st.close()
    if not rows:
        return 1
    g = sum(r["generated"] for r in rows)
    v = sum(r["valid"] for r in rows)
    c = sum(r["checked"] for r in rows)
    u = sum(r["unsupported"] for r in rows)
    out = [f"# Quiz evaluation", "",
           f"Generated {date.today().isoformat()} by `eval/quiz_eval.py --n {args.n}` (one quiz per unit, seed 0). "
           f"Generator `{cfg['llm'][cfg['llm']['provider']]['model']}`, judge "
           f"`{cfg['llm'][cfg['answer']['judge_provider']]['model']}`.", "",
           "| metric | value |", "|---|---|",
           f"| **valid questions** (target >= 95%) | **{v / g:.1%}** ({v}/{g}) |" if g else "| valid questions | - |",
           f"| answer supported by its cited slide | {(c - u) / c:.1%} ({c - u}/{c} checked) |" if c else "| supported | - |",
           "", "| unit | generated | valid | calls | unsupported | rejected reasons |", "|---|---|---|---|---|---|"]
    out += [f"| {r['unit']} | {r['generated']} | {r['valid']} | {r['attempts']} | {r['unsupported']} | "
            f"{'; '.join(r['rejected']) or '-'} |" for r in rows]
    out += ["", "## Questions", ""] + lines
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:9]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
