"""The jetpack in fights and on the map:

1. chase: a man who runs from us up a ledge (3 u up, 5 u off, looking away) is flown after
2. high ground (Heroic and up): with a man 10 u off on our level, a floor 2-5.3 u up within 6 u that sees him is flown to
   (Sword Base, found by a search of the map); not while he watches us
3. escape: a retreat to cover 3 u up 4 u off goes up and over
4. a flight in the fight goes on while men are in sight (a climb on the way stops when one comes into view)
5. the player's Spire move, planned: a bot on the spire top with a full pack and the core's delivery below walks off the
   edge toward it, falls, holds the jetpack only for the last of the fall and lands safely (SAFE_LAND) near the landing
   it planned (simple physics: 2.3 u/s on the stick, 1.5 u/s^2 of air control, Reach's 4.1 u/s^2, the pack's 1.4 net)

usage: python -I test_jetpack_moves.py      -> "jetpack moves OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.equipment as EQ  # noqa: E402
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import Kit  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from test_equipment import A, DT, bot, foe, me_state, plan_now  # noqa: E402
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

SAFE_LAND = getattr(EQ, "SAFE_LAND", 5.0)
G, JET_NET = 4.1, 1.4
DELIVERY = Vec(-163.053, -432.088, -58.374)     # Spire's core delivery (tools/test_spire_drops.py)



def why(p):
    return p[4] if p else None


def map_bot(name, tier="strong", i=1):
    b = Bot(i, 0, make_profile(tier, "rusher", random.Random(i)), get_map(name), random.Random(i))
    b.kit = Kit(b.p, "reach")
    return b


def main():
    testdata.need_lidar("reach_35_island")
    testdata.need("maps/reach_35_island/drops.json")
    fails, info = [], []

    # 1
    b = bot("strong", "reach", "jetpack")
    runner = foe(A + Vec(5, 0, 3), yaw=0.0)                       # 3 u up, 5 u east, looking further east
    p = plan_now(b, [runner], (2,), ("fight", 2))
    if why(p) != "jetpack after him" or p[1] != "fly":
        fails.append(f"a man running from us up a 3 u ledge: {why(p)!r} (want flown after)")

    # 2
    sb = map_bot("reach_20_sword_slayer")
    T = sb.T()
    found = None
    hg = getattr(sb.kit, "high_ground", None)
    for j in range(0, T.nh, 6):
        for i in range(0, T.nw, 6):
            for l in range(T.L):
                if found or not T.lwalk[l, j, i]:
                    continue
                pos = Vec(T.x0 + (i + 0.5) * 0.25, T.y0 + (j + 0.5) * 0.25, float(T.lz[l, j, i]))
                me = PlayerState(1, 0, "bot", pos, alive=True, equipment="jetpack")
                for a in range(4):
                    e = Vec(pos.x + 10 * math.cos(a * 1.57), pos.y + 10 * math.sin(a * 1.57), pos.z)
                    if (T.ground_ok(e.x, e.y, e.z + 0.3, drop=0.6) and T.los(pos, e) and hg is not None
                            and hg(sb, me, PlayerState(2, 1, "human", e, alive=True)) is not None):
                        found = (pos, e)
                        break
    if found is None:
        fails.append("high ground: no spot on Sword Base with a floor 2-5.3 u up that sees a man 10 u off (or none coded)")
    else:
        pos, e = found
        for facing, want in ((False, "jetpack to the high ground"), (True, None)):
            b = map_bot("reach_20_sword_slayer", i=3 if facing else 4)
            yaw = math.atan2(pos.y - e.y, pos.x - e.x) if facing else math.atan2(e.y - pos.y, e.x - pos.x)
            man = PlayerState(2, 1, "human", e, yaw=yaw, alive=True, weapon="dmr")
            b.per.beliefs[2] = Belief(e, Vec(), 1.0, True, "eyes")
            b.per.recognized.add(2)
            b.goal = ("fight", 2)
            me = PlayerState(b.id, 0, "bot", pos, alive=True, equipment="jetpack")
            snap = Snapshot(1.0, [me, man])
            b.kit.perceive(b, 1.0, me, snap)
            got = why(b.kit.plan(b, 1.0, me, snap))
            if got != want:
                fails.append(f"high ground, the man {'watching us' if facing else 'looking away'}: {got!r} (want {want!r})")
        info.append(f"high ground from ({pos.x:.0f}, {pos.y:.0f}, {pos.z:.1f})")

    # 3
    b = bot("strong", "reach", "jetpack")
    got = why(plan_now(b, [foe(A + Vec(-12, 0, 0), yaw=0.0)], (2,), ("retreat", A + Vec(4, 0, 3))))
    if got != "jetpack up and over to cover":
        fails.append(f"a retreat to cover 3 u up 4 u off: {got!r} (want up and over)")

    # 4
    b = bot("strong", "reach", "jetpack")
    b.per.beliefs[2] = Belief(runner.pos, Vec(), 1.0, True, "eyes")
    b.per.recognized.add(2)
    b.goal = ("fight", 2)
    held, t = 0, 1.0
    while t < 2.5:
        me = me_state(b, A, 0.0, 0.0)
        snap = Snapshot(t, [me, runner])
        b.kit.perceive(b, t, me, snap)
        a = Action()
        b.kit.act(b, t, DT, me, snap, a)
        held += a.equipment
        t += DT
    if held < 1.2 / DT:
        fails.append(f"a flight after a man in sight held {held * DT:.2f} s (want on for its climb, past 1.2 s)")

    # 5 (on the top's outer ring 2 u in from the take-off of the player's drop nearest the delivery,
    # maps/reach_35_island/ drops.json: the middle is ringed by the lift shaft's holes, and the walk there is the nav's)
    import json
    drops = json.load(open(os.path.join(HERE, "..", "maps", "reach_35_island", "drops.json")))["drops"]
    to = min((Vec(*d["take_off"]) for d in drops), key=lambda q: (q - DELIVERY).flat())
    mid = Vec(-176.0, -400.5, to.z)
    TOP = to + (mid - to).norm() * 2.0
    sp = map_bot("reach_35_island", tier="top", i=5)
    sp.goal, sp.wp = ("objective", DELIVERY), TOP + (mid - to).norm()
    T = sp.T()
    pos, v, t, jet_hi, plans = Vec(TOP.x, TOP.y, TOP.z), Vec(0, 0, 0), 1.0, None, []
    floor = lambda q: q.z - T.height_over(q.x, q.y, q.z)
    landed, down = False, 0.0
    while t < 20.0 and not landed:
        me = PlayerState(sp.id, 0, "bot", pos, vel=v, alive=True, equipment="jetpack")
        snap = Snapshot(t, [me])
        sp.kit.perceive(sp, t, me, snap)
        a = Action()
        note = sp.kit.act(sp, t, DT, me, snap, a)
        if note:
            plans.append(note)
        on = a.equipment and a.ability
        h = T.height_over(pos.x, pos.y, pos.z)
        if on and jet_hi is None:
            jet_hi = h
        c, sn = math.cos(a.yaw), math.sin(a.yaw)
        want = Vec((c * a.forward - sn * a.strafe) * 2.3, (sn * a.forward + c * a.strafe) * 2.3, 0)
        air = h > 0.05 or v.z < -0.1
        k = min(1.0, (1.5 if air else 30.0) * DT / max(1e-6, (want - Vec(v.x, v.y, 0)).flat()))
        vz = v.z + ((-G + (G + JET_NET if on else 0.0)) * DT if air else 0.0)
        v = Vec(v.x + (want.x - v.x) * k, v.y + (want.y - v.y) * k, vz)
        nxt = Vec(pos.x + v.x * DT, pos.y + v.y * DT, pos.z + v.z * DT)
        f = floor(Vec(nxt.x, nxt.y, pos.z + 0.3))
        if nxt.z <= f and v.z <= 0:                            # on the floor (a step down while walking, or a touchdown)
            landed, down = pos.z < TOP.z - 2.0, -v.z
            nxt, v = Vec(nxt.x, nxt.y, f), Vec(v.x, v.y, 0.0)
        pos = nxt
        t += DT
    planned = any("down off the top" in n for n in plans)
    if not planned or not landed:
        fails.append(f"Spire top, the delivery below: planned {planned}, came down {landed} (z {pos.z:.1f}; want off the "
                     f"edge and down; notes {plans[:3]})")
    else:
        land = getattr(sp.kit, "descent_land", pos)
        if down > SAFE_LAND + 0.3:
            fails.append(f"Spire descent: touched down at {down:.1f} u/s (want {SAFE_LAND} or less)")
        if jet_hi is None or jet_hi > 26.0:
            fails.append(f"Spire descent: the jetpack first pressed {jet_hi} u up (want only for the last of the fall)")
        if (pos - land).flat() > 3.0:
            fails.append(f"Spire descent: down {(pos - land).flat():.1f} u from its landing (want within 3)")
        info.append(f"Spire descent {TOP.z - pos.z:.0f} u in {t - 1.0:.1f} s, jet from {jet_hi:.0f} u, down at {down:.1f} "
                    f"u/s, {(pos - land).flat():.1f} u from the landing")

    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("jetpack moves OK (" + "; ".join(info) + ")")


if __name__ == "__main__":
    main()
