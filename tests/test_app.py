import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from summarease.app import ICON, make_window  # noqa: E402


def test_empty_window_opens_offline():
    app = QApplication.instance() or QApplication([])
    win = make_window()
    win.show()
    app.processEvents()
    assert win.isVisible() and win.windowTitle() == "SummarEase"
    assert ICON.is_file() and not win.windowIcon().isNull()
    win.close()
