"""Handrails: on Countdown, drops off a ledge through a waist-high rail cost terrain.RAIL_COST extra in the nav (never
forbidden: that cut floors off), and the waist ray of Terrain.clearance sees the rail from the walkway.

usage: python -I test_rails.py      -> "rails OK"
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import RAIL_COST  # noqa: E402


def main():
    fails = []
    T = terrain(get_map("reach_45_launch_station"))
    g = T.graph.tocoo()
    over = g.data > RAIL_COST
    if not over.any():
        sys.exit("FAIL\nno drop over a rail costs extra on Countdown")
    # the rail as the walkway sees it: from 0.6 u back from a rail drop, facing it, the clearance stops short
    L, H, W = T.L, T.nh, T.nw
    seen, tried = 0, 0
    for a, b in list(zip(g.row[over], g.col[over]))[:200]:
        la, ja, ia = np.unravel_index(a, (L, H, W))
        lb, jb, ib = np.unravel_index(b, (L, H, W))
        yaw = math.atan2(jb - ja, ib - ia)
        cx, cy = T.x0 + (ia + 0.5) * T.cell * T.nstep, T.y0 + (ja + 0.5) * T.cell * T.nstep
        p = Vec(cx - math.cos(yaw) * 0.6, cy - math.sin(yaw) * 0.6, float(T.lz[la, ja, ia]))
        tried += 1
        seen += T.clearance(p, yaw, 3.0) < 1.5
    if seen < 0.5 * tried:
        fails.append(f"the waist ray saw {seen} of {tried} rails from the walkway")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"rails OK ({int(over.sum())} drops over rails on Countdown; the waist ray sees {seen} of {tried})")


if __name__ == "__main__":
    main()
