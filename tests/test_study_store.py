from datetime import date, timedelta

import pytest

from cornerstone.study_store import Card, StudyStore

TODAY = date(2026, 10, 20)


def card(front="What is a TLB?", page=12, unit="Unit 3", due=TODAY):
    return Card(0, front, "A cache of page table entries.", "Unit 3_Memory.pdf", page, 1, 40, unit, due)


@pytest.fixture
def ss(tmp_path):
    return StudyStore(tmp_path / "study.sqlite")


def test_add_skips_duplicates_and_lists(ss):
    ids = ss.add_cards([card(), card(), card(page=13)])
    assert len(ids) == 2
    assert [c.page for c in ss.list_cards()] == [12, 13]
    assert ss.add_cards([card()]) == []


def test_due_order_limit_and_unit_filter(ss):
    ss.add_cards([card("a", due=TODAY), card("b", due=TODAY - timedelta(days=3)),
                  card("c", due=TODAY + timedelta(days=1)), card("d", unit="Unit 4", due=TODAY)])
    assert [c.front for c in ss.due(TODAY)] == ["b", "a", "d"]
    assert [c.front for c in ss.due(TODAY, limit=1)] == ["b"]
    assert [c.front for c in ss.due(TODAY, units=["Unit 4"])] == ["d"]
    assert ss.due(TODAY, units=[]) == []


def test_review_schedules_with_sm2_and_logs(ss):
    (cid,) = ss.add_cards([card()])
    c = ss.review(cid, 4, TODAY)
    assert (c.reps, c.interval, c.due) == (1, 1, TODAY + timedelta(days=1))
    c = ss.review(cid, 5, c.due)
    assert (c.reps, c.interval) == (2, 6) and c.ef == pytest.approx(2.6)
    c = ss.review(cid, 1, c.due)
    assert (c.reps, c.interval, c.lapses) == (0, 1, 1)
    assert ss.stats(TODAY)["reviews"] == 3


def test_review_errors_change_nothing(ss):
    (cid,) = ss.add_cards([card()])
    with pytest.raises(KeyError):
        ss.review(999, 4, TODAY)
    with pytest.raises(ValueError):
        ss.review(cid, 7, TODAY)
    assert ss.get(cid).reps == 0 and ss.stats(TODAY)["reviews"] == 0


def test_delete_and_reopen(ss, tmp_path):
    (a, b) = ss.add_cards([card("a"), card("b")])
    ss.review(a, 4, TODAY)
    ss.delete_card(a)
    with pytest.raises(KeyError):
        ss.delete_card(a)
    again = StudyStore(tmp_path / "study.sqlite")
    assert [c.front for c in again.list_cards()] == ["b"] and again.stats(TODAY)["reviews"] == 0
