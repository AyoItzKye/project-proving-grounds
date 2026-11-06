"""Firefight teammates (the owner, Nov 6: "have them follow the player around, if player dies have them roam or find a
safe spot"): with the player alive every bot escorts him; with him down they hold the map's two safe spots nearest where
he fell (its holds and named points), split between them, not the open middle.

usage: python -I tools/test_firefight_team.py      -> "firefight team OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402

M = get_map("reach_ff20_courtyard")


def main():
    fails = []
    d = Director(0, M, {}, random.Random(1))
    me = Vec(-101.0, 36.0, 19.0)
    human = PlayerState(0, 0, "you", me, is_bot=False)
    bots = [PlayerState(i, 0, f"b{i}", me + Vec(i, 0, 0)) for i in (1, 2, 3)]
    sn = Snapshot(10.0, [human] + bots, mode="firefight")
    slots = d.role_slots(10.0, sn, 3)
    if any(r != "escort" or dist(p, me) > 0.01 for r, p, _ in slots):
        fails.append(f"player alive: {slots} (want 3 escorts on him)")
    dead = PlayerState(0, 0, "you", me, is_bot=False, alive=False)
    sn = Snapshot(14.0, [dead] + bots, mode="firefight")
    slots = d.role_slots(14.0, sn, 3)
    spots = sorted([q for h in M["holds"].values() for q in h] + list(M["points"].values()), key=lambda q: dist(q, me))
    pts = {(round(p.x, 2), round(p.y, 2)) for _, p, _ in slots}
    want = {(round(q.x, 2), round(q.y, 2)) for q in spots[:2]}
    if any(r != "defender" for r, _, _ in slots) or pts != want:
        fails.append(f"player down: {[(r, p) for r, p, _ in slots]} (want defenders on the 2 spots nearest him {want})")
    if dist(M["points"]["mid"], me) > 5.0 and any(dist(p, M["points"]["mid"]) < 0.5 for _, p, _ in slots):
        fails.append("player down: a bot sent to the open middle")
    if fails:
        print("firefight team FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("firefight team OK")


if __name__ == "__main__":
    main()
