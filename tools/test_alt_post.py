"""A post headway gave up on is swapped for a spot beside it, never a roam.

1. Bot.decide with its order's point banned: an objective spot 3-9 u from it scored (Bot.alt_post), no roam, kept
2. Easy too (the player's Easy walks to objectives)

usage: python -I test_alt_post.py      -> "alt post OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def main():
    fails = []
    M = get_map("reach_70_boneyard")
    T = terrain(M)
    post = Vec(300.0, 107.5, -7.0)
    for tier in ("top", "novice"):
        b = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), M, random.Random(1))
        b._terrain = T
        b.order = Order("runner", post)
        b.goal_ban = {b._goal_key(("objective", post)): 99.0}
        me = PlayerState(1, 0, "b", post + Vec(-30.0, 0.0, 0.0), alive=True)
        me.pos = Vec(me.pos.x, me.pos.y, T.ground(me.pos.x, me.pos.y))
        snap = Snapshot(10.0, [me])
        g1 = b.decide(10.0, me, snap)
        g2 = b.decide(10.5, me, snap)
        alts = [k[1] for k in b.last_scores if k[0] == "objective"]
        ok = g1[0] != "roam" and len(alts) == 1 and 3.0 <= dist(alts[0], post) < 9.0 and g2 == g1
        if not ok:
            fails.append(f"{tier}: banned post -> {g1}, then {g2}, objective spots scored {alts} (want one 3-9 u from "
                         f"{post}, kept, no roam)")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("alt post OK (a banned post becomes a spot beside it, not a roam)")


if __name__ == "__main__":
    main()
