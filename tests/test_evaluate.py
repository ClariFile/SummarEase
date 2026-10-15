"""The one evaluation command: runs on a set of invented documents, reports every automatic check with no problems,
names documents by neutral IDs only, and refuses held-out sets."""
from office_fixtures import make_docx, make_pptx
from tools import evaluate
from tools.sample_docs import make_slide_pdf, make_text_pdf


def test_the_evaluation_reports_the_automatic_checks_by_neutral_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(evaluate, "IDS", tmp_path / "doc_ids.csv")
    docs = tmp_path / "set"
    docs.mkdir()
    make_text_pdf(docs / "Private looking name.pdf", pages=4)
    make_slide_pdf(docs / "deck.pdf")
    make_pptx(docs / "talk.pptx")
    make_docx(docs / "notes.docx")
    assert evaluate.main(["--set", str(docs), "--no-ocr"]) == 0
    out = capsys.readouterr().out
    assert "4 documents found, 4 counted, 0 left out" in out and "by kind: prose 2, slides 2" in out
    assert "Problems: 0" in out
    for method, kind in (("baseline", "prose"), ("baseline", "slides"), ("ranking", "prose"), ("structure", "slides")):
        row = next(l for l in out.splitlines() if l.startswith(f"{method:10} {kind:7}"))
        assert row.count("2/2") == len(evaluate.CHECKS)
    assert "Private" not in out and "deck" not in out                  # neutral IDs only
    assert "Private" not in (tmp_path / "doc_ids.csv").read_text(encoding="utf-8")


def test_held_out_sets_are_refused(tmp_path, capsys):
    for name in ("final-check", "validation", "final-eval"):
        held = tmp_path / name
        held.mkdir()
        assert evaluate.main(["--set", str(held)]) == 2
    assert "Refused" in capsys.readouterr().out


def test_the_range_beside_a_share():
    assert evaluate.wilson(0, 0) == (0.0, 0.0)
    lo, hi = evaluate.wilson(10, 10)
    assert hi == 1.0 and 0.65 < lo < 0.75
