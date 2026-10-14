# CLAUDE.md — SummarEase (offline document summarizer)

You are implementing SummarEase, an offline desktop summarizer, part of the ClariFile suite. ClassiFile (the
categorizer) is a separate project with its own repository. The project owner makes all requirement decisions.

## Authoritative record

@DECISION_RECORD.md

The record above is authoritative.
- If a task, an older file or your own idea conflicts with it, follow the record and tell the owner about the
  conflict.
- Proposals in the record are not rules until the owner confirms them.
- Never edit DECISION_RECORD.md yourself. Propose changes to the owner instead.

## Non-negotiable rules

1. **Never touch the user's source files.** Open them read-only; never modify, move, rename or delete them, change
   their metadata, or create files next to them.
2. **Never overwrite an existing file.** Exports are new files, saved where the user chooses.
3. **Summaries come from the content**, never from the file name. Formatting changes layout, never the words.
4. **Disclose what couldn't be read.** OCR text stays marked as OCR.
5. **No network calls at runtime.** Install dependencies during setup only, with the owner's approval.
6. **No LLMs or extra ML libraries** unless the record allows them for the current milestone.
7. **Report results honestly.** Never present scores as probabilities; never claim accuracy from a few samples.
8. **No document text in logs**, error messages, tracked files or commit messages.
9. **Pasted text is not stored** unless the user chooses to store it.
10. **Never write ClassiFile's data.** Integration goes only through INTEGRATION.md, after ClassiFile v1.

## Working style

- Work one milestone at a time, from MILESTONES.md. Stop at each stop point and report. Never start the next
  milestone without the owner's go-ahead.
- Ask before adding any dependency, and before deleting any file the owner put in the project.
- Write tests alongside code, and run the full suite before reporting.
- If git is available, commit after each completed step with a clear message.
- The target is a native Windows desktop app. Keep paths and file operations cross-platform.
- Keep the interface minimal and readable in light and dark themes.

## Privacy of tracked files

- Never put the owner's name, user-folder paths, real document names, or titles, people or institutions copied
  from documents in tracked files or commit messages.
- Tests refer to development files by neutral IDs, with a local, untracked map.
- Before every push, run the privacy audit (set up in M0); push only with 0 hits. Never force-push.

## Licensing

If SummarEase uses PyMuPDF (AGPL), SummarEase is licensed under AGPL-3.0, like ClassiFile.
