"""A zone holder fights from inside its zone (Bot.keep_in_zone). From live Boneyard B12 195.3 s (trace in
logs/tmp/invasion_regress/traces/trace_reach_70_boneyard_20261105-065313): Elite 12 alone in phase 1's south territory
(255.81, 81.95, box 1.71 x 2.30, 0.86 u to its edge) fighting Spartan 5 at (252.61, 78.58) 4.6 u off; it strafed out
to (255.1, 80.5) and the 10.4 s hold ended (13 of 18 holds in B9-B12 ended that way, holdends.py).

Bot.think with the man in sight for 6 s, the bot's feet moved by its stick (2.3 u/s): it stays within the zone's
size + 0.15 u, and its fight still turns on him (the view on him). A defender of the same territory (posted round it,
not in it) and a slayer fight anywhere: they leave the circle as before.

usage: python -I test_zone_hold.py      -> "zone_hold OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = "reach_70_boneyard"


def run(seed, attacking=True, role="defender", start=None, dash=False, inertia=False):
    m = get_map(M)
    L = invasion.layout(m["objects"])
    zones = L["phases"][1]
    zr = [invasion.zone_radius(L, z) for z in zones]
    zone = min(zones, key=lambda z: (z - Vec(255.81, 81.95, -4.0)).flat())
    r = zr[zones.index(zone)]
    b = Bot(12, 1, make_profile("top", "rusher", random.Random(seed)), m, random.Random(seed))
    b.order = Order(role, zone)
    if dash:
        # the kit's evade (B15 holders 'evade: dash out of his aim' 1.4-2.4 u out): its step points straight away from
        # the zone's middle; the holder's clamp comes after it
        act0 = b.kit.act
        def act1(bot, now, dt, me, snap, act):
            out = act0(bot, now, dt, me, snap, act)
            if bot.goal[0] != "fight":
                return out
            h = math.atan2(me.pos.y - zone.y, me.pos.x - zone.x) - act.yaw
            act.forward, act.strafe = math.cos(h), math.sin(h)
            return "evade: dash (test)"
        b.kit.act = act1
    pos, foe = start or Vec(255.54, 81.76, -4.0), Vec(252.61, 78.58, -3.98)
    yaw, far, fights, on = 0.0, 0.0, 0, 0
    last = []
    vel = Vec(0.0, 0.0, 0.0)
    for k in range(180):
        t = 195.0 + k / 30
        me = PlayerState(12, 1, "e", pos, vel=vel, yaw=yaw, weapon="plasma_repeater")
        f = PlayerState(5, 0, "s", foe + Vec(0.6 * math.sin(t * 2.0), 0.0, 0.0), weapon="assault_rifle")
        sn = Snapshot(t, [me, f], mode="invasion", inv_phase=1, inv_attackers=1 if attacking else 0,
                      inv_zones=list(zones), inv_zone_r=list(zr), inv_phase_t=60.0)
        a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
        yaw = a.yaw
        if b.goal[0] == "fight":
            fights += 1
            on += abs(math.atan2(math.sin(a.yaw - math.atan2(f.pos.y - pos.y, f.pos.x - pos.x)),
                                 math.cos(a.yaw - math.atan2(f.pos.y - pos.y, f.pos.x - pos.x)))) < 0.3
        h, sp = a.yaw + math.atan2(a.strafe, a.forward), min(1.0, math.hypot(a.forward, a.strafe))
        want = Vec(math.cos(h) * sp * 2.3, math.sin(h) * sp * 2.3, 0.0)
        # (inertia: the body's speed follows the stick over ~0.3 s, as Reach's does; else it moves as the stick says)
        vel = vel + (want - vel) * (1.0 / 9.0) if inertia else want
        pos = Vec(pos.x + vel.x / 30, pos.y + vel.y / 30, pos.z)
        far = max(far, (pos - zone).flat()) if start is None else far
        last.append((pos - zone).flat())
    return (far if start is None else max(last[-60:])), r, fights, on


def on_the_way(seed):
    """An attacker on the clock 18 u from its territory, a man 14 u off on the other side shooting at it: it shoots him
    on its way in (the Spire trace 20261105-233940 at 297.9 s: attackers stopped to fight 15-30 u off their territory).
    (distance to the zone at the start, at the end, share of fight ticks with the view on him)"""
    m = get_map(M)
    L = invasion.layout(m["objects"])
    zones = L["phases"][1]
    zr = [invasion.zone_radius(L, z) for z in zones]
    zone = min(zones, key=lambda z: (z - Vec(255.81, 81.95, -4.0)).flat())
    b = Bot(12, 1, make_profile("top", "rusher", random.Random(seed)), m, random.Random(seed))
    b.order = Order("defender", zone)
    # the attackers' side of the platform (open ground), the man 13 u off to its right
    pos = Vec(zone.x - 16.0, zone.y - 9.0, -8.03)
    foe = Vec(pos.x + 4.0, pos.y - 12.0, -8.0)
    yaw, fights, on = math.atan2(foe.y - pos.y, foe.x - pos.x), 0, 0
    start = (pos - zone).flat()
    for k in range(120):
        t = 195.0 + k / 30
        me = PlayerState(12, 1, "e", pos, yaw=yaw, weapon="plasma_repeater")
        f = PlayerState(5, 0, "s", foe + Vec(0.6 * math.sin(t * 2.0), 0.0, 0.0), weapon="assault_rifle")
        sn = Snapshot(t, [me, f], mode="invasion", inv_phase=1, inv_attackers=1, inv_zones=list(zones),
                      inv_zone_r=list(zr), inv_phase_t=60.0)
        b.goal, b.next_decide = ("fight", 5), t + 1.0       # (the fight it is in: its decision is not under test)
        a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
        yaw = a.yaw
        if b.goal[0] == "fight":
            fights += 1
            want = math.atan2(f.pos.y - pos.y, f.pos.x - pos.x)
            on += abs(math.atan2(math.sin(a.yaw - want), math.cos(a.yaw - want))) < 0.3
        h, sp = a.yaw + math.atan2(a.strafe, a.forward), min(1.0, math.hypot(a.forward, a.strafe))
        pos = Vec(pos.x + math.cos(h) * sp * 2.3 / 30, pos.y + math.sin(h) * sp * 2.3 / 30, pos.z)
    return start, (pos - zone).flat(), fights, on


def main():
    fails, out = [], []
    for seed in (1, 2):
        s0, s1, fights, on = on_the_way(seed)
        if fights < 30 or s0 - s1 < 2.0 or on < 0.6 * fights:
            fails.append(f"seed {seed}: an attacker fighting a man 13 u off went {s0:.1f} -> {s1:.1f} u from its territory in 4 s "
                         f"(fight ticks {fights}, view on him {on}): it should shoot on its way in")
    for seed in (1, 2, 3, 4):
        far, r, fights, on = run(seed)
        out.append(round(far, 2))
        if fights < 90:
            fails.append(f"seed {seed}: fought {fights} of 180 ticks (the test wants a fight)")
        elif far > r + 0.15:
            fails.append(f"seed {seed}: the holder fighting got {far:.2f} u from the territory's middle (its size {r:.2f})")
        elif on < 0.6 * fights:
            fails.append(f"seed {seed}: the view on the man {on} of {fights} fight ticks")
    # B13 R1 (trace 20261105-080709): fights on the platform 1-4 u off the territory: from 2.8 u off it, fighting, the
    # holder is in it by the last 2 s of 6
    inn = []
    for seed in (1, 2, 3, 4):
        end, r, fights, _ = run(seed, start=Vec(253.4, 80.6, -4.0))
        inn.append(round(end, 2))
        if fights >= 90 and end > r + 0.15:
            fails.append(f"seed {seed}: fighting 2.8 u off the territory, still {end:.2f} u off its middle in the last 2 s")
    out.append(("from 2.8 u", inn))
    # B16: holders still ended 1.2-1.4 u off with the clamp on: momentum (inertia in the walk here)
    heavy = [round(run(seed, inertia=True)[0], 2) for seed in (1, 2, 3, 4)]
    if max(heavy) > 0.88 + 0.15:
        fails.append(f"with the body's momentum the holder drifted out: {heavy} u from the middle")
    out.append(("momentum", heavy))
    dashes = [round(run(seed, dash=True)[0], 2) for seed in (1, 2)]
    if max(dashes) > 0.88 + 0.15:
        fails.append(f"the kit's dash stepped the holder out of the zone: {dashes} u from its middle")
    out.append(("dash", dashes))
    left = [run(seed, role="slayer")[0] for seed in (1, 2, 3, 4)]
    if max(left) <= 1.0:
        fails.append(f"a slayer's fight kept in the zone too ({left}): only a zone holder is")
    # Territories keeps its old holders: the sim A/B (logs/tmp/invasion_regress/zonesim.py, Boneyard 300 s 6v6, seeds
    # 1-3) took 4 territories with the rule on against 9 off, 32 points against 109: both teams' holders fought inside
    # the same zone, contested, nobody took it
    tb = Bot(3, 0, make_profile("top", "rusher", random.Random(1)), get_map(M), random.Random(1))
    tb.order = Order("defender", Vec(255.81, 81.95, -4.0))
    tsn = Snapshot(0.0, [], mode="territories")
    tsn.obj_zones = [(Vec(255.81, 81.95, -4.0), 0.9, 0)]
    if tb.held_zone(tsn) is not None:
        fails.append("a Territories defender holds its zone from inside (the sim: 4 takes against 9 without)")
    if fails:
        print("zone_hold FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print(f"zone_hold OK (holder's farthest {out}, slayer's {[round(x, 2) for x in left]})")


if __name__ == "__main__":
    main()
