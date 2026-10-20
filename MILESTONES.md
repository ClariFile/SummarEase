# Milestones

Each milestone ends at a stop point: report, then wait for the owner's go-ahead. All tests pass at every stop.
Document-check counts and quality results come from the evaluation command in `EVALUATION.md`. Unit-test counts,
synthetic bug reproductions and proposed UI timings identify their own command and scope; they are not quality
results.

**Order:** M1 to M3 implementation need not wait for ClassiFile v1. M2 quality comparison does need SummarEase's
own development copies and the owner's references. Only M4 waits for ClassiFile v1; every milestone still needs
the owner's go-ahead. Preparing M4 documentation does not authorize building or testing integration.

**Audit checkpoint (2026-10-20):** [the handoff](docs/FROM_CLASSIFILE.md) records H1–H8, owner questions Q1–Q3,
and optional UX1–UX6. Resolve or explicitly disposition the findings before release acceptance. Code is not
fixed by documenting a finding; a green existing suite alone does not close it. This documentation pass starts
no new milestone and changes no application API.

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

## M2 Four summary levels and the redesigned workspace (implemented, audit fixes in; acceptance pending)

**Widened by the owner on 2026-10-15:** M2 is built together with a UI redesign, all four levels (Brief, Key
points, Detailed, Comprehensive), Copy, and Export of the summary. The methods are built and checked automatically;
comparing them on the rubric waits for the owner's reference key points. What stays for M3: Export of the readable
text, and the owner's review of the levels and exports.

- Extractive summaries at Brief, Key points, Detailed and Comprehensive, as the record defines them (C12, C13).
  Each line links to its page, slide or section. Internal level IDs stay `brief`, `key`, `detailed`, `comprehensive`.
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
  - In every method, OCR text is marked and weighs less than native text, and it never stands alone at Brief
    when the document has native text (C12).
  - **A method is kept only if it beats the baseline on the rubric**, for the kind of document it is meant for.
    Otherwise the baseline stays.

**Stop points:** first report the automatic checks per format with exclusions and unresolved findings. After
the owner writes the references, report blind rubric scores. Until then there is no quality comparison or
tuning. The prose app default remains the opening-lines baseline; ranking replaces it only if it wins, and a
tie keeps the baseline. Slides use structure under C12.

**Acceptance:**
- Every summary line is a sentence, bullet or line taken from the document, with a correct page, slide or section
  link. A test checks this on every development file.
- Each level stays within its independently calculated budget and includes the preceding level's lines (C12).
  Comprehensive gets at least Detailed's budget. The many-heading coverage conflict (H1/Q1) still needs the
  owner's rule; never silently increase a budget to hide it.
- The same input gives the same output, and renaming the file changes nothing in its summary. A test checks both.
- Gaps are disclosed wherever the reader found them.
- Apply the regression cases in H2–H5: explicit empty/unsupported/budget outcomes, complete source units,
  reference-label stability, held-out descendant protection, and failing/empty evaluation exits.
- H7/H8 require bounded worker cleanup and partial OCR disclosure. Reader fixes follow `READER.md`; report
  limitations accurately until an upstream tagged fix is available.

## M3 Readable-text Copy/Export and review (built 2026-10-20 at the owner's go-ahead; review pending)

- All four levels, summary Copy and summary Export were brought forward into M2; review them rather than build
  duplicates.
- Complete readable-text Copy/Export (C5, C6, C14), reusing the existing writers. The proposed Summary/Source
  selection must make the content and shown summary level clear.
- Export as PDF or Word: new files only, where the user chooses. Each export is written to a temporary file,
  checked, then published without overwriting anything. Q3 records the unresolved source-folder destination rule.
- UX1, UX3 and the Help/About part of UX4 are proposals for this review, not added requirements.

**Stop point:** the owner reviews the levels and the exports.

**Acceptance:**
- Every level includes the sources of the level below (C12). A test checks this.
- Exports open in common readers, and their text can be searched.
- An existing file is never overwritten.
- The originals' hashes are unchanged.
- H6's failure and collision cases leave no incomplete final export and preserve all pre-existing files.
- H7's export and cancellation cases keep the window responsive and the previous result usable.
- Review active-window keyboard focus, long content/names, both themes, wide panes/narrow tabs, 125%/150%
  scaling and Reduce motion. Screenshots alone do not prove keyboard or screen-reader behavior.

## M4 Integration with ClassiFile (only after ClassiFile v1 is released)

- The registration file, and the request and response format in `INTEGRATION.md`, versioned.
- ClassiFile asks the user before calling SummarEase.

**Stop point:** a demo of a call from ClassiFile.

**Acceptance:**
- Each app works when the other is not installed.
- SummarEase never writes ClassiFile's data.
- A request with an unknown version is refused with a plain reason.
- The proposed protocol acceptance cases in `INTEGRATION.md` cover cancellation, cleanup, independent app
  identities and pasted-text consent. Confirm the protocol before implementation.

## Release and v1.1 proposals

UX5 proposes adapting the installer after core acceptance, with separate app identity and disposable-Windows
tests. It does not waive the M4 gate for registration implementation or authorize new build dependencies.

The owner already accepted keeping PowerPoint bullet levels for v1.1, starting in ClassiFile's reader after
ClassiFile v1. Original-page previews remain a separate UX6 proposal. See `docs/STATUS.md` for the backlog.
