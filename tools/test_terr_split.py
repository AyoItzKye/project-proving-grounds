"""Territories as people split it (Director.terr_split, TERR_SPLIT; the player's rule, Nov 12: three zones, two a zone; a zone
secured, one stays and the other helps take the next). Six of us, three zones on Construct:

1. none ours: two posts on each zone
2. one ours with nobody of theirs on it: one holder there, two on each of the other two, the spare on the zone they hold
3. switch off: the old play (every taker on one zone)
4. the sims (logs/tmp/nov12/terr_ab.txt, 6v6, 4 maps x 2 seeds): points a minute 6.91 -> 9.63, closeness 0.15 -> 0.53

usage: python -I test_terr_split.py      -> "territories split OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.director as DD  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402

M = get_map("h3_construct")
zones = [Vec(-15.0, 0.0, 0.0), Vec(0.0, 0.0, 0.0), Vec(15.0, 0.0, 0.0)]
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def slots(owners, foes=()):
    d = Director(0, M, {}, random.Random(1))
    mine = [PlayerState(k, 0, f"b{k}", Vec(0.0, -20.0 + k, 0.0)) for k in range(6)]
    them = [PlayerState(10 + k, 1, "f", q) for k, q in enumerate(foes)]
    sn = Snapshot(30.0, mine + them, mode="territories")
    sn.obj_zones = [(z, 3.0, o) for z, o in zip(zones, owners)]
    got = d.mode_slots(30.0, sn, 6)[:6]
    return [min(range(3), key=lambda i: dist(zones[i], q)) for r, q, _ in got if r in ("defender", "escort")]


per = slots([-1, -1, -1])
check("1. none ours: two on each zone", sorted(per) == [0, 0, 1, 1, 2, 2], per)
per = slots([0, -1, 1], foes=[Vec(15.0, 1.0, 0.0)])
check("2. one ours and clear: one holder there", per.count(0) == 1, per)
check("2. two or more on each of the others", per.count(1) >= 2 and per.count(2) >= 2, per)
DD.TERR_SPLIT = False
per = slots([-1, -1, -1])
DD.TERR_SPLIT = True
check("3. switch off: every taker on one zone", len(set(per)) == 1, per)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("territories split OK")
