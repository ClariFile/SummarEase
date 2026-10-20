Read CLAUDE.md, DECISION_RECORD.md and DOS_AND_DONTS.md (if present) before any work. They are authoritative.

# AGENTS.md — SummarEase

The rules below are a short copy for agents that skip linked files. If they ever differ, CLAUDE.md and
DECISION_RECORD.md win. Never edit DECISION_RECORD.md; propose changes to the owner.

## Non-negotiable rules

- **Originals are read-only.** Never modify, move, rename or delete the user's documents, change their metadata, or
  create files next to them. Never overwrite an existing file; exports are new files where the user chooses.
- **Held-out data is off limits.** Never open `data\validation`, `data\final-eval` or `data\final-check` (here or in
  ClassiFile) unless the owner says so.
- **Privacy.** No document text, file names or personal data in tracked files, logs, error messages or commits.
  Tests use neutral IDs.
- **Privacy audit before every push;** push only with 0 hits. **Never force-push.**
- **Ask first** before deleting any file the owner put in the project, before adding a dependency, and before
  launching other programs.
- Summaries come from the content, never the file name. OCR stays marked as OCR; disclose what couldn't be read.
- No network calls at runtime. No LLMs or extra ML libraries unless the record allows them. Pasted text is not
  stored unless the user chooses. Never write ClassiFile's data.
- One milestone at a time (MILESTONES.md); stop at each stop point and wait for the owner's go-ahead.

## Commands (Windows, from the repository root)

```
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt   # setup; needs the owner's approval
.venv\Scripts\python -m summarease.app                        # run
.venv\Scripts\python -m pytest                                # test (full suite, before reporting)
.venv\Scripts\python -m pytest -m "not ocr"                   # test without the slower real-OCR tests
.venv\Scripts\python -m tools.audit_terms --range origin/main..main   # privacy audit, before every push
```
