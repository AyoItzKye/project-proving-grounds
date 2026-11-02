"""Evade and thruster out of a grenade's blast and in to close (the coordinator's list; guide EQ-EVADE-01 "grenade at
feet", EQ-JET-01 "escape a grenade by going up", EQ-THRUST-01 the melee finish):

1. a grenade seen landing 1.5 u east (snap.grenades): evade and thruster dash 3 u west, out of it; the jetpack goes up;
   armor lock locks with it at our feet
2. our own grenade landing by us (Bot.own_grenade's spot): the same dash out
3. in to close: evade with a shotgun, him 5 u off: a dash 3 u at him; with a DMR at his full shield, no dash
4. the simulator shows the grenades thrown (brain/simgear.py: snap.grenades) for the brain to see. Live no grenade
   objects are read: there only our own grenades count (BLOCKED live: an enemy's grenade)

usage: python -I test_grenade_dash.py      -> "grenade dash OK (...)"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Snapshot, Vec  # noqa: E402
from brain.sim import Sim  # noqa: E402
from test_equipment import A, bot, foe, me_state  # noqa: E402


def plan(b, foes=(), seen=(), goal=None, grenades=(), me_kw=None, now=1.0):
    from brain.bot import Belief
    for e in foes:
        b.per.beliefs[e.id] = Belief(e.pos, e.vel, now, e.id in seen, "eyes")
        if e.id in seen:
            b.per.recognized.add(e.id)
    b.goal = goal or b.goal
    me = me_state(b, A, 0.0, 0.0, **(me_kw or {}))
    snap = Snapshot(now, [me] + list(foes))
    snap.grenades = [dict(g) for g in grenades]     # (set after: the code before had no such field)
    b.kit.perceive(b, now, me, snap)
    return b.kit.plan(b, now, me, snap)


def main():
    fails, info = [], []
    nade = [dict(pos=A + Vec(1.5, 0, 0), team=1, t=0.7)]
    thrower = foe(A + Vec(12, 0, 0), yaw=math.pi)

    # 1
    for game, kind, want in (("reach", "evade", "dash out of the grenade"), ("h4", "thruster", "dash out of the grenade"),
                             ("reach", "jetpack", "jetpack up out of the grenade"),
                             ("reach", "armor_lock", "armor lock: grenade at my feet")):
        b = bot("strong", game, kind)
        b.cover_from = lambda me, threats: None
        p = plan(b, [thrower], (2,), ("fight", 2), nade)
        if not p or p[4] != want:
            fails.append(f"{kind}, a grenade 1.5 u east: {p and p[4]!r} (want {want!r})")
        elif p[1] == "dash" and (p[2].x - A.x > -2.9 or abs(p[2].y - A.y) > 0.1):
            fails.append(f"{kind}: dashed to {p[2]} (want 3 u west, out of it)")

    # 2
    b = bot("strong", "reach", "evade")
    b.nade_at = (A + Vec(0, 1.0, 0), 4.0)
    p = plan(b, [thrower], (2,), ("fight", 2))
    if not p or p[4] != "dash out of the grenade" or p[2].y - A.y > -2.9:
        fails.append(f"our own grenade 1 u north: {p and p[:3]} (want a dash 3 u south)")

    # 3
    for weapon, shield, want in (("shotgun", 1.0, "dash in to close"), ("dmr", 1.0, None)):
        b = bot("strong", "reach", "evade")
        p = plan(b, [foe(A + Vec(5, 0, 0), yaw=0.0, shield=shield)], (2,), ("fight", 2), me_kw=dict(weapon=weapon))
        got = p[4] if p else None
        if got != want:
            fails.append(f"evade with a {weapon}, him 5 u off at shield {shield}: {got!r} (want {want!r})")
        elif want and abs(p[2].x - A.x - 3.0) > 0.1:
            fails.append(f"evade in to close went to {p[2]} (want 3 u at him)")

    # 4
    sim = Sim("slayer", 4, 3, tiers=["top"], map_name="reach_20_sword_slayer")
    seen = 0
    for _ in range(int(60 / 0.0333)):
        sim.step()
        seen = max(seen, len(getattr(sim.snapshot(), "grenades", [])))
        if seen:
            break
    if not seen:
        fails.append("the simulator listed no grenade in 60 s of Sword Base (snap.grenades)")
    info.append(f"sim grenades seen at {sim.now:.1f} s")

    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("grenade dash OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
