"""Every tools/test_*.py once, each in its own process (tools/shuffle_suites.py runs them in three orders): one line per
file, the failures' last lines at the end, then (a full run, no filter) the no-break table of docs/WORKING_BEHAVIORS.md
from these same results (tools/test_regressions.py report: every live-proven behavior, its test, the result). Exit code
1 when any fails. test_regressions.py itself is not run here (it would run the suite's guarding tests a second time).

usage: python -I run_tests.py [name-filter]
"""
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else ""
    bad, results = [], {}
    for f in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        name = os.path.basename(f)
        if pat not in name or name == "test_regressions.py":
            continue
        t = time.time()
        try:
            r = subprocess.run([sys.executable, "-I", name], cwd=HERE, capture_output=True, text=True, timeout=900)
            out, code = (r.stdout + r.stderr).strip().splitlines(), r.returncode
        except subprocess.TimeoutExpired:
            out, code = ["timed out after 900 s"], 1
        results[name] = (code, out)
        print(f"{'ok  ' if code == 0 else 'FAIL'} {name} ({time.time() - t:.0f} s) {out[-1][:100] if out else ''}", flush=True)
        if code:
            bad.append((name, out[-12:]))
    for name, tail in bad:
        print(f"\n== {name}\n" + "\n".join(tail))
    if not pat:
        sys.path.insert(0, HERE)
        import test_regressions
        print("\n== no-break table (docs/WORKING_BEHAVIORS.md)")
        if not test_regressions.report(results):
            bad.append(("test_regressions", []))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
