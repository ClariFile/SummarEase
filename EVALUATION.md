# Evaluation

How SummarEase's summaries are measured. Every number in a report comes from one command, so it can be run again
and give the same result. The counts describe the owner's development documents; they are not accuracy
estimates, and a score is never a probability.

## The documents

- **Development set:** copies of ClassiFile's development files (its `data\development`, `data\real-samples` and
  the six sample PDFs), placed in SummarEase's own `data\development`. The originals are never opened for
  writing; only the copies are read.
- **Never read ClassiFile's `data\validation` or `data\final-eval`** until ClassiFile's CP5 is done. They are
  ClassiFile's held-out sets, and reading them would turn them into development data.
- **SummarEase's own held-out set** (`data\final-check`): after ClassiFile's CP5 is done, copies of ClassiFile's
  `data\validation` and `data\final-eval` files become SummarEase's held-out set. SummarEase has never seen them,
  so they are held out for it too. Until then they are not read or copied. Once in place, the set is used once per
  frozen version, for a final check, as in ClassiFile. The tools refuse it otherwise.
- Documents are named in reports by neutral IDs (D1, D2, …), with a local, untracked map. No document text,
  title or name goes into tracked files.

## The owner's references

For about 10 development documents (slides, prose and scanned pages, mixed), the owner writes the **reference
key points**: the 3 to 8 points a reader must come away with. They are kept in a local file
(`data\references.csv`: document ID, point number, the point in the owner's words, and the page, slide or section
it comes from). They are written before any method is tuned and are not changed to suit a method.

## The rubric (the owner scores)

Each summary, at each level being tested, is scored by the owner on four points, each 0, 1 or 2:

| Point | 0 | 1 | 2 |
|---|---|---|---|
| **Covers the main points** | misses most reference points | covers some | covers all, or all the level has room for |
| **Faithful** | a line misleads out of context | a line needs its context | every line reads true on its own |
| **Readable** | hard to follow | followable with effort | reads cleanly in order |
| **No repeats** | several lines say the same | one repeat | none |

- Scoring is blind: the owner sees the summaries without the method's name, in a shuffled order.
- A method is kept only if its total beats the baseline (opening lines) for the documents it is meant for
  (`MILESTONES.md`, M2). A tie keeps the baseline.

## Automatic checks (a test each, on every development document and level)

1. **Traceable:** every line equals a sentence, bullet or line of the document, word for word, and its page,
   slide or section link points to where that text is.
2. **Gaps disclosed:** every gap the reader reported (unread pictures, failed OCR, unreadable pages) is said in
   the summary.
3. **Same input, same output:** two runs give identical summaries.
4. **Renaming changes nothing:** the same bytes under another file name give the same summary.
5. **Levels nest and keep their budgets** (record C12).

## One command

`python -m tools.evaluate` (built in M2: the automatic checks so far; blind scoring and `--final` are added with the
reference key points) runs every method on the development set, writes the summaries for blind scoring, runs the
automatic checks, and prints one report: documents counted and left out (with the reason),
each method's rubric totals per document kind, the checks, and a simple range beside each share. It is
deterministic: anything drawn at random uses a fixed seed. `--final` runs the held-out set once per frozen version
and refuses a second run.
