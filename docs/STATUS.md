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

## Built: UI redesign and M2 (2026-10-15), waiting at its stop point

**Interface**
- A compact header (the app, the document's name shortened with "…", Open document…, Paste text) and a workspace
  of two resizable panes, Source and Summary (Summary a little wider), each with one scroll area. Below 960 px the
  panes become tabs. Text lines stop at about 80 characters while the panes fill the window. 24/16/8 px spacing;
  violet only on Summarize, focus outlines, the current tab and links.
- The Summary pane: Copy and Export… on its caption row; the Detail level control, Summarize, the level's one-line
  explanation and a notice line. States: empty, working (the last summary stays), done, and error (the last summary
  stays). Changing the level never starts work or clears the summary; a summary of another level is said.
- Every summary line links to its page, slide or section; a click scrolls the Source pane there (and opens the
  Source tab when narrow).
- Reduce motion: the app has no animations of its own; when Windows' animation effects are off, Qt's animated
  menus, combo boxes and tooltips are switched off too.
- Screenshots: `python -m tools.screenshots` (invented documents; 100%, 125%, 150%; light and dark; wide and
  narrow; every summary state; keyboard focus), saved in `data\screenshots` (not tracked).

**Reading quality**
- PDF headings: only a short run of lines (12 words or fewer) at the start of a block, clearly larger than the
  page's body text (1.2 times) or bold where the body is not, and not ending like a sentence. The reader keeps
  sizes but not weights, so the worker reads the font weights from the same bytes (checked by hash).
- What couldn't be read: one short note per page at most, one line at the top, details behind "Show details".
  Dropped OCR noise is no longer mentioned.

**Summaries** (`summarease/summarize.py`, record C12, C13)
- Four levels built by one rule set from any method's ranking: Detailed first (each section's heading and up to
  3 lines), Key points and Brief chosen from it, Comprehensive adding to it, so the levels nest. Budgets as C12.
  Speaker notes and hidden slides appear only at Comprehensive; OCR never stands alone at Brief when there is native
  text; headers, footers and template lines are left out.
- Three methods: the opening-lines baseline; structure first for slides (PPTX, and PDFs that are mostly landscape
  with few words a page); sentence ranking with near-duplicates removed for prose. The app uses structure for slides
  (C12) and the baseline for prose until a method beats it on the rubric (MILESTONES.md).
- Copy and Export (PDF and Word) share one text: each line, then where it is from, OCR and notes marked. An export
  is read back and checked before it is saved, and never overwrites a file.
- `python -m tools.evaluate`: the automatic checks on the development set, by neutral ID. Not yet run on the
  development files: see Open.
- **Tests (84).**

## Done: M1 Read files and show the readable text view (2026-10-15)

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

- **The development set in `data\development`:** copying ClassiFile's development files there was refused by the
  agent's permission check (personal documents). The owner copies them, allows the copy, or runs the evaluation on
  ClassiFile's folders in place (`python -m tools.evaluate --set <folders>`, read only; the renaming check makes a
  temporary copy of each file and deletes it).
- **A reading of C12 for the owner to confirm:** below 375 words, 40% of W is less than Detailed's floor of 150
  words, so Comprehensive could not hold Detailed. The code gives Comprehensive at least Detailed's budget.
- **The owner's reference key points** for about 10 development documents, written before any method is tuned.
- **SummarEase's held-out set** (`data\final-check`): copies of ClassiFile's `data\validation` and
  `data\final-eval`, taken after ClassiFile's CP5 (`EVALUATION.md`). Until then they stay unread.
- The repository's commits are pushed to GitHub's `main`, each push after the privacy audit (0 hits).

## Decided, 2026-10-15 (record 0.3; level names in 0.4)

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

The rubric comparison of M2's methods, once the owner's reference key points exist (`EVALUATION.md`); then M3
(Export of the readable text, the owner's review). Only on the owner's go-ahead.
