"""H8, from the second ClassiFile handoff: a unit with native text, one picture OCR read and one it could not open.
The text read stays, and the unread picture is named in every summary level, Copy, the HTML view and both exports;
a fully read counterpart has no gap. The check reads the reader's own outcomes, not the view's."""
from html import escape

import pymupdf

from summarease import checks, export, present, tokens
from summarease.readable import from_record
from summarease.reader import ocr, read_document
from summarease.summarize import LEVELS, build, source_from_record

NATIVE = ("Routers forward packets between networks using routing tables. " * 3).strip()


def record(tmp_path, monkeypatch, fail):
    path = tmp_path / "net.pdf"
    d = pymupdf.open()
    for _ in range(2):
        d.new_page().insert_text((72, 72), NATIVE, fontsize=11)
    d.save(path)
    d.close()
    rec = read_document(path).record
    monkeypatch.delenv("CLASSIFILE_OCR", raising=False)
    monkeypatch.setattr(ocr, "tessdata", lambda: "here")
    monkeypatch.setattr(ocr, "ocr_pixmap", lambda pix, folder, with_layout=False: (
        "Gateway subnet latency diagram with switch ports", []))
    pix = lambda: pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 8, 8), 0)

    def broken():
        raise ValueError("a picture MuPDF cannot open")

    u = rec.units[0]
    u.suspected_unread, u.suspect_rule = True, "r"
    ocr.run([u], {u.index: [pix, broken] if fail else [pix, pix]})
    return rec


def test_one_picture_read_and_one_not_is_disclosed_everywhere(tmp_path, monkeypatch):
    rec = record(tmp_path, monkeypatch, fail=True)
    assert rec.units[0].ocr_status == "partial" and "Gateway" in rec.units[0].ocr_text
    blocks = from_record(rec)
    detail = "Page 1: 1 of its 2 pictures couldn't be read (it could not be opened)."
    assert any(b.kind == "ocr" and "Gateway" in b.text for b in blocks)         # the text read is kept
    assert blocks[0].kind == "gaps" and (1, detail) in blocks[0].rows
    src = source_from_record(rec, blocks)
    for level in LEVELS:
        s = build(src, level, "baseline")
        assert (1, detail) in s.gaps and detail in present.as_text(s)          # Copy
        assert escape(detail) in present.to_html(s, tokens.THEMES["light"], True)   # the view, details open
        assert not checks.gaps_disclosed(s, blocks, rec)
    paras = present.paragraphs(build(src, "detailed", "baseline"))
    for suffix in (".pdf", ".docx"):
        final, _ = export.save(paras, tmp_path / f"Summary{suffix}")
        export.check(final, paras)                                             # read back, gap line included
        assert ("gap", detail) in paras


def test_the_check_catches_a_partial_gap_the_view_lost(tmp_path, monkeypatch):
    rec = record(tmp_path, monkeypatch, fail=True)
    rec.units[0].ocr_status = "done"                    # a view or an older status saying "done" is not believed:
    blocks = [b for b in from_record(rec) if b.kind not in ("gap", "gaps")]
    s = build(source_from_record(rec, blocks), "key", "baseline")
    assert checks.gaps_disclosed(s, blocks, rec) == ["key: 1 gap(s) not disclosed"]   # the outcomes decide


def test_a_fully_read_unit_has_no_gap(tmp_path, monkeypatch):
    rec = record(tmp_path, monkeypatch, fail=False)
    assert rec.units[0].ocr_status == "done"
    blocks = from_record(rec)
    assert not any(b.kind in ("gap", "gaps") for b in blocks)
    assert not build(source_from_record(rec, blocks), "brief", "baseline").gaps
