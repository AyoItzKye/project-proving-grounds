"""The no-break gate: runs every test that guards a behavior in docs/WORKING_BEHAVIORS.md (the ledger of behaviors
proven working live), plus every tools/test_reg_*.py, and prints one row per behavior: id, behavior, test, result.
Exit 1 when any guarding test fails, is missing, or crashes. Ledger rows whose test is NONE are counted, not run.

A test named file::check (tools/test_reg_core.py::air_wall) is that file's line "ok   <check>" / "FAIL <check>"; the
file runs once. Each file runs in its own process (cwd tools/, python -I, 900 s at most), as tools/run_tests.py does.

usage: python -I test_regressions.py            run the gate, print the table
       python -I test_regressions.py --list     the ledger's rows and tests, nothing run
       python -I test_regressions.py --gate     as the release builders call it: a pass already recorded for this exact
                                                code (HEAD + the uncommitted diff of brain/ tools/ native/ maps/_*/ and
                                                the ledger) is reused, else the gate runs
tools/run_tests.py prints the same table from its own results at the end of a full run (report()).
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
LEDGER = os.path.join(ROOT, "docs", "WORKING_BEHAVIORS.md")
PASSED = os.path.join(ROOT, "logs", "verify", "regressions_pass.json")
TEST = re.compile(r"tools/(test_\w+\.py)(?:::(\w+))?")
CHECK_LINE = re.compile(r"^(ok  |FAIL) (\w+)\s*$")


def ledger():
    """[(id, area, behavior, [(file, check or None)])] from the ledger's table rows (the id cell like AIR-01); [] in a
    copy without the ledger (the public release leaves docs/ out but the code guide)."""
    rows, area = [], ""
    if not os.path.exists(LEDGER):
        return rows
    for line in open(LEDGER, encoding="utf-8"):
        if line.startswith("## "):
            area = line[3:].strip()
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) < 5 or not re.fullmatch(r"[A-Z]+-\d+", cells[0]):
            continue
        # (a NONE cell may still name a test in its note, "NONE (tools/test_x.py covers only ...)": not a guard)
        tests = [] if cells[-1].upper().startswith("NONE") else [(f, c or None) for f, c in TEST.findall(cells[-1])]
        rows.append((cells[0], area, cells[1], tests))
    return rows


def extra_files(rows):
    named = {f for *_, tests in rows for f, _ in tests}
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(HERE, "test_reg_*.py"))
                  if os.path.basename(f) not in named)


def run_file(name):
    """(exit code, output lines) of one test file."""
    if not os.path.exists(os.path.join(HERE, name)):
        return 2, [f"missing: tools/{name}"]
    try:
        r = subprocess.run([sys.executable, "-I", name], cwd=HERE, capture_output=True, text=True, timeout=900,
                           encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout + r.stderr).strip().splitlines()
    except subprocess.TimeoutExpired:
        return 1, ["timed out after 900 s"]


def verdict(res, f, check):
    """'PASS' / 'SKIP' / 'FAIL: why' for a ledger test from its file's result (code, lines)."""
    if res is None:
        return "NOT RUN"
    code, lines = res
    if check:
        got = [m.group(1) for m in map(CHECK_LINE.match, lines) if m and m.group(2) == check]
        if not got:
            return f"FAIL: no line for check {check}" + (f" ({lines[-1][:80]})" if lines else "")
        return "PASS" if got[-1] == "ok  " else "FAIL: " + next(
            (x for x in lines if x.startswith(check + ":")), "see the file's output")[:120]
    if code:
        return "FAIL: " + (lines[-1][:120] if lines else f"exit {code}")
    return "SKIP" if lines and "SKIP" in lines[-1] else "PASS"


def report(results, out=print):
    """Print the table for results {file name: (code, lines)}; True when no guarding test failed."""
    rows = ledger()
    extra = extra_files(rows)
    bad, none, guarded = [], 0, 0
    if not rows:
        out("no-break table: no docs/WORKING_BEHAVIORS.md in this copy (only the tools/test_reg_*.py files count)")
    out(f"{'id':8} {'behavior':60} {'test':42} result")
    for rid, area, what, tests in rows:
        if not tests:
            none += 1
            out(f"{rid:8} {what[:60]:60} {'NONE':42} (no test guards it)")
            continue
        guarded += 1
        for f, c in tests:
            v = verdict(results.get(f), f, c)
            out(f"{rid:8} {what[:60]:60} {(f + ('::' + c if c else ''))[:42]:42} {v}")
            if v.startswith("FAIL") or v == "NOT RUN":
                bad.append((rid, what, f + ("::" + c if c else ""), v))
    # a guarding file that failed in a check no row names still fails the gate
    for f in sorted({f for *_, tests in rows for f, _ in tests}):
        if results.get(f, (0,))[0] and not any(t.split("::")[0] == f for _, _, t, _ in bad):
            v = verdict(results[f], f, None)
            out(f"{'(file)':8} {'(a failure outside the checks the ledger names)':60} {f[:42]:42} {v}")
            bad.append(("(file)", "", f, v))
    for f in extra:
        v = verdict(results.get(f), f, None)
        out(f"{'(reg)':8} {'(a test_reg file not in the ledger yet)':60} {f[:42]:42} {v}")
        if v.startswith("FAIL") or v == "NOT RUN":
            bad.append(("(reg)", "", f, v))
    out(f"\n{len(rows)} behaviors: {guarded} guarded, {none} with no test; {len(bad)} failing row(s)")
    for rid, what, t, v in bad:
        out(f"  FAILING {rid} {what[:70]} | {t} | {v}")
    return not bad


def files_needed():
    rows = ledger()
    return sorted({f for *_, tests in rows for f, _ in tests} | set(extra_files(rows)))


def code_key():
    """HEAD and the uncommitted diff of the code, the maps' data (learned files change test results too) and the
    ledger, with the untracked files' names there: a recorded pass holds for exactly this only."""
    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True).stdout
    paths = ["brain", "tools", "native", "maps", "docs/WORKING_BEHAVIORS.md"]
    h = hashlib.sha256(git("diff", "HEAD", "--binary", "--", *paths))
    h.update(git("ls-files", "--others", "--exclude-standard", "--", *paths))
    return git("rev-parse", "HEAD").decode().strip() + ":" + h.hexdigest()


def main():
    args = sys.argv[1:]
    if "--list" in args:
        for rid, area, what, tests in ledger():
            print(f"{rid:8} {area[:24]:24} {what[:60]:60} {', '.join(f + ('::' + c if c else '') for f, c in tests) or 'NONE'}")
        return
    key = code_key() if "--gate" in args else None
    if key is not None:
        try:
            if json.load(open(PASSED, encoding="utf-8")).get("key") == key:
                print("regressions: passed already on this exact code (logs/verify/regressions_pass.json)")
                return
        except (OSError, ValueError):
            pass
    t0, results = time.time(), {}
    for f in files_needed():
        t = time.time()
        results[f] = run_file(f)
        print(f"{'ok  ' if results[f][0] == 0 else 'FAIL'} {f} ({time.time() - t:.0f} s)", flush=True)
    print()
    ok = report(results)
    print(f"({time.time() - t0:.0f} s)")
    if ok:
        os.makedirs(os.path.dirname(PASSED), exist_ok=True)
        json.dump({"key": key or code_key(), "when": time.strftime("%Y-%m-%d %H:%M:%S")}, open(PASSED, "w"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
