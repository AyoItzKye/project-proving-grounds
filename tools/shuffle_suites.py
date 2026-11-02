"""Code Master TS-17: every tools/test_*.py in three seeded random orders, each file in its own process; any file whose
result changes with the order is reported. The checks inside one file keep their order (script-style tests).
Writes logs/verify/shuffle_<HEAD>.txt.

usage: python -I shuffle_suites.py
"""
import glob
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def main():
    files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(HERE, "test_*.py")))
    first, lines, bad = {}, [], 0
    for seed in (11, 22, 33):
        order = files[:]
        random.Random(seed).shuffle(order)
        res = {}
        for f in order:
            r = subprocess.run([sys.executable, "-I", f], cwd=HERE, capture_output=True, text=True, timeout=900)
            tail = (r.stdout + r.stderr).strip().splitlines()
            res[f] = (r.returncode, tail[-1][:120] if tail else "")
        ok = sum(1 for v in res.values() if v[0] == 0)
        lines.append(f"seed {seed}: {ok}/{len(files)} pass; order: {' '.join(x[5:-3] for x in order)}")
        for f, v in res.items():
            if v[0] != 0:
                lines.append(f"   FAIL {f}: {v[1]}")
            if f in first and first[f][0] != v[0]:
                bad += 1
                lines.append(f"   ORDER-DEPENDENT {f}: {first[f]} then {v}")
            first.setdefault(f, v)
    lines.append(f"order-dependent results: {bad}")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    os.makedirs(os.path.join(ROOT, "logs", "verify"), exist_ok=True)
    path = os.path.join(ROOT, "logs", "verify", f"shuffle_{head}.txt")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
