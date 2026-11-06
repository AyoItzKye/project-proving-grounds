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
    # 3. headway never gives up a zone the bot is to stand in (live Spire 20261105-005649: attackers took alt posts 3-9 u
    #    off phase 2's territory for half their decisions); a plain post 7 s without progress still goes
    for mode, want_ban in (("invasion", False), ("slayer", True)):
        b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
        b._terrain = T
        me = PlayerState(1, 0, "b", post + Vec(-12.0, 0.0, 0.0), alive=True)
        me.pos = Vec(me.pos.x, me.pos.y, T.ground(me.pos.x, me.pos.y))
        snap = Snapshot(0.0, [me])
        snap.mode, snap.inv_phase, snap.inv_attackers = mode, 2, 0
        snap.inv_zones, snap.inv_zone_r = ([post], [0.6]) if mode == "invasion" else ([], [])
        for t in range(0, 9):
            b.headway(float(t), me, ("objective", post), snap)
        banned = bool(getattr(b, "goal_ban", {}))
        if banned != want_ban:
            fails.append(f"3. {mode}: 8 s without progress to {post}: banned {banned} (want {want_ban})")
    # 4. on a floor the nav lacks, its next point right under the bot: step off to a nav floor at its height (live
    #    Boneyard 20261105-015943: an attacker stood 110 s at this spot)
    V = "reach_70_boneyard/variants/v86d95e85"
    if os.path.exists(os.path.join(HERE, "..", "maps", V, "variant.json")):
        MV = get_map(V)
        b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), MV, random.Random(1))
        b._terrain = TV = terrain(MV)
        me = PlayerState(1, 0, "b", Vec(279.45, 110.52, -5.87), alive=True)
        off = b.off_lost_floor(me, Vec(279.467, 110.519, -8.48))
        on = b.off_lost_floor(me, Vec(281.0, 110.5, -5.9))
        j, i = TV._cell(off) if off is not None else (0, 0)
        if off is None or not any(abs(float(z) + 5.87) < 0.6 for z in TV.lz[:, j, i] if z == z) or on is not None:
            fails.append(f"4. a lost floor: step off {off}, an ordinary next point {on} (want a spot at -5.87, None)")
        # its own floor in the nav, the point under it a planned drop (the issue #4 stairs' tread, live 064324)
        tread = PlayerState(1, 0, "b", Vec(256.9, 106.1, -5.0), alive=True)
        drop = b.off_lost_floor(tread, Vec(256.9, 106.1, -7.39))
        if drop is not None:
            fails.append(f"4. on the stairs' tread (its floor in the nav) over a drop: stepped off to {drop} (want None)")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("alt post OK (a banned post becomes a spot beside it, not a roam)")


if __name__ == "__main__":
    main()
