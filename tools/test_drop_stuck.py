"""A walker stuck stepping down to the nav's next point reports that landing as the stuck spot, at the landing's own
height, not the floor it stands on (the player Avalanche CTF; live, logs/tmp/perch.py on
trace_h3_sidewinder_20261031-015423: 25+ walker stalls at (25.6, -30.6, -0.8) by the red flag and its mirror (-28.4,
-30.6) by the blue one, "step down" notes, the nav's next point (25.34, -30.49) on a 0.25 u strip at -2.4 under a beam,
the way on a drop to the ground at -4.4; no person walked that strip. Four stuck spots had been learned round it at
-0.8, the level the bots stood on: their cost never touched the drop, so the nav kept it. With 2ed0919 the live game of
learned (25.3, -30.5, -2.4) itself, maps/h3_sidewinder/nav_learned.json).

The stall is driven at that frame with the nav's step down given (b.wp, the strip's landing), whatever the map's nav and
learned spots are now: Terrain.learn_stuck's calls are recorded, not the map changed.

1. two bots stuck there twice each report the landing, its height -2.4 (the old code reported their own floor, -0.8)
2. a stall on the flat (the next point at its own height) still reports the spot ahead on its own floor

usage: python -I test_drop_stuck.py      -> "drop stuck OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
PERCH = Vec(25.6, -30.6, -0.78)          # the live stalls (logs/tmp/stalls.py)
LANDING = Vec(25.34, -30.49, -2.40)      # the nav's next point there (logs/tmp/perch_nav.py)


def stalls(wp):
    """Two bots, two stalls each, pushing at wp from PERCH: the heights unstuck reported to learn_stuck."""
    calls = []
    real = T.learn_stuck
    T.learn_stuck = lambda p, sure=False, who=None: calls.append(p)
    try:
        t = 100.0
        for bid in (12, 5):
            b = Bot(bid, 0, make_profile("top", "rusher", random.Random(bid)), M, rng=random.Random(bid))
            b._terrain, b.goal = T, ("vehicle", 1)
            me = PlayerState(bid, 0, "bot", PERCH, alive=True)
            for _ in range(2):                       # two stalls each, the wiggle's time between
                b.wp = wp
                for _ in range(60):
                    t += 1 / 30
                    b.now, b.notes, b.planned_jump = t, [], False
                    act = Action(yaw=math.atan2(wp.y - PERCH.y, wp.x - PERCH.x))
                    act.forward = 1.0
                    b.unstuck(t, me, act, Snapshot(t, [me]))
                t += 1.5
    finally:
        T.learn_stuck = real
    return calls


def main():
    fails = []
    down = stalls(LANDING)
    if not down or any(abs(p.z - LANDING.z) > 0.1 or (p - LANDING).flat() > 0.1 for p in down):
        fails.append(f"stuck stepping down: reported {[(round(p.x, 2), round(p.y, 2), round(p.z, 2)) for p in down]} "
                     f"(want the landing {LANDING} each time)")
    flat = stalls(Vec(25.1, -30.6, -0.78))
    if not flat or any(abs(p.z - PERCH.z) > 0.1 for p in flat):
        fails.append(f"stuck on the flat: reported {[(round(p.x, 2), round(p.y, 2), round(p.z, 2)) for p in flat]} "
                     f"(want the spot ahead on its own floor)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"drop stuck OK ({len(down)} reports at the landing's height {LANDING.z}; on the flat {len(flat)} on its own floor)")


if __name__ == "__main__":
    main()
