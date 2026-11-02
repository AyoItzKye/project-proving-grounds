"""A runner at the wheel gets out at their flag (live Avalanche CTF, trace_h3_sidewinder_20261031-070402, master 86f0e19:
558 s, no flag ever carried; the runners' rows within 3 u flat of the enemy flag were mostly in vehicles 4 u under its
platform: #6 in a Mongoose 5,059 rows, #1 in a Wraith 3,128 and a Warthog 1,141, #5 in a Warthog 3,088. Each had
boarded as the team's crew ("drive": crew_ride), so the end of its trip was "on to the next place", never out). Frames
from that trace:

1. #1, runner, a Warthog at (-29.72, -30.86, -4.43) by red's flag (-27.0, -31.65, -0.49), 60.0 s: out
2. #6, runner, a Mongoose at (24.80, -29.35, -4.44) by blue's flag (27.0, -31.65, -0.49), 215.8 s: out
3. the same Mongoose driven by a crew bot that is no runner: it drives on (the crew rule unchanged)

usage: python -I test_runner_exit.py      -> "runner exit OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
FRAMES = (("#1 Warthog", 0, "top", Vec(-29.72, -30.86, -4.43), -0.785, "warthog_snow", Vec(-27.0, -31.65, -0.49)),
          ("#6 Mongoose", 1, "average", Vec(24.80, -29.35, -4.44), -1.057, "mongoose_snow", Vec(27.0, -31.65, -0.49)))


def ride(team, tier, pos, yaw, kind, flag, role):
    b = Bot(1, team, make_profile(tier, "rusher", random.Random(1)), M, random.Random(1))
    b._terrain = T
    b.order = Order("drive", pos, target=9)
    v = dict(handle=9, kind=kind, pos=(pos.x, pos.y, pos.z), riders=1, occupied=True, team=team,
             fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), gunner=False, turrets=[], manned=[])
    out = 0
    for k in range(90):
        t = 50.0 + k / 30
        me = PlayerState(1, team, "r", pos, yaw=yaw, vehicle=9)
        snap = Snapshot(t, [me], {0: FlagState(0, M["flags"][0], M["flags"][0]), 1: FlagState(1, M["flags"][1],
                                                                                            M["flags"][1])},
                        mode="ctf", vehicles=[v])
        a = Action(yaw=yaw)
        b.drive(t, 1 / 30, me, snap, a, lambda p, q, **kw: q)
        if k == 0:                       # boarded as the team's crew, then made the runner (director.assign_roles)
            b.order = Order(role, flag)
            b.drive_to = flag
        out += a.action
    return out, b.crew_ride


def main():
    fails = []
    for name, team, tier, pos, yaw, kind, flag in FRAMES:
        out, crew = ride(team, tier, pos, yaw, kind, flag, "runner")
        if not out or crew != 9:
            fails.append(f"{name}: a runner 4 u under their flag pressed get-out {out} ticks (crew {crew}; want out)")
    name, team, tier, pos, yaw, kind, flag = FRAMES[1]
    out, _ = ride(team, tier, pos, yaw, kind, flag, "drive")
    if out:
        fails.append(f"a crew driver that is no runner got out at the end of its trip ({out} ticks)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("runner exit OK (#1 and #6 out under their flags; a crew driver drives on)")


if __name__ == "__main__":
    main()
