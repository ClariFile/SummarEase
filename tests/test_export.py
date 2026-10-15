"""Export (record C6, C14): new PDF and Word files whose text is the summary's, word for word and searchable; nothing
that exists is ever overwritten; a file that fails its check is never saved."""
import hashlib

import pytest

from summarease import export, present
from summarease.readable import from_text
from summarease.summarize import build, source_from_text

TEXT = "\n\n".join(f"Paragraph {i} explains caching, “quotes”, naïve café words, office files to find, efficient affine flows and memory. It adds detail."
                   for i in range(1, 7))


def summary(level="detailed"):
    return build(source_from_text(from_text(TEXT)), level, "baseline")


@pytest.mark.parametrize("suffix", [".pdf", ".docx"])
def test_an_export_is_a_new_file_whose_text_is_the_summary(tmp_path, suffix):
    paras = present.paragraphs(summary())
    final, sha = export.save(paras, tmp_path / f"Summary{suffix}")
    assert final == tmp_path / f"Summary{suffix}" and hashlib.sha256(final.read_bytes()).hexdigest() == sha
    export.check(final, paras)                                   # the reader reads it back, word for word
    assert sorted(p.name for p in tmp_path.iterdir()) == [f"Summary{suffix}"]   # no temporary file left


@pytest.mark.parametrize("suffix", [".pdf", ".docx"])
def test_an_existing_file_is_never_overwritten(tmp_path, suffix):
    taken = tmp_path / f"Summary{suffix}"
    taken.write_bytes(b"the user's own file")
    (tmp_path / f"Summary (2){suffix}").write_bytes(b"another")
    final, _ = export.save(present.paragraphs(summary()), taken)
    assert final.name == f"Summary (3){suffix}"
    assert taken.read_bytes() == b"the user's own file"
    assert (tmp_path / f"Summary (2){suffix}").read_bytes() == b"another"


def test_a_file_that_fails_its_check_is_not_saved(tmp_path, monkeypatch):
    def bad(path, paras):
        raise export.ExportError("the new file's text did not match the summary")
    monkeypatch.setattr(export, "check", bad)
    with pytest.raises(export.ExportError):
        export.save(present.paragraphs(summary()), tmp_path / "Summary.pdf")
    assert list(tmp_path.iterdir()) == []


def test_other_formats_are_refused(tmp_path):
    with pytest.raises(export.ExportError):
        export.save(present.paragraphs(summary()), tmp_path / "Summary.txt")


def test_copy_export_and_screen_say_the_same_and_mark_where_each_line_is_from():
    s = summary("key")
    text = present.as_text(s)
    assert text.startswith("Key points summary\n" + present.NOTE)
    for line in s.lines:
        assert f"• {line.text} ({present.where(s, line)})" in text
    assert present.where(s, s.lines[0]) == "Paragraph 1" or present.where(s, s.lines[0]).startswith("Paragraph")


def test_the_pdf_can_be_searched_for_its_words_including_ligature_pairs(tmp_path):
    import pymupdf

    final, _ = export.save(present.paragraphs(summary()), tmp_path / "Summary.pdf")
    with pymupdf.open(final) as doc:
        for word in ("office", "files", "find", "efficient", "affine", "flows", "café"):
            assert any(page.search_for(word) for page in doc), word
