"""The core carrier's jump onto Spire's delivery platform (match 211159 at 703-717 s: the carrier jumped from a person's
take-off, landed short on the lip below the platform and tried again for 10 s). On the people's jump it took
(maps/reach_35_island/lidar.json: take-off (-161.57, -427.11), landing (-162.38, -428.95), 0.33 u up):

1. a bot carrying nothing jumps from the person's take-off
2. a carrier does not jump there: it goes on 0.3-0.6 u nearer the landing, on floor, and jumps from there
3. a jump it fell short of twice (down more than 1 u from the landing): the bot leaves that jump and asks the nav for
   another way (no people's jumps); one short try does not
4. a jump that landed is not counted against

usage: python -I test_carrier_jump.py      -> "carrier jump OK"
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
from brain.terrain import JumpVec  # noqa: E402

M = get_map("reach_35_island")
T = terrain(M)
TAKE_OFF, LAND, RUNUP = (-161.57, -427.11, -58.64), (-162.38, -428.95, -58.31), (-161.42, -426.74, -58.78)
GOAL = Vec(-163.05, -432.09, -58.37)


def bot():
    b = Bot(1, 0, make_profile("strong", "objector", random.Random(1)), M, random.Random(1))
    b._terrain = T
    return b


def nav_log(calls):
    def nav(p, q, **k):
        calls.append(k)
        if k.get("human"):
            return JumpVec(LAND[0], LAND[1], LAND[2], TAKE_OFF[0], TAKE_OFF[1], RUNUP[0], RUNUP[1])
        return Vec(p.x - 1.0, p.y, p.z)                       # (another way: anywhere but the jump)
    return nav


def step(b, at, now, carrying, calls):
    b.now = now
    b.runup_done = True                                       # (past the run-up: at the take-off)
    b.runup_key = (round(TAKE_OFF[0], 2), round(TAKE_OFF[1], 2))
    me = PlayerState(1, 0, "b", Vec(*at), has_flag=carrying)
    act = Action(yaw=0.0)
    b.move_to(me, GOAL, act, nav_log(calls))
    return act


def main():
    fails = []
    calls = []
    if not step(bot(), TAKE_OFF, 10.0, False, calls).jump:
        fails.append("carrying nothing, at the person's take-off: no jump (want it to jump there)")
    c = bot()
    a = step(c, TAKE_OFF, 10.0, True, calls)
    if a.jump:
        fails.append("the carrier jumped at the person's take-off (want it nearer the landing)")
    start = c.carrier_take_off(Vec(*TAKE_OFF), Vec(*LAND))
    moved = math.dist((start.x, start.y), TAKE_OFF[:2])
    toward = math.dist((start.x, start.y), LAND[:2]) < math.dist(TAKE_OFF[:2], LAND[:2])
    if not (0.3 <= moved <= 0.61 and toward and T.ground_ok(start.x, start.y, TAKE_OFF[2] + 0.4, drop=1.0)):
        fails.append(f"the carrier's take-off {moved:.2f} u on, toward the landing {toward} (want 0.3-0.6 u nearer it, on floor)")
    if not step(c, (start.x, start.y, TAKE_OFF[2]), 11.0, True, calls).jump:
        fails.append("the carrier at its own take-off: no jump")
    short = (-162.1, -428.6, -58.9)                           # the lip below the platform (where it landed, live)
    j = bot()
    t = 20.0
    for k in range(2):
        step(j, TAKE_OFF, t, False, calls)                    # jumps
        calls.clear()
        step(j, short, t + 2.0, False, calls)                 # down, short: judged
        t += 4.0
        if k == 0 and any(not c.get("human") for c in calls):
            fails.append("after one short jump it already went another way (want one more try)")
    calls.clear()
    step(j, TAKE_OFF, t, False, calls)
    if not any(not c.get("human") for c in calls):
        fails.append(f"after two short jumps the nav was asked {calls} (want another way: no people's jumps)")
    ok = bot()
    step(ok, TAKE_OFF, 50.0, False, calls)
    calls.clear()
    step(ok, LAND, 52.0, False, calls)
    if getattr(ok, "jump_fails", {}):
        fails.append(f"a jump that landed was counted short: {ok.jump_fails}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"carrier jump OK (a carrier goes {moved:.2f} u nearer the landing; two short jumps and the bot goes another way)")


if __name__ == "__main__":
    main()
