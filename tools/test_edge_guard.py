"""Offline checks for the edge guard on H2A Lockdown (falls were 17 of ~90 deaths): a bot running at
a deadly edge brakes against its motion, a fight jump whose landing is over the void is dropped, a
bot knocked off steers back even when a far lower floor is under it, and the run to a jump's
take-off is not braked. Positions are from the fall traces (tools/fall_check.py).

usage: python -I test_edge_guard.py      -> "edge guard OK"
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

MAP = get_map("h2a_ca_lockout")
OFF = 0.38                                  # H2A reports positions this far above the floor


def bot():
    return Bot(1, 0, make_profile("strong", "flanker", random.Random(1)), MAP, random.Random(1))


def me(x, y, z):
    return PlayerState(1, 0, "bot", Vec(x, y, z))


def world_move(act):
    c, sn = math.cos(act.yaw), math.sin(act.yaw)
    return c * act.forward - sn * act.strafe, sn * act.forward + c * act.strafe


def main():
    # 1. running at 2.3 u/s toward the void past x -4.4 (floor 0.4 up to there): brake, push back (+x)
    b = bot()
    b.edge_guard(0.0, me(-3.60, -1.9, 0.4 + OFF), Action())
    act = Action(forward=-1.0, yaw=0.0)     # backpedalling toward -x (a fight strafe)
    b.edge_guard(0.1, me(-3.83, -1.9, 0.4 + OFF), act)
    mx, _ = world_move(act)
    assert mx > 0.5 and not act.jump, ("no brake at the edge", act)

    # 2. a jump shot 1.1 from that edge, moving toward it: no jump (the landing drifts over the void)
    b = bot()
    b.edge_guard(0.0, me(-3.10, -1.9, 0.03 + OFF), Action())
    act = Action(forward=-1.0, yaw=0.0, jump=True)
    b.edge_guard(0.1, me(-3.33, -1.9, 0.03 + OFF), act)
    assert not act.jump, ("jumped toward the void", act)

    # 3. knocked off at (-5.0, 0.9) from floor 0.4 at (-4.4, 0.3): a floor 4.2 further down (-3.43)
    #    is no landing; steer back toward the ledge (+x, +... toward -4.4, 0.3)
    b = bot()
    b.last_ground = Vec(-4.4, 0.3, 0.4 + OFF)
    act = Action(yaw=0.0)
    b.edge_guard(1.0, me(-5.0, 0.9, -1.0), act)
    mx, my = world_move(act)
    assert mx > 0.3 and my < 0.0, ("no air steer back", act)

    # 4. the run to a take-off (a jump people made at -5.98, 0.01): trusted, not braked
    b = bot()
    b.edge_guard(0.0, me(-6.70, -0.10, 0.43 + OFF), Action())
    act = Action(forward=1.0, yaw=math.atan2(0.11, 0.72))
    b.nav_cmd, b.runup_t = (act.forward, act.strafe), 0.1
    b.edge_guard(0.1, me(-6.47, -0.07, 0.43 + OFF), act)
    assert act.forward == 1.0 and act.strafe == 0.0, ("braked on a jump run-up", act)
    print("edge guard OK")


if __name__ == "__main__":
    main()
