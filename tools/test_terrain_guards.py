"""Terrain guards: no line of sight to a NaN position (a NaN belief failed a whole brain tick, live Spire game 6), the edge
guard flying a long planned drop to its landing, and a carrier's safe nav (Terrain.nav safe=True): round people's big
drops while another way exists, else still the drop (Spire's top has no way down under 34 u).

usage: python -I test_terrain_guards.py      -> "terrain guards OK"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def main():
    testdata.need_lidar("h2a_ca_ascension", "reach_35_island", "reach_70_boneyard")
    fails = []
    m = get_map("reach_35_island")
    T = terrain(m)
    a = Vec(-150.0, -370.0, -55.0)
    for bad in (Vec(math.nan, -370.0, -55.0), Vec(-151.0, -370.0, math.inf)):
        try:
            if T.los(a, bad) or T.los(bad, a):
                fails.append(f"los to {bad}: want False")
        except ValueError as e:
            fails.append(f"los to {bad} raised {e}")
    if not T.los(a, Vec(-151.0, -370.0, -55.0)):
        fails.append("los 1 u apart on open ground: want True")
    # a man 2 u straight overhead stands on a floor: no shot up through it, whatever the heightmap holds; nor down
    # through the shooter's own floor
    above = Vec(a.x + 0.5, a.y + 1.0, a.z + 2.0)
    if T.los(a, above) or T.los(above, a):
        fails.append("los to a man 2 u overhead: want False (the floor he stands on)")
    deliver = invasion.layout(m["objects"])["phases"][3][0]
    # Spire's top: every way down is a big drop, so the carrier still takes the people's 37 u one (link 121)
    east = Vec(-169.9, -400.6, -24.08)
    if T._field(deliver, human=True, safe=True)[T._node(east)] < T.BARRIER_COST:
        fails.append("Spire top: a carrier's safe way down under the big-drop cost (the map has none)")
    p = east
    for _ in range(60):
        w = T.nav(p, deliver, human=True, safe=True)
        if type(w).__name__ == "JumpVec":
            break
        d = math.hypot(w.x - p.x, w.y - p.y)
        p = Vec(p.x + (w.x - p.x) * min(1, 0.5 / max(d, 1e-6)), p.y + (w.y - p.y) * min(1, 0.5 / max(d, 1e-6)), w.z)
    # (any of the big drops: drop 121 until; with people's hop runs no longer read as jumps, the drop down the lift
    # shaft by the landing, the one someone went down and lived)
    if type(w).__name__ != "JumpVec" or w.z > -50.0:
        fails.append(f"Spire top: the carrier with no safe way down did not fall back to a drop ({w})")
    # with a lower threshold the plateau's 0.9 u hop to the ramp foot (link 142 back) is a big drop: a carrier walks the
    # ramp (walked floor pramp27) instead; everyone else still hops
    plateau, foot = Vec(-175.6, -405.0, -23.4), Vec(-172.3, -405.4, -24.08)
    T.RISKY_DROP, T._risky_memo = 0.5, {}
    T._hfields.clear()
    try:
        safe = T.nav(plateau, foot, human=True, safe=True)
        plain = T.nav(plateau, foot, human=True)
    finally:
        del T.RISKY_DROP
        T._risky_memo = {}
        T._hfields.clear()
    if type(safe).__name__ == "JumpVec":
        fails.append(f"plateau to the ramp foot with a walk there: the carrier still hops ({safe})")
    if type(plain).__name__ != "JumpVec":
        fails.append(f"plateau to the ramp foot, not carrying: want the hop, got {plain}")
    # a planned jump off the 37 u drop flies on to its landing all the way down (live: after 1.2 s the edge guard
    # steered the carriers back under the take-off onto a ledge; the fall killed all four)
    import random
    from brain.bot import Action, Bot
    from brain.core import PlayerState
    from brain.profiles import make_profile
    b = Bot(1, 0, make_profile("top", "objector", random.Random(3)), m, rng=random.Random(3))
    b.notes, b.planned_jump, b.jump_land = [], True, Vec(-167.26, -414.65, -61.17)
    b.edge_guard(10.0, PlayerState(1, 0, "c", Vec(-166.81, -406.8, -24.2)), Action())
    b.notes, b.planned_jump = [], False
    b.edge_guard(12.5, PlayerState(1, 0, "c", Vec(-167.6, -409.2, -40.0)), Action())
    if "air steer back" in b.notes or b.jump_until < 14.0:
        fails.append(f"37 u drop: 2.5 s into the fall the guard steers back ({b.notes}, jump until {b.jump_until:.1f})")
    # the live sequence (game 10): move_to marks a person's run-up and take-off final steps (final_step_until now + 0.3)
    # on the same tick it jumps; the window must still be set, and on the slope the bot lands on first (floor 0.3 under
    # it) it keeps going for the landing, not back to the take-off. Old code: no window, "air steer back" 0.3 s after
    # the nav stopped offering the jump, and the carrier fell onto the ledge under the take-off
    b2 = Bot(2, 0, make_profile("top", "objector", random.Random(4)), m, rng=random.Random(4))
    land = Vec(-167.26, -414.65, -61.17)
    for t, pos, planned in ((684.27, (-166.89, -406.9, -23.9), True), (684.9, (-166.98, -408.02, -23.7), False),
                            (685.17, (-167.0, -408.4, -24.14), False), (685.46, (-167.03, -408.72, -24.98), False),
                            (686.2, (-167.18, -409.16, -28.27), False)):
        b2.notes, b2.planned_jump = [], planned
        if planned:
            b2.jump_land = land
        b2.final_step_until = t + 0.3 if t < 685.2 else b2.__dict__.get("final_step_until", 0.0)
        act = Action()
        act.forward, act.strafe, act.yaw = -1.0, 0.0, -math.pi / 2     # move_to's steer back to the take-off (north)
        me2 = PlayerState(2, 0, "c", Vec(*pos))
        b2.edge_guard(t, me2, act)
        south = -(act.forward * math.sin(act.yaw) + act.strafe * math.cos(act.yaw))   # the command's world y, negated
        if "air steer back" in b2.notes or south < 0.3:
            fails.append(f"live drop sequence at {t}: {b2.notes}, command south {south:.2f} (want on to the landing)")
            break
    # standing still on floor the level data lacks is ground (Boneyard, live: two bots stood 418 s and 81 s at z
    # -5.25 off their spawn platform's edge, "air steer back" every tick pushing them at the last mapped ground and
    # cancelling every jump the unstuck wiggle asked for)
    b3 = Bot(3, 1, make_profile("top", "objector", random.Random(5)), get_map("reach_70_boneyard"), rng=random.Random(5))
    b3.last_ground = Vec(266.97, 92.77, -4.88)
    spot = PlayerState(3, 1, "w", Vec(267.25, 93.21, -5.25))
    back = jumps = 0
    for k in range(60):                       # 2 s there, the wiggle asking for a jump west, onto the platform
        b3.notes = []
        act = Action()
        act.forward, act.strafe, act.yaw, act.jump = 1.0, 0.0, math.pi, True
        b3.edge_guard(20.0 + k / 30, spot, act)
        if k >= 30:
            back += "air steer back" in b3.notes
            jumps += bool(act.jump)
    if back or not jumps:
        fails.append(f"resting 1-2 s on floor the data lacks: air steer back on {back} of 30 ticks, jumps {jumps} "
                     f"(want none and the wiggle's jumps)")
    # H2A reports a body H2A_FEET over its floor: walking flat floor (Zenith) is no step down (the guard was skipped on
    # 20,044 of ~33,000 walking ticks), and the nav's real 0.51 u ledge is one
    zen = get_map("h2a_ca_ascension")
    for label, feet, wp, want in (("flat floor", Vec(19.44, -1.38, 0.003), Vec(20.44, -1.38, 0.003), False),
                                  ("a 0.51 u ledge", Vec(0.44, -27.88, 4.667), Vec(1.44, -27.88, 4.159), True)):
        b4 = Bot(4, 0, make_profile("top", "objector", random.Random(6)), zen, rng=random.Random(6))
        b4.notes, b4.wp = [], wp
        act = Action()
        act.forward, act.strafe, act.yaw = 1.0, 0.0, math.atan2(wp.y - feet.y, wp.x - feet.x)
        b4.edge_guard(30.0, PlayerState(4, 0, "z", feet + Vec(0, 0, 0.38)), act)
        if ("step down" in b4.notes) != want:
            fails.append(f"H2A {label}: step down {'missing' if want else 'read'} (notes {b4.notes})")
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print("terrain guards OK")


if __name__ == "__main__":
    main()
