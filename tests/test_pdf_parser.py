import pymupdf
import pytest

from cornerstone import CorruptFile, EmptyFile, PasswordProtected
from cornerstone.ingest.pdf_parser import extract_pdf


def _make_pdf(path, pages):
    """pages: list of dicts {text: str|None, image: bool}."""
    doc = pymupdf.open()
    for spec in pages:
        p = doc.new_page()
        if spec.get("text"):
            p.insert_text((72, 100), spec["text"], fontsize=spec.get("size", 11))
        if spec.get("image"):
            pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 60, 60), False)
            pix.clear_with(180)
            p.insert_image(pymupdf.Rect(100, 200, 400, 500), pixmap=pix)
    doc.save(path)
    doc.close()
    return path


def test_sample_every_page_accounted_for(small_pdf, cfg):
    pages = extract_pdf(small_pdf, cfg)
    assert len(pages) == 28
    assert [p.page_no for p in pages] == list(range(1, 29))
    ok = [p for p in pages if p.status == "ok"]
    assert len(ok) >= 20
    assert all(p.text.strip() for p in ok)
    # every non-ok page has a reason (no silent skipping)
    assert all(p.reason for p in pages if p.status != "ok")


def test_sample_headings_detected(small_pdf, cfg):
    pages = extract_pdf(small_pdf, cfg)
    heads = [h for p in pages for h in p.headings]
    assert heads, "expected some headings (slide titles are large font)"
    for p in pages:
        lines = p.text.split("\n")
        for h in p.headings:
            assert lines[h.line_no] == h.text
            assert 1 <= h.level <= 3


def test_scanned_page_flagged_needs_ocr(tmp_path, cfg):
    pdf = _make_pdf(tmp_path / "mixed.pdf", [
        {"text": "This page has a proper text layer with enough words to be indexed."},
        {"image": True},
        {},
    ])
    pages = extract_pdf(pdf, cfg)
    assert [p.status for p in pages] == ["ok", "needs_ocr", "empty"]
    assert "OCR" in pages[1].reason
    assert pages[2].reason


def test_empty_file(tmp_path, cfg):
    f = tmp_path / "e.pdf"
    f.write_bytes(b"")
    with pytest.raises(EmptyFile):
        extract_pdf(f, cfg)


def test_corrupt_file(tmp_path, cfg):
    f = tmp_path / "bad.pdf"
    f.write_bytes(b"this is definitely not a pdf" * 20)
    with pytest.raises(CorruptFile):
        extract_pdf(f, cfg)


def test_password_protected(tmp_path, cfg):
    src = _make_pdf(tmp_path / "plain.pdf", [{"text": "secret"}])
    out = tmp_path / "locked.pdf"
    doc = pymupdf.open(src)
    doc.save(out, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="o", user_pw="u")
    doc.close()
    with pytest.raises(PasswordProtected):
        extract_pdf(out, cfg)
