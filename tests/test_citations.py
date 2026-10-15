import pytest

from cornerstone.citations import (Citation, check_citations, parse_citations, parse_judge_reply, split_sentences,
                                   strip_invalid_refs)
from cornerstone.llm import FakeProvider


@pytest.fixture
def jcfg():
    return {"answer": {"judge_max_tokens": 200}}


def test_single_refs_and_sentence_text_without_markers():
    cits, uncited, bad = parse_citations("Paging uses frames [1]. A TLB caches translations [2].", 3)
    assert cits == [Citation("Paging uses frames.", [1]), Citation("A TLB caches translations.", [2])]
    assert uncited == [] and bad == []


def test_groups_ranges_adjacent_and_dedup():
    cits, _, _ = parse_citations("Deadlock needs four conditions [1, 3][2-4] [1].", 5)
    assert cits[0].refs == [1, 3, 2, 4]


def test_ref_after_full_stop_belongs_to_previous_sentence():
    cits, uncited, _ = parse_citations("SCAN moves like an elevator. [2] Next, C-SCAN returns to the start [3].", 3)
    assert [c.refs for c in cits] == [[2], [3]]
    assert cits[0].sentence == "SCAN moves like an elevator." and uncited == []


def test_invalid_refs_are_collected_and_not_counted():
    cits, uncited, bad = parse_citations("Semaphores avoid busy waiting in this design [7]. Monitors wrap them [0][2].", 5)
    assert bad == [0, 7]
    assert [c.refs for c in cits] == [[2]]
    assert uncited == ["Semaphores avoid busy waiting in this design."]


def test_uncited_factual_sentences_vs_headings_and_labels():
    text = ("## Introduction\nKey points:\n- Threads share the address space of their process [1].\n"
            "- Each thread has its own stack and registers.\nConclusion\nNOT_IN_NOTES")
    cits, uncited, _ = parse_citations(text, 2)
    assert [c.refs for c in cits] == [[1]]
    assert uncited == ["- Each thread has its own stack and registers."]


def test_no_refs_at_all_and_empty_text():
    cits, uncited, bad = parse_citations("The kernel schedules processes using many policies.", 3)
    assert cits == [] and len(uncited) == 1 and bad == []
    assert parse_citations("", 3) == ([], [], [])


def test_decimals_and_abbreviations_do_not_split_wrongly():
    s = split_sentences("Average waiting time is 3.5 ms [1]. Done.")
    assert s == ["Average waiting time is 3.5 ms [1].", "Done."]


def test_backwards_or_huge_range_yields_ends_only():
    _, _, bad = parse_citations("Odd citation here today [5-2] and [1-500].", 5)
    assert bad == [500]                      # 5, 2 and 1 are valid; 500 is not


def test_strip_invalid_refs():
    assert strip_invalid_refs("Paging [1, 9]. TLB [8]. Frames [2][2].", 3) == "Paging [1]. TLB. Frames [2][2]."


def test_parse_judge_reply():
    assert parse_judge_reply('{"unsupported": [2]}', 3) == [1]
    assert parse_judge_reply('Sure! ```json\n{"unsupported": []}\n```', 3) == []
    assert parse_judge_reply('{"unsupported": [9, 1, 1]}', 3) == [0]
    for bad in ("no json", '{"other": []}', '{"unsupported": "2"}', '{"unsupported": [true]}'):
        assert parse_judge_reply(bad, 3) is None


def test_check_citations_retries_once_then_reports_unchecked(jcfg):
    cits = [Citation("Paging uses frames.", [1]), Citation("The TLB is a disk.", [2])]
    src = {1: "Paging divides memory into frames.", 2: "The TLB is a cache of page table entries."}
    judge = FakeProvider(["not json", '{"unsupported": [2]}'])
    assert check_citations(cits, src, judge, jcfg) == [1]
    assert len(judge.calls) == 2 and "Cited slides" in judge.calls[0][1] and "frames" in judge.calls[0][1]
    assert check_citations(cits, src, FakeProvider(["nope"]), jcfg) is None
    assert check_citations([], src, FakeProvider(["x"]), jcfg) == []


def test_gap_sentence_needs_no_citation():
    _, uncited, _ = parse_citations("Paging uses frames [1]. The notes do not cover inverted page tables.\n"
                                    "Segment sizes are not covered in your notes.", 2)
    assert uncited == []
