"""The SummarEase window. Run with: python -m summarease.app"""
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow

ICON = Path(__file__).resolve().parent.parent / "assets" / "icons" / "summarease" / "summarease.ico"


def make_window():
    win = QMainWindow()
    win.setWindowTitle("SummarEase")
    win.setWindowIcon(QIcon(str(ICON)))
    win.resize(900, 640)
    return win


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SummarEase")
    win = make_window()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
