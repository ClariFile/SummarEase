"""M1: the readable text view shows the reader's words, all of them, in order (record C5), marks OCR text and says
what couldn't be read (C8). Test documents are made here, with invented content."""
import os

import pymupdf
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication, QTextDocument  # noqa: E402

from office_fixtures import make_docx, make_odt, make_pptx  # noqa: E402
from summarease import tokens  # noqa: E402
from summarease.readable import (  # noqa: E402
    DOC_KINDS, OCR_CAPTION, OCR_GAPS, Block, doc_words, from_record, from_text, to_html, words,
)
from summarease.reader import UnitRecord, read_document  # noqa: E402
from test_reader import make_pdf  # noqa: E402


def make_structured_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Invented Report Title", fontsize=28)
    y = 120
    for line in ("Body text that runs across", "two lines of one paragraph.", "1. First listed point",
                 "2. Second listed point", "Closing body sentence here."):
        page.insert_text((72, y), line, fontsize=11)
        y += 14
    doc.new_page().insert_text((72, 72), "Second page sentence.", fontsize=11)
    doc.save(path)
    return path


def reader_words(rec):
    """The reader's words in order: each unit's text, then its OCR text, then its speaker notes."""
    return [w for u in rec.units for part in (u.text, u.ocr_text or "", u.notes or "") for w in words(part)]


def shown_words(blocks):
    """What a QTextDocument shows for the blocks, as words (labels and notes included)."""
    QGuiApplication.instance() or QGuiApplication([])
    doc = QTextDocument()
    doc.setHtml(to_html(blocks, tokens.THEMES["light"]))
    return words(doc.toPlainText())


MAKERS = [(make_pdf, "a.pdf"), (make_structured_pdf, "s.pdf"), (make_pptx, "a.pptx"), (make_docx, "a.docx"),
          (make_odt, "a.odt")]


@pytest.mark.parametrize("make, name", MAKERS)
def test_the_view_shows_the_readers_words_in_order_and_only_adds_its_own_labels(tmp_path, make, name):
    rec = read_document(make(tmp_path / name)).record
    blocks = from_record(rec)
    assert doc_words(blocks) == reader_words(rec)
    assert shown_words(blocks) == [w for b in blocks for w in b.words()]   # the HTML drops and adds nothing


def test_pdf_layout_gives_headings_paragraphs_and_list_items(tmp_path):
    blocks = from_record(read_document(make_structured_pdf(tmp_path / "s.pdf")).record)
    doc = [(b.kind, b.text) for b in blocks if b.kind in DOC_KINDS]
    assert doc[0] == ("heading", "Invented Report Title") and blocks[1].level == 1
    assert ("paragraph", "Body text that runs across two lines of one paragraph.") in doc
    assert ("paragraph", "1. First listed point") in doc
    assert ("paragraph", "2. Second listed point Closing body sentence here.") in doc   # a wrapped item flows on
    assert [b.text for b in blocks if b.kind == "label"] == ["Page 1", "Page 2"]


def test_slides_flow_documents_and_tables_keep_their_structure(tmp_path):
    slides = from_record(read_document(make_pptx(tmp_path / "a.pptx")).record)
    assert Block("heading", "Firewalls") in slides
    assert Block("lines", "Packet filtering\nStateful inspection") in slides
    notes = slides.index(Block("note", "Speaker notes"))
    assert slides[notes + 1].kind == "notes" and "stateful inspection" in slides[notes + 1].text
    docx = from_record(read_document(make_docx(tmp_path / "a.docx")).record)
    assert docx[1] == Block("title", "Database Systems Handbook", level=1)
    assert Block("heading", "Introduction", level=1) in docx
    table = next(b for b in docx if b.kind == "table")
    assert table.rows[1] == ["Cell A2", "Cell B2"]
    odt = from_record(read_document(make_odt(tmp_path / "a.odt")).record)
    assert Block("list", rows=["First item", "Nested item"]) in odt


def test_a_picture_that_was_not_read_is_disclosed_where_it_is_and_at_the_top(tmp_path):
    blocks = from_record(read_document(make_docx(tmp_path / "a.docx")).record)   # OCR is off in this test
    assert blocks[0].kind == "gap" and "Not everything could be read: 1 place" in blocks[0].text
    assert Block("gap", OCR_GAPS["disabled"]) in blocks[1:]


def test_every_ocr_status_that_leaves_text_unread_is_disclosed():
    for status, note in OCR_GAPS.items():
        u = UnitRecord(index=3, kind="page", text="", native_chars=0, text_area=0, image_area=0.5,
                       nonrepeated_image_area=0.5, suspected_unread=True, suspect_rule="r", ocr_status=status)
        rec = type("R", (), {"format": "pdf", "unit": "page", "units": [u]})()
        blocks = from_record(rec)
        assert blocks[0] == Block("gap", "Not everything could be read: page 3. Each is marked below.")
        assert Block("gap", note) in blocks


def test_a_long_list_of_gaps_is_shortened_at_the_top():
    units = [UnitRecord(index=i, kind="page", text="", native_chars=0, text_area=0, image_area=0.5,
                        nonrepeated_image_area=0.5, suspected_unread=True, suspect_rule="r", ocr_status="no_text")
             for i in range(1, 14)]
    rec = type("R", (), {"format": "pdf", "unit": "page", "units": units})()
    assert from_record(rec)[0].text == \
        "Not everything could be read: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 and 3 more. Each is marked below."


@pytest.mark.ocr
def test_ocr_text_is_shown_marked_as_ocr(tmp_path):
    blocks = from_record(read_document(make_docx(tmp_path / "pic.docx")).record)
    i = next(i for i, b in enumerate(blocks) if b.kind == "ocr")
    assert blocks[i - 1] == Block("note", OCR_CAPTION) and "Diagram" in blocks[i].text


def test_if_the_layout_ever_disagrees_with_the_text_the_text_is_shown():
    u = UnitRecord(index=1, kind="page", text="Real words here.", native_chars=14, text_area=0.1, image_area=0,
                   nonrepeated_image_area=0, suspected_unread=False, suspect_rule=None,
                   layout={"blocks": [{"bbox": None, "lines": [{"text": "Other words", "bbox": None, "size": 11}]}]})
    rec = type("R", (), {"format": "pdf", "unit": "page", "units": [u]})()
    assert doc_words(from_record(rec)) == ["Real", "words", "here."]


def test_pasted_text_keeps_its_words_and_line_breaks():
    text = "First line\nsecond line\n\n  Next paragraph <b>not markup</b> & more\n"
    blocks = from_text(text)
    assert [b.text for b in blocks] == ["First line\nsecond line", "  Next paragraph <b>not markup</b> & more\n"]
    assert doc_words(blocks) == words(text) == shown_words(blocks)
