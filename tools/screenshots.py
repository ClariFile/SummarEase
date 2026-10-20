"""Screenshots of the window for review, saved in data/screenshots (not tracked). Invented documents only.

Usage: python -m tools.screenshots            all scalings (100%, 125%, 150%), each in its own process
       python -m tools.screenshots --scale 1.25

Each scaling covers: empty, a long document with a long file name (wide and narrow, light and dark), every summary
state (working with the last summary kept, done, another level chosen, error), gap details open, keyboard focus, and
at 1536x864 (the owner's 1920x1080 screen at 125%): a summary line selected in the Source with Back to summary, find,
zoom, Cancel while working, and an empty summary that says why.
The window is drawn off screen with the native platform, so fonts and scaling are Windows' own."""
import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "screenshots"
SCALES = ("1", "1.25", "1.5")
LONG_NAME = "An invented handbook with a very long file name that goes on and on to test shortening in the header.pdf"


def run(scale):
    os.environ["QT_SCALE_FACTOR"] = scale
    os.environ["CLASSIFILE_OCR"] = "off"     # the pictures here are not part of the review
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from summarease.app import MainWindow
    from tools.sample_docs import make_slide_pdf, make_text_pdf

    app = QApplication([])
    app.setStyle("Fusion")
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    text_pdf = make_text_pdf(tmp / LONG_NAME, pages=40)
    slides = make_slide_pdf(tmp / "Invented slides.pdf", slides=12)

    w = MainWindow()
    w.setAttribute(Qt.WA_DontShowOnScreen)
    w.show()

    def wait(done):
        end = time.monotonic() + 120
        while not done() and time.monotonic() < end:
            QTest.qWait(50)

    def shot(name, size=(1440, 900), theme="light"):
        w.resize(*size)
        w.apply_theme(theme)
        QTest.qWait(30)
        w.grab().save(str(OUT / f"{scale}x-{theme}-{size[0]}x{size[1]}-{name}.png"))

    def summarize(level):
        w.level.setCurrentIndex(["brief", "key", "detailed", "comprehensive"].index(level))
        w.start_summary()
        wait(lambda: w.sum_job is None)

    shot("1-empty")
    w.open_file(text_pdf)
    wait(lambda: w.read_job is None)
    shot("2-document-no-summary")
    summarize("key")
    for theme in ("light", "dark"):
        shot("3-key-points", theme=theme)
        shot("4-narrow-source-tab", (820, 760), theme)
        w.tabs.setCurrentWidget(w.summary_pane)
        shot("5-narrow-summary-tab", (820, 760), theme)
        w.tabs.setCurrentWidget(w.source_pane)
    w.resize(1440, 900)
    w.level.setCurrentIndex(2)
    shot("6-other-level-chosen")
    w.start_summary()
    shot("7-working-last-summary-kept")
    wait(lambda: w.sum_job is None)
    shot("8-detailed")
    w.source_view.verticalScrollBar().setValue(w.source_view.verticalScrollBar().maximum() // 2)
    shot("9-long-document-scrolled")
    w.summary_state, w.error = "error", "it took longer than the time limit"
    w.refresh_summary_controls()
    shot("10-error-last-summary-kept")
    w.summary_state = "idle"
    w.open_file(slides)
    wait(lambda: w.read_job is None)
    summarize("brief")
    shot("11-slides-brief")
    summarize("comprehensive")
    shot("12-slides-comprehensive", theme="dark")
    w.summarize_button.setFocus(Qt.TabFocusReason)
    shot("13-keyboard-focus-summarize")
    w.level.setFocus(Qt.TabFocusReason)
    shot("14-keyboard-focus-level", theme="dark")
    w.open_file(text_pdf)
    wait(lambda: w.read_job is None)
    summarize("detailed")
    line = w.summary.lines[len(w.summary.lines) // 2]
    for theme in ("light", "dark"):
        w.resize(1536, 864)
        w.apply_theme(theme)        # before the link: a new theme draws the text again, without the selection
        QTest.qWait(30)
        w.follow(QUrl(f"#l{line.id}"), "summary")
        shot("15-line-selected-back-to-summary", (1536, 864), theme)
    w.find_field.setText("model")
    w.find_next()
    w.find_field.setFocus(Qt.TabFocusReason)
    shot("16-find-in-source", (1536, 864))
    w.set_zoom(1)
    w.set_zoom(1)
    shot("17-zoomed-120", (1536, 864), "dark")
    w.set_zoom(0)
    w.start_summary()
    shot("18-working-cancel-shown", (1536, 864))
    w.cancel_work()
    w.paste_text(" ".join(["word"] * 199) + " end.")
    summarize("brief")
    shot("19-empty-summary-says-why", (1536, 864))
    w.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scale")
    a = ap.parse_args()
    if a.scale:
        run(a.scale)
        return 0
    for scale in SCALES:
        subprocess.run([sys.executable, "-m", "tools.screenshots", "--scale", scale], cwd=ROOT, check=True)
    print(f"{len(list(OUT.glob('*.png')))} screenshots in {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
