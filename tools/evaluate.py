"""The one evaluation command (EVALUATION.md). Runs every method on the development set and prints one report.

Usage: python -m tools.evaluate [--set FOLDER ...] [--no-ocr]      (default: data/development)

For now it reports the automatic checks only: traceable lines, budgets kept, empty summaries explained, levels
nested, gaps disclosed, the same output for the same input (a rebuild and a fresh read), and renaming a file changes
nothing. Rubric scoring (blind summaries for the owner) is added when the owner's reference key points exist.
Documents are named by neutral IDs (data/doc_ids.csv, not tracked); the report holds no document text, file names
or paths. Held-out sets are refused before any file is opened, also when a chosen folder contains one or leads to
one. Each document is checked in a worker process with a time limit. A copy of the report is saved in
data/reports/ (not tracked); until the run ends it says it is incomplete.

Exit codes: 0 every check passed on every document; 1 a check failed; 2 refused or nothing to check; 3 no check
failed but some documents could not be checked (unreadable, timed out or crashed).
Deterministic: the same files give the same report.
"""
import argparse
import csv
import hashlib
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SET = ROOT / "data" / "development"
IDS = ROOT / "data" / "doc_ids.csv"
REPORTS = ROOT / "data" / "reports"
HELD_OUT = ("final-check", "validation", "final-eval")
CHECKS = ("traceable", "budgets", "explained", "nesting", "gaps", "same output", "renaming")
DOC_LIMIT = 960     # seconds per document: three reads with OCR (the worker's 300 s each) and the builds


def wilson(k, n, z=1.96):
    """A simple 95% range for k of n."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def protected(path):
    return any(part.casefold() in HELD_OUT for part in Path(path).parts)


def collect(folders):
    """(document paths, None) or (None, a refusal). Locations are checked before anything is opened or hashed: a
    held-out folder, a folder inside one, a folder that holds one, and a link or junction that leads to one are all
    refused."""
    from summarease.reader import READERS

    paths = []
    for folder in folders:
        if protected(folder) or protected(folder.resolve()):
            return None, "Refused: that is a held-out set (EVALUATION.md)."
        if not folder.is_dir():
            return None, "Refused: a --set folder does not exist."
        found = []
        for root, dirs, files in os.walk(folder):
            here = Path(root)
            if any(protected(d) or protected((here / d).resolve()) for d in dirs):
                return None, "Refused: the set contains a held-out set (EVALUATION.md)."
            for name in files:
                p = here / name
                if p.suffix.lower() in READERS:
                    if protected(p.resolve()):
                        return None, "Refused: the set contains a held-out set (EVALUATION.md)."
                    found.append(p)
        paths += sorted(found, key=lambda p: p.relative_to(folder).as_posix().casefold())
    return paths, None


def doc_ids(files):
    """{sha256: "D<n>"}, kept in data/doc_ids.csv; new documents get the next numbers, in path order."""
    ids = {}
    if IDS.exists():
        with open(IDS, newline="", encoding="utf-8") as f:
            ids = {r["sha256"]: r["id"] for r in csv.DictReader(f)}
    n = max((int(i[1:]) for i in ids.values()), default=0)
    for path, sha in files:
        if sha not in ids:
            n += 1
            ids[sha] = f"D{n}"
    IDS.parent.mkdir(parents=True, exist_ok=True)
    with open(IDS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sha256", "id"])
        w.writerows(sorted(ids.items(), key=lambda kv: int(kv[1][1:])))
    return ids


def analyse(path):
    """(record, blocks) for one file, read as the app reads it, or (None, reason)."""
    from summarease.readable import from_record
    from summarease.reader import read_document
    from summarease.worker import pdf_bold

    res = read_document(path)
    if res.status != "ok":
        return None, res.reason or res.status
    bold = pdf_bold(path, res.sha256) if res.record.format == "pdf" else None
    return (res.record, from_record(res.record, bold)), None


def summaries(record, blocks, method):
    from summarease.summarize import LEVELS, build, source_from_record

    src = source_from_record(record, blocks)
    return src, {level: build(src, level, method) for level in LEVELS}


def check_document(path, tmp):
    """Every check on one document, in a worker: {"group", "found": {method: {check: [problems]}}, "empty":
    {method: {level: reason}}}, or {"left_out": reason}. Problems hold no document text."""
    from summarease import checks

    path = Path(path)
    got, reason = analyse(path)
    if got is None:
        return {"left_out": f"unreadable ({reason})"}
    record, blocks = got
    fresh, _ = analyse(path)
    renamed = Path(tmp) / f"renamed{path.suffix.lower()}"
    shutil.copyfile(path, renamed)
    moved_doc, _ = analyse(renamed)
    renamed.unlink()
    texts = checks.unit_texts(record)
    src, _ = summaries(record, blocks, "baseline")
    kind = "slides" if src.slides else "prose"
    out = {"group": f"pdf {kind}" if record.format == "pdf" else f"{record.format} ({kind})", "found": {}, "empty": {}}
    for method in ("baseline", "structure" if src.slides else "ranking"):
        _, levels = summaries(record, blocks, method)
        _, twice = summaries(record, blocks, method)
        _, again = summaries(*fresh, method) if fresh else (None, {})
        _, moved = summaries(*moved_doc, method) if moved_doc else (None, {})
        out["found"][method] = {
            "traceable": [p for s in levels.values() for p in checks.traceable(s, texts)],
            "budgets": [p for s in levels.values() for p in checks.within_budget(s, blocks)],
            "explained": [p for s in levels.values() for p in checks.explained(s)],
            "nesting": checks.nested(levels),
            "gaps": [p for s in levels.values() for p in checks.gaps_disclosed(s, blocks, record)],
            "same output": [f"{lv}: differs on a rebuild" for lv in levels if not checks.same(levels[lv], twice[lv])]
            + [f"{lv}: differs on a fresh read" for lv in levels
               if lv not in again or not checks.same(levels[lv], again[lv])],
            "renaming": [f"{lv}: differs under another name" for lv in levels
                         if lv not in moved or not checks.same(levels[lv], moved[lv])],
        }
        out["empty"][method] = {lv: s.empty for lv, s in levels.items() if s.empty}
    return out


def evaluate(files, tmp, progress=lambda *a: None):
    from summarease.worker import STOPPED, TIMED_OUT, Job, call

    results = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # (method, format) -> check -> [passed, checked]
    failures, left_out, kinds = [], [], defaultdict(int)
    empty = defaultdict(int)                                     # (method, format, level, reason) -> documents
    for n, (doc_id, path) in enumerate(files, 1):
        progress(doc_id, n, len(files))
        job = Job(call, check_document, str(path), tmp, time_limit=DOC_LIMIT)
        while (res := job.poll()) is None:
            time.sleep(0.05)
        state, got = res
        if state != "ok" or "left_out" in got:
            left_out.append((doc_id, got["left_out"] if state == "ok" else got if got in (STOPPED, TIMED_OUT)
                             else f"error ({got})"))
            continue
        kinds[got["group"]] += 1
        for method, found in got["found"].items():
            for check, problems in found.items():
                cell = results[(method, got["group"])][check]
                cell[1] += 1
                cell[0] += not problems
                failures += [(doc_id, method, check, p) for p in problems]
            for level, reason in got["empty"][method].items():
                empty[(method, got["group"], level, reason)] += 1
    return results, failures, left_out, kinds, empty


def versions(no_ocr):
    """What the report was made with: code revision and whether it had local changes, reader and PyMuPDF versions,
    and whether OCR was really available."""
    import pymupdf

    from summarease.reader import ocr

    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rev = git("rev-parse", "--short", "HEAD") or "unknown"
    dirty = " with local changes" if git("status", "--porcelain") else ""
    tag = next((l.split("**`")[1].split("`")[0] for l in (ROOT / "summarease" / "reader" / "SOURCE.md")
                .read_text(encoding="utf-8").splitlines() if "**`" in l), "unknown")
    available = not no_ocr and ocr.tessdata() is not None
    return (f"Code {rev}{dirty}; reader {tag}; PyMuPDF {pymupdf.VersionBind}; "
            f"OCR {'on' if available else 'off'}{' (requested on, not installed)' if not no_ocr and not available else ''}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--set", type=Path, nargs="+", default=[DEFAULT_SET], help="development folders, read only")
    ap.add_argument("--no-ocr", action="store_true", help="switch OCR off (quicker; pictures count as gaps)")
    a = ap.parse_args(argv)
    paths, refusal = collect(a.set)
    if refusal:
        print(refusal)
        return 2
    if not paths:
        print("Nothing to check: no PDF, PPTX, DOCX or ODT files were found in the set.")
        return 2
    if a.no_ocr:
        os.environ["CLASSIFILE_OCR"] = "off"

    shas = [(p, hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    ids = doc_ids(shas)
    first = {}
    for p, s in shas:
        first.setdefault(s, p)
    files = sorted(((ids[s], p) for s, p in first.items()), key=lambda f: int(f[0][1:]))
    fingerprint = hashlib.sha256("\n".join(sorted(first)).encode()).hexdigest()[:16]
    header = [f"SummarEase evaluation, {datetime.now():%Y-%m-%d %H:%M}",
              f"Command: python -m tools.evaluate ({len(a.set)} set folder(s){', --no-ocr' if a.no_ocr else ''})",
              versions(a.no_ocr), f"Set fingerprint {fingerprint}"]
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = REPORTS / f"evaluation-{datetime.now():%Y%m%d-%H%M%S}.txt"
    report.write_text("\n".join(header + ["Status: INCOMPLETE (the run has not finished)"]) + "\n", encoding="utf-8")

    progress = lambda doc_id, n, total: print(f"  checking {doc_id} ({n} of {total})", file=sys.stderr, flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        results, failures, left_out, kinds, empty = evaluate(files, tmp, progress)

    out = header + [""]
    dupes = len(paths) - len(files)
    counted = len(files) - len(left_out)
    out.append(f"Development set: {len(paths)} files, {len(files)} documents (unique contents; {dupes} duplicate "
               f"file{'s' * (dupes != 1)} not counted again), {counted} checked, {len(left_out)} left out")
    out += [f"  left out {doc_id}: {reason}" for doc_id, reason in left_out]
    out.append("  by format: " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())))
    out += ["", "Automatic checks: documents passing every level, of documents checked (95% range)",
            f"{'method':10} {'format':14} " + " ".join(f"{c:>20}" for c in CHECKS)]
    for (method, group), cells in sorted(results.items()):
        row = []
        for c in CHECKS:
            k, n = cells[c]
            lo, hi = wilson(k, n)
            row.append(f"{k}/{n} ({lo:.0%}-{hi:.0%})")
        out.append(f"{method:10} {group:14} " + " ".join(f"{r:>20}" for r in row))
    out += ["", "Empty summaries (explained, but not useful summaries): documents per method, format, level, reason"]
    out += [f"  {m:10} {g:14} {lv:13} {r}: {n}" for (m, g, lv, r), n in sorted(empty.items())] or ["  none"]
    out += ["", f"Problems: {len(failures)}"]
    out += [f"  {doc_id} {method} {check}: {problem}" for doc_id, method, check, problem in failures]
    code = 1 if failures else 3 if left_out else 0
    out += ["", "These counts describe the owner's development documents; they are not accuracy estimates.",
            f"Status: complete; exit code {code}"]
    print("\n".join(out))
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Saved a copy of this report in data/reports/{report.name}.")
    return code


if __name__ == "__main__":
    sys.exit(main())
