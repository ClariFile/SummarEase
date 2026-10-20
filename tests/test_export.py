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


# -- H6: a failed export never leaves a file that looks finished; the readable text exports too (C14) -------------
def test_a_write_failure_leaves_no_final_file_and_keeps_every_existing_file(tmp_path, monkeypatch):
    taken = tmp_path / "Summary.pdf"
    taken.write_bytes(b"the user's own file")

    def disk_full(fd):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(export.os, "fsync", disk_full)
    with pytest.raises(OSError):
        export.save(present.paragraphs(summary()), taken)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Summary.pdf"] and taken.read_bytes() == b"the user's own file"


def test_a_read_back_mismatch_removes_the_new_file(tmp_path, monkeypatch):
    data = export.prepare(present.paragraphs(summary()), ".docx")
    real = export.Path.read_bytes
    monkeypatch.setattr(export.Path, "read_bytes", lambda self: real(self)[:16])
    with pytest.raises(export.ExportError):
        export.publish(data, tmp_path / "Summary.docx")
    assert list(tmp_path.iterdir()) == []


def test_a_competing_writer_never_loses_its_file(tmp_path, monkeypatch):
    data = export.prepare(present.paragraphs(summary()), ".pdf")
    real = export.free_name
    raced = []

    def racing(path):
        name = real(path)
        if not raced:                       # another program takes the free name just before we create it
            name.write_bytes(b"theirs")
            raced.append(name)
        return name
    monkeypatch.setattr(export, "free_name", racing)
    final, _ = export.publish(data, tmp_path / "Summary.pdf")
    assert raced[0].read_bytes() == b"theirs" and final != raced[0] and final.read_bytes() == data


def test_the_check_copy_is_made_in_the_system_temporary_folder_not_beside_the_export(tmp_path, monkeypatch):
    made = []
    real = export.tempfile.mkstemp
    monkeypatch.setattr(export.tempfile, "mkstemp", lambda **kw: (made.append(kw), real(**kw))[1])
    export.save(present.paragraphs(summary()), tmp_path / "Summary.pdf")
    assert made and all("dir" not in kw for kw in made)


@pytest.mark.parametrize("suffix", [".pdf", ".docx"])
def test_the_readable_text_exports_word_for_word_with_its_marks(tmp_path, suffix):
    from summarease.readable import Block, OCR_CAPTION

    blocks = [Block("label", "Page 1", unit=1), Block("heading", "Invented heading", unit=1),
              Block("paragraph", "A paragraph of invented words.", unit=1), Block("list", rows=["One item", "Two"], unit=1),
              Block("table", rows=[["Cell a", "Cell b"]], unit=1), Block("note", OCR_CAPTION, unit=1),
              Block("ocr", "Words read by OCR\nOn two lines", unit=1)]
    paras = present.source_paragraphs(blocks)
    final, _ = export.save(paras, tmp_path / f"Readable{suffix}")
    export.check(final, paras)
    text = present.as_text(paras)
    assert OCR_CAPTION in text and "Cell a | Cell b" in text and "• One item" in text
    for b in blocks:
        for w in b.words():
            assert w in text.split()
