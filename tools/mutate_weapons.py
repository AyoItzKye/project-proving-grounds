"""Code Master TS-14: mutation check of tools/test_weapons.py. In a git-archive copy of a commit (tools/baseline_compare.py
extract: maps linked, removed safely), each mutant switches one weapon behaviour off in brain/bot.py; the test must fail
("KILLED") on every one. Writes logs/verify/mutate_weapons_<commit>.txt.

usage: python -I mutate_weapons.py [commit]      (default HEAD)
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from baseline_compare import ROOT, extract, remove  # noqa: E402

MUTANTS = [   # (name, text to replace or None to append, replacement)
    ("no close-range spam (FIRE_FAST empty)", None, "\nFIRE_FAST = {}\n"),
    ("no charge weapons (CHARGE empty)", None, "\nCHARGE = {}\n"),
    ("no close-quarters guns (CQ empty)", None, "\nCQ = set()\n"),
    ("no zoom (SCOPED empty)", None, "\nSCOPED = set()\n"),
    ("no dry switch", "        if cur >= 0 and ammo[cur] == 0:\n", "        if False:\n"),
    ("no empty-magazine switch", "            if mag[cur] == 0 and not recruit and d < 15.0:\n", "            if False:\n"),
    ("no blast switch", "            if me.weapon in BLAST and d < BLAST[me.weapon] + 0.5:\n", "            if False:\n"),
    ("no finishing hold", "            return -1      # a shot or two from the kill", "            pass      # a shot or two from the kill"),
    ("no trade inside the blast", "        trade = cornered and facing and", "        trade = False and cornered and facing and"),
    ("no reload between fights", "        if me.weapon not in me.weapons or s.per.visible_enemies():\n", "        if True:\n"),
    ("no spray hold up close", "                s.spray_until = now + s.rng.uniform(0.25, 0.45)", "                s.spray_until = now"),
    ("a charge survives a switch", "            s.charge_since = None      # a charge belongs to the gun", "            pass      # a charge belongs to the gun"),
    ("range rule only in fights", "        if b is None:\n            # no fight this tick", "        if False:\n            # no fight this tick"),
]


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    sha = subprocess.run(["git", "rev-parse", "--short", commit], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    d = os.path.join(tempfile.mkdtemp(prefix="halo_mutate_"), "copy")
    extract(commit, d)
    bot = os.path.join(d, "brain", "bot.py")
    orig = open(bot, encoding="utf-8").read()
    lines = []
    try:
        for name, old, new in MUTANTS:
            src = orig + new if old is None else orig.replace(old, new, 1)
            if old is not None and src == orig:
                lines.append(f"{name}: NOT APPLIED (pattern missing)")
                continue
            open(bot, "w", encoding="utf-8").write(src)
            r = subprocess.run([sys.executable, "-I", "test_weapons.py"], cwd=os.path.join(d, "tools"),
                               capture_output=True, text=True, timeout=900)
            tail = (r.stdout + r.stderr).strip().splitlines()
            lines.append(f"{name}: {'KILLED' if r.returncode else 'SURVIVED'} | {tail[-1][:200] if tail else ''}")
        open(bot, "w", encoding="utf-8").write(orig)
        r = subprocess.run([sys.executable, "-I", "test_weapons.py"], cwd=os.path.join(d, "tools"), capture_output=True,
                           text=True, timeout=900)
        lines.append(f"unmutated: {'PASS' if r.returncode == 0 else 'FAIL'}")
    finally:
        remove(d)
        os.rmdir(os.path.dirname(d))
    killed = sum(1 for x in lines if "KILLED" in x)
    lines.append(f"killed {killed} of {len(MUTANTS)}")
    path = os.path.join(ROOT, "logs", "verify", f"mutate_weapons_{sha}.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
