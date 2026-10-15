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


def test_equivalent_pages_count_as_hit_but_not_as_pages_found():
    res = [r("a.pdf", 40)]
    s = ev.score_question(res, "a.pdf", [15], [40])
    assert s["hit"] and s["rank"] == 1 and s["pages_found"] == []
    assert not ev.score_question(res, "a.pdf", [15])["hit"]


def test_equivalent_pages_validation(tmp_path):
    ok = write(tmp_path, {"question": "q one?", "file": F4, "pages": [10], "equivalent_pages": [35]})
    qs, errs = ev.validate_questions(ok, SAMPLES)
    assert errs == [] and qs[0]["equivalent_pages"] == [35]
    for bad in ({"equivalent_pages": [10]}, {"equivalent_pages": [99]}, {"equivalent_pages": "35"}):
        p = write(tmp_path, {"question": "q two?", "file": F4, "pages": [10], **bad})
        assert ev.validate_questions(p, SAMPLES)[1], bad


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


# ---- Stage 2 format: id/split, cross-file targets, unanswerable questions
F1 = "Unit 1_Part 1_Introduction & OS Structure.pdf"


def test_cross_file_unanswerable_and_split_are_parsed(tmp_path):
    p = write(tmp_path,
              {"id": 1, "split": "dev", "question": "One file?", "file": F5, "pages": [3]},
              {"id": 2, "split": "test", "question": "Two files?",
               "targets": [{"file": F5, "pages": [10]}, {"file": F4, "pages": [10], "equivalent_pages": [35]}]},
              {"id": 3, "split": "test", "question": "Not in the notes?", "answerable": False, "note": "absent"})
    qs, errs = ev.validate_questions(p, SAMPLES)
    assert errs == [] and [q["split"] for q in qs] == ["dev", "test", "test"]
    assert qs[0]["targets"] == [{"file": F5, "pages": [3], "equivalent_pages": []}] and qs[0]["file"] == F5
    assert len(qs[1]["targets"]) == 2 and "file" not in qs[1]
    assert qs[2]["answerable"] is False and qs[2]["targets"] == []
    assert "1 cross-file" in ev.describe(qs) and "1 unanswerable" in ev.describe(qs)


@pytest.mark.parametrize("obj, needle", [
    ({"question": "q?", "targets": [{"file": F5, "pages": [1]}]}, "at least 2"),
    ({"question": "q?", "targets": [{"file": F5, "pages": [1]}, {"file": F5, "pages": [2]}]}, "different files"),
    ({"question": "q?", "targets": [{"file": F5, "pages": [1]}, {"file": F4, "pages": [99]}]}, "do not exist"),
    ({"question": "q?", "targets": [{"file": F5, "pages": [1]}, "x"]}, "must be an object"),
    ({"question": "q?", "file": F5, "pages": [1], "targets": [{"file": F5, "pages": [1]}, {"file": F4, "pages": [1]}]},
     "not both"),
    ({"question": "q?", "answerable": False, "file": F5}, "must not have"),
    ({"question": "q?", "answerable": "no"}, "true or false"),
    ({"id": 1, "split": "train", "question": "q?", "file": F5, "pages": [1]}, "'split'"),
    ({"id": "1", "split": "dev", "question": "q?", "file": F5, "pages": [1]}, "'id'"),
])
def test_stage2_invalid_lines_are_rejected(tmp_path, obj, needle):
    qs, errs = ev.validate_questions(write(tmp_path, obj), SAMPLES)
    assert qs == [] and any(needle in e for e in errs), errs


def test_ids_unique_and_meta_all_or_nothing(tmp_path):
    p = write(tmp_path, {"id": 1, "split": "dev", "question": "a?", "file": F5, "pages": [1]},
              {"id": 1, "split": "dev", "question": "b?", "file": F5, "pages": [2]})
    assert any("unique" in e for e in ev.validate_questions(p, SAMPLES)[1])
    p = write(tmp_path, {"id": 1, "split": "dev", "question": "a?", "file": F5, "pages": [1]},
              {"question": "b?", "file": F5, "pages": [2]})
    assert any("missing on 1" in e for e in ev.validate_questions(p, SAMPLES)[1])


def test_score_targets_cross_file():
    t = [{"file": "a.pdf", "pages": [5]}, {"file": "b.pdf", "pages": [9], "equivalent_pages": [30]}]
    s = ev.score_targets([r("x.pdf", 1), r("b.pdf", 30), r("a.pdf", 4, 6)], t)
    assert s["rank"] == 2 and s["hit"] and s["pages_found"] == [("a.pdf", 5)]
    assert s["files_found"] == ["a.pdf", "b.pdf"]          # b found through its duplicate page
    s = ev.score_targets([r("a.pdf", 5)], t)
    assert s["files_found"] == ["a.pdf"]
    rows = [{"hit": True, "rr": 1.0, "pages": [("a.pdf", 5), ("b.pdf", 9)], "pages_found": [("a.pdf", 5)],
             "n_files": 2, "files_found": ["a.pdf"]}]
    sm = ev.summarise(rows)
    assert (sm["cross_n"], sm["cross_all_files"], sm["multi_n"]) == (1, 0, 1)


def test_check_mode_with_split(tmp_path):
    good = write(tmp_path, {"id": 1, "split": "dev", "question": "a?", "file": F5, "pages": [3]},
                 {"id": 2, "split": "test", "question": "b?", "answerable": False})
    assert ev.main(["--check", "--split", "test", "--questions", str(good)]) == 0
    nometa = tmp_path / "n.jsonl"
    nometa.write_text(json.dumps({"question": "a?", "file": F5, "pages": [3]}), encoding="utf-8")
    assert ev.main(["--check", "--split", "dev", "--questions", str(nometa)]) == 1
    assert ev.main(["--check", "--questions", str(nometa)]) == 0
