# SummarEase status

2026-10-15 · decision record version 0.2

## Done: M0 Project setup (2026-10-14)

- Python 3.12 virtual environment; pinned requirements: PyMuPDF and PySide6, and pytest for development.
- AGPL-3.0 licence (PyMuPDF is AGPL); `.gitignore` leaves out `data/` and test output.
- The reader, copied unchanged from ClassiFile (READER.md, option (a)). Since 2026-10-15 its source is ClassiFile's
  tag `reader-v6`, with the hash of each file in `summarease/reader/SOURCE.md`; the copy matches all six.
- The pre-push privacy audit (`tools/audit_terms.py`) with a local, untracked term list.
- An empty PySide6 window with the SummarEase icon.
- 10 tests: the reader reads a PDF, a PPTX, a DOCX and an ODT made for the tests without changing them; OCR reads
  text that is only in a picture; the reader imports nothing from the rest of SummarEase; the window opens with
  the network blocked; the audit matches plain and pattern terms; the reader check (added 2026-10-15, moved
  forward from M1 at the owner's request): `tests/test_reader_copy.py` fails if any file in `summarease/reader/`
  is added, missing or differs from the hashes in `SOURCE.md`.

## Done: M1 Read files and show the readable text view (2026-10-15), waiting at its stop point

- **The window** (`summarease/app.py`): open a document with the button, Ctrl+O or drag-and-drop, or paste text
  with the button or Ctrl+V. The text is shown in one reading column; the status line says what was read.
- **The readable text** (`summarease/readable.py`): the reader's words, laid out only. PDF: headings from the
  reader's font sizes (a short block clearly larger than the body text), paragraphs from its blocks, list items
  where a line starts with a list mark. PPTX: each slide's title as a heading, each shape's lines kept. DOCX and
  ODT: the reader's titles, headings, paragraphs, lists, tables and footnotes. Page and slide labels, captions and
  gap notes are SummarEase's own blocks, kept apart from the document's words. If a page's layout ever disagreed
  with its text, the text itself is shown.
- **OCR text** is shown in a shaded block under the caption "Text read by OCR from a picture. It may contain
  errors." **Gaps** are said where they are (OCR found no text, a picture couldn't be opened, OCR failed, not
  installed, out of time, switched off, or noise left out) and summed up at the top.
- **The worker** (`summarease/worker.py`): each file is read in its own process with a 5-minute limit; a timeout or
  a crash is reported plainly and nothing is shown for it. The window polls it and is updated in place.
- **Themes:** light and dark from one tokens file (`summarease/tokens.py`, ClassiFile's structure, violet), the
  style sheet and the Qt palette rebuilt when Windows' setting changes, keeping the scroll position.
- **Tests (35):** the words shown equal the reader's words, in order, for a PDF, a PPTX, a DOCX and an ODT made for
  the tests, and the rendered view adds or drops nothing; the original's hash is unchanged and nothing is written
  next to it; pasted text leaves no file anywhere and is not logged; no document text or file name is logged; every
  OCR gap is disclosed; a hung or crashed worker is reported; every colour pair in both themes is readable.
- **A read-only check on ClassiFile's development files** (78 documents: 58 PDF, 8 PPTX, 5 DOCX, 7 ODT; not part
  of the test suite), run with OCR off and again with OCR on: all 78 read both times; on every one, the view's
  words equal the reader's words and the rendered text equals the view. 35 of 1,148 PDF pages fell back to their
  plain text. With OCR on, 62 of the 78 show at least one gap note (this counts notes about OCR noise left out);
  the slowest document took 32 s.

## Planning, 2026-10-15 (documents only; no code changed)

- Record 0.2: four levels (C12) and extractive first (C13) confirmed by the owner, with testable definitions:
  what each level contains, length budgets relative to document length, nesting of sources, slides by structure,
  OCR trusted less. A local LLM (P3) stays a proposal.
- `EVALUATION.md`: the development set (copies of ClassiFile's development files), the owner's reference key
  points, the rubric, the automatic checks, one command, and a held-out set for a final check.
- `MILESTONES.md`: M1 starts with the reader check; M2 compares three methods against a baseline and keeps a
  method only if it beats the baseline on the rubric; M2's acceptance fixed (sentence, bullet or line, with a
  correct page, slide or section link).
- `DOS_AND_DONTS.md`: lessons since the handoff (themes and contrast, worker processes, in-place updates, safe
  exports, tests without timing, one evaluation command, update checks on everything) and the look.

## Open

- **The owner's reference key points** for about 10 development documents, written before any method is tuned.
- **SummarEase's held-out set** (`data\final-check`): copies of ClassiFile's `data\validation` and
  `data\final-eval`, taken after ClassiFile's CP5 (`EVALUATION.md`). Until then they stay unread.
- The repository's commits are pushed to GitHub's `main`, each push after the privacy audit (0 hits).

## Decided, 2026-10-15 (record 0.3)

- **Export (C14, was P6):** the summary and the readable text, as PDF or Word; the Word file built with the
  standard library. A searchable copy of a scanned document is allowed later, as a new file made on request, but
  not in v1.
- **Length budgets (C12):** the table is accepted as starting defaults, tuned in M2 with the rubric.
- **Order:** M1 to M3 need none of ClassiFile's data and may start now. Only M4 waits for ClassiFile v1.
- **Held-out set:** ClassiFile's validation and final-eval files, copied after its CP5 (above).

## Background: the Export options (decided as d, "a and b")

The record confirms that Export makes a searchable PDF or a Word file, as new files only (C6). Which content it
holds is open.

| Option | What the user gets | Notes |
|---|---|---|
| a. The summary | the level on screen, each line with its page, slide or section | small; the links make it checkable |
| b. The readable text | the whole document as readable text (C5) | the words are the reader's, in order |
| c. A searchable copy of a scanned document | the scanned pages with their OCR text laid under them | a different feature: it writes OCR text into a copy of the document |
| d. Several of these | a and b; c later if wanted | |

**Recommendation: d, as "a and b".** Export what is on screen: the summary at its level, or the readable text,
each as a new PDF with real text (searchable by nature) or a Word file. Leave c out of v1:
- it is a separate feature with its own risks (OCR text placed under the wrong words, a copy that looks like the
  original but is not);
- ClariFile's rule so far is that OCR text is never inserted into any document, original or copy (ClassiFile's
  record A8). Option c would need the owner's explicit exception.

**How a Word file would be made.** A .docx file is a zip of a few XML parts. ClassiFile's and SummarEase's tests
already write .docx files by hand with the standard library (`tests/office_fixtures.py`). Recommendation: the
standard library (`zipfile` and plain XML for the document, its styles and its relationships), about 150 lines,
tested by reading the result back with the reader. The alternative is a new dependency (python-docx, MIT): less
code and richer formatting, but one more package to approve, pin and ship. A PDF needs nothing new: PyMuPDF,
already installed, writes PDF pages with real text.

## Next milestone

**M2 The Minimum and Key points levels** (`MILESTONES.md`), after the owner has tried M1's view on development
files and given the go-ahead. Before M2's methods are compared: copies of ClassiFile's development files in
SummarEase's `data\development`, and the owner's reference key points (`EVALUATION.md`).
