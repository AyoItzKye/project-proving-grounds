"""Test baseline across commits (Code Master OL-03 / TS-18): runs (1) the old commit's code with its own suites, (2) the
new commit's code with its own suites, (3) the old commit's suites against the new commit's code, which shows every
old expectation the change broke (each must be a reviewed spec change or a bug the change fixed). Each run is a
git-archive extract in %TEMP% with maps/ linked (a junction to this repo's maps: removed first, never followed),
every tools/test_*.py in its own process. Writes logs/verify/baseline_<old>_<new>.txt.

usage: python -I baseline_compare.py <old commit> <new commit>
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def extract(commit, into, tests_from=None):
    os.makedirs(into)
    tar = subprocess.run(["git", "archive", commit, "brain", "tools", "native/shared.h"], cwd=ROOT, capture_output=True,
                         check=True).stdout
    subprocess.run(["tar", "-x", "-C", into], input=tar, check=True)
    if tests_from:                                   # the old suites over the new code
        for f in glob.glob(os.path.join(into, "tools", "test_*.py")):
            os.remove(f)
        tar = subprocess.run(["git", "archive", tests_from, "tools"], cwd=ROOT, capture_output=True, check=True).stdout
        tmp = into + "_t"
        os.makedirs(tmp)
        subprocess.run(["tar", "-x", "-C", tmp], input=tar, check=True)
        for f in glob.glob(os.path.join(tmp, "tools", "test_*.py")):
            shutil.copy(f, os.path.join(into, "tools"))
        shutil.rmtree(tmp)
    os.makedirs(os.path.join(into, "logs"))
    # maps: each map folder linked to this repo's (9 GB, read only), but maps/_inputs (the decoded buttons, which change
    # with the code) from the commit itself: with today's a pre-change run failed its own test_buttons
    maps = os.path.join(into, "maps")
    os.makedirs(maps)
    for e in os.listdir(os.path.join(ROOT, "maps")):
        src = os.path.join(ROOT, "maps", e)
        if e == "_inputs":
            continue
        if os.path.isdir(src):
            subprocess.run(["cmd", "/c", "mklink", "/J", os.path.join(maps, e), src], capture_output=True, check=True)
        else:
            shutil.copy2(src, maps)
    tar = subprocess.run(["git", "archive", commit, "maps/_inputs"], cwd=ROOT, capture_output=True).stdout
    if tar:                                          # (a commit from before maps/_inputs existed has none)
        subprocess.run(["tar", "-x", "-C", into], input=tar, check=True)


def remove(into):
    """Delete an extract, links first (never followed). Also takes one that failed part way, or one from before a6b69da
    whose maps folder is itself a junction (third review N5)."""
    maps = os.path.join(into, "maps")
    if os.path.isjunction(maps):
        subprocess.run(["cmd", "/c", "rmdir", maps], capture_output=True)                      # the link only
    for e in (os.listdir(maps) if os.path.isdir(maps) and not os.path.isjunction(maps) else []):
        if os.path.isjunction(os.path.join(maps, e)):
            subprocess.run(["cmd", "/c", "rmdir", os.path.join(maps, e)], capture_output=True)   # the link only
    left = [e for e in (os.listdir(maps) if os.path.isdir(maps) and not os.path.isjunction(maps) else [])
            if os.path.isjunction(os.path.join(maps, e))]
    if left or os.path.isjunction(maps):
        sys.exit(f"map junctions in {maps} not removed ({left[:3] or 'maps'}): stopping before any delete")
    if os.path.isdir(into):
        shutil.rmtree(into)


def run_suites(into):
    out = []
    for f in sorted(glob.glob(os.path.join(into, "tools", "test_*.py"))):
        r = subprocess.run([sys.executable, "-I", f], cwd=os.path.join(into, "tools"), capture_output=True, text=True,
                           timeout=900)
        tail = (r.stdout + r.stderr).strip().splitlines()
        out.append((os.path.basename(f), r.returncode, tail[-1][:300] if tail else ""))
    return out


def main():
    old, new = sys.argv[1], sys.argv[2]
    base = tempfile.mkdtemp(prefix="halo_baseline_")
    runs = [(f"(1) {old}: its own suites", old, None), (f"(2) {new}: its own suites", new, None),
            (f"(3) {old}'s suites against {new}'s code", new, old)]
    lines = []
    try:
        for k, (title, code, tests) in enumerate(runs):
            d = os.path.join(base, f"run{k}")
            try:
                extract(code, d, tests)           # (inside: an extract that fails part way is removed too)
                res = run_suites(d)
            finally:
                remove(d)
            ok = sum(1 for _, rc, _ in res if rc == 0)
            lines.append(f"== {title}: {ok} / {len(res)} pass")
            lines += [f"   {'PASS' if rc == 0 else 'FAIL'} {name}: {tail}" for name, rc, tail in res]
    finally:
        if os.path.isdir(base) and not os.listdir(base):
            os.rmdir(base)
    os.makedirs(os.path.join(ROOT, "logs", "verify"), exist_ok=True)
    path = os.path.join(ROOT, "logs", "verify", f"baseline_{old[:7]}_{new[:7]}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("written:", path)


if __name__ == "__main__":
    main()
