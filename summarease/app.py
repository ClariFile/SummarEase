"""The SummarEase window. Run: python -m summarease.app

A compact header (the app, the document's name, Open, Paste, Help, and Cancel while work runs), then the workspace:
the Source pane (find, Copy and Export of the readable text, the text itself) and the Summary pane (the detail level,
Summarize, Copy and Export), side by side and resizable, or as two tabs on a narrow window. Reading, summarizing and
building an export run in worker processes (worker.py); the window polls them and is updated in place. Pasted text stays in memory (record C9). Logs carry counts and fixed reasons only: never document text or
file names."""
import ctypes
import logging
import multiprocessing
import re
import sys
import time
from pathlib import Path

from PySide6.QtCore import QRegularExpression, QStandardPaths, Qt, QTimer
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QGuiApplication, QIcon, QKeySequence, QPalette, QShortcut, QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSplitter, QStackedWidget, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from . import export, present
from . import tokens as tk
from .readable import DETAILS, from_record, from_text, to_html
from .reader import READERS, ocr
from .summarize import (
    DEFAULT_LEVEL, LEVEL_HINTS, LEVEL_NAMES, LEVELS, source_from_record, source_from_text, summarize,
)
from .worker import Job, call, read

ICON = Path(__file__).resolve().parent.parent / "assets" / "icons" / "summarease" / "summarease.ico"
POLL_MS = 100
SUMMARIZE_LIMIT = 120   # seconds
EXPORT_LIMIT = 300      # seconds to build and check an export
ZOOM_STEP, ZOOM_MIN, ZOOM_MAX = 0.1, 0.8, 2.0     # text zoom of both reading panes
FORMATS = "PDF, PPTX, DOCX and ODT"
EMPTY_SOURCE = f"Open a document ({FORMATS}) or paste text. Nothing you paste is stored."
EMPTY_SUMMARY = "Open a document or paste text, then press Summarize."
READY_SUMMARY = "Choose a detail level and press Summarize."
log = logging.getLogger("summarease")
HELP = """<p><b>SummarEase</b> summarizes documents and pasted text on this computer. It makes no network
connections: nothing you open or paste leaves the computer.</p>
<p>Every summary line is taken word for word from the document, with a link to where it is. Your documents are only
read, never changed. Pasted text is kept in memory only. Copy and Export make nothing unless you ask: an export is a
new file, saved where you choose, and never replaces a file.</p>
<p>OCR (reading text in pictures): {ocr}. Text read by OCR is marked, and what couldn't be read is said.</p>
<p><b>Keys</b><br>Ctrl+O open · Ctrl+V paste · Ctrl+F find in the source · Enter / Shift+Enter next / previous
match<br>Ctrl+= / Ctrl+- / Ctrl+0 text size · Esc cancel the work in progress</p>
<p><b>Licences</b><br>SummarEase is free software under the GNU Affero General Public License, version 3. It uses
PyMuPDF (GNU AGPL 3), Qt for Python (PySide6, GNU LGPL 3) and Tesseract OCR (Apache 2.0).</p>"""


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
QLineEdit {{ border: {tk.HAIR}px solid {t['control']}; border-radius: {tk.RADIUS_CONTROL}px; background: {t['base']};
             padding: {tk.RELATED - tk.HAIR}px {tk.RELATED + tk.TIGHT}px; min-height: {tk.CONTROL_TEXT}px;
             selection-background-color: {t['selection']}; selection-color: {t['text']}; }}
QPushButton:focus, QComboBox:focus, QLineEdit:focus {{ border: {tk.HAIR + 1}px solid {t['accent']}; }}
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
        self.base_column = self.column = round(QFontMetrics(font).horizontalAdvance(sample) / len(sample)
                                               * tk.READING_CHARS)
        self.zoom = 1.0

    def set_html(self, html, keep_scroll=False):
        """Show html, every text size scaled by the zoom; the column scales with it, so lines keep READING_CHARS."""
        bar = self.verticalScrollBar()
        at = bar.value()
        self.column = round(self.base_column * self.zoom)
        self.setHtml(re.sub(r"font-size:\s*(\d+)px", lambda m: f"font-size:{round(int(m[1]) * self.zoom)}px", html))
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
        self.read_job = self.sum_job = self.export_job = None
        self.exporting = None                                       # (path, "summary" | "source") being built
        self.reading = None
        self.source_info = ""                                       # the Source pane's status for this document
        self.return_to = None                                       # the summary's scroll position before a link
        self.details = {"source": False, "summary": False}         # gap details open

        # header
        self.open_button = QPushButton("Open document…")
        self.open_button.clicked.connect(self.choose_file)
        self.paste_button = QPushButton("Paste text")
        self.paste_button.setToolTip("Show the text on the clipboard. It is not stored.")
        self.paste_button.clicked.connect(lambda: self.paste_text())
        self.doc_label = ElidedLabel("docname")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setToolTip("Stop the work in progress (Esc). What is shown stays.")
        self.cancel_button.clicked.connect(self.cancel_work)
        self.cancel_button.hide()
        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)
        header = QHBoxLayout()
        header.setSpacing(tk.RELATED)
        header.addWidget(label("SummarEase", "brand"))
        header.addSpacing(tk.GROUP)
        header.addWidget(self.doc_label, 1)
        header.addSpacing(tk.GROUP)
        header.addWidget(self.cancel_button)
        header.addWidget(self.open_button)
        header.addWidget(self.paste_button)
        header.addWidget(self.help_button)

        # Source pane
        self.source_status = label("", "secondary")
        self.source_view = ReadingView("Source text")
        self.source_view.anchorClicked.connect(lambda url: self.follow(url, "source"))
        self.find_field = QLineEdit()
        self.find_field.setPlaceholderText("Find in source")
        self.find_field.setAccessibleName("Find in source")
        self.find_field.setClearButtonEnabled(True)
        self.find_field.returnPressed.connect(lambda: self.find_next())
        self.back_button = QPushButton("Back to summary")
        self.back_button.clicked.connect(self.back_to_summary)
        self.back_button.hide()
        self.source_copy = QPushButton("Copy")
        self.source_copy.setAccessibleName("Copy the readable text")
        self.source_copy.clicked.connect(self.copy_source)
        self.source_export = QPushButton("Export…")
        self.source_export.setAccessibleName("Export the readable text")
        self.source_export.clicked.connect(self.export_source)
        find_row = QHBoxLayout()
        find_row.setSpacing(tk.RELATED)
        find_row.addWidget(self.find_field, 1)
        find_row.addWidget(self.back_button)
        self.source_pane = pane("SOURCE", self.source_view, beside=[self.source_status],
                                right=[self.source_copy, self.source_export], rows=[find_row])

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
        self.copy_button.setAccessibleName("Copy the summary")
        self.copy_button.clicked.connect(self.copy_summary)
        self.export_button = QPushButton("Export…")
        self.export_button.setAccessibleName("Export the summary")
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
        order = (self.cancel_button, self.open_button, self.paste_button, self.help_button, self.source_copy,
                 self.source_export, self.find_field, self.back_button, self.source_view, self.copy_button,
                 self.export_button, self.level, self.summarize_button, self.summary_view)    # the screen's order
        for a, b in zip(order, order[1:]):
            QWidget.setTabOrder(a, b)

        QShortcut(QKeySequence.Paste, self, lambda: self.paste_text())
        QShortcut(QKeySequence.Open, self, self.choose_file)
        QShortcut(QKeySequence.Find, self, self.focus_find)
        QShortcut(QKeySequence("Shift+Return"), self.find_field, lambda: self.find_next(backward=True),
                  context=Qt.WidgetShortcut)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.cancel_work)
        for keys, step in ((QKeySequence.ZoomIn, 1), (QKeySequence("Ctrl+="), 1), (QKeySequence.ZoomOut, -1),
                           (QKeySequence("Ctrl+0"), 0)):
            QShortcut(keys, self, lambda step=step: self.set_zoom(step))
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
        self._anchors = None

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
        self.refresh_buttons()
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
        self.source_info = status
        self.source_status.setText(status)
        self.back_button.hide()
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
        self.refresh_buttons()
        state = self.summary_state
        if state == "working":
            text = f"Summarizing ({LEVEL_NAMES[self.working_level]})…" + (" The last summary stays until it is ready."
                                                                         if self.summary else "")
        elif state == "error":
            text = f"Couldn't summarize: {self.error}." + (" The last summary is still shown." if self.summary else "")
        elif self.summary and self.summary.level != level:
            text = (f"This is the {LEVEL_NAMES[self.summary.level]} summary. "
                    f"Press Summarize for {LEVEL_NAMES[level]}.")
        elif self.summary and self.summary.empty:
            text = f"{LEVEL_NAMES[self.summary.level]}: no lines. The summary says why."
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

    def copy_source(self):
        """The readable text, as shown (record C5, C6), with SummarEase's marks: OCR, notes, what couldn't be read."""
        if self.blocks:
            QGuiApplication.clipboard().setText(present.as_text(present.source_paragraphs(self.blocks)))
            self.source_status.setText("Copied the readable text.")

    def export_summary(self):
        if self.summary:
            self._export("summary", f"Export the {LEVEL_NAMES[self.summary.level]} summary",
                         f"{LEVEL_NAMES[self.summary.level]} summary")

    def export_source(self):
        if self.blocks:
            self._export("source", "Export the readable text", "Readable text")

    def _export(self, what, title, suffix):
        folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        stem = Path(self.name).stem if self.name and self.source and self.source.unit != "paragraph" else "Pasted text"
        path, _ = QFileDialog.getSaveFileName(self, title, str(Path(folder) / f"{stem} - {suffix}.pdf"),
                                              "PDF (*.pdf);;Word document (*.docx)",
                                              options=QFileDialog.DontConfirmOverwrite)
        if path:
            self.export_to(path, what)

    def refresh_buttons(self):
        """Copy and Export of each pane, and Cancel, for what is shown and what runs."""
        self.copy_button.setEnabled(self.summary is not None)
        self.export_button.setEnabled(self.summary is not None and not self.export_job)
        self.source_copy.setEnabled(bool(self.blocks))
        self.source_export.setEnabled(bool(self.blocks) and not self.export_job)
        self.cancel_button.setVisible(any((self.read_job, self.sum_job, self.export_job)))

    def tell(self, what, text):
        (self.notice if what == "summary" else self.source_status).setText(text)

    def export_to(self, path, what="summary"):
        """Build and check a new file in a worker (the window stays responsive), then save it here: a taken name
        gets a number, so nothing is overwritten."""
        if self.export_job:
            return
        kind = Path(path).suffix.lower()
        if kind not in (".pdf", ".docx"):
            self.tell(what, "Couldn't export: SummarEase exports PDF and Word (.docx) files.")
            return
        paras = present.paragraphs(self.summary) if what == "summary" else present.source_paragraphs(self.blocks)
        self.export_job = Job(call, export.prepare, paras, kind, time_limit=EXPORT_LIMIT)
        self.exporting = (Path(path), what)
        self.tell(what, "Exporting…")
        self.refresh_buttons()
        self.timer.start()

    def _export_done(self, outcome):
        (path, what), self.exporting = self.exporting, None
        state, value = outcome
        try:
            if state != "ok":
                raise export.ExportError("the new file did not pass its check" if value == "ExportError" else value)
            final, _ = export.publish(value, path)
        except (export.ExportError, OSError) as e:
            reason = str(e) if isinstance(e, export.ExportError) else "the file could not be written there"
            self.tell(what, f"Couldn't export: {reason}. Nothing was saved.")
            log.info("export failed: %s", type(e).__name__)
            return None
        renamed = "" if final == path else " That name was taken, so a number was added."
        self.tell(what, f"Exported as {final.name}.{renamed}")
        log.info("exported %s %s", what, final.suffix)
        return final

    def cancel_work(self):
        """Stop whatever runs. What is shown stays: the last summary, the open document."""
        if self.read_job:
            self.read_job.cancel()
            self.read_job = None
            self.source_status.setText(f"Stopped reading. {self.source_info}".strip())
        if self.sum_job:
            self.sum_job.cancel()
            self.sum_job = None
            self.summary_state = "idle"
            self.refresh_summary_controls()
            self.notice.setText("Stopped." + (" The last summary is still shown." if self.summary else ""))
        if self.export_job:
            self.export_job.cancel()
            what = self.exporting[1]
            self.export_job = self.exporting = None
            self.tell(what, "Export stopped. Nothing was saved.")
        self.refresh_buttons()

    def show_help(self):
        box = QMessageBox(self)
        box.setWindowTitle("Help and about SummarEase")
        box.setTextFormat(Qt.RichText)
        box.setText(HELP.format(ocr="available" if ocr.tessdata() else "not installed, so text in pictures is "
                                                                         "listed as not read"))
        box.exec()

    # -- source: find, zoom, links --------------------------------------------------------------------------------
    def focus_find(self):
        if self.narrow:
            self.tabs.setCurrentWidget(self.source_pane)
        self.find_field.setFocus()
        self.find_field.selectAll()

    def find_next(self, backward=False):
        """The next (or previous) match in the Source, from where the last one was; at the end it starts again."""
        text = self.find_field.text().strip()
        if not text:
            return False
        view = self.source_view
        flags = QTextDocument.FindBackward if backward else QTextDocument.FindFlag(0)
        if not view.find(text, flags):
            cursor = view.textCursor()
            cursor.movePosition(cursor.MoveOperation.End if backward else cursor.MoveOperation.Start)
            view.setTextCursor(cursor)
            if not view.find(text, flags):
                self.source_status.setText("No match in the source.")
                return False
        self.source_status.setText(self.source_info)
        return True

    def set_zoom(self, step):
        """Text size of both reading panes: step 1 larger, -1 smaller, 0 back to normal."""
        zoom = 1.0 if step == 0 else min(ZOOM_MAX, max(ZOOM_MIN, self.source_view.zoom + step * ZOOM_STEP))
        for view in (self.source_view, self.summary_view):
            view.zoom = round(zoom, 2)
        self.render_source(keep_scroll=True)
        self.render_summary(keep_scroll=True)

    def anchors(self):
        """{anchor name: position} in the Source pane's text, found once per rendering."""
        if self._anchors is not None:
            return self._anchors
        out, block = {}, self.source_view.document().begin()
        while block.isValid():
            for name in block.charFormat().anchorNames():      # an anchor before a paragraph sits on its block
                out.setdefault(name, block.position())
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                for name in frag.charFormat().anchorNames():
                    out.setdefault(name, frag.position())
                it += 1
            block = block.next()
        self._anchors = out
        return out

    def show_line(self, line):
        """Scroll the Source to a summary line and select it there: that occurrence, in its own page, slide or
        paragraph, not the first match elsewhere. If the text can't be found as shown, scroll to its unit."""
        view = self.source_view
        view.scrollToAnchor(f"u{line.unit}")
        anchors = self.anchors()
        start = anchors.get(f"u{line.unit}")
        if start is None:
            return False
        later = [p for p in anchors.values() if p > start]
        words = r"\s+".join(QRegularExpression.escape(w) for w in line.text.split())
        found = view.document().find(QRegularExpression(words, QRegularExpression.UseUnicodePropertiesOption), start)
        if found.isNull() or (later and found.selectionStart() >= min(later)):
            return False
        view.setTextCursor(found)
        view.ensureCursorVisible()
        return True

    def back_to_summary(self):
        if self.narrow:
            self.tabs.setCurrentWidget(self.summary_pane)
        if self.return_to is not None:
            self.summary_view.verticalScrollBar().setValue(self.return_to)
        self.summary_view.setFocus()
        self.back_button.hide()

    def follow(self, url, where):
        """A link: "#gap-details" opens or closes that pane's gap details; "#l<id>" shows and selects that summary
        line in the Source; "#u<n>" shows unit n in the Source."""
        anchor = url.toString()
        if anchor == DETAILS:
            self.details[where] = not self.details[where]
            (self.render_source if where == "source" else self.render_summary)(keep_scroll=True)
            return
        if not anchor.startswith(("#u", "#l")):
            return
        if self.narrow:
            self.tabs.setCurrentWidget(self.source_pane)
        if where == "summary":
            self.return_to = self.summary_view.verticalScrollBar().value()
            self.back_button.show()
        line = next((l for l in self.summary.lines if f"#l{l.id}" == anchor), None) if self.summary else None
        if line:
            self.show_line(line)
        elif anchor.startswith("#u"):
            self.source_view.scrollToAnchor(anchor[1:])

    # -- workers --------------------------------------------------------------------------------------------------
    def _poll(self):
        if self.read_job and (res := self.read_job.poll()) is not None:
            self._read_done(res, time.monotonic() - self.read_job.started)
            self.read_job = None
        if self.sum_job and (res := self.sum_job.poll()) is not None:
            self._summary_done(res, time.monotonic() - self.sum_job.started)
            self.sum_job = None
        if self.export_job and (res := self.export_job.poll()) is not None:
            self.export_job = None
            self._export_done(res)
        if not self.read_job and not self.sum_job and not self.export_job:
            self.timer.stop()
        self.refresh_buttons()

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
        for job in (self.read_job, self.sum_job, self.export_job):
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
