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
    c = {**cfg, "chunking": {"target_tokens": 50, "overlap_tokens": 10, "min_tokens": 8, "hard_max_tokens": 80,
                             "mode": "section"}}
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


# ---- Stage 2: slide mode (ARCHITECTURE 10.4)
from cornerstone.chunking import context_header, embedding_text, slide_title  # noqa: E402
from cornerstone.dedup import mark_duplicates  # noqa: E402
from conftest import SAMPLES  # noqa: E402


@pytest.fixture
def slide_cfg(cfg):
    return {**cfg, "chunking": {"target_tokens": 50, "overlap_tokens": 10, "min_tokens": 8, "hard_max_tokens": 80,
                                "mode": "slide", "slide_max_tokens": 60, "slide_min_tokens": 5, "slide_title_lines": 2,
                                "slide_title_max_chars": 60}}


def slide(no, title, body, title_line=0):
    lines = [body] * title_line + [title] + ([body] if title_line == 0 else [])
    return Page(no, "\n".join(lines), headings=[Heading(title, 1, title_line)])


def test_one_chunk_per_slide_with_header(slide_cfg):
    pages = [slide(1, "Paging", para("a", 20)), slide(2, "Segmentation", para("b", 20))]
    chunks = chunk_pages(pages, 1, "Unit 3_Memory.pdf", slide_cfg, words)
    assert [(c.page_start, c.page_end, c.section_heading) for c in chunks] == [(1, 1, "Paging"), (2, 2, "Segmentation")]
    assert chunks[0].context_header == "Unit 3_Memory > Paging"
    assert embedding_text(chunks[0]).startswith("Unit 3_Memory > Paging\nPaging\n")
    assert chunks[0].token_count == words(embedding_text(chunks[0]))


def test_same_title_on_consecutive_slides_stays_separate(slide_cfg):
    pages = [slide(i, "Practice Problem", para(f"p{i}_", 20)) for i in (5, 6, 7)]
    chunks = chunk_pages(pages, 1, "a.pdf", slide_cfg, words)
    assert [(c.page_start, c.page_end) for c in chunks] == [(5, 5), (6, 6), (7, 7)]


def test_title_rules_carry_previous_title(slide_cfg):
    c = slide_cfg["chunking"]
    assert slide_title(slide(1, "Deadlock", "x"), c) == "Deadlock"
    assert slide_title(slide(1, "• Execute user programs and make solving user problems easier", "x"), c) is None
    assert slide_title(slide(1, "x" * 61, "y"), c) is None
    assert slide_title(slide(1, "Late heading", "body", title_line=3), c) is None
    pages = [slide(1, "Threads", para("a", 20)), slide(2, "➢ a bullet promoted to heading", para("b", 20))]
    assert [ch.section_heading for ch in chunk_pages(pages, 1, "a.pdf", slide_cfg, words)] == ["Threads", "Threads"]


def test_long_slide_is_windowed_inside_its_page(slide_cfg):
    body = " ".join(para(f"s{i}_", 12) for i in range(10))           # 120 words > 60 budget
    chunks = chunk_pages([slide(9, "Banker", body)], 1, "a.pdf", slide_cfg, words)
    assert len(chunks) > 1 and all((c.page_start, c.page_end) == (9, 9) for c in chunks)
    assert all(c.token_count <= 60 for c in chunks)
    joined = " ".join(c.text for c in chunks)
    assert all(f"s{i}_11." in joined for i in range(10))               # nothing lost


def test_tiny_slide_merges_into_next(slide_cfg):
    pages = [Page(20, "Deadlock", headings=[Heading("Deadlock", 1, 0)]), slide(21, "Deadlock", para("d", 20))]
    chunks = chunk_pages(pages, 1, "a.pdf", slide_cfg, words)
    assert len(chunks) == 1 and (chunks[0].page_start, chunks[0].page_end) == (20, 21)


def test_tiny_slide_never_jumps_a_gap_or_merges_backwards(slide_cfg):
    pages = [slide(26, "C-LOOK", para("c", 20)), Page(30, "Magnetic Disk", headings=[Heading("Magnetic Disk", 1, 0)]),
             slide(32, "Disk", para("d", 20)), Page(33, "Types", headings=[Heading("Types", 1, 0)])]
    chunks = chunk_pages(pages, 1, "a.pdf", slide_cfg, words)
    assert [(c.page_start, c.page_end) for c in chunks] == [(26, 26), (30, 30), (32, 32), (33, 33)]


def test_short_but_real_slide_is_not_merged(slide_cfg):
    pages = [slide(11, "FCFS", para("adv", 6)), slide(12, "SSTF", para("s", 20))]   # 7 words >= slide_min 5
    assert [(c.page_start, c.page_end) for c in chunk_pages(pages, 1, "a.pdf", slide_cfg, words)] == [(11, 11), (12, 12)]


def test_docx_sections_ignore_slide_mode(slide_cfg):
    pages = [Page(None, "Intro\n" + para("a", 20), headings=[Heading("Intro", 1, 0)], para_start=0, para_end=1)]
    chunks = chunk_pages(pages, 1, "notes.docx", slide_cfg, words)
    assert chunks[0].page_start is None and chunks[0].para_start == 0 and chunks[0].context_header == "notes > Intro"


def test_context_header_without_section():
    assert context_header("dir/Unit 5_Part 2.pdf", None) == "Unit 5_Part 2"


def test_real_unit4_slides_get_exact_pages(cfg):
    count = load_token_counter(cfg)
    f = SAMPLES / "Unit 4_Storage management_ Disk Schduling.pdf"
    chunks = chunk_pages(mark_duplicates(load_document(f, cfg), cfg), 1, f.name, cfg, count)
    fcfs = [c for c in chunks if c.page_start <= 10 <= c.page_end]
    assert len(fcfs) == 1 and (fcfs[0].page_start, fcfs[0].page_end) == (10, 10)
    assert fcfs[0].section_heading == "First Come First Serve Algorithm"
    assert all(c.token_count <= cfg["chunking"]["slide_max_tokens"] for c in chunks)
    spans = [(c.page_start, c.page_end) for c in chunks if c.page_start != c.page_end]
    assert all(b == a + 1 for a, b in spans)                                  # merges only into the next page
    assert (11, 11) in [(c.page_start, c.page_end) for c in chunks]           # FCFS advantages slide on its own
