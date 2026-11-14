"""An objective within OBJ_REACH with a clear straight line is walked at straight (Bot.redirect), not turned off by the
wall behind it. Live Battle Creek CTF, Nov 14: red's runners came within 4 u of blue's flag 10 times and took it once,
"wall ahead: stepping around" 1.3-2.6 u from the flag (its stand is against the base's wall).

Here: Battle Creek, a runner 1.3 u from blue's flag walking at a wall that is under REDIRECT_D away. With the objective
goal on the flag the step turns onto the flag; with the goal a point far off (or OBJ_REACH 0) it steps round as before.

usage: python -I test_obj_reach.py      -> "obj reach OK"
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

M = get_map("beavercreek")
T = terrain(M)
FLAG = M["flags"][1]


def scene():
    """A spot 0.9-2.6 u from the flag with a clear line to it and a heading that runs into a wall within REDIRECT_D."""
    b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), M, random.Random(1))
    b.feet_off = 0.0
    for r in (1.3, 1.6, 2.0, 2.4, 0.9):
        for k in range(24):
            a = k * math.pi / 12
            p = Vec(FLAG.x + r * math.cos(a), FLAG.y + r * math.sin(a), FLAG.z)
            p = Vec(p.x, p.y, T.nav_z(p.x, p.y, FLAG.z))
            if abs(p.z - FLAG.z) > 0.5:
                continue
            to_flag = math.atan2(FLAG.y - p.y, FLAG.x - p.x)
            if T.clearance(p, to_flag, 1.5) < min(r, 1.5) - 0.1:
                continue
            for j in range(36):
                yaw = j * math.pi / 18
                if T.clearance(p, yaw, 1.5) < b.REDIRECT_D and abs(math.remainder(yaw - to_flag, 2 * math.pi)) > 0.6:
                    return b, p, yaw, to_flag
    raise SystemExit("FAIL: no spot by blue's flag with a wall ahead and a clear line to the flag")


def walk_dir(b, p, yaw, goal):
    me = PlayerState(1, 0, "b1", p)
    b.goal = goal
    b.notes = []
    act = Action(forward=1.0, yaw=yaw)
    b.redirect(10.0, me, act)
    return act.yaw + math.atan2(act.strafe, act.forward), b.notes


def main():
    b, p, yaw, to_flag = scene()
    fails = []
    d, notes = walk_dir(b, p, yaw, ("objective", FLAG))
    if abs(math.remainder(d - to_flag, 2 * math.pi)) > 0.05 or "objective in reach: straight at it" not in notes:
        fails.append(f"flag {math.dist((p.x, p.y), (FLAG.x, FLAG.y)):.1f} u off: walked {math.degrees(d):.0f} deg, the flag "
                     f"at {math.degrees(to_flag):.0f} ({notes})")
    far = Vec(FLAG.x + 30.0, FLAG.y, FLAG.z)
    d, notes = walk_dir(b, p, yaw, ("objective", far))
    if "objective in reach: straight at it" in notes:
        fails.append(f"a goal 30 u off taken straight ({notes})")
    Bot.OBJ_REACH = 0.0
    try:
        d, notes = walk_dir(b, p, yaw, ("objective", FLAG))
        if "objective in reach: straight at it" in notes:
            fails.append("OBJ_REACH 0: still straight at the flag")
    finally:
        Bot.OBJ_REACH = 3.0
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"obj reach OK (Battle Creek, {math.dist((p.x, p.y), (FLAG.x, FLAG.y)):.1f} u from blue's flag, a wall "
          f"{T.clearance(p, yaw, 1.5):.2f} u ahead: straight onto the flag; a far goal and OBJ_REACH 0 step round)")


if __name__ == "__main__":
    main()
