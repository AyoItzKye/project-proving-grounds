"""Offline check of Spire's way down (a recorded Invasion match: the drops onto the heat vents, and no jumps down a
one-way gravity lift):
1. jump_ways: a person's ride up a lift or launcher (up more than 4 u) is one-way; a small climb still two-way, and one
   someone did back stays two-way
2. maps/reach_35_island/drops.json: the eight drops off the top onto the heat vents load, one way, as the player's
3. a core carrier (safe) and a bot without it, walked by the nav from the core's spot on top to the core's delivery
   point, come down onto a vent; neither is offered the jump down the middle lift's shaft
usage: python -I test_spire_drops.py      -> "spire drops OK"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import jump_ways  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

CORE = Vec(-176.0, -400.5, -24.1)              # the core's spot on the spire top (live: -178.2, -405.3 lies in
DELIVERY = Vec(-163.053, -432.088, -58.374)    # its stand); where the carrier's goal pointed (bot 13, 299.9 s)
SHAFT = (-176.6, -398.8)                       # the middle lift's foot (people's rides up start here, z -62.4)


def walk(T, a, b, safe, steps=600):
    """The nav from a to b, a waypoint at a time; the first drop of 20 u or more as (take-off, landing), or None."""
    p = a
    for _ in range(steps):
        nxt = T.nav(p, b, jump=True, human=True, safe=safe)
        if hasattr(nxt, "path"):
            nxt = Vec(*nxt.path[-1][:3])
        q = Vec(nxt.x, nxt.y, nxt.z)
        if p.z - q.z >= 20.0:
            return p, q
        if (q - p).flat() < 0.05 and abs(q.z - p.z) < 0.05:
            return None                          # stuck
        p = q
        if (p - b).flat() < 1.0:
            return None
    return None


def main():
    testdata.need_lidar("reach_35_island")
    fails = []
    lift = dict(take_off=[-176.6, -398.8, -62.4], land=[-174.2, -399.4, -24.1], apex=-22.84)
    if jump_ways(lift) != "one-way":
        fails.append("a 38 u ride up the middle lift is two-way")
    if jump_ways(dict(lift, back=1)) != "two-way":
        fails.append("a ride someone did back is one-way")
    if jump_ways(dict(take_off=[0.0, 0.0, 0.0], land=[1.0, 0.0, 0.5], apex=0.6)) != "two-way":
        fails.append("a half-unit climb is one-way")
    m = get_map("reach_35_island")
    T = terrain(m)
    soft = [k for f, t, k, w in getattr(T, "hjumps", ()) if k.get("soft")]
    if len(soft) != 8:
        fails.append(f"{len(soft)} vent drops in the nav (want 8)")
    vents = [Vec(*o["pos"]) for o in m["objects"]["placed"] if o["name"] == "covy_heat_vent"]
    # (and a carrier going toward the foot of people's drop 121, 37 u down 2.9 u off a vent, where carriers died twice
    # on: a vent drop is no risk to him, so he takes one rather than 121)
    for safe, goal in ((True, DELIVERY), (False, DELIVERY), (True, Vec(-167.3, -414.0, -61.2))):
        got = walk(T, CORE, goal, safe)
        who = ("the carrier" if safe else "a bot without the core") + f" to ({goal.x:.0f}, {goal.y:.0f})"
        if got is None:
            fails.append(f"{who}: no drop off the top on the way to the delivery point")
            continue
        p, q = got
        near = min((q - v).flat() for v in vents)
        if math.hypot(q.x - SHAFT[0], q.y - SHAFT[1]) < 2.5:
            fails.append(f"{who}: down the middle lift's shaft ({q})")
        elif near > 1.0:
            fails.append(f"{who}: off the top at {p} to {q}, {near:.1f} u from the nearest vent")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("spire drops OK (lift rides one way; 8 vent drops; carrier and bot come down onto a vent)")


if __name__ == "__main__":
    main()
