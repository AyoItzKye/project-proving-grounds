"""The edge guard's momentum brake does not brake against the motion its own brake made (sim Sidewinder CTF seed 3: a bot
stood 41.6 s at the red flag room's ledge (29.5, -31.9, -0.84), 0.07 u to and fro every tick: each brake's push read as
momentum over the drop on the other side and was braked back; the nav's stick never came back; logs/tmp/sim_rows.py).
Replayed: the two positions it swapped between, 1/30 s apart, its stick toward its waypoint.

1. old behaviour gone: of 20 ticks swapping between the two spots, no more than every other one is a brake
2. still a brake from real momentum: a bot running at 2.5 u/s straight off that ledge's drop side brakes

usage: python -I test_brake_pingpong.py      -> "brake ping-pong OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
A, B = Vec(29.49, -31.89, -0.84), Vec(29.45, -31.83, -0.82)
WP = Vec(29.34, -32.24, -0.84)


def bot():
    b = Bot(2, 0, make_profile("top", "rusher", random.Random(2)), M, rng=random.Random(2))
    b._terrain, b.goal, b.planned_jump = T, ("hunt", WP), False
    b.wp = WP
    return b


def main():
    fails = []
    b = bot()
    brakes, t = 0, 50.0
    for k in range(20):
        t += 1 / 30
        p = A if k % 2 == 0 else B
        b.now, b.notes = t, []
        me = PlayerState(2, 0, "bot", p, alive=True)
        act = Action(yaw=math.atan2(WP.y - p.y, WP.x - p.x))
        act.forward = 1.0
        b.edge_guard(t, me, act)
        brakes += "edge brake" in b.notes
    if brakes > 10:
        fails.append(f"swapping between the two ledge spots: {brakes} of 20 ticks braked (want every other at most)")
    # real momentum off the drop: from A along the brake's first direction's opposite (where the drop was)
    b = bot()
    drop = None
    for a in range(0, 360, 10):
        q = Vec(A.x + math.cos(math.radians(a)) * 0.4, A.y + math.sin(math.radians(a)) * 0.4, A.z)
        if not T.ground_ok(q.x, q.y, A.z, drop=3.5):
            drop = math.radians(a)
            break
    hit = None
    if drop is not None:
        start = Vec(A.x - math.cos(drop) * 0.08, A.y - math.sin(drop) * 0.08, A.z)
        b.now, b.notes = 60.0, []
        b.edge_guard(60.0, PlayerState(2, 0, "bot", start, alive=True), Action(yaw=drop, forward=1.0))
        b.now, b.notes = 60.0 + 1 / 30, []
        act = Action(yaw=drop, forward=1.0)
        b.edge_guard(b.now, PlayerState(2, 0, "bot", A, alive=True), act)
        hit = "edge brake" in b.notes or "edge stop" in b.notes
    if drop is None or not hit:
        fails.append(f"running off the drop at 2.5 u/s (heading {drop}): {b.notes} (want a brake or a stop)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"brake ping-pong OK ({brakes} of 20 swap ticks braked; running off the drop still held: {b.notes})")


if __name__ == "__main__":
    main()
