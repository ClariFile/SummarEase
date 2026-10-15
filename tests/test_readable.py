"""The readable text view shows the reader's words, all of them, in order (record C5), finds headings without ever
promoting a paragraph, marks OCR text, and says what couldn't be read (C8): one short note per page at most and one
line at the top, with details behind a disclosure. Test documents are made here, with invented content."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication, QTextDocument  # noqa: E402

from office_fixtures import make_docx, make_odt, make_pptx  # noqa: E402
from summarease import tokens  # noqa: E402
from summarease.readable import (  # noqa: E402
    DOC_KINDS, GAP_NOTE, GAP_REASONS, OCR_CAPTION, Block, doc_words, from_record, from_text, to_html, words,
)
from summarease.reader import UnitRecord, read_document  # noqa: E402
from summarease.worker import pdf_bold  # noqa: E402
from test_reader import make_pdf  # noqa: E402
from tools.sample_docs import make_slide_pdf, make_text_pdf  # noqa: E402


def reader_words(rec):
    """The reader's words in order: each unit's text, then its OCR text, then its speaker notes."""
    return [w for u in rec.units for part in (u.text, u.ocr_text or "", u.notes or "") for w in words(part)]


def plain(blocks, details=False):
    QGuiApplication.instance() or QGuiApplication([])
    doc = QTextDocument()
    doc.setHtml(to_html(blocks, tokens.THEMES["light"], details))
    return doc.toPlainText()


def view(path):
    res = read_document(path)
    return res.record, from_record(res.record, pdf_bold(path, res.sha256) if path.suffix == ".pdf" else None)


MAKERS = [(make_pdf, "a.pdf"), (make_text_pdf, "t.pdf"), (make_slide_pdf, "s.pdf"), (make_pptx, "a.pptx"),
          (make_docx, "a.docx"), (make_odt, "a.odt")]


@pytest.mark.parametrize("make, name", MAKERS)
def test_the_view_shows_the_readers_words_in_order_and_only_adds_its_own_labels(tmp_path, make, name):
    rec, blocks = view(make(tmp_path / name))
    assert doc_words(blocks) == reader_words(rec)
    mine = [b for b in blocks if b.kind in DOC_KINDS]
    assert words(plain(mine)) == doc_words(blocks)                    # the HTML drops and adds nothing
    shown, it = words(plain(blocks)), iter(words(plain(blocks)))
    assert all(w in it for w in doc_words(blocks)) and shown           # with labels, still all there in order


def headings(blocks):
    return [(b.text, b.level) for b in blocks if b.kind == "heading"]


def test_text_pdf_headings_are_short_and_larger_or_bolder_never_a_paragraph(tmp_path):
    _, blocks = view(make_text_pdf(tmp_path / "t.pdf", pages=2))
    assert headings(blocks) == [("Invented Handbook of Systems", 1), ("Part 1 Overview of the model", 2),
                                ("Design notes", 3), ("Part 2 Overview of the model", 2), ("Design notes", 3)]
    paras = [b.text for b in blocks if b.kind == "paragraph"]
    assert any(p.startswith("A large print paragraph") for p in paras)          # larger, but a paragraph
    assert any(p.startswith("A bold sentence in the body text") for p in paras)  # bold, but a paragraph


def test_slide_pdf_headings_are_the_slide_titles_only(tmp_path):
    _, blocks = view(make_slide_pdf(tmp_path / "s.pdf", slides=6))
    assert [t for t, _ in headings(blocks)] == ["Invented Course on Networks", "Agenda", "Topic 1 of the course",
                                                "Topic 2 of the course", "Topic 3 of the course", "Summary"]
    assert all(len(t.split()) <= 12 for t, _ in headings(blocks))


def test_without_font_weights_a_bold_line_is_not_a_heading_but_size_still_counts(tmp_path):
    blocks = from_record(read_document(make_text_pdf(tmp_path / "t.pdf", pages=1)).record)   # no bold map
    assert ("Design notes", 3) not in headings(blocks)
    assert ("Part 1 Overview of the model", 2) in headings(blocks)


def test_slides_flow_documents_and_tables_keep_their_structure(tmp_path):
    _, slides = view(make_pptx(tmp_path / "a.pptx"))
    assert Block("heading", "Firewalls", unit=2) in slides
    assert Block("lines", "Packet filtering\nStateful inspection", unit=2) in slides
    notes = slides.index(Block("note", "Speaker notes", unit=2))
    assert slides[notes + 1].kind == "notes" and "stateful inspection" in slides[notes + 1].text
    _, docx = view(make_docx(tmp_path / "a.docx"))
    assert Block("title", "Database Systems Handbook", level=1, unit=1) in docx
    table = next(b for b in docx if b.kind == "table")
    assert table.rows[1] == ["Cell A2", "Cell B2"]
    _, odt = view(make_odt(tmp_path / "a.odt"))
    assert any(b.kind == "list" and b.rows == ["First item", "Nested item"] for b in odt)


def unread(index, status):
    return UnitRecord(index=index, kind="page", text="", native_chars=0, text_area=0, image_area=0.5,
                      nonrepeated_image_area=0.5, suspected_unread=True, suspect_rule="r", ocr_status=status)


def fake(units, unit="page", fmt="pdf"):
    return type("R", (), {"format": fmt, "unit": unit, "units": units})()


def test_gaps_one_short_note_per_page_one_line_at_the_top_and_details_behind_a_link():
    rec = fake([unread(i, s) for i, s in enumerate(GAP_REASONS, 1)])
    blocks = from_record(rec)
    assert blocks[0].kind == "gaps" and blocks[0].text == f"Some pictures couldn't be read: {len(GAP_REASONS)} pages."
    assert [b.unit for b in blocks if b.kind == "gap"] == list(range(1, len(GAP_REASONS) + 1))
    assert all(b.text == GAP_NOTE for b in blocks if b.kind == "gap")
    closed, opened = plain(blocks), plain(blocks, details=True)
    assert "Show details" in closed and "OCR switched off" not in closed and "OCR is switched off" not in closed
    for i, reason in enumerate(GAP_REASONS.values(), 1):
        assert f"Page {i}: a picture couldn't be read ({reason})." in opened


def test_ocr_noise_that_was_dropped_is_not_mentioned():
    u = unread(1, "done")
    u.ocr_text, u.ocr_discarded_chars = "Readable words found by OCR", 40
    blocks = from_record(fake([u]))
    assert not any(b.kind in ("gap", "gaps") for b in blocks)
    assert "noise" not in plain(blocks)


def test_a_flow_document_counts_places_not_pages(tmp_path):
    _, blocks = view(make_docx(tmp_path / "a.docx"))   # OCR is off in this test, so its picture is a gap
    assert blocks[0].text == "Some pictures couldn't be read: 1 place."
    assert blocks[0].rows[0][1] == "Place 1: a picture couldn't be read (OCR is switched off)."


@pytest.mark.ocr
def test_ocr_text_is_shown_marked_as_ocr(tmp_path):
    _, blocks = view(make_docx(tmp_path / "pic.docx"))
    i = next(i for i, b in enumerate(blocks) if b.kind == "ocr")
    assert blocks[i - 1].kind == "note" and blocks[i - 1].text == OCR_CAPTION and "Diagram" in blocks[i].text


def test_if_the_layout_ever_disagrees_with_the_text_the_text_is_shown():
    u = UnitRecord(index=1, kind="page", text="Real words here.", native_chars=14, text_area=0.1, image_area=0,
                   nonrepeated_image_area=0, suspected_unread=False, suspect_rule=None,
                   layout={"blocks": [{"bbox": None, "lines": [{"text": "Other words", "bbox": None, "size": 11}]}]})
    assert doc_words(from_record(fake([u]))) == ["Real", "words", "here."]


def test_every_unit_has_an_anchor_for_the_summary_links(tmp_path):
    rec, blocks = view(make_text_pdf(tmp_path / "t.pdf", pages=3))
    html = to_html(blocks, tokens.THEMES["light"])
    assert all(f'<a name="u{u.index}"></a>' in html for u in rec.units)


def test_pasted_text_keeps_its_words_and_line_breaks():
    text = "First line\nsecond line\n\n  Next paragraph <b>not markup</b> & more\n"
    blocks = from_text(text)
    assert [(b.text, b.unit) for b in blocks] == [("First line\nsecond line", 1),
                                                  ("  Next paragraph <b>not markup</b> & more\n", 2)]
    assert doc_words(blocks) == words(text) == words(plain(blocks))
