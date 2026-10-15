import sys
from types import SimpleNamespace as NS

from cornerstone.answer import Source, finalise

from conftest import ROOT

sys.path.insert(0, str(ROOT / "eval"))
import answer_eval as ae  # noqa: E402

FILE = "Unit 4_Disk.pdf"


def q(id_, answerable=True, pages=(10,)):
    return {"id": id_, "question": f"q{id_}", "answerable": answerable,
            "targets": [{"file": FILE, "pages": list(pages), "equivalent_pages": []}] if answerable else []}


def ans(raw, unsupported=None, ttft=500.0, cached=False, pages=(10, 12)):
    sources = [Source(i, i, 1, FILE, p, p, "s", "text") for i, p in enumerate(pages, 1)]
    a = finalise("q", "concise", raw, sources, ttft_ms=ttft, cached=cached, top_vector_score=0.7)
    a.unsupported = unsupported
    return a


def test_score_answer_faithful_and_right_page():
    r = ae.score_answer(ans("Seek time is head movement [1]. SCAN sweeps [2].", unsupported=[]), q(1))
    assert r["faithful"] and r["correct_page"] and r["n_citations"] == 2 and r["checked"]


def test_unsupported_or_uncited_is_unfaithful():
    r = ae.score_answer(ans("Seek time is head movement [1]. SCAN sweeps [2].", unsupported=[1]), q(1))
    assert r["faithful"] is False and r["unsupported"] == 1
    r = ae.score_answer(ans("Seek time is head movement [1]. The disk spins very fast always.", unsupported=[]), q(1))
    assert r["faithful"] is False and r["uncited"] == 1


def test_wrong_page_and_unchecked():
    r = ae.score_answer(ans("SCAN sweeps across the disk [2].", unsupported=None), q(1))
    assert r["correct_page"] is False and r["checked"] is False and r["faithful"] is None


def test_summary_counts_abstention_and_ttft():
    rows = [ae.score_answer(ans("Seek time is head movement [1].", unsupported=[]), q(1)),
            ae.score_answer(ans("Seek is movement [1]. Rotation is latency [2].", unsupported=[1], cached=True), q(2)),
            ae.score_answer(ans("NOT_IN_NOTES"), q(3)),                              # false abstention
            ae.score_answer(ans("NOT_IN_NOTES"), q(4, answerable=False)),
            ae.score_answer(ans("Football is a sport played widely [1].", unsupported=[0]), q(5, answerable=False))]
    sm = ae.summarise(rows)
    assert sm["n_answerable"] == 3 and sm["n_unanswerable"] == 2
    assert sm["abstained_unanswerable"] == 1 and sm["false_abstentions"] == 1
    assert sm["citations"] == 4 and sm["unsupported"] == 2 and sm["citation_accuracy"] == 0.5
    assert sm["faithful"] == 1 and sm["checked"] == 3
    assert sm["ttft_n"] == 4 and sm["ttft_p50"] == 500.0      # the cached answer is not timed; model abstentions are


def test_report_renders_partial_and_spotcheck():
    rows = [ae.score_answer(ans("Seek time is head movement [1].", unsupported=[]), q(1)),
            ae.score_answer(ans("NOT_IN_NOTES"), q(4, answerable=False))]
    answers = [ans("Seek time is head movement [1].", unsupported=[]), ans("NOT_IN_NOTES")]
    cfg = {"llm": {"provider": "groq", "groq": {"model": "m1"}, "gemini": {"model": "m2"}},
           "answer": {"judge_provider": "gemini", "k": 5, "min_vector_score": 0.0}}
    args = NS(split="dev", label="x", mode="concise", provider=None, config="config.yaml")
    summary, spot = ae.report(rows, answers, ae.summarise(rows), args, cfg, partial="LLMRateLimited: x")
    assert "PARTIAL RUN" in summary and "abstention on unanswerable** | **1/1**" in summary
    assert "## 1. q" in spot and "Seek time" in spot
