"""A bot already on a person's run line, past the run-up, runs on to the take-off (Bot.move_to). Live Boneyard B18
phase 3 (trace logs/tmp/invasion_regress/traces/trace_reach_70_boneyard_20261105-101023.jsonl, Spartan 1 at 579.5-585.1 s):
on the narrow walkway 1.1 u from the drop's take-off (265.67, 89.63), the person's run-up (262.87, 90.05) 2 u behind,
it went back for it among teammates for 5.5 s ("run-up not reached: from here" only after RUNUP_GIVE_UP); every
attacker life of the core run passes there.

1. On the line past the run-up, moving east: steered on east at the take-off, not back west to the run-up.
2. Off the line (1 u to its side, short of the run-up): still to the run-up first.

usage: python -I test_runup_line.py      -> "runup line OK"
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
from brain.terrain import JumpVec  # noqa: E402

M = "reach_70_boneyard/variants/v86d95e85"
J = JumpVec(272.42, 89.96, -10.18, sx=265.67, sy=89.63, rx=262.87, ry=90.05)


def heading(pos, yaw):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), get_map(M), random.Random(1))
    b.now = 580.0
    me = PlayerState(1, 0, "s", pos, vel=Vec(1.5, -0.2, 0.0), yaw=yaw)
    act = Action(yaw=yaw)
    b.move_to(me, Vec(308.91, 103.03, -9.37), act, lambda a, q, **kw: J)
    return act.yaw + math.atan2(act.strafe, act.forward)


def off(h, to):
    return abs(math.atan2(math.sin(h - to), math.cos(h - to)))


def main():
    fails = []
    p = Vec(264.82, 90.31, -5.0)
    h = heading(p, -0.4)
    if off(h, math.atan2(89.63 - p.y, 265.67 - p.x)) > 0.5:
        fails.append(f"on the run line past the run-up: heading {h:.2f}, not on to the take-off")
    q = Vec(262.4, 91.1, -5.0)
    h = heading(q, -0.4)
    if off(h, math.atan2(90.05 - q.y, 262.87 - q.x)) > 0.5:
        fails.append(f"off the line short of the run-up: heading {h:.2f}, not to the run-up")
    if fails:
        print("runup line FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("runup line OK")


if __name__ == "__main__":
    main()
