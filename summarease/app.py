"""The SummarEase window. Run: python -m summarease.app

A compact header (the app, the document's name, Open and Paste), then the workspace: the Source pane (the readable
text) and the Summary pane (the detail level, Summarize, Copy and Export), side by side and resizable, or as two tabs
on a narrow window. Reading and summarizing run in worker processes (worker.py); the window polls them and is updated
in place. Pasted text stays in memory (record C9). Logs carry counts and fixed reasons only: never document text or
file names."""
import ctypes
import logging
import multiprocessing
import sys
import time
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSplitter,
    QStackedWidget, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from . import export, present
from . import tokens as tk
from .readable import DETAILS, from_record, from_text, to_html
from .reader import READERS
from .summarize import (
    DEFAULT_LEVEL, LEVEL_HINTS, LEVEL_NAMES, LEVELS, source_from_record, source_from_text, summarize,
)
from .worker import Job, call, read

ICON = Path(__file__).resolve().parent.parent / "assets" / "icons" / "summarease" / "summarease.ico"
POLL_MS = 100
SUMMARIZE_LIMIT = 120   # seconds
FORMATS = "PDF, PPTX, DOCX and ODT"
EMPTY_SOURCE = f"Open a document ({FORMATS}) or paste text. Nothing you paste is stored."
EMPTY_SUMMARY = "Open a document or paste text, then press Summarize."
READY_SUMMARY = "Choose a detail level and press Summarize."
log = logging.getLogger("summarease")


def style_sheet(t):
    """The window's style sheet for a theme: every colour comes from it, none from the system. Violet only on the
    primary button, focus outlines, the current tab's bar and links (as teal in ClassiFile)."""
    return f"""
QWidget {{ font-family: "{tk.FONT}"; font-size: {tk.TEXT_BODY}px; color: {t['text']}; }}
QMainWindow, QWidget#page {{ background: {t['window']}; }}
QFrame#pane {{ background: {t['base']}; border-radius: {tk.RADIUS_PANEL}px; }}
QLabel#brand {{ font-size: {tk.TEXT_HEADING}px; font-weight: {tk.WEIGHT_STRONG}; }}
QLabel#docname, QLabel#secondary {{ color: {t['secondary']}; }}
QLabel#hint, QLabel#notice {{ font-size: {tk.TEXT_SECONDARY}px; color: {t['secondary']}; }}
QLabel#notice[state="error"] {{ color: {t['red']}; }}
QLabel#caption {{ font-size: {tk.TEXT_CAPTION}px; font-weight: {tk.WEIGHT_STRONG}; color: {t['secondary']};
                  letter-spacing: {tk.SPACED}px; }}
QPushButton {{ border: {tk.HAIR}px solid {t['control']}; border-radius: {tk.RADIUS_CONTROL}px; background: transparent;
               color: {t['text']}; padding: {tk.RELATED - tk.HAIR}px {tk.GROUP - tk.HAIR}px;
               min-height: {tk.CONTROL_TEXT}px; }}
QPushButton:hover {{ background: {t['hover']}; }}
QPushButton:pressed {{ background: {t['pressed']}; }}
QPushButton:disabled {{ color: {t['disabled']}; border-color: {t['disabled_fill']}; }}
QPushButton#primary {{ background: {t['primary']}; color: {t['on_primary']}; border-color: {t['primary']};
                       font-weight: {tk.WEIGHT_STRONG}; }}
QPushButton#primary:hover {{ background: {t['primary_hover']}; border-color: {t['primary_hover']}; }}
QPushButton#primary:disabled {{ background: {t['disabled_fill']}; color: {t['disabled']};
                                border-color: {t['disabled_fill']}; }}
QPushButton:focus, QComboBox:focus {{ border: {tk.HAIR + 1}px solid {t['accent']}; }}
QComboBox {{ border: {tk.HAIR}px solid {t['control']}; border-radius: {tk.RADIUS_CONTROL}px; background: {t['base']};
             padding: {tk.RELATED - tk.HAIR}px {tk.RELATED + tk.TIGHT}px; min-height: {tk.CONTROL_TEXT}px; }}
QComboBox:hover {{ background: {t['hover']}; }}
QComboBox QAbstractItemView {{ background: {t['raised']}; border: {tk.HAIR}px solid {t['divider']};
                               selection-background-color: {t['selection']}; selection-color: {t['text']}; }}
QTextBrowser {{ background: {t['base']}; border: none; selection-background-color: {t['selection']};
                selection-color: {t['text']}; }}
QSplitter::handle {{ background: {t['window']}; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; color: {t['secondary']}; padding: {tk.RELATED}px {tk.GROUP}px;
                border: none; border-bottom: {tk.HAIR * 2}px solid transparent; }}
QTabBar::tab:hover {{ color: {t['text']}; background: {t['hover']}; }}
QTabBar::tab:selected {{ color: {t['text']}; border-bottom-color: {t['accent']}; }}
QTabBar::tab:focus {{ color: {t['text']}; }}
QScrollBar:vertical {{ background: transparent; width: {tk.RELATED + tk.TIGHT}px; margin: {tk.TIGHT}px; }}
QScrollBar::handle:vertical {{ background: {t['control']}; border-radius: {tk.TIGHT}px; min-height: {tk.PAD}px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


def qt_palette(t):
    """The Qt palette for a theme: what native drawing (dialogs, menus) uses."""
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


def animations_enabled():
    """Windows' "Animation effects" setting (Reduce motion). Elsewhere, assume on."""
    if sys.platform != "win32":
        return True
    on = ctypes.c_bool(True)
    ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(on), 0)   # SPI_GETCLIENTAREAANIMATION
    return bool(on.value)


def label(text, name):
    w = QLabel(text)
    w.setObjectName(name)
    return w


class ReadingView(QTextBrowser):
    """A pane's one scroll area. The view fills the pane; its text column starts at the pane's padding, in line with
    the controls above it, and stops at about READING_CHARS characters, so lines stay readable at any width."""

    def __init__(self, accessible_name):
        super().__init__()
        self.setOpenLinks(False)
        self.setFrameShape(QFrame.NoFrame)
        self.setAccessibleName(accessible_name)
        font = QFont(tk.FONT)
        font.setPixelSize(tk.TEXT_READING)
        sample = "the quick brown fox jumps over the lazy dog "     # the width of ordinary text, per character
        self.column = round(QFontMetrics(font).horizontalAdvance(sample) / len(sample) * tk.READING_CHARS)

    def set_html(self, html, keep_scroll=False):
        bar = self.verticalScrollBar()
        at = bar.value()
        self.setHtml(html)
        self._fit()
        bar.setValue(at if keep_scroll else 0)

    def _fit(self):
        right = max(tk.PAD, self.viewport().width() - tk.PAD - self.column)
        root = self.document().rootFrame()
        fmt = root.frameFormat()
        if (fmt.leftMargin(), fmt.rightMargin(), fmt.topMargin()) != (tk.PAD, right, tk.PAD):
            fmt.setLeftMargin(tk.PAD)
            fmt.setRightMargin(right)
            fmt.setTopMargin(tk.PAD)
            fmt.setBottomMargin(tk.PAD)
            root.setFrameFormat(fmt)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit()


class ElidedLabel(QLabel):
    """A label that shortens its text with "…" in the middle when it does not fit; the full text is its tooltip."""

    def __init__(self, name):
        super().__init__()
        self.setObjectName(name)
        self.full = ""
        self.setMinimumWidth(tk.PAD * 2)

    def set_full(self, text):
        self.full = text
        self.setToolTip(text)
        self._elide()

    def _elide(self):
        super().setText(self.fontMetrics().elidedText(self.full, Qt.ElideMiddle, self.width()))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide()


def pane(caption, view, beside=(), right=(), rows=()):
    """A pane: its caption row (the caption, widgets beside it, widgets at the right), more rows, then its view."""
    frame = QFrame()
    frame.setObjectName("pane")
    box = QVBoxLayout(frame)
    box.setContentsMargins(0, tk.GROUP, 0, 0)
    box.setSpacing(tk.RELATED)
    top = QHBoxLayout()
    top.setSpacing(tk.RELATED)
    top.addWidget(label(caption, "caption"))
    for w in beside:
        top.addSpacing(tk.RELATED)
        top.addWidget(w)
    top.addStretch()
    for w in right:
        top.addWidget(w)
    for row in (top, *rows):
        row.setContentsMargins(tk.PAD, 0, tk.PAD, 0)
        box.addLayout(row)
    box.addWidget(view, 1)
    return frame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SummarEase")
        self.setWindowIcon(QIcon(str(ICON)))
        self.resize(*tk.WINDOW)
        self.setMinimumSize(*tk.MIN_WINDOW)
        self.setAcceptDrops(True)
        self.theme = None
        self.blocks, self.source, self.name = [], None, None       # what the Source pane shows
        self.summary, self.summary_state = None, "idle"              # idle | working | error
        self.read_job = self.sum_job = None
        self.reading = None
        self.details = {"source": False, "summary": False}         # gap details open

        # header
        self.open_button = QPushButton("Open document…")
        self.open_button.clicked.connect(self.choose_file)
        self.paste_button = QPushButton("Paste text")
        self.paste_button.setToolTip("Show the text on the clipboard. It is not stored.")
        self.paste_button.clicked.connect(lambda: self.paste_text())
        self.doc_label = ElidedLabel("docname")
        header = QHBoxLayout()
        header.setSpacing(tk.RELATED)
        header.addWidget(label("SummarEase", "brand"))
        header.addSpacing(tk.GROUP)
        header.addWidget(self.doc_label, 1)
        header.addSpacing(tk.GROUP)
        header.addWidget(self.open_button)
        header.addWidget(self.paste_button)

        # Source pane
        self.source_status = label("", "secondary")
        self.source_view = ReadingView("Source text")
        self.source_view.anchorClicked.connect(lambda url: self.follow(url, "source"))
        self.source_pane = pane("SOURCE", self.source_view, beside=[self.source_status])

        # Summary pane
        self.level = QComboBox()
        self.level.setAccessibleName("Detail level")
        for key in LEVELS:
            self.level.addItem(LEVEL_NAMES[key], key)
        self.level.setCurrentIndex(LEVELS.index(DEFAULT_LEVEL))
        self.level.currentIndexChanged.connect(self.refresh_summary_controls)
        level_label = label("Detail level", "secondary")
        level_label.setBuddy(self.level)
        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.setObjectName("primary")
        self.summarize_button.clicked.connect(self.start_summary)
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_summary)
        self.export_button = QPushButton("Export…")
        self.export_button.clicked.connect(self.export_summary)
        self.hint = label("", "hint")
        self.notice = label("", "notice")
        self.notice.setWordWrap(True)
        self.summary_view = ReadingView("Summary")
        self.summary_view.anchorClicked.connect(lambda url: self.follow(url, "summary"))
        controls = QHBoxLayout()
        controls.setSpacing(tk.RELATED)
        controls.addWidget(level_label)
        controls.addWidget(self.level)
        controls.addWidget(self.summarize_button)
        controls.addStretch()
        texts = QVBoxLayout()
        texts.setSpacing(tk.TIGHT)
        texts.addWidget(self.hint)
        texts.addWidget(self.notice)
        self.summary_pane = pane("SUMMARY", self.summary_view, right=[self.copy_button, self.export_button],
                                 rows=[controls, texts])

        # workspace: side by side, or tabs when narrow
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(tk.GROUP)
        self.splitter.setChildrenCollapsible(False)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setDrawBase(False)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.splitter)
        self.stack.addWidget(self.tabs)
        self.narrow = None
        self._layout_panes()

        column = QVBoxLayout()
        column.setContentsMargins(tk.PAD, tk.GROUP, tk.PAD, tk.PAD)
        column.setSpacing(tk.GROUP)
        column.addLayout(header)
        column.addWidget(self.stack, 1)
        page = QWidget()
        page.setObjectName("page")
        page.setLayout(column)
        self.setCentralWidget(page)
        order = (self.open_button, self.paste_button, self.source_view, self.copy_button, self.export_button,
                 self.level, self.summarize_button, self.summary_view)         # the screen's order
        for a, b in zip(order, order[1:]):
            QWidget.setTabOrder(a, b)

        QShortcut(QKeySequence.Paste, self, lambda: self.paste_text())
        QShortcut(QKeySequence.Open, self, self.choose_file)
        self.timer = QTimer(self, interval=POLL_MS)
        self.timer.timeout.connect(self._poll)
        QGuiApplication.styleHints().colorSchemeChanged.connect(lambda *_: self.apply_theme())
        self.apply_theme()
        self.refresh_summary_controls()

    # -- layout and theme -----------------------------------------------------------------------------------------
    def _layout_panes(self):
        narrow = self.width() < tk.NARROW
        if narrow == self.narrow:
            return
        self.narrow = narrow
        for caption in self.findChildren(QLabel, "caption"):     # the tabs name the panes
            caption.setVisible(not narrow)
        if narrow:
            self.tabs.addTab(self.source_pane, "Source")
            self.tabs.addTab(self.summary_pane, "Summary")
            self.stack.setCurrentWidget(self.tabs)
        else:
            self.tabs.clear()
            self.splitter.addWidget(self.source_pane)
            self.splitter.addWidget(self.summary_pane)
            self.source_pane.show()
            self.summary_pane.show()
            share = int(1000 * tk.SUMMARY_SHARE)
            self.splitter.setSizes([1000 - share, share])
            self.stack.setCurrentWidget(self.splitter)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._layout_panes()

    def apply_theme(self, name=None):
        """Use "light", "dark" or (None) Windows' setting: the style sheet, the palette and both texts are rebuilt,
        in place, keeping their scroll positions."""
        name = name or system_theme()
        if name == self.theme:
            return
        self.theme = name
        t = tk.THEMES[name]
        QApplication.setPalette(qt_palette(t))
        self.setStyleSheet(style_sheet(t))
        self.render_source(keep_scroll=True)
        self.render_summary(keep_scroll=True)

    def _placeholder(self, text):
        t = tk.THEMES[self.theme]
        return (f'<body style="font-family:\'{tk.FONT}\'; font-size:{tk.TEXT_READING}px;">'
                f'<p style="color:{t["secondary"]};">{text}</p></body>')

    def render_source(self, keep_scroll=False):
        html = to_html(self.blocks, tk.THEMES[self.theme], self.details["source"]) if self.blocks \
            else self._placeholder(EMPTY_SOURCE)
        self.source_view.set_html(html, keep_scroll)

    def render_summary(self, keep_scroll=False):
        if self.summary:
            html = present.to_html(self.summary, tk.THEMES[self.theme], self.details["summary"])
        else:
            html = self._placeholder(READY_SUMMARY if self.source else EMPTY_SUMMARY)
        self.summary_view.set_html(html, keep_scroll)

    # -- input ----------------------------------------------------------------------------------------------------
    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open document", "",
                                              "Documents (" + " ".join(f"*{e}" for e in READERS) + ")")
        if path:
            self.open_file(path)

    def open_file(self, path):
        path = Path(path)
        if path.suffix.lower() not in READERS:
            self.source_status.setText(f"SummarEase reads {FORMATS} files. That file was not opened.")
            return
        if self.read_job:
            self.read_job.cancel()
        self.read_job = Job(read, str(path))
        self.reading = path.name
        self.source_status.setText("Reading…")
        self.timer.start()

    def paste_text(self, text=None):
        """Show pasted text (the clipboard's, unless given). It is kept in memory only, never written anywhere."""
        text = QGuiApplication.clipboard().text() if text is None else text
        if not text.strip():
            self.source_status.setText("The clipboard has no text to paste.")
            return
        if self.read_job:
            self.read_job.cancel()
            self.read_job = None
        blocks = from_text(text)
        self.set_source(blocks, source_from_text(blocks), "Pasted text (not stored)",
                        f"{len(blocks)} paragraph{'s' * (len(blocks) != 1)}")
        log.info("pasted text shown: %d words", len(text.split()))

    def set_source(self, blocks, source, name, status):
        """A new document: the Source pane shows it, and the summary of the last one goes (it is not this one's)."""
        if self.sum_job:
            self.sum_job.cancel()
            self.sum_job = None
        self.blocks, self.source, self.name = blocks, source, name
        self.summary, self.summary_state = None, "idle"
        self.details = {"source": False, "summary": False}
        self.doc_label.set_full(name)
        self.setWindowTitle(f"{name} - SummarEase")
        self.source_status.setText(status)
        self.render_source()
        self.render_summary()
        self.refresh_summary_controls()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() or e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if files:
            self.open_file(files[0])
            if len(files) > 1:
                self.source_status.setText("Reading the first of the dropped files…")
        elif e.mimeData().hasText():
            self.paste_text(e.mimeData().text())

    # -- summary --------------------------------------------------------------------------------------------------
    def chosen_level(self):
        return self.level.currentData()

    def refresh_summary_controls(self):
        """The level's one-line explanation, the buttons, and the notice for the summary's state. Changing the
        level only changes this: it never starts work and never clears the summary shown."""
        level = self.chosen_level()
        self.hint.setText(LEVEL_HINTS[level])
        self.summarize_button.setEnabled(self.source is not None and self.summary_state != "working")
        self.copy_button.setEnabled(self.summary is not None)
        self.export_button.setEnabled(self.summary is not None)
        state = self.summary_state
        if state == "working":
            text = f"Summarizing ({LEVEL_NAMES[self.working_level]})…" + (" The last summary stays until it is ready."
                                                                         if self.summary else "")
        elif state == "error":
            text = f"Couldn't summarize: {self.error}." + (" The last summary is still shown." if self.summary else "")
        elif self.summary and self.summary.level != level:
            text = (f"This is the {LEVEL_NAMES[self.summary.level]} summary. "
                    f"Press Summarize for {LEVEL_NAMES[level]}.")
        elif self.summary:
            n = len(self.summary.lines)
            text = (f"{LEVEL_NAMES[self.summary.level]}: {n} line{'s' * (n != 1)}, {self.summary.words} of "
                    f"{self.summary.total} words.")
        else:
            text = ""
        self.notice.setText(text)
        self.notice.setProperty("state", "error" if state == "error" else "")
        self.notice.style().unpolish(self.notice)
        self.notice.style().polish(self.notice)

    def start_summary(self):
        if not self.source or self.summary_state == "working":
            return
        self.working_level = self.chosen_level()
        self.sum_job = Job(call, summarize, self.source, self.working_level, time_limit=SUMMARIZE_LIMIT)
        self.summary_state = "working"
        self.refresh_summary_controls()
        self.timer.start()

    def copy_summary(self):
        if self.summary:
            QGuiApplication.clipboard().setText(present.as_text(self.summary))
            self.notice.setText(f"Copied the {LEVEL_NAMES[self.summary.level]} summary.")

    def export_summary(self):
        if not self.summary:
            return
        folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        stem = Path(self.name).stem if self.name and self.source and self.source.unit != "paragraph" else "Pasted text"
        default = str(Path(folder) / f"{stem} - {LEVEL_NAMES[self.summary.level]} summary.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Export summary", default,
                                              "PDF (*.pdf);;Word document (*.docx)",
                                              options=QFileDialog.DontConfirmOverwrite)
        if path:
            self.export_to(path)

    def export_to(self, path):
        """Save the summary as a new file; a taken name gets a number, so nothing is overwritten."""
        try:
            final, _ = export.save(present.paragraphs(self.summary), path)
        except (export.ExportError, OSError) as e:
            reason = str(e) if isinstance(e, export.ExportError) else "the file could not be written there"
            self.notice.setText(f"Couldn't export: {reason}.")
            log.info("export failed: %s", type(e).__name__)
            return None
        renamed = "" if Path(final) == Path(path) else " That name was taken, so a number was added."
        self.notice.setText(f"Exported as {Path(final).name}.{renamed}")
        log.info("exported %s", Path(final).suffix)
        return final

    def follow(self, url, where):
        """A link: "#gap-details" opens or closes that pane's gap details; "#u<n>" shows unit n in the Source."""
        anchor = url.toString()
        if anchor == DETAILS:
            self.details[where] = not self.details[where]
            (self.render_source if where == "source" else self.render_summary)(keep_scroll=True)
        elif anchor.startswith("#u"):
            if self.narrow:
                self.tabs.setCurrentWidget(self.source_pane)
            self.source_view.scrollToAnchor(anchor[1:])

    # -- workers --------------------------------------------------------------------------------------------------
    def _poll(self):
        if self.read_job and (res := self.read_job.poll()) is not None:
            self._read_done(res, time.monotonic() - self.read_job.started)
            self.read_job = None
        if self.sum_job and (res := self.sum_job.poll()) is not None:
            self._summary_done(res, time.monotonic() - self.sum_job.started)
            self.sum_job = None
        if not self.read_job and not self.sum_job:
            self.timer.stop()

    def _read_done(self, outcome, seconds):
        state, value = outcome
        res, bold = value if state == "ok" else (None, None)
        if res is not None and res.status == "ok":
            rec = res.record
            blocks = from_record(rec, bold)
            counts = f"{rec.unit_count} {rec.unit}{'s' * (rec.unit_count != 1)}" if rec.unit != "block" else ""
            empty = not any(b.kind not in ("label", "note", "gap", "gaps") for b in blocks)
            status = " · ".join(s for s in (counts, "No text was found in this document." if empty else "") if s)
            self.set_source(blocks, source_from_record(rec, blocks), self.reading, status or "Read in full.")
            log.info("read %s: %d %ss, %d blocks, %.1f s", rec.format, rec.unit_count, rec.unit, len(blocks), seconds)
        else:
            reason = value if res is None else "it is too large to read" if res.status == "pending" else res.reason
            self.source_status.setText(f"Couldn't open {self.reading}: {reason}.")
            log.info("read failed: %s, %.1f s", reason, seconds)

    def _summary_done(self, outcome, seconds):
        state, value = outcome
        if state == "ok":
            self.summary, self.summary_state = value, "idle"
            self.details["summary"] = False
            self.render_summary()
            log.info("summary %s by %s: %d lines, %d of %d words (budget %d), %.1f s", value.level, value.method,
                     len(value.lines), value.words, value.total, value.budget, seconds)
        else:
            self.summary_state, self.error = "error", value
            log.info("summary failed: %s, %.1f s", value, seconds)
        self.refresh_summary_controls()

    def closeEvent(self, e):
        for job in (self.read_job, self.sum_job):
            if job:
                job.cancel()
        super().closeEvent(e)


def main():
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("SummarEase")
    app.setStyle("Fusion")
    if not animations_enabled():    # Reduce motion: no animated menus, combo boxes or tooltips
        for effect in (Qt.UI_AnimateMenu, Qt.UI_FadeMenu, Qt.UI_AnimateCombo, Qt.UI_AnimateTooltip,
                       Qt.UI_FadeTooltip, Qt.UI_AnimateToolBox):
            QApplication.setEffectEnabled(effect, False)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
