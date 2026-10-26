"""M0 acceptance: the copied reader reads a PDF, a PPTX, a DOCX and an ODT made for the tests (invented content)."""
import ast
import hashlib
from pathlib import Path

import pymupdf
import pytest

from office_fixtures import make_docx, make_odt, make_pptx
from summarease.reader import RECORD_VERSION, read_document

READER = Path(__file__).resolve().parent.parent / "summarease" / "reader"


def make_pdf(path):
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Invented test sentence on page one.")
    doc.new_page().insert_text((72, 72), "Second page sentence.")
    doc.save(path)
    return path


CASES = [
    (make_pdf, "a.pdf", "pdf", "Invented test sentence on page one."),
    (make_pptx, "a.pptx", "pptx", "Packet filtering"),
    (make_docx, "a.docx", "docx", "Keep this sentence."),
    (make_odt, "a.odt", "odt", "Database Systems Handbook"),
]


@pytest.mark.parametrize("make, name, fmt, phrase", CASES)
def test_reader_reads_each_format_without_changing_it(tmp_path, make, name, fmt, phrase):
    path = make(tmp_path / name)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    res = read_document(path)
    assert res.status == "ok", res.reason
    rec = res.record
    assert rec.format == fmt and rec.record_version == RECORD_VERSION == 7
    text = "\n".join(u.text for u in rec.units)
    assert text.strip()
    assert phrase in text
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before == res.sha256
    assert sorted(p.name for p in tmp_path.iterdir()) == [name]  # nothing written next to the source


@pytest.mark.ocr
def test_ocr_reads_text_only_in_a_picture(tmp_path):
    rec = read_document(make_docx(tmp_path / "pic.docx")).record
    assert any(u.ocr_status == "done" and "Diagram" in (u.ocr_text or "") for u in rec.units)


def test_reader_imports_nothing_from_the_rest_of_summarease():
    for p in READER.glob("*.py"):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module or ""] if isinstance(node, ast.ImportFrom) and not node.level else []
            assert not [m for m in mods if m.split(".")[0] in ("summarease", "classifile")], p.name
