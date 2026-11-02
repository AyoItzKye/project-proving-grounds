"""A driver wedged where its trip ends backs out, also while its exits are on hold (live Avalanche CTF match 064500,
coordinator's check: 248 s of ground-vehicle stalls with no note. CosmicPilot (#5), a runner driving a taxi Warthog
(director.vehicle_jobs: drive_to its order point, the red flag on the floor above at (27.0, -31.6, -0.5)), sat in the
red garage at (24.33, -30.83, -4.44) 147-367 s: the flag 4.8 u off read "arrived", its exits were on hold
(exit_block_until) and that branch cleared drive_pos every tick, so it never counted as stuck and never reversed: no
Use and no reverse in 224 s of rows; #1's Warthog and #5's Mongoose the same later).

1. that frame held still for 20 s, the director setting the taxi's drive_to every half second: it tries to get out,
   then backs off again and again (3+ reverses), not a frozen throttle
2. a driver not wedged (moving) during the hold is left alone: no reverse

usage: python -I test_vehicle_wedge.py      -> "vehicle wedge OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
GARAGE, FLAG = Vec(24.33, -30.83, -4.44), Vec(27.0, -31.6, -0.5)
FLAGS = {0: FlagState(0, FLAG, FLAG), 1: FlagState(1, Vec(-27.0, -31.6, -0.5), Vec(-27.0, -31.6, -0.5))}


def drive(moving, seconds=20.0):
    b = Bot(5, 1, make_profile("top", "rusher", random.Random(5)), M, random.Random(5))
    b.can_pickup = False
    b.order = Order("runner", FLAG)
    yaw, pos = -1.917, GARAGE
    reverses, uses, prev = 0, 0, False
    for k in range(int(seconds * 30)):
        t = 180.0 + k / 30
        if moving:
            pos = GARAGE + Vec(0.0, 3.0 * math.sin(t), 0.0)      # (rolling to and fro: not wedged)
        car = dict(handle=7, kind="warthog_snow", pos=(pos.x, pos.y, pos.z), occupied=True, riders=1, team=1,
                   fwd=(math.cos(yaw), math.sin(yaw), 0.0))
        me = PlayerState(5, 1, "bot", pos, yaw=yaw, alive=True, vehicle=7, weapon="assault_rifle", weapons=["assault_rifle"])
        if k % 15 == 0:
            b.vjob, b.drive_to = "taxi", FLAG                    # (director.vehicle_jobs, twice a second)
        a = b.think(t, 1 / 30, Snapshot(t, [me], mode="ctf", vehicles=[car], flags=FLAGS), lambda p, q: True, T.nav, [])
        back = a.forward < -0.5
        reverses += back and not prev
        prev = back
        uses += bool(a.action)
    return reverses, uses


def main():
    fails = []
    rev, uses = drive(False)
    if rev < 3 or not uses:
        fails.append(f"wedged in the garage 20 s: {rev} reverses (want 3+), {uses} Use ticks (want its exits tried first)")
    rev2, _ = drive(True, 6.0)
    if rev2:
        fails.append(f"rolling, not wedged: {rev2} reverses (want none)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"vehicle wedge OK (wedged: {rev} reverses after {uses} Use ticks; rolling: none)")


if __name__ == "__main__":
    main()
