# Milestones

Each milestone ends at a stop point: report, then wait for the owner's go-ahead. All tests pass at every stop.
Every number reported comes from the one evaluation command in `EVALUATION.md`.

**Order:** M1 to M3 need none of ClassiFile's data and may start without waiting for ClassiFile. Only M4 waits for
ClassiFile v1.

## M0 Project setup (done 2026-10-14; see `docs/STATUS.md`)

- Environment: Python 3.11+, a virtual environment, requirements files, a licence file, `.gitignore` (with
  `data/` and test output left out).
- The reader decision (`READER.md`), confirmed by the owner, then set up.
- The privacy audit tool and a local list of private terms.
- An empty window that opens (the GUI toolkit is confirmed in M0).

**Stop point:** environment report; reader set up.

**Acceptance:**
- The app starts offline.
- Tests run.
- The reader reads a PDF, a PPTX, a DOCX and an ODT made for the tests.

## M1 Read files and show the readable text view (done 2026-10-15; see `docs/STATUS.md`)

- **First task: the reader check** (done early, in M0, on 2026-10-15: `tests/test_reader_copy.py`). A test that fails if any file in `summarease/reader/` differs from ClassiFile's
  tag `reader-v6`: it hashes each file (SHA-256, with Windows line endings read as plain line breaks) and compares
  the result with the table in `summarease/reader/SOURCE.md`. A new or missing file fails it too.
- Open a document (drag-and-drop or a file chooser), or paste text.
- Show its text as readable text: headings, paragraphs and lists from the reader's layout. Layout changes only,
  never the words.
- OCR text is marked, and parts that couldn't be read are said.
- Reading runs in a worker process with a time limit per file; the window is updated in place
  (`DOS_AND_DONTS.md`).

**Stop point:** the owner tries the view on development files.

**Acceptance:**
- The reader check passes.
- The words shown equal the reader's words, in order. A test compares them.
- The original's hash is unchanged after opening.
- Nothing pasted is stored.
- No document text appears in the logs.

## M2 The Minimum and Key points levels

**Widened by the owner on 2026-10-15:** M2 is built together with a UI redesign, all four levels (Brief, Key
points, Detailed, Comprehensive), Copy, and Export of the summary. The methods are built and checked automatically;
comparing them on the rubric waits for the owner's reference key points. What stays for M3: Export of the readable
text, and the owner's review of the levels and exports.

- Extractive summaries at two levels, as the record defines them (C12, C13). Each line links to its page, slide or
  section.
- Gaps are disclosed in the summary.
- File names are never used.
- **Methods to compare, not one fixed method.** Each is run by the evaluation command on the development set and
  scored by the owner with the rubric (`EVALUATION.md`):
  1. **Baseline: opening lines.** The first lines of the document (or of each section), up to the level's budget.
     Every other method must beat it.
  2. **Structure first, for slides.** Slide titles and top-level bullets, choosing slides by structure (title,
     agenda and summary slides, and slides whose title repeats a heading) rather than by ranking sentences.
  3. **Sentence ranking with repeats removed, for prose.** Sentences scored by how central their words are to the
     document (word weights fitted on that document only), near-duplicates and repeated template lines (headers,
     footers) removed, then shown in document order.
  - In every method, OCR text is marked and weighs less than native text, and it never stands alone at Minimum
    when the document has native text (C12).
  - **A method is kept only if it beats the baseline on the rubric**, for the kind of document it is meant for.
    Otherwise the baseline stays.

**Stop point:** a short report on development files: the rubric scores per method, and the automatic checks.

**Acceptance:**
- Every summary line is a sentence, bullet or line taken from the document, with a correct page, slide or section
  link. A test checks this on every development file.
- Each level stays within its budget, and Key points includes every source of Minimum (C12). A test checks this.
- The same input gives the same output, and renaming the file changes nothing in its summary. A test checks both.
- Gaps are disclosed wherever the reader found them.

## M3 All levels, Copy and Export

- The remaining levels (By section, Maximum), with the same checks as M2.
- Copy.
- Export of the summary and the readable text, as PDF or Word (record C14): new files only, where the user chooses. Each
  export is written to a temporary file, checked, then saved without overwriting anything.

**Stop point:** the owner reviews the levels and the exports.

**Acceptance:**
- Every level includes the sources of the level below (C12). A test checks this.
- Exports open in common readers, and their text can be searched.
- An existing file is never overwritten.
- The originals' hashes are unchanged.

## M4 Integration with ClassiFile (only after ClassiFile v1 is released)

- The registration file, and the request and response format in `INTEGRATION.md`, versioned.
- ClassiFile asks the user before calling SummarEase.

**Stop point:** a demo of a call from ClassiFile.

**Acceptance:**
- Each app works when the other is not installed.
- SummarEase never writes ClassiFile's data.
- A request with an unknown version is refused with a plain reason.
