import json
import sys
from types import SimpleNamespace as NS

import pytest

from conftest import ROOT, SAMPLES

sys.path.insert(0, str(ROOT / "eval"))
import retrieval_eval as ev  # noqa: E402

F5 = "Unit 5_Part 2_System Protection.pdf"          # 28 pages
F4 = "Unit 4_Storage management_ Disk Schduling.pdf"


def write(tmp_path, *objs):
    p = tmp_path / "q.jsonl"
    p.write_text("\n".join(o if isinstance(o, str) else json.dumps(o) for o in objs), encoding="utf-8")
    return p


def test_valid_file_passes_and_pages_are_sorted_unique(tmp_path):
    p = write(tmp_path, {"question": "What is a domain?", "file": F5, "pages": [9, 3, 3]},
              {"question": "Explain SCAN.", "file": F4, "pages": [20]})
    qs, errs = ev.validate_questions(p, SAMPLES)
    assert errs == [] and qs[0]["pages"] == [3, 9] and len(qs) == 2


@pytest.mark.parametrize("obj, needle", [
    ({"question": "q?", "file": F5}, "missing field"),
    ({"file": F5, "pages": [1]}, "missing field"),
    ({"question": "q?", "file": F5, "pages": 3}, "list of integers"),
    ({"question": "q?", "file": F5, "pages": []}, "list of integers"),
    ({"question": "q?", "file": F5, "pages": ["3"]}, "list of integers"),
    ({"question": " ", "file": F5, "pages": [1]}, "non-empty string"),
    ({"question": "q?", "file": "Nope.pdf", "pages": [1]}, "not found in samples"),
    ({"question": "q?", "file": F5, "pages": [29]}, "do not exist"),
    ({"question": "q?", "file": F5, "pages": [0]}, "do not exist"),
    ("{not json", "invalid JSON"),
])
def test_invalid_lines_are_rejected(tmp_path, obj, needle):
    qs, errs = ev.validate_questions(write(tmp_path, obj), SAMPLES)
    assert qs == [] and any(needle in e for e in errs), errs


def test_duplicates_and_missing_file(tmp_path):
    p = write(tmp_path, {"question": "What is X?", "file": F5, "pages": [1]},
              {"question": "what is x", "file": F5, "pages": [2]})
    qs, errs = ev.validate_questions(p, SAMPLES)
    assert len(qs) == 1 and any("duplicate" in e for e in errs)
    assert ev.validate_questions(tmp_path / "ghost.jsonl", SAMPLES)[1]


def r(file, a, b=None):
    return NS(chunk=NS(file_name=file, page_start=a, page_end=b or a))


def test_score_hit_rank_and_pages_found():
    res = [r("other.pdf", 3), r("a.pdf", 10, 12), r("a.pdf", 40)]
    s = ev.score_question(res, "a.pdf", [11, 40, 99])
    assert s["rank"] == 2 and s["hit"] and s["rr"] == 0.5
    assert s["pages_found"] == [11, 40]              # 11 inside chunk 10-12; 99 not found


def test_hit_requires_top5_but_mrr_counts_top10():
    res = [r("x.pdf", i) for i in range(1, 8)] + [r("a.pdf", 5)]
    s = ev.score_question(res, "a.pdf", [5])
    assert s["rank"] == 8 and not s["hit"] and s["rr"] == pytest.approx(1 / 8)
    assert ev.score_question([r("x.pdf", 1)], "a.pdf", [5]) == {"rank": None, "hit": False, "rr": 0.0,
                                                                "pages_found": []}


def test_wrong_file_same_page_is_not_a_hit():
    assert not ev.score_question([r("b.pdf", 5)], "a.pdf", [5])["hit"]


def test_summarise_and_step5_exclusion_matching():
    rows = [{"hit": True, "rr": 1.0, "pages": [1], "pages_found": [1]},
            {"hit": False, "rr": 0.0, "pages": [2, 3], "pages_found": [3]}]
    sm = ev.summarise(rows)
    assert sm["hit_at_5"] == 0.5 and sm["mrr"] == 0.5 and sm["multi_n"] == 1
    assert (sm["multi_pages_found"], sm["multi_pages_total"]) == (1, 2)
    assert ev._norm("What are the four necessary conditions for deadlock??") in {
        ev._norm(q) for q in ev.STEP5_QUESTIONS}


def test_check_mode_exit_codes(tmp_path):
    good = write(tmp_path, {"question": "What is a domain?", "file": F5, "pages": [3]})
    assert ev.main(["--check", "--questions", str(good)]) == 0
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"question": "q"}', encoding="utf-8")
    assert ev.main(["--check", "--questions", str(bad)]) == 1
