"""The window: it opens offline; shows a document's words as the reader gave them; leaves the original unchanged;
stores nothing pasted; logs no document text or file name; lays out Source and Summary side by side or as tabs;
and runs the summary only when asked, keeping the last one until the next is ready."""
import hashlib
import logging
import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtGui import QFont, QFontMetrics  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from office_fixtures import make_docx, make_pptx  # noqa: E402
from summarease import tokens  # noqa: E402
from summarease.app import EMPTY_SOURCE, EMPTY_SUMMARY, ICON, READY_SUMMARY, MainWindow, style_sheet  # noqa: E402
from summarease.readable import doc_words, words  # noqa: E402
from summarease.reader import read_document  # noqa: E402
from summarease.summarize import LEVEL_HINTS  # noqa: E402
from test_readable import reader_words  # noqa: E402
from tools.sample_docs import make_text_pdf  # noqa: E402

LIMIT = 120   # seconds; only stops a hung test


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    yield w
    w.close()


def wait(cond):
    end = time.monotonic() + LIMIT
    while not cond() and time.monotonic() < end:
        QTest.qWait(50)                                                 # events run while waiting
    assert cond(), "the worker gave no result"


def read_in(w, path):
    w.open_file(path)
    wait(lambda: w.read_job is None)


def summarize_in(w, level):
    w.level.setCurrentIndex(w.level.findData(level))
    w.start_summary()
    wait(lambda: w.sum_job is None)


def test_the_window_opens_offline_and_empty(window):
    assert window.isVisible() and window.windowTitle() == "SummarEase"
    assert ICON.is_file() and not window.windowIcon().isNull()
    assert EMPTY_SOURCE in window.source_view.toPlainText()
    assert EMPTY_SUMMARY in window.summary_view.toPlainText()
    assert not window.summarize_button.isEnabled() and not window.copy_button.isEnabled()


@pytest.mark.parametrize("make, name", [(make_docx, "a.docx"), (make_pptx, "a.pptx")])
def test_opening_shows_the_readers_words_and_leaves_the_original_unchanged(window, tmp_path, caplog, capfd, make,
                                                                          name):
    caplog.set_level(logging.DEBUG)
    path = make(tmp_path / name)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    read_in(window, path)
    summarize_in(window, "comprehensive")
    assert doc_words(window.blocks) == reader_words(read_document(path).record)
    assert window.doc_label.full == name and window.summary.lines
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [name]          # nothing written next to it
    logged = caplog.text + "".join(capfd.readouterr())
    assert "read " in caplog.text and "summary comprehensive" in caplog.text
    for secret in ("Handbook", "Firewalls", "normalization", "Packet", name, str(tmp_path)):
        assert secret not in logged                                     # no text and no name in the logs


def test_pasted_text_is_shown_summarized_and_never_stored(window, tmp_path, monkeypatch, caplog, capfd):
    caplog.set_level(logging.DEBUG)
    for var in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOME", "TEMP", "TMP"):
        monkeypatch.setenv(var, str(tmp_path / var))
    monkeypatch.chdir(tmp_path)
    secret = "Invented pasted sentence about quokka migration routes. It has a second sentence too."
    QApplication.clipboard().setText(secret)
    window.paste_button.click()
    assert words(window.source_view.toPlainText()) == words(secret)
    assert "not stored" in window.doc_label.full
    summarize_in(window, "key")
    assert "quokka" in window.summary_view.toPlainText()
    assert list(tmp_path.rglob("*")) == []                              # no file, no folder, anywhere
    assert "quokka" not in caplog.text + "".join(capfd.readouterr())


def test_changing_the_level_never_starts_work_or_clears_the_summary(window, tmp_path):
    read_in(window, make_text_pdf(tmp_path / "t.pdf", pages=3))
    assert READY_SUMMARY in window.summary_view.toPlainText()
    summarize_in(window, "key")
    shown = window.summary_view.toPlainText()
    window.level.setCurrentIndex(window.level.findData("detailed"))
    assert window.sum_job is None and window.summary_view.toPlainText() == shown
    assert window.notice.text() == "This is the Key points summary. Press Summarize for Detailed."
    assert window.hint.text() == LEVEL_HINTS["detailed"]
    window.start_summary()
    assert window.summary_state == "working" and window.summary_view.toPlainText() == shown   # last one stays
    assert "Summarizing (Detailed)" in window.notice.text() and not window.summarize_button.isEnabled()
    wait(lambda: window.sum_job is None)
    assert window.summary.level == "detailed" and window.summary_view.toPlainText() != shown
    assert window.notice.text().startswith("Detailed:")


def test_a_failed_summary_says_why_and_keeps_the_last_one(window, tmp_path, monkeypatch):
    read_in(window, make_text_pdf(tmp_path / "t.pdf", pages=2))
    summarize_in(window, "key")
    shown = window.summary_view.toPlainText()
    window._summary_done(("failed", "it took longer than the time limit"), 1.0)
    assert window.summary_view.toPlainText() == shown
    assert window.notice.text() == ("Couldn't summarize: it took longer than the time limit. "
                                    "The last summary is still shown.")
    assert window.notice.property("state") == "error"


def test_a_link_in_the_summary_scrolls_the_source_there(window, tmp_path):
    window.resize(1400, 700)
    read_in(window, make_text_pdf(tmp_path / "t.pdf", pages=12))
    summarize_in(window, "detailed")
    last = window.summary.lines[-1]
    assert last.unit > 3
    bar = window.source_view.verticalScrollBar()
    assert bar.value() == 0
    window.follow(QUrl(f"#u{last.unit}"), "summary")
    assert bar.value() > 0
    window.resize(700, 700)                                             # narrow: tabs
    QApplication.processEvents()
    window.tabs.setCurrentWidget(window.summary_pane)
    window.follow(QUrl("#u1"), "summary")
    assert window.tabs.currentWidget() is window.source_pane


def test_wide_windows_show_both_panes_narrow_windows_use_tabs(window):
    window.resize(1400, 800)
    QApplication.processEvents()
    assert window.stack.currentWidget() is window.splitter and window.splitter.count() == 2
    source, summary = window.splitter.sizes()
    assert summary > source                                             # Summary slightly wider
    window.resize(800, 800)
    QApplication.processEvents()
    assert window.stack.currentWidget() is window.tabs and window.tabs.count() == 2
    assert [window.tabs.tabText(i) for i in range(2)] == ["Source", "Summary"]
    window.resize(1400, 800)
    QApplication.processEvents()
    assert window.splitter.count() == 2 and window.tabs.count() == 0


def test_text_lines_stop_at_a_reading_width_while_the_pane_fills_the_window(window, tmp_path):
    """The column is READING_CHARS characters of ordinary text in the reading font. (The test platform draws every
    character equally wide, so the pixel width is checked in the screenshots, drawn with Windows' fonts.)"""
    read_in(window, make_text_pdf(tmp_path / "t.pdf", pages=1))
    view = window.source_view
    font = QFont(tokens.FONT)
    font.setPixelSize(tokens.TEXT_READING)
    sample = "the quick brown fox jumps over the lazy dog "
    assert abs(view.column / (QFontMetrics(font).horizontalAdvance(sample) / len(sample)) - tokens.READING_CHARS) < 1
    view.column = 300                                                   # a pane wider than its text column
    for width in (1600, 2400):
        window.resize(width, 900)
        QApplication.processEvents()
        fmt = view.document().rootFrame().frameFormat()
        assert fmt.leftMargin() == tokens.PAD                           # in line with the controls above
        assert view.viewport().width() - fmt.leftMargin() - fmt.rightMargin() == view.column
        assert view.width() > view.column + 2 * tokens.PAD              # the pane fills, the lines do not


def test_a_long_document_name_is_shortened_in_the_header(window):
    window.resize(900, 700)
    name = "A very long invented document name " * 6 + ".pdf"
    window.doc_label.set_full(name)
    QApplication.processEvents()
    assert "…" in window.doc_label.text() and window.doc_label.toolTip() == name


def test_copy_and_export_the_shown_summary(window, tmp_path):
    read_in(window, make_text_pdf(tmp_path / "t.pdf", pages=2))
    summarize_in(window, "key")
    window.copy_button.click()
    copied = QApplication.clipboard().text()
    assert copied.startswith("Key points summary") and all(l.text in copied for l in window.summary.lines)
    out = tmp_path / "out"
    out.mkdir()
    (out / "Summary.docx").write_bytes(b"keep me")
    final = window.export_to(out / "Summary.docx")
    assert final.name == "Summary (2).docx" and (out / "Summary.docx").read_bytes() == b"keep me"
    assert "a number was added" in window.notice.text()


def test_the_tab_order_follows_the_screen(window):
    order, w = [], window.open_button
    w.setFocus()
    for _ in range(8):
        order.append(w)
        w = w.nextInFocusChain()
        while not (w.focusPolicy() & 0x1) or not w.isVisibleTo(window):   # Qt.TabFocus
            w = w.nextInFocusChain()
    assert order[:7] == [window.open_button, window.paste_button, window.source_view, window.copy_button,
                         window.export_button, window.level, window.summarize_button]


def test_switching_the_theme_rebuilds_the_look_in_place_and_keeps_the_scroll_position(window):
    window.resize(1200, 500)
    window.paste_text("\n\n".join(f"Paragraph number {i} of invented text." for i in range(200)))
    QApplication.processEvents()
    bar = window.source_view.verticalScrollBar()
    bar.setValue(bar.maximum() // 2)
    at, view = bar.value(), window.source_view
    for name in ("dark", "light"):
        window.apply_theme(name)
        assert window.styleSheet() == style_sheet(tokens.THEMES[name])
        assert QApplication.palette().window().color().name().upper() == tokens.THEMES[name]["window"]
        assert window.source_view is view and bar.value() == at > 0


def test_an_unknown_format_and_an_unreadable_file_are_said_plainly(window, tmp_path):
    other = tmp_path / "notes.txt"
    other.write_text("x", encoding="utf-8")
    window.open_file(other)
    assert window.read_job is None and "PDF, PPTX, DOCX and ODT" in window.source_status.text()
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"%PDF-1.4 not really a pdf")
    read_in(window, bad)
    assert window.source_status.text() == "Couldn't open broken.pdf: corrupt or unreadable PDF."
