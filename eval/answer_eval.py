"""Answer quality on labelled questions: citation accuracy, faithfulness, abstention, time to first token.

Definitions (ARCHITECTURE.md 11.4; fixed before the first run, do not change after looking at results):
  * citation accuracy   = supported citations / all citations, over answered questions whose citations the
                          judge could check (judge: does the cited slide text state or directly imply the sentence?).
  * faithfulness        = answered questions whose every factual sentence is cited, no citation is unsupported and
                          no invalid [n] was produced / answered questions that could be checked.
  * correct page        = answered answerable questions citing at least one labelled page (no judge needed).
  * abstention          = unanswerable questions answered "Not in your notes." / unanswerable questions.
  * false abstention    = answerable questions answered "Not in your notes." / answerable questions.
  * time to first token = p50 / p95 over live (not cached) answers: question submitted -> first model text.
The three Step 5 questions are excluded, as in retrieval_eval.py. Calls are paced by the provider's rate limiter;
a provider failure after the retry cap stops the run and the partial results are written, marked PARTIAL.

    PYTHONPATH=src python eval/answer_eval.py --split dev                    # tuning split
    PYTHONPATH=src python eval/answer_eval.py --split dev --limit 5          # quick check
    PYTHONPATH=src python eval/answer_eval.py --split test --label "Phase 2"  # once, logged in NOTES.md
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
sys.path.insert(0, str(ROOT / "eval"))

from retrieval_eval import QUESTIONS, STEP5_QUESTIONS, _norm, validate_questions  # noqa: E402

RESULTS_DIR = ROOT / "eval" / "results"
SPOT_N = 20


def cites_labelled_page(answer, targets: list[dict]) -> bool:
    """True if any cited source covers a labelled page (or a verbatim duplicate page) of any target."""
    accept = [(t["file"], p) for t in targets for p in list(t["pages"]) + list(t.get("equivalent_pages", []))]
    return any(s.file_name == f and s.page_start is not None and s.page_start <= p <= (s.page_end or s.page_start)
               for s in answer.cited_sources() for f, p in accept)


def score_answer(answer, question: dict) -> dict:
    """Per-question numbers from one final Answer (pure function; no model calls)."""
    row = {"id": question["id"], "question": question["question"], "answerable": question["answerable"],
           "abstained": answer.abstained, "reason": answer.abstain_reason, "top_vector": answer.top_vector_score,
           "n_citations": len(answer.citations), "unsupported": None, "faithful": None, "checked": False,
           "correct_page": None, "uncited": len(answer.uncited_sentences), "invalid": len(answer.invalid_refs),
           "ttft_ms": answer.ttft_ms, "cached": answer.cached}
    if answer.abstained:
        return row
    if answer.unsupported is not None:
        row["checked"] = True
        row["unsupported"] = len(answer.unsupported)
        row["faithful"] = not answer.unsupported and not answer.uncited_sentences and not answer.invalid_refs
    if question["answerable"]:
        row["correct_page"] = cites_labelled_page(answer, question["targets"])
    return row


def summarise(rows: list[dict]) -> dict:
    ans = [r for r in rows if r["answerable"]]
    unans = [r for r in rows if not r["answerable"]]
    answered = [r for r in rows if not r["abstained"]]
    checked = [r for r in answered if r["checked"]]
    n_cit = sum(r["n_citations"] for r in checked)
    n_bad = sum(r["unsupported"] for r in checked)
    answered_ans = [r for r in ans if not r["abstained"]]
    live = [r["ttft_ms"] for r in rows if r["ttft_ms"] is not None and not r["cached"]]
    pct = lambda xs, q: float(np.percentile(xs, q)) if xs else None   # noqa: E731
    return {
        "n": len(rows), "n_answerable": len(ans), "n_unanswerable": len(unans),
        "answered": len(answered), "checked": len(checked), "unchecked": len(answered) - len(checked),
        "citations": n_cit, "unsupported": n_bad,
        "citation_accuracy": (n_cit - n_bad) / n_cit if n_cit else None,
        "faithful": sum(bool(r["faithful"]) for r in checked),
        "faithfulness": sum(bool(r["faithful"]) for r in checked) / len(checked) if checked else None,
        "correct_page": sum(bool(r["correct_page"]) for r in answered_ans),
        "correct_page_rate": sum(bool(r["correct_page"]) for r in answered_ans) / len(answered_ans) if answered_ans else None,
        "abstained_unanswerable": sum(r["abstained"] for r in unans),
        "false_abstentions": sum(r["abstained"] for r in ans),
        "ttft_n": len(live), "ttft_p50": pct(live, 50), "ttft_p95": pct(live, 95),
    }


def _f(x, pct=False) -> str:
    if x is None:
        return "-"
    return f"{x:.1%}" if pct else f"{x:.0f}"


def report(rows, answers, sm, args, cfg, partial: str | None) -> tuple[str, str]:
    """(summary markdown, spot-check markdown)."""
    prov = cfg["llm"][args.provider or cfg["llm"]["provider"]]["model"]
    judge = cfg["llm"][cfg["answer"]["judge_provider"]]["model"]
    title = f"# Answer evaluation - split `{args.split}`" + (f" - {args.label}" if args.label else "")
    lines = [title, ""]
    if partial:
        lines += [f"**PARTIAL RUN**: stopped after {len(rows)} questions: {partial}", ""]
    lines += [
        f"Generated {date.today().isoformat()} by `eval/answer_eval.py --split {args.split} --mode {args.mode}`. "
        f"Answerer `{prov}`, judge `{judge}`, k={cfg['answer']['k']}, retrieval gate "
        f"min_vector_score={cfg['answer']['min_vector_score']}, config `{Path(args.config).name}`.", "",
        "| metric | value |", "|---|---|",
        f"| questions | {sm['n']} ({sm['n_answerable']} answerable, {sm['n_unanswerable']} unanswerable) |",
        f"| answered (not abstained) | {sm['answered']} ({sm['checked']} checked by the judge, {sm['unchecked']} not checkable) |",
        f"| **citation accuracy** | **{_f(sm['citation_accuracy'], True)}** ({sm['citations'] - sm['unsupported']}/{sm['citations']} citations supported) |",
        f"| **faithfulness** | **{_f(sm['faithfulness'], True)}** ({sm['faithful']}/{sm['checked']} answers fully cited and supported) |",
        f"| cites a labelled page | {_f(sm['correct_page_rate'], True)} ({sm['correct_page']} answered answerable questions) |",
        f"| **abstention on unanswerable** | **{sm['abstained_unanswerable']}/{sm['n_unanswerable']}** |",
        f"| false abstention on answerable | {sm['false_abstentions']}/{sm['n_answerable']} |",
        f"| **time to first token p50 / p95** | **{_f(sm['ttft_p50'])} ms / {_f(sm['ttft_p95'])} ms** ({sm['ttft_n']} live answers) |",
        "", "## Per question", "",
        "| id | ans? | outcome | top vec | cites | unsupported | uncited | invalid | right page | TTFT ms |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        outcome = f"abstained ({r['reason']})" if r["abstained"] else ("faithful" if r["faithful"] else
                                                                       "answered" if r["faithful"] is None else "unfaithful")
        lines.append(f"| {r['id']} | {'yes' if r['answerable'] else 'no'} | {outcome} | "
                     f"{r['top_vector']:.3f} | {r['n_citations']} | {'-' if r['unsupported'] is None else r['unsupported']} | "
                     f"{r['uncited']} | {r['invalid']} | {'-' if r['correct_page'] is None else ('yes' if r['correct_page'] else 'no')} | "
                     f"{_f(r['ttft_ms'])}{' (cached)' if r['cached'] else ''} |"
                     if r["top_vector"] is not None else
                     f"| {r['id']} | {'yes' if r['answerable'] else 'no'} | {outcome} | - | 0 | - | 0 | 0 | - | - |")
    scores_a = sorted(r["top_vector"] for r in rows if r["answerable"] and r["top_vector"] is not None)
    scores_u = sorted(r["top_vector"] for r in rows if not r["answerable"] and r["top_vector"] is not None)
    lines += ["", "## Top vector score (for the retrieval gate; choose on dev only)", "",
              f"- answerable: min {min(scores_a, default=0):.3f}, values {', '.join(f'{x:.3f}' for x in scores_a[:8])} ...",
              f"- unanswerable: {', '.join(f'{x:.3f}' for x in scores_u)}"]

    spot = [f"# Answers for manual spot check - split `{args.split}`", "",
            "Check each: is every sentence supported by the cited slide? Is anything important missing? Note "
            "disagreements with the judge in NOTES.md.", ""]
    for a, r in list(zip(answers, rows))[:SPOT_N]:
        spot += [f"## {r['id']}. {a.question}", "", f"*{a.mode}; {'abstained: ' + str(a.abstain_reason) if a.abstained else 'answered'}; "
                 f"judge unsupported: {'not checked' if a.unsupported is None else [i + 1 for i in a.unsupported]}*", "",
                 a.text, ""]
        for s in (a.cited_sources() if not a.abstained else a.sources[:3]):
            spot.append(f"- [{s.n}] {s.label()} - {s.section or ''}: {' '.join(s.text.split())[:240]}")
        spot.append("")
    return "\n".join(lines) + "\n", "\n".join(spot) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("dev", "test"), required=True)
    ap.add_argument("--mode", default="concise")
    ap.add_argument("--limit", type=int, default=None, help="first N questions only (quick checks)")
    ap.add_argument("--provider", choices=("groq", "gemini"), default=None)
    ap.add_argument("--label", default="")
    ap.add_argument("--config", default=str(ROOT / "config.yaml"))
    ap.add_argument("--sleep", type=float, default=0.0, help="extra seconds between questions")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    questions, errors = validate_questions(QUESTIONS)
    if errors:
        print(f"questions.jsonl has {len(errors)} problem(s); fix them first", file=sys.stderr)
        return 1
    excluded = {_norm(q) for q in STEP5_QUESTIONS}
    qs = [q for q in questions if q["split"] == args.split and _norm(q["question"]) not in excluded]
    qs.sort(key=lambda q: (not q["answerable"], q["id"]))     # deterministic order
    if args.limit:
        # keep the mix: a few unanswerable questions in every quick run
        a = [q for q in qs if q["answerable"]]
        u = [q for q in qs if not q["answerable"]]
        nu = min(len(u), max(1, args.limit // 4))
        qs = a[: args.limit - nu] + u[:nu]

    from cornerstone import LLMError
    from cornerstone.answer import answer as run_answer
    from cornerstone.cli import load_config, open_stack
    from cornerstone.llm import make_provider

    cfg = load_config(Path(args.config))
    provider = make_provider(cfg, args.provider)
    judge = make_provider(cfg, cfg["answer"]["judge_provider"])
    st = open_stack(cfg, ROOT, for_search=True)
    rows, answers, partial = [], [], None
    t0 = time.time()
    try:
        for i, q in enumerate(qs, 1):
            try:
                a = run_answer(q["question"], args.mode, cfg, st.store, st.index, st.embedder, provider,
                               reranker=st.reranker, judge=judge, check=True)
            except LLMError as e:
                partial = f"{type(e).__name__}: {e}"
                print(f"stopping: {partial}", file=sys.stderr)
                break
            answers.append(a)
            rows.append(score_answer(a, q))
            r = rows[-1]
            status = f"abstained ({r['reason']})" if r["abstained"] else "answered"
            if r["unsupported"] is not None:
                status += f", unsupported {r['unsupported']}"
            print(f"[{i}/{len(qs)}] id {q['id']}: {status}  ({time.time() - t0:.0f} s)", flush=True)
            if args.sleep:
                time.sleep(args.sleep)
    finally:
        st.close()
    if not rows:
        print("nothing answered", file=sys.stderr)
        return 1
    sm = summarise(rows)
    summary, spot = report(rows, answers, sm, args, cfg, partial)
    out = Path(args.out) if args.out else RESULTS_DIR / f"answer_eval_{args.split}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")
    spot_path = out.with_name(out.stem.replace("answer_eval", "answer_spotcheck") + ".md")
    spot_path.write_text(spot, encoding="utf-8")
    raw = out.with_suffix(".jsonl")
    raw.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(summary.split("## Per question")[0])
    print(f"saved {out}, {spot_path.name}, {raw.name}")
    return 0 if not partial else 2


if __name__ == "__main__":
    sys.exit(main())
