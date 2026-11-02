"""The core carrier lines up behind a person's run-up before a running jump (live Spire: VaporRaven came at the player's
drop onto the heat vent from the side, passed the run-up 0.32 u off and circled 1.65 s back to it, left it moving
276-288 deg against the jump's 305, went by its take-off 0.68 u off (the jump is pressed within 0.35 u), slid off the
top's rim and the core fell where no bot reached it). The drop (maps/reach_35_island/drops.json): run-up (-169.75,
-408.37), take-off (-169.35, -408.94), landing (-164.59, -415.67, -58.25), 34 u down.

1. property (Code Master TS-11): from every start on the floor 1-2.2 u round the take-off, walking at it, moves
   followed with a lag (0.15 s and 0.3 s, live 0.1-0.4 s), with and without 0.6 s of lost footing at the run-up
   (live: 0.2-0.66 u over the floor there, its turn not followed 0.6 s): the carrier presses the jump within 8 s,
   never off the floor before it, moving at 1.5 u/s or more within 35 deg of the run (run-up to take-off; in the air
   it steers on at the landing). The code before this fix: off the floor from 5 of 44 starts with footing lost,
   jumps up to 84 deg off the run (the live start: 68-77 deg)
2. the carrier counts the run-up as it passes within 0.35 u (live: 0.32 u, then a 1.65 s circle back)
3. a bot carrying nothing goes straight at the run-up as before (no line-up)
4. a run with no floor behind its run-up: the carrier's line-up point is never off the floor

usage: python -I test_runup_lineup.py      -> "runup lineup OK"
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
RUNUP, TAKE_OFF, LAND = (-169.75, -408.37), (-169.35, -408.94), (-164.59, -415.67, -58.25)
Z = -24.33
GOAL = Vec(-163.05, -432.09, -58.37)
LANE = math.atan2(TAKE_OFF[1] - RUNUP[1], TAKE_OFF[0] - RUNUP[0])
DT = 1 / 30


def bot():
    b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), M, random.Random(1))
    b._terrain = T
    return b


def nav_for(run, take):
    def nav(p, q, **k):
        if k.get("human"):
            return JumpVec(LAND[0], LAND[1], LAND[2], take[0], take[1], run[0], run[1])
        return Vec(q.x, q.y, q.z)                            # (the walk graph: straight there)
    return nav


def approach(start, tau, carrying=True, run=RUNUP, take=TAKE_OFF, secs=8.0, targets=None, hop=0.0):
    """Walk the bot at the jump with moves followed tau late, and hop s with no footing (its moves not followed) as it
    first comes within 0.5 u of the run-up (live: 0.2-0.66 u over the floor there, its turn not followed 0.6 s).
    (press: (s, dist, heading err deg, speed) or None, off the floor: (x, y) or None)"""
    b = bot()
    if targets is not None:
        steer0 = b.steer
        b.steer = lambda me, p, act, *a, **k: (targets.append(Vec(p.x, p.y, p.z)), steer0(me, p, act, *a, **k))[1]
    nav = nav_for(run, take)
    pos = Vec(start[0], start[1], Z)
    to = math.atan2(take[1] - pos.y, take[0] - pos.x)
    vel, yaw, t = Vec(2.0 * math.cos(to), 2.0 * math.sin(to), 0.0), LANE, 0.0
    hop_until = None
    carrier_take = b.carrier_take_off(Vec(take[0], take[1], Z), JumpVec(*LAND, take[0], take[1], run[0], run[1])) \
        if carrying else Vec(take[0], take[1], Z)
    while t < secs:
        b.now = 100.0 + t
        act = Action(yaw=yaw)
        b.move_to(PlayerState(1, 0, "b", pos, vel=vel, yaw=yaw, has_flag=carrying), GOAL, act, nav)
        if act.jump:
            err = abs((math.atan2(vel.y, vel.x) - LANE + math.pi) % (2 * math.pi) - math.pi)
            return (t, (pos - carrier_take).flat(), math.degrees(err), vel.flat()), None
        mag = min(1.0, math.hypot(act.forward, act.strafe))
        w = act.yaw + math.atan2(act.strafe, act.forward)
        want = Vec(math.cos(w) * 2.25 * mag, math.sin(w) * 2.25 * mag, 0.0)
        if hop_until is None and (pos - Vec(run[0], run[1], Z)).flat() < 0.5:
            hop_until = t + hop
        if hop_until is None or t >= hop_until:
            vel = vel + (want - vel) * min(1.0, DT / tau)
        pos = Vec(pos.x + vel.x * DT, pos.y + vel.y * DT, Z)
        if not T.ground_ok(pos.x, pos.y, Z + 0.4, drop=1.0):
            return None, (round(pos.x, 2), round(pos.y, 2))
        t += DT
    return None, None


def main():
    fails, n = [], 0
    starts = []
    for r in (1.0, 1.6, 2.2):
        for k in range(12):
            a = k * math.pi / 6
            p = (TAKE_OFF[0] + r * math.cos(a), TAKE_OFF[1] + r * math.sin(a))
            if T.ground_ok(p[0], p[1], Z + 0.4, drop=1.0):
                starts.append(p)
    worst = 0.0
    for tau, hop in ((0.15, 0.0), (0.3, 0.0), (0.15, 0.6), (0.3, 0.6)):
        for p in starts:
            n += 1
            press, off = approach(p, tau, hop=hop)
            where = f"start ({p[0]:.2f}, {p[1]:.2f}), moves {tau:.2f} s late, footing lost {hop:.1f} s"
            if off is not None:
                fails.append(f"{where}: off the floor at {off} before any jump")
            elif press is None:
                fails.append(f"{where}: no jump in 8 s")
            elif press[2] > 35.0 or press[3] < 1.5:
                fails.append(f"{where}: jumped {press[1]:.2f} u from its take-off moving {press[3]:.1f} u/s, "
                             f"{press[2]:.0f} deg off the run (want 1.5 u/s or more, within 35 deg)")
            else:
                worst = max(worst, press[2])
    # 2: the live pass, 0.32 u from the run-up, moving east (VaporRaven at 504.26 s)
    b = bot()
    nav = nav_for(RUNUP, TAKE_OFF)
    b.now = 100.0
    pos = Vec(RUNUP[0] + 0.16, RUNUP[1] - 0.28, Z)
    b.lined_up = True                                        # (behind it already: only the count is tested)
    b.runup_key, b.runup_done, b.runup_t0 = (round(TAKE_OFF[0], 2), round(TAKE_OFF[1], 2)), False, 100.0
    b.move_to(PlayerState(1, 0, "b", pos, vel=Vec(2.0, 0.3, 0.0), has_flag=True), GOAL, Action(yaw=0.0), nav)
    if not b.runup_done:
        fails.append("the carrier passing 0.32 u from the run-up did not count it (want it counted within 0.35 u)")
    # 3: carrying nothing, from the west: its first target is the run-up itself
    targets = []
    approach((TAKE_OFF[0] - 2.0, TAKE_OFF[1]), 0.15, carrying=False, secs=0.1, targets=targets)
    if not targets or (targets[0] - Vec(*RUNUP, Z)).flat() > 0.01:
        fails.append(f"carrying nothing, its first target {targets[:1]} (want straight at the run-up {RUNUP})")
    # 4: the run turned round (its run-up on the rim, the floor ahead of it): no line-up point off the floor
    targets = []
    approach((TAKE_OFF[0] - 1.5, TAKE_OFF[1] + 1.0), 0.15, run=TAKE_OFF, take=RUNUP, secs=3.0, targets=targets)
    bad = [q for q in targets if not T.ground_ok(q.x, q.y, Z + 0.4, drop=1.0)
           and (q - Vec(*LAND)).flat() > 0.01]                  # (the landing: its steer once the jump is pressed)
    if bad:
        fails.append(f"the run with no floor behind its run-up: steered at {bad[0]} off the floor")
    if fails:
        sys.exit(f"FAIL ({len(fails)})\n" + "\n".join(fails))
    print(f"runup lineup OK ({n} approaches from {len(starts)} starts: every jump within 35 deg of the run, worst "
          f"{worst:.0f}; a 0.32 u pass counts; nothing carried: straight at the run-up)")


if __name__ == "__main__":
    main()
