"""The one evaluation command (EVALUATION.md). Runs every method on the development set and prints one report.

Usage: python -m tools.evaluate [--set FOLDER ...] [--no-ocr]      (default: data/development)

For now it reports the automatic checks only: traceable lines, budgets kept, levels nested, gaps disclosed, the same
output for the same input, and renaming a file changes nothing. Rubric scoring (blind summaries for the owner) is
added when the owner's reference key points exist. Documents are named by neutral IDs (data/doc_ids.csv, not
tracked); the report holds no document text or file names. Held-out sets are refused.
Deterministic: the same files give the same report.
"""
import argparse
import csv
import hashlib
import math
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SET = ROOT / "data" / "development"
IDS = ROOT / "data" / "doc_ids.csv"
HELD_OUT = ("final-check", "validation", "final-eval")
CHECKS = ("traceable", "budgets", "nesting", "gaps", "same output", "renaming")


def wilson(k, n, z=1.96):
    """A simple 95% range for k of n."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


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
    """(record, blocks, bold) for one file, read as the app reads it, or (None, reason)."""
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


def evaluate(files, tmp):
    from summarease import checks

    results = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # (method, format) -> check -> [passed, checked]
    failures, left_out, kinds = [], [], defaultdict(int)
    for doc_id, path in files:
        got, reason = analyse(path)
        if got is None:
            left_out.append((doc_id, reason))
            continue
        record, blocks = got
        renamed = Path(tmp) / f"renamed{path.suffix.lower()}"
        shutil.copyfile(path, renamed)
        again, _ = analyse(renamed)
        renamed.unlink()
        texts = checks.unit_texts(record)
        src, _ = summaries(record, blocks, "baseline")
        kind = "slides" if src.slides else "prose"
        group = f"pdf {kind}" if record.format == "pdf" else f"{record.format} ({kind})"
        kinds[group] += 1
        for method in ("baseline", "structure" if src.slides else "ranking"):
            _, levels = summaries(record, blocks, method)
            _, twice = summaries(record, blocks, method)
            _, moved = summaries(*again, method) if again else (None, {})
            found = {
                "traceable": [p for s in levels.values() for p in checks.traceable(s, texts)],
                "budgets": [p for s in levels.values() for p in checks.within_budget(s)],
                "nesting": checks.nested(levels),
                "gaps": [p for s in levels.values() for p in checks.gaps_disclosed(s, blocks)],
                "same output": [f"{lv}: differs on a second run" for lv in levels
                                if not checks.same(levels[lv], twice[lv])],
                "renaming": [f"{lv}: differs under another name" for lv in levels
                             if lv not in moved or not checks.same(levels[lv], moved[lv])],
            }
            for check, problems in found.items():
                cell = results[(method, group)][check]
                cell[1] += 1
                cell[0] += not problems
                failures += [(doc_id, method, check, p) for p in problems]
    return results, failures, left_out, kinds


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--set", type=Path, nargs="+", default=[DEFAULT_SET], help="development folders, read only")
    ap.add_argument("--no-ocr", action="store_true", help="switch OCR off (quicker; pictures count as gaps)")
    a = ap.parse_args(argv)
    if any(part.casefold() in HELD_OUT for folder in a.set for part in folder.resolve().parts):
        print("Refused: that is a held-out set (EVALUATION.md).")
        return 2
    if a.no_ocr:
        os.environ["CLASSIFILE_OCR"] = "off"
    from summarease.reader import READERS

    paths = [p for folder in a.set for p in sorted(
        (p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in READERS),
        key=lambda p: p.relative_to(folder).as_posix().casefold())]
    shas = [(p, hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    ids = doc_ids(shas)
    files = sorted(((ids[s], p) for p, s in shas), key=lambda f: int(f[0][1:]))
    with tempfile.TemporaryDirectory() as tmp:
        results, failures, left_out, kinds = evaluate(files, tmp)

    counted = len(files) - len(left_out)
    print(f"Development set: {len(files)} documents found, {counted} counted, {len(left_out)} left out"
          f" (OCR {'off' if a.no_ocr else 'on'})")
    for doc_id, reason in left_out:
        print(f"  left out {doc_id}: {reason}")
    print("  by format: " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())))
    print("\nAutomatic checks: documents passing every level, of documents checked (95% range)")
    print(f"{'method':10} {'format':14} " + " ".join(f"{c:>20}" for c in CHECKS))
    for (method, group), cells in sorted(results.items()):
        row = []
        for c in CHECKS:
            k, n = cells[c]
            lo, hi = wilson(k, n)
            row.append(f"{k}/{n} ({lo:.0%}-{hi:.0%})")
        print(f"{method:10} {group:14} " + " ".join(f"{r:>20}" for r in row))
    print(f"\nProblems: {len(failures)}")
    for doc_id, method, check, problem in failures:
        print(f"  {doc_id} {method} {check}: {problem}")
    print("\nThese counts describe the owner's development documents; they are not accuracy estimates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
