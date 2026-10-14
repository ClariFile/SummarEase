# Decision Record — SummarEase

Version 0.1 · 2026-10-14

**Status:** authoritative. Only the owner can change it. Every change goes in the changelog at the end.
Confirmed entries come from ClassiFile's decision record (A11) and the owner's earlier decisions. Proposals are
kept apart and are not rules until the owner confirms them.

## Confirmed

**C1 A separate project.**
- Own folder, environment and repository. Usable on its own.
- ClassiFile may use SummarEase only after asking the user each time. It finds an installed SummarEase through a
  registration file in `%LOCALAPPDATA%\ClariFile`. Each app works without the other.

**C2 Offline.** Documents are processed on the computer. No paid API. Installation and model downloads may use
the internet; normal use does not.

**C3 User-facing.** It accepts documents (PDF, PPTX, DOCX, ODT) and pasted text.

**C4 At least three summary levels.**

**C5 A readable text view.** Formatting may change layout only (line breaks, headings, lists, spacing), never the
words.

**C6 Copy and Export.**
- Copy puts the text on the clipboard.
- Export creates a searchable PDF or a Word file.
- Exports are new files, made only on request and saved where the user chooses. Originals are never changed.

**C7 Content only.** Summaries come from the document's content, never from its file name.

**C8 Gaps are disclosed.** Parts that couldn't be read (for example, where OCR found no text) are said in the
summary.

**C9 Pasted text** is not stored unless the user chooses to store it.

**C10 English first.** Other languages come later.

**C11 Look.** The SummarEase colour is violet (#6C47FF), and it uses the SummarEase icon.

## Proposals (not confirmed)

- **P1 Four named levels:** Minimum, Key points, By section, Maximum. Each summary line links to its page (or slide,
  or section).
- **P2 Extractive first:** summaries are made of sentences taken from the document.
- **P3 A local LLM only later:** optional, and only to rewrite an extractive draft, never to add content.
- **P4 Evaluation** (carried over from ClassiFile's record, B6): page references do not prove that a summary keeps
  the meaning. Kept meaning and qualifications must be checked.
- **P5 The reader:** see `READER.md`.

## Changelog

- **0.1 (2026-10-14):** first record, from ClassiFile's A11 and the owner's earlier decisions. Authorized by the
  owner.
