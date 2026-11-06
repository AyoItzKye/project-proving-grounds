"""Places LiDAR's links lead bots to that no bot can leave (sim A/B Nov 4, logs/tmp/lidar_ab/RESULTS.md: on
h3_construct, with LiDAR, bots spent 10.6% of their time in the unstuck wiggle against 2.1% without, and pushed without
moving 19% against 0.4%; with only the "links" key dropped it went back to the no-LiDAR numbers):

1. a lift well (Terrain.trap): floor 2.5 u under the rim of Construct's side lifts, reachable by a drop, with no way
   out to any spawn. Fighters backed off the rim into it and pushed there for the rest of the life. Movement
   (Terrain.can_step) never steps into a trap from outside; along the rim it still walks
2. a people's jump landing on a cell edge (Sim.step): the raw LiDAR point (-5.76, -2.31, 11.53) is in a cell with no
   floor at that height, so every step from it was refused. The sim lands bodies on the landing's nav node
3. a lift ride from a floor over the well (Bot.ride_lift): 3 s on, not in the column and no higher, the ride ends and
   the bot leaves every people's take-off into that column from that height for 60 s (jump_blocked); a ride in the
   column at its base goes on

usage: python -I test_lidar_traps.py      -> "lidar traps OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec, angles_to  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

NAME = "h3_construct"
M = get_map(NAME)
T = terrain(M)
RIM, WELL = Vec(2.15, -5.95, 3.0), Vec(2.16, -5.97, 0.5)          # (a bot's step into it, sim seed 1 at 4.6 s)
TAKE_OFF, LAND = (-1.98, -4.25, 10.62), (-5.76, -2.31, 11.53)       # a people's jump, two-way, bots landed it live 5x
BASE, TOP = Vec(4.245, -8.287, 3.2), Vec(7.39, -8.51, 12.52)        # the east side lift, and its top
LEDGE = Vec(3.62, -7.65, 6.41)                                      # the middle floor over its well


def free(p):
    return [a for a in range(8) if T.can_step(p, Vec(p.x + math.cos(a * math.pi / 4) * 0.08,
                                                     p.y + math.sin(a * math.pi / 4) * 0.08, p.z))]


def main():
    fails = []
    # 1. the well
    trap = getattr(T, "trap", None)
    if trap is None or not trap[T._node(WELL)]:
        fails.append("Construct's lift well is not marked a trap")
    if T.can_step(RIM, Vec(WELL.x, WELL.y)):
        fails.append("movement still steps off the rim into the lift well")
    if not free(RIM):
        fails.append("the trap guard froze a bot on the rim")
    # 2. the landing
    from brain.sim import Sim, SPEED
    sim = Sim("slayer", per_team=1, seed=1, map_name=NAME)
    p, b = sim.players[0], sim.bots[0]
    if not any(math.hypot(k["take_off"][0] - TAKE_OFF[0], k["take_off"][1] - TAKE_OFF[1]) < 0.05
               for _, _, k, _ in sim.T.hjumps):
        fails.append("the people's jump onto (-5.76, -2.31) is gone from the nav (test data)")
    yaw = angles_to(Vec(*TAKE_OFF), Vec(*LAND))[0]
    p.pos, p.vel = Vec(*TAKE_OFF), Vec(math.cos(yaw) * SPEED, math.sin(yaw) * SPEED, 0)
    b.think = lambda *a, **k: Action(forward=1.0, yaw=yaw, jump=True)
    sim.step()
    if (p.pos - Vec(*LAND)).flat() > 0.5 or abs(p.pos.z - LAND[2]) > 0.7:
        fails.append(f"the jump did not land: {p.pos}")
    elif not free(p.pos):
        fails.append(f"landed at {p.pos} where every step is refused")
    # 3. the lift ride from the ledge
    rb = Bot(1, 0, make_profile("strong", "objector", random.Random(1)), M, random.Random(1))
    rb._terrain = T
    key = (3.5, -7.6)
    for now, want in ((2.0, True), (3.5, False)):
        rb.lift_ride, rb.lift_from, rb.now = (BASE, TOP, 0.0), (LEDGE.z, key), now
        rb.jump_fails = {}
        going = rb.ride_lift(PlayerState(1, 0, "b", LEDGE), Action())
        if going != want:
            fails.append(f"a ride stalled on the ledge at {now} s: riding {going}, want {want}")
    blocked = getattr(rb, "jump_fails", {})
    if key not in blocked or len(blocked) < 3:
        fails.append(f"the stalled ride did not block the ledge's take-offs into that column: {sorted(blocked)}")
    rb.lift_ride, rb.lift_from, rb.now, rb.jump_fails = (BASE, TOP, 0.0), (BASE.z, key), 3.5, {}
    if not rb.ride_lift(PlayerState(1, 0, "b", BASE), Action()):
        fails.append("a ride in the column at its base was ended")
    if fails:
        print("FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("lidar traps OK")


if __name__ == "__main__":
    main()
