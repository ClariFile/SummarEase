# Decision Record — SummarEase

Version 0.2 · 2026-10-15

**Status:** authoritative. Only the owner can change it. Every change goes in the changelog at the end.
Confirmed entries come from ClassiFile's decision record (A11) and the owner's decisions. Proposals are kept apart
and are not rules until the owner confirms them. **[Default]** marks a starting value that changes only with
evidence (`EVALUATION.md`) and the owner's approval.

## Confirmed

**C1 A separate project.**
- Own folder, environment and repository. Usable on its own.
- ClassiFile may use SummarEase only after asking the user each time. It finds an installed SummarEase through a
  registration file in `%LOCALAPPDATA%\ClariFile`. Each app works without the other.

**C2 Offline.** Documents are processed on the computer. No paid API. Installation and model downloads may use
the internet; normal use does not.

**C3 User-facing.** It accepts documents (PDF, PPTX, DOCX, ODT) and pasted text.

**C4 At least three summary levels.** Four, since 0.2 (C12).

**C5 A readable text view.** Formatting may change layout only (line breaks, headings, lists, spacing), never the
words.

**C6 Copy and Export.**
- Copy puts the text on the clipboard.
- Export creates a searchable PDF or a Word file.
- Exports are new files, made only on request and saved where the user chooses. Originals are never changed.
- What is exported is still open (P6).

**C7 Content only.** Summaries come from the document's content, never from its file name.

**C8 Gaps are disclosed.** Parts that couldn't be read (for example, where OCR found no text) are said in the
summary.

**C9 Pasted text** is not stored unless the user chooses to store it.

**C10 English first.** Other languages come later.

**C11 Look.** The SummarEase colour is violet (#6C47FF), and it uses the SummarEase icon.

**C12 Four levels** (confirmed in 0.2, was P1): Minimum, Key points, By section, Maximum.
- **What a line is.** Every summary line is a sentence, a bullet or a line taken from the document, word for word,
  with a correct link to its page, slide or section. Nothing is reworded, joined or invented (C13).
- **What each level contains.**
  - *Minimum:* the gist, in 1 to 3 lines.
  - *Key points:* the document's main points, in document order.
  - *By section:* each section's heading (a heading, a slide title, or a page range when there are no headings),
    with up to 3 lines under it. Every section that has readable text appears.
  - *Maximum:* every section, with more lines each; the most a summary shows short of the readable text (C5).
- **Length budgets [Default]**, in words of the document's readable text (W). A level never goes over its budget.

  | Level | Budget | Lines |
  |---|---|---|
  | Minimum | the larger of 30 words and 3% of W | 1 to 3 |
  | Key points | the larger of 80 words and 10% of W | at most 12 |
  | By section | the larger of 150 words and 20% of W | at most 3 per section |
  | Maximum | 40% of W | no fixed limit |

  A document shorter than a level's floor may be shown whole at that level, still as linked source lines.
- **Each higher level includes the sources of the level below:** every line of Minimum is in Key points, every
  line of Key points is in By section, and every line of By section is in Maximum. A line appears once per level.
- **Slides** are summarized by their structure, not by ranking sentences: a slide contributes its title and its
  top-level bullets, in slide order. Sub-bullets appear only at Maximum. Speaker notes appear only at Maximum,
  marked as notes. Which slides reach the lower levels is the method's choice (`MILESTONES.md`, M2).
- **OCR text** is marked wherever it appears and is trusted less: it never stands alone at Minimum when the
  document has native text.

**C13 Extractive first** (confirmed in 0.2, was P2): summaries are made of sentences, bullets and lines taken from
the document. Any later rewriting (P3) is a separate decision.

## Proposals (not confirmed)

- **P3 A local LLM only later:** optional, and only to rewrite an extractive draft, never to add content.
- **P4 Evaluation** (carried over from ClassiFile's record, B6): page references do not prove that a summary keeps
  the meaning. Kept meaning and qualifications must be checked. The plan is in `EVALUATION.md`.
- **P5 The reader:** see `READER.md` (option (a) was taken in M0; the copy is ClassiFile's tag `reader-v6`).
- **P6 What Export exports** (the owner decides; the options and a recommendation are in `docs/STATUS.md`).

## Changelog

- **0.1 (2026-10-14):** first record, from ClassiFile's A11 and the owner's earlier decisions. Authorized by the
  owner.
- **0.2 (2026-10-15):** C12 four levels (was P1) and C13 extractive first (was P2) confirmed by the owner, with
  testable level definitions: what each level contains, length budgets [Default] relative to document length,
  nesting of sources, slides by structure, OCR trusted less. P3 stays a proposal. P6 (what Export exports) added
  as an open decision. Authorized by the owner.
