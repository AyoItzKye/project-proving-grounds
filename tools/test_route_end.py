"""The jump window ends on landing (Bot.edge_guard). Live Boneyard B11-B14 (trace in logs/tmp/invasion_regress/traces,
20261105-082153, Elite 12 at 60.9-61.7 s): at the top of the plank route up to the -6 walkway (every step of a person's
walked route is a planned jump) the window stayed 1.2 s and steered the bot back to the route's last point (249.55,
89.73) as it walked on toward (248.72, 92.27): the stick forward / back every 0.3 s, 550-750 such rows a match.

1. On the floor at the landing, no jump offered, window open: the walk goes on (forward kept).
2. In the air over the drop off the walkway, no jump offered, window open: still steered onto its landing.

usage: python -I test_route_end.py      -> "route end OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def guard(pos, land, yaw):
    b = Bot(12, 1, make_profile("top", "objector", random.Random(1)), get_map("reach_70_boneyard/variants/v86d95e85"),
            random.Random(1))
    now = 61.2
    b.planned_jump, b.jump_land, b.jump_until = False, land, now + 0.9
    me = PlayerState(12, 1, "e", pos, yaw=yaw)
    act = Action(forward=1.0, strafe=0.0, yaw=yaw)
    b.edge_guard(now, me, act)
    return act


def main():
    fails = []
    yaw = math.atan2(92.27 - 90.66, 248.72 - 249.19)      # toward the next waypoint
    a = guard(Vec(249.19, 90.66, -6.0), Vec(249.55, 89.73, -5.94), yaw)
    if a.forward < 0.5:
        fails.append(f"landed at the route's end: the guard turned the walk round (forward {a.forward:.2f})")
    # in the air 2 u over the floor under the walkway's west edge, its landing ahead: steered on to it
    land = Vec(244.61, 90.5, -8.69)
    a = guard(Vec(246.66, 90.88, -5.33), land, math.atan2(-0.38, -2.05) + math.pi)
    to = math.atan2(land.y - 90.88, land.x - 246.66)
    mv = a.yaw + math.atan2(a.strafe, a.forward)
    if abs(math.atan2(math.sin(mv - to), math.cos(mv - to))) > 0.5:
        fails.append("in the air over the drop: no longer steered onto its landing")
    if fails:
        print("route end FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("route end OK")


if __name__ == "__main__":
    main()
