"""A banned person's route (jump_blocked: short of its end twice) keeps the bot on the walking way all round its start,
not only where the nav offers it (Bot.move_to). Live Boneyard B21 (trace in logs/tmp/invasion_regress/traces,
20261105-123839, Elite 9 24.6-104.7 s at the plank's foot (251, 82, -10)): its next point flipped between the route's
run-up (people's ways asked from a step off it) and the walking way's lip (the ban's fallback) every 0.3-0.5 s.

1. The plank route banned, the bot 1.9 u off its start: the nav is asked without people's ways.
2. Its next points from both of B21's flip spots lead the same way (no back and forth).
3. With no ban, people's ways as before.

usage: python -I test_ban_area.py      -> "ban area OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = "reach_70_boneyard/variants/v86d95e85"
GOAL = Vec(251.217, 94.975, -4.0)


def step(at, ban, T, kws):
    b = Bot(9, 1, make_profile("top", "objector", random.Random(9)), get_map(M), random.Random(9))
    b.now, b.order = 100.0, Order("defender", GOAL)
    if ban:
        b.jump_fails = {(250.7, 80.4): (2, 160.0)}

    def nav(a, q, **kw):
        kws.append(kw)
        return T.nav(a, q, **kw)
    act = Action(yaw=0.0)
    b.move_to(PlayerState(9, 1, "e", at, yaw=0.0), GOAL, act, nav)
    return getattr(b, "wp", None)


def main():
    fails = []
    m = get_map(M)
    T = terrain(m)
    L = invasion.layout(m["objects"])
    invasion.apply_barriers(T, L, {b["key"]: True for b in L["barriers"] if b["kind"] == "gate"})
    kws = []
    a, b = Vec(251.03, 82.22, -9.8), Vec(250.35, 81.52, -9.7)       # B21's two flip spots (79.3 / 82.1 s)
    wa = step(a, True, T, kws)
    if any(k.get("human") for k in kws):
        fails.append(f"1. route banned, 1.9 u off its start: the nav asked with people's ways {kws}")
    wb = step(b, True, T, [])
    if wa is not None and wb is not None and (wa - a).flat() > 0 and (wb - b).flat() > 0:
        da = math.atan2(wa.y - a.y, wa.x - a.x)
        db = math.atan2(wb.y - b.y, wb.x - b.x)
        if math.cos(da - db) < 0.0:
            fails.append(f"2. the two spots' next points lead opposite ways: {wa} from {a}, {wb} from {b}")
    kws = []
    step(a, False, T, kws)
    if not any(k.get("human") for k in kws):
        fails.append("3. no ban: people's ways not asked")
    if fails:
        print("ban area FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("ban area OK")


if __name__ == "__main__":
    main()
