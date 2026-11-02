"""Did the bots' armor abilities and equipment come on? Per kind in a trace (live or simulated): ticks the equipment or
ability button was sent, ticks with the hold-mode button (botctl BTN ability, 1 << 23: Reach +0x08 bit 8), ticks the
game read it on (eq [kind, on]), presses (button rising edges) and presses that came on within 0.5 s; then the uses'
notes.. The Spire match 012320 before the hold bit: camo 36 of 37 presses on, sprint 71 of 164, armor lock 0 of 50,
evade 0 of 183, hologram 0 of 135, jetpack 0 of 27, drop shield 0 of 3. (Halo 3 equipment is thrown: its "on" is not
read, count the uses in the notes.)

usage: python -I ability_report.py <trace.jsonl> [...]
"""
import json
import os
import sys
from collections import defaultdict

EQUIP, HOLD = 128, 1 << 23        # tools/botctl.py BTN equipment, ability


def report(path):
    sent, bit, on, presses, took = (defaultdict(int) for _ in range(5))
    rows, notes, last = defaultdict(int), defaultdict(int), {}
    for line in open(path, encoding="utf-8", errors="replace"):
        if '"eq"' not in line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        eq, cmd = r.get("eq"), r.get("cmd")
        if not eq or not cmd:
            continue
        k, o, b = eq[0] or "-", bool(eq[1]), int(cmd[3])
        rows[k] += 1
        down = b & (EQUIP | HOLD)          # (a hold-mode kind sends the ability button alone, 0ecaed9)
        sent[k] += bool(down)
        bit[k] += bool(b & HOLD)
        on[k] += o
        for n in r.get("notes", []):
            if n.split(":")[0] in (k, "jetpack"):
                notes[n] += 1
        pb, pt, pk, done = last.get(r["id"], (0, -9.0, k, True))
        if down and not pb:
            presses[k] += 1
            pt, pk, done = r["t"], k, False
        if not done and o and r["t"] - pt < 0.5:
            took[pk] += 1
            done = True
        last[r["id"]] = (down, pt, pk, done)
    print(os.path.basename(path))
    for k in sorted(rows):
        print(f"  {k:16s} rows {rows[k]:6d}  button {sent[k]:6d}  hold bit {bit[k]:6d}  on {on[k]:6d}  "
              f"presses {presses[k]:5d}  on within 0.5 s {took[k]:4d}")
    for n, c in sorted(notes.items(), key=lambda kv: -kv[1])[:15]:
        print(f"    {c:5d}  {n}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        report(p)


if __name__ == "__main__":
    main()
