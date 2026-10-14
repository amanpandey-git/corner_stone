import pytest

from cornerstone import Heading, Page
from cornerstone.chunking import chunk_pages
from cornerstone.embeddings import load_token_counter
from cornerstone.ingest.loader import load_document


def words(text: str) -> int:
    """Fake tokenizer: 1 word = 1 token. Keeps unit tests fast and exact."""
    return len(text.split())


def para(prefix: str, n: int) -> str:
    return " ".join(f"{prefix}{i}" for i in range(n)) + "."


@pytest.fixture
def small_cfg(cfg):
    c = {**cfg, "chunking": {"target_tokens": 50, "overlap_tokens": 10, "min_tokens": 8, "hard_max_tokens": 80}}
    return c


def test_empty_and_non_ok_pages(small_cfg):
    assert chunk_pages([], 1, "a.pdf", small_cfg, words) == []
    flagged = [Page(1, "some text here", status="needs_ocr", reason="r"), Page(2, "", status="empty", reason="r")]
    assert chunk_pages(flagged, 1, "a.pdf", small_cfg, words) == []


def test_no_headings_document(small_cfg):
    pages = [Page(1, para("a", 30) + "\n\n" + para("b", 30)), Page(2, para("c", 30))]
    chunks = chunk_pages(pages, 7, "n.pdf", small_cfg, words)
    assert chunks and all(c.section_heading is None for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert all(c.doc_id == 7 and c.file_name == "n.pdf" and c.chunk_id == 0 for c in chunks)
    assert chunks[0].page_start == 1 and chunks[-1].page_end == 2


def test_long_section_split_with_overlap_and_nothing_lost(small_cfg):
    text = " ".join(para(f"s{i}_", 12) for i in range(15))  # 15 sentences x 12 words
    page = Page(1, "Deadlock\n" + text, headings=[Heading("Deadlock", 1, 0)])
    chunks = chunk_pages([page], 1, "d.pdf", small_cfg, words)
    assert len(chunks) >= 3
    assert all(c.token_count <= 80 for c in chunks)
    assert all(c.section_heading == "Deadlock" for c in chunks)
    all_words = set(" ".join(c.text for c in chunks).split())
    assert all(w in all_words for w in text.split())          # nothing truncated
    for a, b in zip(chunks, chunks[1:]):                      # consecutive chunks overlap
        assert set(a.text.split()) & set(b.text.split())


def test_single_giant_sentence_split_by_words(small_cfg):
    page = Page(1, " ".join(f"w{i}" for i in range(400)))     # no punctuation at all
    chunks = chunk_pages([page], 1, "g.pdf", small_cfg, words)
    assert len(chunks) > 5 and all(c.token_count <= 80 for c in chunks)
    assert {f"w{i}" for i in range(400)} <= set(" ".join(c.text for c in chunks).split())


def test_lone_heading_merged_with_neighbour(small_cfg):
    text = "Intro\n" + para("x", 30) + "\nTiny\n" + para("y", 30)
    page = Page(1, text, headings=[Heading("Intro", 1, 0), Heading("Tiny", 1, 2)])
    chunks = chunk_pages([page], 1, "t.pdf", small_cfg, words)
    assert not any(c.text.strip() == "Tiny" for c in chunks)
    assert any("Tiny" in c.text and "y0" in c.text for c in chunks)


def test_sections_split_on_headings_and_heading_persists_across_pages(small_cfg):
    p1 = Page(1, "Paging\n" + para("a", 20), headings=[Heading("Paging", 1, 0)])
    p2 = Page(2, para("b", 20))                                # continues "Paging"
    p3 = Page(3, "Segmentation\n" + para("c", 20), headings=[Heading("Segmentation", 1, 0)])
    chunks = chunk_pages([p1, p2, p3], 1, "s.pdf", small_cfg, words)
    heads = [c.section_heading for c in chunks]
    assert heads[0] == "Paging" and heads[-1] == "Segmentation"
    paging = [c for c in chunks if c.section_heading == "Paging"]
    assert paging[0].page_start == 1 and paging[-1].page_end == 2


def test_docx_chunks_carry_paragraph_range_not_pages(small_cfg):
    page = Page(None, "Intro\n" + para("a", 20), headings=[Heading("Intro", 1, 0)], para_start=3, para_end=9)
    c = chunk_pages([page], 1, "d.docx", small_cfg, words)[0]
    assert c.page_start is None and c.page_end is None
    assert (c.para_start, c.para_end) == (3, 9)


def test_real_samples_with_model_tokenizer(small_pdf, cfg):
    count = load_token_counter(cfg)
    pages = load_document(small_pdf, cfg)
    chunks = chunk_pages(pages, 1, small_pdf.name, cfg, count)
    ch = cfg["chunking"]
    assert chunks
    assert all(c.token_count <= ch["hard_max_tokens"] for c in chunks)
    assert all(c.text.strip() for c in chunks)
    # every ok page is covered by at least one chunk (no silent loss)
    ok_pages = {p.page_no for p in pages if p.status == "ok"}
    covered = set()
    for c in chunks:
        covered.update(range(c.page_start, c.page_end + 1))
    assert ok_pages <= covered
