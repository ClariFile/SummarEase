# Dos and don'ts

Short rules learned while building ClassiFile.

Reviewed 2026-10-20. [The handoff](docs/FROM_CLASSIFILE.md) distinguishes reported suite direction, verified
implementation findings (H1–H8), owner questions (Q1–Q3) and proposals (UX1–UX6). These notes do not amend the
authoritative decision record or grant permission to start another milestone.

## Documents

- **Never modify originals.** Open them read-only. Never move, rename, delete or re-save them, and never write
  files next to them.
- **Read the contents, not the file name.** A file name is never evidence of what a document says.
- **Keep OCR text marked as OCR.** It is less reliable than native text: say where it was used, and say what
  couldn't be read.
- **Exports are new files.** Never write into an existing file. Write each export to a temporary file in the
  system's temporary folder (never beside the destination or an original; owner, 2026-10-20), check it (it opens,
  its text is there, its hash is recorded), then save it under its final name by exclusive creation, without any
  overwrite path, and read it back. A name already taken gets a suffix.
- **Failed exports must not look complete.** Publication and cleanup must cover unsupported hard links,
  collisions and partial write/close failures (H6), not only errors while building the temporary file.
  Clean only artifacts owned by that export; preserve all pre-existing files. Q3 (owner, 2026-10-20): the user
  may choose the source document's folder for a new export; nothing incidental is ever created there.

## Privacy

- **No document text in logs** or error messages.
- **No document text, document names or personal data in tracked files**, tests or commit messages. Refer to test
  documents by neutral IDs, with a local map that is not tracked.
- **Check before every push** with a list of private terms kept outside the repository.

## Measuring

- **One evaluation command for document checks and quality results.** Record versions, effective OCR settings,
  denominators, exclusions and completion state, with a descriptive range beside small counts. Unit-test counts,
  synthetic reproductions and proposed UI timings identify their own command and purpose; they are not quality
  estimates. An old number without its report is history, not a newly verified result.
- **Update checks look at everything,** not only the recent changes: compare the old and the new version on the
  same full evaluation, and keep the new one only if it is no worse on what matters.
- **Measure before tuning.** Change one thing at a time and keep the report.
- **Keep development, validation and final-test files separate.** Tune on development only; look at validation
  rarely; run the final test once per frozen version. Looking at a held-out set repeatedly makes it development
  data.
- **Report counts, not promises.** A score is not a probability, and a few sample files prove no accuracy.
- **Checks must challenge the producer.** Verify complete source units, calculate allowed budgets independently
  and compare visible references/disclosures, not only line text. Empty output and failed checks need explicit
  outcomes. Validate each file's resolved location before reading or hashing it (H2–H5).
- **References stay independent.** Preserve the owner's own-word points before showing summaries. An annotation
  aid may collect source locations, not suggest points or turn source-line overlap into rubric scores.

## Working

- **One milestone at a time,** with stop points. Stop and report; wait for the owner's go-ahead.
- **Ask first** before deleting any of the owner's files, even exact duplicates, and before adding a dependency.
- **Don't use ClassiFile's internal summary as training data.** It was built for categorizing, not for reading.
- **Test alongside the code,** and run the whole suite before reporting.
- **Tests never depend on timing.** No fixed sleeps and no "it should be done within N seconds": wait for the
  condition itself, with a generous limit that only stops a hung test.
- **Heavy work runs in worker processes** with a time limit per file. A crash or a timeout is an operational
  failure, reported plainly, never a result.
- **Bound the whole job.** Include result transfer, worker cleanup and export, not just parsing. Cancellation
  must keep the last completed result usable and prevent stale results from replacing it (H7).
- **The window is updated in place,** never rebuilt: rows, typed text, focus and scroll position stay when new
  results arrive.

## The look

- **Two complete colour themes, light and dark, in one tokens file** from day one: every surface, text, line,
  accent and status colour, for both. Build the style sheet and the Qt palette from the theme in use, and rebuild
  both when the theme or Windows' setting changes. Never mix fixed colours with the system palette.
- **Reuse ClassiFile's token structure** (`classifile/app/tokens.py`, one dictionary per theme: window, sidebar,
  base, raised, inset, text, secondary, divider, control, hover, pressed, disabled, primary, primary_hover,
  on_primary, accent, selection, link, toast, the status colours amber and red, and a few more), with violet
  (#6C47FF) where ClassiFile has teal. The 2026-10-20 suite direction removes green; SummarEase still has unused
  green tokens. The proposed shared-token snapshot checks explicit roles at a ClassiFile tag without a runtime
  dependency on its checkout. Current notice-colour and heading-size differences are recorded in the handoff.
- **The accent is used sparingly,** as teal is in ClassiFile: the primary button, the selection bar, the focus
  outline and links. Large surfaces, lines and hover states stay neutral grey. No neon, no tinted backgrounds.
- Measured for violet: white text on #6C47FF is 5.27:1 and #6C47FF text on white is 5.27:1, so it works as the
  light theme's button and link colour. On ClassiFile's dark page (#1C1E21) it is only 3.17:1: the dark theme needs
  a lighter tint for text and links, for example #9D85FF (5.75:1 on the page, 4.96:1 on panels).
- **A contrast test from day one,** like ClassiFile's `tests/test_theme.py`: text at least 4.5:1 on every surface
  it sits on, icons, control borders and the selection and focus bars at least 3:1, in both themes.
- **Reading panes have a different job from application cards.** Keep the owner's 70–90-character reading
  width while panes fill the window, switching to tabs when narrow. Do not import ClassiFile's full-width text
  rule into this view. Separate application typography from document headings before aligning token sizes.
- **Verify actual interaction.** Record logical window size and scale, review 125% and 150%, both themes, active
  keyboard focus, narrow tabs and Reduce motion. Offscreen screenshots cannot establish active-window focus.
  Page-preview rendering tips apply only if that later feature is approved.
