# Milestones

Each milestone ends at a stop point: report, then wait for the owner's go-ahead. All tests pass at every stop.

## M0 Project setup

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

## M1 Read files and show the readable text view

- Open a document (drag-and-drop or a file chooser), or paste text.
- Show its text as readable text: headings, paragraphs and lists from the reader's layout. Layout changes only,
  never the words.
- OCR text is marked, and parts that couldn't be read are said.

**Stop point:** the owner tries the view on development files.

**Acceptance:**
- The words shown equal the reader's words, in order. A test compares them.
- The original's hash is unchanged after opening.
- Nothing pasted is stored.
- No document text appears in the logs.

## M2 The Minimum and Key points levels

- Extractive summaries at two levels. Each line links to its page, slide or section.
- Gaps are disclosed in the summary.
- File names are never used.

**Stop point:** a short report on development files, made by the owner's own review of the summaries.

**Acceptance:**
- Every summary line is a sentence from the document, with a correct page link. A test checks this.
- Renaming the file changes nothing in its summary.

## M3 All levels, Copy and Export

- The remaining levels.
- Copy.
- Export as a searchable PDF and as a Word file: new files only, where the user chooses; nothing is overwritten.

**Stop point:** the owner reviews the levels and the exports.

**Acceptance:**
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
