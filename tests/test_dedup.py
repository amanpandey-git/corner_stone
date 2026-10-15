import pytest

from cornerstone import Page
from cornerstone.dedup import find_duplicate_pages, jaccard, mark_duplicates, page_signature
from cornerstone.ingest.loader import load_document
from conftest import SAMPLES

BODY = ("The disk arm moves toward the end of the disk and serves the requests coming into its path, "
        "then reverses direction and returns to the other end without serving requests.")


def test_signature_and_jaccard_basics():
    assert page_signature("A b C d") == {"a b c", "b c d"}
    assert page_signature("two words") == {"two words"} and page_signature("  ") == set()
    assert jaccard({"x"}, {"x"}) == 1.0 and jaccard(set(), set()) == 0.0
    assert jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)


def test_later_copies_map_to_the_earliest_original(cfg):
    pages = [Page(1, BODY), Page(2, "Something else entirely, long enough to be compared with others. " * 2),
             Page(3, BODY), Page(4, BODY + " ")]
    assert find_duplicate_pages(pages, cfg) == {3: 1, 4: 1}     # never "4 duplicates 3"


def test_short_pages_never_marked(cfg):
    pages = [Page(1, "Practice Problem"), Page(2, "Practice Problem"), Page(3, "Magnetic Disk")]
    assert find_duplicate_pages(pages, cfg) == {}


def test_digits_keep_worked_examples_apart(cfg):
    fcfs = "Example: head starts at 50. Seek time = (82-50) + (170-82) + (170-43) + (140-43) = 642 for this sequence."
    sstf = "Example: head starts at 50. Seek time = (50-43) + (43-24) + (24-16) + (82-16) = 208 for this sequence."
    assert find_duplicate_pages([Page(1, fcfs), Page(2, sstf)], cfg) == {}


def test_flagged_and_docx_pages_are_ignored(cfg):
    pages = [Page(1, BODY, status="needs_ocr", reason="x"), Page(2, BODY), Page(None, BODY), Page(None, BODY)]
    assert find_duplicate_pages(pages, cfg) == {}


def test_mark_duplicates_sets_status_reason_and_source(cfg):
    pages = mark_duplicates([Page(1, BODY), Page(2, BODY)], cfg)
    assert (pages[0].status, pages[0].duplicate_of) == ("ok", None)
    assert (pages[1].status, pages[1].duplicate_of, pages[1].reason) == ("duplicate", 1, "near-duplicate of p.1")


def test_unit4_pdf_repeats_are_found(cfg):
    pages = load_document(SAMPLES / "Unit 4_Storage management_ Disk Schduling.pdf", cfg)
    d = find_duplicate_pages(pages, cfg)
    assert len(d) == 23 and d[27] == 2 and d[35] == 10 and d[51] == 26
    assert 30 not in d and 33 not in d                          # short picture slides: kept, by design
    assert all(orig <= 26 for orig in d.values())


def test_preemptive_and_non_preemptive_examples_are_not_merged(cfg):
    pages = load_document(SAMPLES / "Unit 1_Part 2_ Process management.pdf", cfg)
    d = find_duplicate_pages(pages, cfg)
    assert d == {67: 66}                                        # 66/67: identical slide text
    assert 54 not in d and 86 not in d                          # SJF / priority variants differ by one word
