"""The SummarEase window: open a document or paste text, and read it as readable text. Run: python -m summarease.app

The document is read in a worker process (worker.py); the window polls it and is updated in place. Pasted text stays
in memory (record C9). Logs carry counts and fixed reasons only: never document text or file names."""
import logging
import multiprocessing
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextBrowser, QVBoxLayout, QWidget,
)

from . import tokens as tk
from .readable import Block, from_record, from_text, to_html
from .reader import READERS
from .worker import ReadJob

ICON = Path(__file__).resolve().parent.parent / "assets" / "icons" / "summarease" / "summarease.ico"
POLL_MS = 100
FORMATS = "PDF, PPTX, DOCX and ODT"
WELCOME = f"Open a document ({FORMATS}) or paste text. Nothing you paste is stored."
log = logging.getLogger("summarease")


def style_sheet(t):
    """The window's style sheet for a theme: every colour comes from it, none from the system."""
    return f"""
QWidget {{ font-family: "{tk.FONT}"; font-size: {tk.TEXT_BODY}px; color: {t['text']}; }}
QMainWindow, QWidget#page {{ background: {t['window']}; }}
QLabel#status {{ font-size: {tk.TEXT_SECONDARY}px; color: {t['secondary']}; }}
QPushButton {{ border: {tk.HAIR}px solid {t['control']}; border-radius: {tk.RADIUS_CONTROL}px; background: transparent;
               color: {t['text']}; padding: {tk.RELATED - tk.HAIR}px {tk.GROUP - tk.HAIR}px;
               min-height: {tk.CONTROL_TEXT}px; }}
QPushButton:hover {{ background: {t['hover']}; }}
QPushButton:pressed {{ background: {t['pressed']}; }}
QPushButton#primary {{ background: {t['primary']}; color: {t['on_primary']}; border-color: {t['primary']};
                       font-weight: {tk.WEIGHT_STRONG}; }}
QPushButton#primary:hover {{ background: {t['primary_hover']}; border-color: {t['primary_hover']}; }}
QPushButton:focus {{ border: {tk.HAIR + 1}px solid {t['accent']}; }}
QTextBrowser {{ background: {t['base']}; border: {tk.HAIR}px solid {t['divider']}; border-radius: {tk.RADIUS_CONTROL}px;
                selection-background-color: {t['selection']}; selection-color: {t['text']}; }}
QTextBrowser:focus {{ border-color: {t['accent']}; }}
"""


def qt_palette(t):
    """The Qt palette for a theme: what native drawing (scroll bars, dialogs) uses."""
    p = QPalette()
    for role, key in ((QPalette.Window, "window"), (QPalette.WindowText, "text"), (QPalette.Base, "base"),
                      (QPalette.AlternateBase, "hover"), (QPalette.Text, "text"), (QPalette.Button, "raised"),
                      (QPalette.ButtonText, "text"), (QPalette.PlaceholderText, "secondary"),
                      (QPalette.Highlight, "selection"), (QPalette.HighlightedText, "text"), (QPalette.Link, "link"),
                      (QPalette.ToolTipBase, "raised"), (QPalette.ToolTipText, "text"), (QPalette.Mid, "control"),
                      (QPalette.Midlight, "divider"), (QPalette.Dark, "control")):
        p.setColor(role, QColor(t[key]))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, QColor(t["disabled"]))
    return p


def system_theme():
    return "dark" if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark else "light"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SummarEase")
        self.setWindowIcon(QIcon(str(ICON)))
        self.resize(*tk.WINDOW)
        self.setAcceptDrops(True)
        self.blocks, self.job, self.theme, self.reading = [], None, None, None

        self.open_button = QPushButton("Open a document…")
        self.open_button.setObjectName("primary")
        self.open_button.clicked.connect(self.choose_file)
        self.paste_button = QPushButton("Paste text")
        self.paste_button.setToolTip("Show the text on the clipboard as readable text. It is not stored.")
        self.paste_button.clicked.connect(lambda: self.paste_text())
        QShortcut(QKeySequence.Paste, self, lambda: self.paste_text())
        QShortcut(QKeySequence.Open, self, self.choose_file)
        self.status = QLabel(WELCOME)
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.view = QTextBrowser()
        self.view.setOpenLinks(False)
        self.view.setAccessibleName("Readable text")
        self.view.setMaximumWidth(tk.READING_WIDTH)
        self.view.document().setDocumentMargin(tk.PAD)

        bar = QHBoxLayout()
        bar.setSpacing(tk.RELATED)
        bar.addWidget(self.open_button)
        bar.addWidget(self.paste_button)
        bar.addStretch()
        column = QVBoxLayout()
        column.setContentsMargins(tk.PAD, tk.PAD, tk.PAD, tk.PAD)
        column.setSpacing(tk.GROUP)
        column.addLayout(bar)
        column.addWidget(self.status)
        column.addWidget(self.view, 1, Qt.AlignHCenter)
        page = QWidget()
        page.setObjectName("page")
        page.setLayout(column)
        self.setCentralWidget(page)

        self.timer = QTimer(self, interval=POLL_MS)
        self.timer.timeout.connect(self._poll)
        QGuiApplication.styleHints().colorSchemeChanged.connect(lambda *_: self.apply_theme())
        self.apply_theme()

    # -- theme ----------------------------------------------------------------------------------------------------
    def apply_theme(self, name=None):
        """Use "light", "dark" or (None) Windows' setting: the style sheet, the palette and the text are rebuilt,
        in place, keeping the scroll position."""
        name = name or system_theme()
        if name == self.theme:
            return
        self.theme = name
        t = tk.THEMES[name]
        QApplication.setPalette(qt_palette(t))
        self.setStyleSheet(style_sheet(t))
        self._render(keep_scroll=True)

    def _render(self, keep_scroll=False):
        bar = self.view.verticalScrollBar()
        at = bar.value()
        self.view.setHtml(to_html(self.blocks, tk.THEMES[self.theme]))
        bar.setValue(at if keep_scroll else 0)

    def show_blocks(self, blocks, status, title=None):
        self.blocks = blocks
        self.status.setText(status)
        self.setWindowTitle(f"{title} - SummarEase" if title else "SummarEase")
        self._render()

    # -- input ----------------------------------------------------------------------------------------------------
    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open a document", "",
                                              "Documents (" + " ".join(f"*{e}" for e in READERS) + ")")
        if path:
            self.open_file(path)

    def open_file(self, path):
        path = Path(path)
        if path.suffix.lower() not in READERS:
            self.status.setText(f"SummarEase reads {FORMATS} files. This one was not opened.")
            return
        self.cancel()
        self.job = ReadJob(path)
        self.reading = path.name
        self.show_blocks([], "Reading…", path.name)
        self.timer.start()

    def paste_text(self, text=None):
        """Show pasted text (the clipboard's, unless given). It is kept in memory only, never written anywhere."""
        text = QGuiApplication.clipboard().text() if text is None else text
        if not text.strip():
            self.status.setText("The clipboard has no text to paste.")
            return
        self.cancel()
        self.show_blocks(from_text(text), "Pasted text. It is not stored.", "Pasted text")
        log.info("pasted text shown: %d words", len(text.split()))

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() or e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if files:
            self.open_file(files[0])
            if len(files) > 1:
                self.status.setText(self.status.text() + " Only the first of the dropped files is shown.")
        elif e.mimeData().hasText():
            self.paste_text(e.mimeData().text())

    # -- reading --------------------------------------------------------------------------------------------------
    def _poll(self):
        res = self.job.poll() if self.job else None
        if res is None:
            return
        seconds = time.monotonic() - self.job.started
        self.job = None
        self.timer.stop()
        if res.status == "ok":
            rec = res.record
            blocks = from_record(rec)
            gaps = blocks[0].kind == "gap" if blocks else False
            counts = f"{rec.unit_count} {rec.unit}{'s' * (rec.unit_count != 1)}" if rec.unit != "block" else ""
            status = " · ".join(s for s in (counts, "Some parts couldn't be read; they are marked in the text"
                                            if gaps else "", "OCR text is marked"
                                            if any(b.kind == "ocr" for b in blocks) else "") if s)
            if not any(b.kind not in ("label", "note", "gap") for b in blocks):
                status = (status + " · " if status else "") + "No text was found in this document."
            self.show_blocks(blocks, status or "Shown in full.", self.reading)
            log.info("read %s: %d %ss, %d blocks, gaps=%s, %.1f s", rec.format, rec.unit_count, rec.unit,
                     len(blocks), gaps, seconds)
        else:
            reason = "it is too large to read" if res.status == "pending" else res.reason
            self.show_blocks([Block("gap", f"This document could not be read: {reason}.")],
                             "The document was not shown.", self.reading)
            log.info("read %s: %s, %.1f s", res.status, reason, seconds)

    def cancel(self):
        if self.job:
            self.job.cancel()
            self.job = None
            self.timer.stop()

    def closeEvent(self, e):
        self.cancel()
        super().closeEvent(e)


def main():
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("SummarEase")
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
