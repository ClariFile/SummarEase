# Dos and don'ts

Short rules learned while building ClassiFile.

## Documents

- **Never modify originals.** Open them read-only. Never move, rename, delete or re-save them, and never write
  files next to them.
- **Read the contents, not the file name.** A file name is never evidence of what a document says.
- **Keep OCR text marked as OCR.** It is less reliable than native text: say where it was used, and say what
  couldn't be read.
- **Exports are new files.** Never write into an existing file.

## Privacy

- **No document text in logs** or error messages.
- **No document text, document names or personal data in tracked files**, tests or commit messages. Refer to test
  documents by neutral IDs, with a local map that is not tracked.
- **Check before every push** with a list of private terms kept outside the repository.

## Measuring

- **Measure before tuning.** Change one thing at a time and keep the report.
- **Keep development, validation and final-test files separate.** Tune on development only; look at validation
  rarely; run the final test once per frozen version. Looking at a held-out set repeatedly makes it development
  data.
- **Report counts, not promises.** A score is not a probability, and a few sample files prove no accuracy.

## Working

- **One milestone at a time,** with stop points. Stop and report; wait for the owner's go-ahead.
- **Ask first** before deleting any of the owner's files, even exact duplicates, and before adding a dependency.
- **Don't use ClassiFile's internal summary as training data.** It was built for categorizing, not for reading.
- **Test alongside the code,** and run the whole suite before reporting.
- **Check the look in both light and dark themes,** and test the contrast of every text and background pair.
