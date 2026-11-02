"""The nav's planned step down onto a ledge passes the edge guard (the player, Breakneck King of the Hill: "both
teams really didnt seem to interested in playing the objective"; 52% of the edge stops were on two walkway edges over
the hill, 2.4 u above the ledge the path drops to, and the hill holders sat a median 20 u from the hill).
1. at the walkway edge (-11.4, 14.7, 7.7) with the path's next point on the ledge 2.4 below: it walks on ("step down")
2. a "next point" 5 u below (past MAX_DROP, the pit) never passes as a step down; facing away with the command slowed by
   the turn-first rule (the live moment, next point 1.5 u off on the ledge) it steps down
(The live stop itself did not reproduce offline: the map data reads solid floor round that spot now; the live guard
state, its last floor and momentum, differed. The step down passes before any probe or brake.)
3. the second stuck edge (-11.5, 10.3, 8.8) dropping to 6.4: walks on

usage: python -I test_step_down.py      -> "step down OK"
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


def guard(pos, wp, yaw_deg=None):
    """One edge-guard tick moving at wp, 2.3 u/s. yaw_deg: facing elsewhere (live 85 degrees with the next point at
    -151): the command toward wp at 0.3, slowed by the turn-first rule, so it is not the nav's own command."""
    b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), get_map("reach_cex_headlong"), random.Random(1))
    me = PlayerState(1, 0, "b1", pos)
    act = Action()
    to = math.atan2(wp.y - pos.y, wp.x - pos.x) if (wp - pos).flat() > 1e-3 else 0.0
    act.yaw = to if yaw_deg is None else math.radians(yaw_deg)
    act.forward, act.strafe = math.cos(to - act.yaw), math.sin(to - act.yaw)       # (strafe + = left)
    b.wp, b.nav_cmd, b.notes = wp, (act.forward, act.strafe), []
    if yaw_deg is not None:
        act.forward, act.strafe = act.forward * 0.3, act.strafe * 0.3
    d = Vec(math.cos(to), math.sin(to), 0)                    # running at it, 2.3 u/s (the live momentum brake)
    b._eg_last = (9.9, Vec(pos.x - d.x * 0.23, pos.y - d.y * 0.23, pos.z))
    b.edge_guard(10.0, me, act)
    return abs(act.forward) + abs(act.strafe), list(b.notes)      # how hard it still moves (0: held)


def main():
    fails = []
    fwd, notes = guard(Vec(-11.4, 14.7, 7.7), Vec(-11.3, 14.8, 5.2))
    if fwd < 0.9 or "step down" not in notes:
        fails.append(f"walkway edge over the ledge: move {fwd}, notes {notes} (want it to step down)")
    fwd, notes = guard(Vec(-11.4, 14.7, 7.7), Vec(-11.3, 14.8, 2.65))
    if "step down" in notes:
        fails.append(f"a 5 u drop to the pit passed as a step down: forward {fwd}, notes {notes}")
    fwd, notes = guard(Vec(-11.45, 14.75, 7.66), Vec(-12.79, 14.0, 5.2), yaw_deg=85)   # the live moment, 1.54 u off
    if fwd < 0.25 or "step down" not in notes:
        fails.append(f"walkway edge, facing away, the next point on the ledge: move {fwd}, notes {notes}")
    fwd, notes = guard(Vec(-11.45, 14.75, 7.66), Vec(-12.79, 14.0, 2.65), yaw_deg=85)
    if "step down" in notes:
        fails.append(f"facing away, the next point down in the pit passed as a step down: {notes}")
    fwd, notes = guard(Vec(-11.5, 10.3, 8.8), Vec(-11.3, 10.0, 6.4))
    if fwd < 0.9 or "step down" not in notes:
        fails.append(f"the second walkway edge: move {fwd}, notes {notes}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("step down OK")


if __name__ == "__main__":
    main()
