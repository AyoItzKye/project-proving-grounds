"""Offline check of Sandtrap's Elephants (the player: "The bots have issues on H3 with delivering the flag on
elephants ... the last bot that had a flag sat on the first level the whole time"):
1. Bot.way_in: a goal in an Elephant's bay (vehicles.ELEPHANT, from its model) is reached round the hull to the rear
   ramp's foot, then straight up the ramp and along the bay floor; walked from in front, beside and behind, the way never
   crosses the hull outside the ramp's lane and ends at the goal; a goal outside the bay is left alone.
2. Director.capture_point: the team's flag return where the map has one (Narrows' lie 0.7 u off the stands), else the
   stand (Blood Gulch has none).
usage: python -I test_elephant.py      -> "elephant OK"
"""
import math
import os
import random
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

E = vehicles.ELEPHANT


def floor_z(f, l):
    """The model's walking height in the Elephant's frame (z over its origin), roughly: the sand round it 0, the ramp
    rising 0 to 0.55 from f -3.6 to -2.5 in its lane, the bay floor 0.55."""
    (af, al), _ = E["ramp"]
    f0, f1, w = E["bay"]
    if abs(l - al) <= 0.6 and -3.6 <= f <= -2.5:
        return 0.55 * (f + 3.6) / 1.1
    if f0 <= f <= f1 and abs(l) <= w and f > -2.5:
        return 0.55
    return 0.0


def walk(bot, el, start, goal, steps=400):
    """Walk the bot from start (Elephant frame f, l) to the goal by way_in's waypoints, 0.25 u a step. Returns
    (reached, crossed the hull outside the ramp lane and bay)."""
    local, world = vehicles.frame_of(el)
    f, l = start
    h0, h1, hw = E["hull"]
    (af, al), _ = E["ramp"]
    f0, f1, w = E["bay"]
    crossed = False
    for _ in range(steps):
        p = world(f, l, floor_z(f, l))
        way = bot.way_in(PlayerState(1, 0, "bot", p, yaw=0.0), goal)
        target = goal if way is None else way[0]
        tf, tl, _ = local(target)
        d = math.hypot(tf - f, tl - l)
        gf, gl, _ = local(goal)
        if math.hypot(gf - f, gl - l) < 0.3:
            return True, crossed
        k = min(1.0, 0.25 / max(d, 1e-6))
        f, l = f + (tf - f) * k, l + (tl - l) * k
        inside = h0 <= f <= h1 and abs(l) <= hw
        lane = abs(l - al) <= 0.8 and f <= -2.4
        bay = f0 <= f <= f1 and abs(l) <= w and floor_z(f, l) > 0.35
        if inside and not lane and not bay:
            crossed = True
    return False, crossed


def main():
    fails = []
    m = get_map("h3_shrine")
    bot = Bot(1, 0, make_profile("average", "rusher", random.Random(1)), m, random.Random(1))
    el = dict(handle=7, kind="behemoth", pos=(-0.27, -58.56, -22.26), fwd=(-1.0, 0.0, 0.0), occupied=False, riders=0)
    bot.vehicles_now = [el]
    local, world = vehicles.frame_of(el)
    goal = world(*E["flag_return"][:2], E["flag_return"][2])
    flag = world(1.45, -0.47, 1.67)
    for name, start, g in (("in front", (7.0, 0.5), goal), ("beside", (0.5, -4.5), goal), ("behind", (-8.0, 2.0), goal),
                           ("in front, to the flag", (6.0, -1.0), flag)):
        reached, crossed = walk(bot, el, start, g)
        if not reached or crossed:
            fails.append(f"{name}: reached {reached}, through the hull {crossed}")
    w0 = bot.way_in(PlayerState(1, 0, "bot", world(-4.7, -0.5, 0.0), yaw=0.0), goal)
    if not (w0 and w0[1] and abs(local(w0[0])[0] - E["ramp"][1][0]) < 0.01):
        fails.append(f"at the ramp's foot: {w0} (want straight up to its top)")
    w1 = bot.way_in(PlayerState(1, 0, "bot", world(-1.0, 0.0, 0.6), yaw=0.0), goal)
    if not (w1 and w1[1] and w1[0] is goal):
        fails.append(f"on the bay floor: {w1} (want straight to the goal)")
    w2 = bot.way_in(PlayerState(1, 0, "bot", world(-1.0, 0.0, 3.0), yaw=0.0), goal)
    if not w2 or w2[1]:
        fails.append(f"on its roof: {w2} (want off it to the ramp's foot by the nav, not straight on)")
    if bot.way_in(PlayerState(1, 0, "bot", world(8.0, 0.0, 0.0), yaw=0.0), world(12.0, 0.0, 0.0)) is not None:
        fails.append("a goal outside the bay was routed")
    bot.vehicles_now = [dict(el, fwd=None)]
    if bot.way_in(PlayerState(1, 0, "bot", world(7.0, 0.0, 0.0), yaw=0.0), goal) is not None:
        fails.append("an Elephant with no facing read was routed")
    # 2. the capture point
    for name, side, want_return in (("h3_chill", 0, True), ("bloodgulch", 0, False)):
        mp = get_map(name)
        d = Director(side, mp, {})
        snap = SimpleNamespace(flags={t: FlagState(t, mp["flags"][t], mp["flags"][t]) for t in (0, 1)}, mode="ctf",
                               players=[])
        got, want = d.capture_point(snap), (mp["returns"][side] if want_return else mp["flags"][side])
        if (got - want).flat() > 0.01 or (want_return and (want - mp["flags"][side]).flat() < 0.3):
            fails.append(f"{name}: capture point {got} (want {want}, the stand {mp['flags'][side]})")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("elephant OK (round the hull and up the ramp from in front, beside and behind; captures at the flag return)")


if __name__ == "__main__":
    main()
