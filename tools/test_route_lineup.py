"""A person's route hops along his way at the take-off, not across it (Bot.move_to's route block). Live Boneyard B15
(trace logs/tmp/invasion_regress/traces/trace_reach_70_boneyard_20261105-085417.jsonl, Elite 7 at 51.5-57 s): onto the
plank route under phase 1's south territory from the east, it hopped north-west at the take-off (250.94, 81.75), off the
plank's side, and walked the route's line on the floor under it ("route: short of its end", 9 a match; two and the route
is banned 60 s and the bots wiggle at the plank's lip instead).

1. At the take-off moving north-west (across the person's way north): no hop, back to the run-up (250.71, 80.39).
2. At the take-off moving north along it: the hop.
3. After lining up at the run-up, the route goes on from there (the take-off next).

usage: python -I test_route_lineup.py      -> "route lineup OK"
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

M = "reach_70_boneyard/variants/v86d95e85"


def plank():
    T = terrain(get_map(M))
    return next([(Vec(*q[:3]), q[3]) for q in path] for src, dst, path, w in T.hroutes
                if math.hypot(path[0][0] - 250.71, path[0][1] - 80.39) < 0.3)


def step(pos, vel):
    b = Bot(7, 1, make_profile("top", "sniper", random.Random(7)), get_map(M), random.Random(7))
    b.now = 52.8
    r = plank()
    b.route, b.route_full, b.route_until, b.lineups, b.route_lineup = list(r), list(r), 70.0, 0, None
    b.route_key, b.route_end = (round(r[0][0].x, 1), round(r[0][0].y, 1)), r[-1][0]
    me = PlayerState(7, 1, "e", pos, vel=vel, yaw=math.atan2(vel.y, vel.x))
    act = Action(yaw=me.yaw)
    b.move_to(me, Vec(251.217, 94.975, -4.0), act, lambda a, q, **kw: q)
    return b, act


def main():
    fails = []
    b, a = step(Vec(251.05, 81.7, -9.7), Vec(-1.6, 1.4, 0.0))       # B15 52.84 s: from the east, north-west
    mv = a.yaw + math.atan2(a.strafe, a.forward)
    to = math.atan2(80.39 - 81.7, 250.71 - 251.05)
    if a.jump or abs(math.atan2(math.sin(mv - to), math.cos(mv - to))) > 0.4:
        fails.append(f"across the way at the take-off: jump {a.jump}, not back to the run-up")
    b2, a2 = step(Vec(250.92, 81.6, -9.72), Vec(0.25, 2.1, 0.0))     # in along the person's way
    if not a2.jump:
        fails.append("along the way at the take-off: no hop")
    # 3: lined up (at the run-up now): the route goes on to the take-off
    b.now += 1.0
    act = Action(yaw=1.4)
    b.move_to(PlayerState(7, 1, "e", Vec(250.72, 80.4, -9.63), vel=Vec(0.0, 0.0, 0.0), yaw=1.4), Vec(251.217, 94.975, -4.0),
              act, lambda a, q, **kw: q)
    if not b.route or (b.route[0][0] - Vec(250.94, 81.75, -9.75)).flat() > 0.05:
        fails.append(f"after the line-up the route is not on to the take-off: {b.route and b.route[0]}")
    if fails:
        print("route lineup FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("route lineup OK")


if __name__ == "__main__":
    main()
