"""The window: it opens offline, shows a document's words as the reader gave them, leaves the original unchanged,
stores nothing pasted, and logs no document text or file name (M1 acceptance)."""
import hashlib
import logging
import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from office_fixtures import make_docx, make_pptx  # noqa: E402
from summarease import tokens  # noqa: E402
from summarease.app import ICON, WELCOME, MainWindow, style_sheet  # noqa: E402
from summarease.readable import doc_words, words  # noqa: E402
from summarease.reader import read_document  # noqa: E402
from test_readable import reader_words  # noqa: E402

LIMIT_MS = 120_000   # only stops a hung test


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    yield w
    w.close()


def read_in(w, path):
    w.open_file(path)
    end = time.monotonic() + LIMIT_MS / 1000
    while w.job is not None and time.monotonic() < end:
        QTest.qWait(50)                                                 # events run while waiting
    assert w.job is None, "the reader gave no result"


def test_the_window_opens_offline(window):
    assert window.isVisible() and window.windowTitle() == "SummarEase"
    assert ICON.is_file() and not window.windowIcon().isNull()
    assert window.status.text() == WELCOME


@pytest.mark.parametrize("make, name", [(make_docx, "a.docx"), (make_pptx, "a.pptx")])
def test_opening_shows_the_readers_words_and_leaves_the_original_unchanged(window, tmp_path, caplog, capfd, make,
                                                                          name):
    caplog.set_level(logging.DEBUG)
    path = make(tmp_path / name)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    read_in(window, path)
    assert doc_words(window.blocks) == reader_words(read_document(path).record)
    assert words(window.view.toPlainText()) == [w for b in window.blocks for w in b.words()]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [name]          # nothing written next to it
    logged = caplog.text + "".join(capfd.readouterr())
    assert "read " in caplog.text                                       # the read was logged ...
    for secret in ("Handbook", "Firewalls", "normalization", "Packet", name, str(tmp_path)):
        assert secret not in logged                                     # ... without its text or its name


def test_pasted_text_is_shown_and_never_stored(window, tmp_path, monkeypatch, caplog, capfd):
    caplog.set_level(logging.DEBUG)
    for var in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOME", "TEMP", "TMP"):
        monkeypatch.setenv(var, str(tmp_path / var))
    monkeypatch.chdir(tmp_path)
    secret = "Invented pasted sentence about quokka migration."
    QApplication.clipboard().setText(secret)
    window.paste_button.click()
    assert words(window.view.toPlainText()) == words(secret)
    assert "not stored" in window.status.text()
    assert list(tmp_path.rglob("*")) == []                              # no file, no folder, anywhere it could go
    assert "quokka" not in caplog.text + "".join(capfd.readouterr())


def test_an_empty_clipboard_and_an_unknown_format_are_said_plainly(window, tmp_path):
    QApplication.clipboard().setText("  ")
    window.paste_text()
    assert window.status.text() == "The clipboard has no text to paste." and window.blocks == []
    other = tmp_path / "notes.txt"
    other.write_text("x", encoding="utf-8")
    window.open_file(other)
    assert window.job is None and "PDF, PPTX, DOCX and ODT" in window.status.text()


def test_a_document_that_cannot_be_read_says_why(window, tmp_path):
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"%PDF-1.4 not really a pdf")
    read_in(window, bad)
    assert "could not be read: corrupt or unreadable PDF" in window.view.toPlainText()


def test_switching_the_theme_rebuilds_the_look_in_place_and_keeps_the_scroll_position(window):
    window.resize(600, 400)
    window.paste_text("\n\n".join(f"Paragraph number {i} of invented text." for i in range(200)))
    QApplication.processEvents()
    bar = window.view.verticalScrollBar()
    bar.setValue(bar.maximum() // 2)
    at, view = bar.value(), window.view
    for name in ("dark", "light"):
        window.apply_theme(name)
        assert window.styleSheet() == style_sheet(tokens.THEMES[name])
        assert QApplication.palette().window().color().name().upper() == tokens.THEMES[name]["window"]
        assert window.view is view and bar.value() == at > 0
