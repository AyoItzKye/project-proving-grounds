"""CTF's attack as a wave, the normal plan (wave 2: the sim's runners on The Pit died one by one 6-18 u from the stand, 50
lives in 200 s on master, none within 5 u). On h3_cyberdyne, 5 of us (the plan: one defender), both flags home, the
attackers by our base:

1. the attackers gather at the rally short of their base (role mid there); our defender stays on its post
2. most of them there: all go in together, runners on two prongs, with the urgency (blitz_until)
3. the pickup ends the wave (the carry play takes over); so does their flag leaving its stand
4. WAVE off: no wave (the play before)

usage: python -I test_ctf_wave.py      -> "ctf wave OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_cyberdyne")
RED, BLUE = M["flags"][0], M["flags"][1]


def setup():
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), M, random.Random(i)) for i in range(1, 6)}
    d = Director(0, M, bots, random.Random(0))
    d.split, d.split_until = False, 1e9
    return d, bots


def snap_at(t, where, carried=False):
    ps = [PlayerState(i, 0, f"b{i}", where.get(i, RED + Vec(i * 0.6, 1.0, 0.0)), has_flag=carried and i == 2)
          for i in range(1, 6)] + [PlayerState(20 + k, 1, f"e{k}", BLUE + Vec(k, 2, 0)) for k in range(5)]
    f1 = FlagState(1, BLUE, ps[1].pos, "carried", 2) if carried else FlagState(1, BLUE, BLUE, "home")
    return Snapshot(t, ps, {0: FlagState(0, RED, RED, "home"), 1: f1}, mode="ctf")


def main():
    fails = []
    d, bots = setup()
    snap = snap_at(10.0, {})
    d.update(10.0, snap)
    w = getattr(d, "wave", None)
    att = [b for b in bots.values() if d.roles.get(b.id) != "defender"]
    dfd = [b for b in bots.values() if d.roles.get(b.id) == "defender"]
    if w is None or w["go"] is not None or not att or any(b.order.role != "mid" or dist(b.order.point, w["rally"]) > 0.5
                                                          for b in att):
        fails.append(f"far from their base: wave {w and w['go']}, attackers {[(b.order.role) for b in att]} "
                     f"(want a gather at the rally)")
    if not dfd or any(dist(b.order.point, RED) > 12.0 for b in dfd):
        fails.append("the defender left its post for the wave")
    # 2. most at the rally: go
    if w is not None:
        where = {b.id: w["rally"] + Vec(0.5 * k, 0, 0) for k, b in enumerate(att)}
        snap = snap_at(11.0, where)
        d.update(11.0, snap)
        prongs = {b.order.via for b in att}
        if w["go"] is None or any(b.order.role != "runner" or b.blitz_until <= 11.0 for b in att) or len(prongs) < 2:
            fails.append(f"at the rally: go {w['go']}, roles {[b.order.role for b in att]}, prongs {len(prongs)}")
        # 3. the pickup ends it
        d.update(12.0, snap_at(12.0, where, carried=True))
        if getattr(d, "wave", None) is not None:
            fails.append("the pickup did not end the wave")
    # 4. off
    D.WAVE = False
    try:
        d, bots = setup()
        d.update(10.0, snap_at(10.0, {}))
        if getattr(d, "wave", None) is not None:
            fails.append("WAVE off: a wave started")
    finally:
        D.WAVE = True
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("ctf wave OK (gather at the rally, the defender home; all in on two prongs; over at the pickup)")


if __name__ == "__main__":
    main()
