from cornerstone import Heading, Page
from cornerstone.ingest.cleaner import clean_pages, normalise_text
from cornerstone.ingest.pdf_parser import extract_pdf


def _pages(texts):
    return [Page(page_no=i + 1, text=t) for i, t in enumerate(texts)]


def test_repeated_footer_and_page_numbers_removed(cfg):
    words = ["paging", "segments", "deadlock", "semaphores", "scheduling"]
    pages = _pages([f"{w.title()} overview\nbody line about {w} here\nDr X, MITS-DU\n{i}"
                    for i, w in enumerate(words, 1)])
    out = clean_pages(pages, cfg)
    for p in out:
        assert "MITS" not in p.text
        assert not p.text.strip().endswith(str(p.page_no))
        assert "body line" in p.text


def test_footer_spelling_variants_and_top_band(cfg):
    pages = _pages(["Dr X MITS DU\nalpha beta", "Dr X, MITS-DU\ngamma delta", "Dr X MITS-DU\nepsilon zeta",
                    "unrelated content here"])
    out = clean_pages(pages, cfg)
    assert [p.text for p in out[:3]] == ["alpha beta", "gamma delta", "epsilon zeta"]


def test_repeated_footer_in_middle_of_text_removed(cfg):
    pages = _pages([f"Topic {w}\nfoot MITS-DU\ntail words {w}" for w in ("a", "b", "c", "d")])
    assert all("MITS" not in p.text for p in clean_pages(pages, cfg))


def test_footer_only_page_with_image_is_needs_ocr(cfg):
    pages = [Page(i, f"Dr X MITS-DU\nbody about {w}") for i, w in enumerate(("a", "b", "c", "d"), 1)]
    pages.append(Page(5, "Dr X MITS-DU", has_image=True))
    out = clean_pages(pages, cfg)
    assert out[-1].status == "needs_ocr" and "OCR" in out[-1].reason


def test_non_repeating_edge_line_kept(cfg):
    pages = _pages(["Intro\nbody a", "Scheduling\nbody b", "Deadlock\nbody c", "Memory\nbody d"])
    out = clean_pages(pages, cfg)
    assert [p.text for p in out] == [p.text for p in pages]


def test_symbols_and_ligatures_preserved(cfg):
    raw = "∑ i ≤ n → α ∈ S, ﬁle ﬂow e­fficient"
    out = normalise_text(raw)
    for sym in "∑≤→α∈":
        assert sym in out
    assert "file flow efficient" in out


def test_private_use_bullet_glyphs_removed_real_bullets_kept():
    assert normalise_text(" Item • two") == "Item • two"


def test_normalise_idempotent_and_whitespace():
    raw = "a  \t b c\n\n\n\n\nconti-\nnuous   x  "
    once = normalise_text(raw)
    assert once == "a b c\n\ncontinuous x"
    assert normalise_text(once) == once


def test_page_with_only_footer_becomes_empty_with_reason(cfg):
    pages = _pages([f"body {i} words here\nFooter Name" for i in range(1, 5)] + ["Footer Name\n9"])
    out = clean_pages(pages, cfg)
    assert out[-1].status == "empty" and out[-1].reason


def test_headings_relocated_after_cleaning(cfg):
    p = Page(2, "Footer Name\nIntro\ntext", headings=[Heading("Intro", 1, 1)])
    others = [Page(i, f"Footer Name\nstuff {i}") for i in (1, 3, 4)]
    out = clean_pages([others[0], p, others[1], others[2]], cfg)[1]
    assert out.text == "Intro\ntext"
    assert out.headings == [Heading("Intro", 1, 0)]


def test_sample_footer_gone_everywhere(small_pdf, cfg):
    out = clean_pages(extract_pdf(small_pdf, cfg), cfg)
    assert sum(len(p.text) for p in out) > 5000
    assert not any("Nishant" in p.text for p in out)
    ok = [p for p in out if p.status == "ok"]
    assert len(ok) >= 20
    for p in out:
        lines = p.text.split("\n")
        assert all(lines[h.line_no] == h.text for h in p.headings)
