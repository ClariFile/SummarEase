"""The one evaluation command: runs on a set of invented documents, reports every automatic check with no problems,
names documents by neutral IDs only, refuses held-out sets before opening anything, and fails loudly (H4, H5)."""
import os
import subprocess

import pytest

from office_fixtures import make_docx, make_pptx
from tools import evaluate
from tools.sample_docs import make_slide_pdf, make_text_pdf


@pytest.fixture(autouse=True)
def local(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate, "IDS", tmp_path / "doc_ids.csv")
    monkeypatch.setattr(evaluate, "REPORTS", tmp_path / "reports")


def test_the_evaluation_reports_the_automatic_checks_by_neutral_id(tmp_path, capsys):
    docs = tmp_path / "set"
    docs.mkdir()
    make_text_pdf(docs / "Private looking name.pdf", pages=4)
    make_slide_pdf(docs / "deck.pdf")
    make_pptx(docs / "talk.pptx")
    make_docx(docs / "notes.docx")
    (docs / "copy of notes.docx").write_bytes((docs / "notes.docx").read_bytes())
    assert evaluate.main(["--set", str(docs), "--no-ocr"]) == 0
    out = capsys.readouterr().out
    assert "5 files, 4 documents (unique contents; 1 duplicate file not counted again), 4 checked, 0 left out" in out
    assert "by format: docx (prose) 1, pdf prose 1, pdf slides 1, pptx (slides) 1" in out
    assert "Problems: 0" in out and "Status: complete; exit code 0" in out
    rows = [("baseline", g) for g in ("docx (prose)", "pdf prose", "pdf slides", "pptx (slides)")] \
        + [("ranking", "docx (prose)"), ("ranking", "pdf prose"), ("structure", "pdf slides"),
           ("structure", "pptx (slides)")]
    for method, group in rows:
        row = next(l for l in out.splitlines() if l.startswith(f"{method:10} {group:14}"))
        assert row.count("1/1") == len(evaluate.CHECKS)
    assert "Private" not in out and "deck" not in out and str(tmp_path) not in out      # neutral IDs only
    assert "Private" not in (tmp_path / "doc_ids.csv").read_text(encoding="utf-8")
    saved = next((tmp_path / "reports").iterdir()).read_text(encoding="utf-8")
    assert "Status: complete" in saved and "OCR off" in saved and "Set fingerprint" in saved and "Private" not in saved


def test_held_out_sets_are_refused(tmp_path, capsys):
    for name in ("final-check", "Validation", "FINAL-EVAL"):
        held = tmp_path / name
        held.mkdir()
        assert evaluate.main(["--set", str(held)]) == 2
    assert "Refused" in capsys.readouterr().out


def test_a_parent_of_a_held_out_set_is_refused_before_any_file_is_opened(tmp_path, monkeypatch, capsys):
    parent = tmp_path / "parent"
    (parent / "nested" / "Validation").mkdir(parents=True)
    make_docx(parent / "dev.docx")
    sentinel = make_docx(parent / "nested" / "Validation" / "invented.docx")
    read = []
    monkeypatch.setattr(evaluate.Path, "read_bytes", lambda self: read.append(self))
    assert evaluate.main(["--set", str(parent)]) == 2
    assert "Refused" in capsys.readouterr().out
    assert read == []                                                           # nothing was read or hashed
    assert sentinel.is_file()


@pytest.mark.skipif(os.name != "nt", reason="junctions are a Windows feature")
def test_a_junction_that_leads_into_a_held_out_set_is_refused(tmp_path, capsys):
    held = tmp_path / "final-check"
    held.mkdir()
    make_docx(held / "invented.docx")
    root = tmp_path / "dev"
    root.mkdir()
    subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "innocent"), str(held)], check=True, capture_output=True)
    assert evaluate.main(["--set", str(root)]) == 2
    assert "Refused" in capsys.readouterr().out


def test_a_missing_or_empty_set_is_not_a_success(tmp_path, capsys):
    assert evaluate.main(["--set", str(tmp_path / "missing")]) == 2
    (tmp_path / "empty").mkdir()
    assert evaluate.main(["--set", str(tmp_path / "empty")]) == 2
    out = capsys.readouterr().out
    assert "does not exist" in out and "Nothing to check" in out


def test_a_failing_check_and_an_unreadable_file_fail_the_command(tmp_path, monkeypatch, capsys):
    docs = tmp_path / "set"
    docs.mkdir()
    make_docx(docs / "a.docx")
    (docs / "broken.pdf").write_bytes(b"%PDF-1.4 not really a pdf")
    assert evaluate.main(["--set", str(docs), "--no-ocr"]) == 3                # left out, no check failed
    out = capsys.readouterr().out
    assert "1 checked, 1 left out" in out and "unreadable" in out and "exit code 3" in out
    real = evaluate.evaluate

    def failing(files, tmp, progress):
        results, failures, left_out, kinds, empty = real(files, tmp, progress)
        return results, failures + [("D1", "baseline", "traceable", "brief line 1: invented")], left_out, kinds, empty
    monkeypatch.setattr(evaluate, "evaluate", failing)
    assert evaluate.main(["--set", str(docs), "--no-ocr"]) == 1


def test_a_document_that_hangs_is_stopped_and_left_out(tmp_path, monkeypatch, capsys):
    docs = tmp_path / "set"
    docs.mkdir()
    make_docx(docs / "a.docx")
    monkeypatch.setattr(evaluate, "DOC_LIMIT", 0)
    assert evaluate.main(["--set", str(docs), "--no-ocr"]) == 3
    assert "took longer than the time limit" in capsys.readouterr().out


def test_the_range_beside_a_share():
    assert evaluate.wilson(0, 0) == (0.0, 0.0)
    lo, hi = evaluate.wilson(10, 10)
    assert hi == 1.0 and 0.65 < lo < 0.75
