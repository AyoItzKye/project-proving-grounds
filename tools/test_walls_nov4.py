"""Halo 4 ca_blood_cavern Infection playtests, Nov 4 (bots kept getting stuck on this wall, F9 at 143 s): 187 wall
pushes of 2 s or more, 824 s, in the two games; about 130 within 1.5 u of one spot, the ledge at (-8.1, 6.4, 2.75).
1. the lid rule (brain/terrain.py _build_nav): the nav's way from that ledge to the hold below (-15.8, 12.7) dropped
   2.6 u at once into the floor under the ledge (the column has the ledge's own floor at 2.69 over it). Without the
   rule the way drops through the floor (the live frames); with it it walks round to a real drop. No floor people
   walked is cut off (priced, not removed)
2. Halo 4 reports the body 0.39 u over its floor, as H2A does (tools/ground_offset.py); Bot.feet takes it off for the
   level-data probes. On flat floor the nav's next point read as a step down (the edge guard skipped, 52% of Halo 4's
   walking ticks): not any more; Halo 3's position is the feet (unchanged)

usage: python -I test_walls_nov4.py      -> "walls nov4 OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np  # noqa: E402

from brain import maps  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import Terrain  # noqa: E402

LEDGE, HOLD = Vec(-8.08, 6.42, 2.75), Vec(-15.8, 12.7, 0.14)


def drops_through(T, way, start):
    """a step of the way > 0.5 u down into a column that has floor at about the height it left"""
    prev = start
    for q in way:
        if q.z < prev.z - 0.5:
            j, i = T._cell(q)
            if any(q.z + 0.3 < float(f) <= prev.z + 0.18 for f in T.lz[:, j, i] if np.isfinite(f)):
                return True
        prev = q
    return False


def main():
    fails = []
    m = maps.get_map("h4_ca_blood_cavern")
    was = Terrain.lid_rule
    try:
        Terrain.lid_rule = False
        old = maps._build(m, None)
        Terrain.lid_rule = True
        new = maps._build(m, None)
    finally:
        Terrain.lid_rule = was
    if not drops_through(old, old.path_ahead(LEDGE, HOLD, n=12), LEDGE):
        fails.append("without the lid rule the way no longer drops through the ledge (the live bug did not replay)")
    way = new.path_ahead(LEDGE, HOLD, n=60)
    if drops_through(new, way, LEDGE):
        fails.append(f"the way from the ledge still drops through its floor: {[(round(q.x, 2), round(q.y, 2), round(q.z, 2)) for q in way[:6]]}")
    if not new.reaches(LEDGE, HOLD):
        fails.append("the hold below is no longer reached from the ledge")
    if int(old.reach.sum()) != int(new.reach.sum()):
        fails.append(f"reachable floor changed: {int(old.reach.sum())} -> {int(new.reach.sum())}")

    # 2. flat floor on the same level (3.55), the nav's next point 0.8 u on, the body read 0.39 over the floor
    b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), m, random.Random(1))
    pos, wp = Vec(-7.08, 3.67, 3.55 + 0.39), Vec(-7.33, 2.92, 3.55)
    if abs(b.feet(PlayerState(1, 0, "b1", pos)).z - 3.55) > 0.02:
        fails.append(f"Halo 4 feet: {b.feet(PlayerState(1, 0, 'b1', pos)).z} (want 3.55)")
    me = PlayerState(1, 0, "b1", pos)
    act = Action()
    act.yaw = math.atan2(wp.y - pos.y, wp.x - pos.x)
    act.forward, act.strafe = 1.0, 0.0
    b.wp, b.nav_cmd, b.notes = wp, (1.0, 0.0), []
    b.edge_guard(10.0, me, act)
    if "step down" in b.notes:
        fails.append(f"Halo 4 flat floor read as a step down: {b.notes}")
    h3 = Bot(2, 0, make_profile("top", "objector", random.Random(2)), maps.get_map("h3_deadlock"), random.Random(2))
    q = Vec(-10.6, 3.8, 13.7)
    if h3.feet(PlayerState(2, 0, "b2", q)) is not q and h3.feet(PlayerState(2, 0, "b2", q)).z != q.z:
        fails.append("Halo 3's position moved off its feet")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("walls nov4 OK")


if __name__ == "__main__":
    main()
