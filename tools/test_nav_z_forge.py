"""Sim walkers stay on a Forge canvas's floor and climb the stairs the nav sends them up (coordinator's mode matrix:
h4_ca_warhouse CTF bots in the unstuck wiggle 30% of the time). logs/tmp/fall_in.py: 16 sim falls in 120 s from the
canvas (z 0-2.4) to the level's floor 15 u under it, each on a plain step to the next waypoint at about the same
height: Terrain.nav_z fell back to the cell's lowest floor whenever the climb rule (MAX_RISE) missed the step up (a
stair riser, STAIR_RISE on these maps), and the bots then stood at people's links up 16-27 u. And can_step judged by
the climb rule alone, so the stairs the nav's graph climbs were walls to the sim.

1. the live-sim fall frames: nav_z from the bot's height gives the canvas floor (within 0.5 u), not the floor 15 u down
2. nav_z with no floor in the climb rule's reach and no height given still gives the lowest walkable floor (unchanged)
3. can_step follows the graph: every one of 200 graph edges between neighbour cells that climbs more than MAX_RISE is a
   step the sim can take

usage: python -I test_nav_z_forge.py      -> "nav_z forge OK (...)"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import MAX_RISE, NAV_CELL  # noqa: E402

T = terrain(get_map("h4_ca_warhouse"))
FALLS = [(Vec(-7.662, -4.283, 0.0), (-7.6425, -4.3568)), (Vec(-1.2438, 7.7361, 0.6875), (-1.193, 7.6787)),
         (Vec(2.908, -0.5452, 0.0859), (2.8968, -0.4693)), (Vec(-4.2586, -7.0343, -0.3), (-4.2763, -7.0491)),
         (Vec(-26.0018, -17.9146, 2.0885), (-25.9422, -17.8664))]


def main():
    fails = []
    for p, (x, y) in FALLS:
        z = T.nav_z(x, y, p.z)
        if abs(z - p.z) > 0.5:
            fails.append(f"step from {p} to ({x}, {y}): nav_z {z:.2f} (want the canvas floor, about {p.z:.2f})")
    x, y = FALLS[0][1]
    j, i = T._cell(Vec(x, y))
    low = next(float(T.lz[k, j, i]) for k in range(T.L) if T.lwalk[k, j, i])
    if abs(T.nav_z(x, y) - low) > 1e-6:
        fails.append(f"nav_z with no height: {T.nav_z(x, y):.2f} (want the lowest walkable floor {low:.2f})")
    g = T.graph.tocoo()
    N = T.nh * T.nw
    la, ra = np.divmod(g.row, N)
    lb, rb = np.divmod(g.col, N)
    ja, ia = np.divmod(ra, T.nw)
    jb, ib = np.divmod(rb, T.nw)
    za, zb = T.lz[la, ja, ia], T.lz[lb, jb, ib]
    pick = np.nonzero((np.abs(ja - jb) <= 1) & (np.abs(ia - ib) <= 1) & (zb - za > MAX_RISE + 0.01) & (zb - za < 0.4))[0][:200]
    bad = 0
    for k in pick:
        a = Vec(T.x0 + (ia[k] + 0.5) * NAV_CELL, T.y0 + (ja[k] + 0.5) * NAV_CELL, float(za[k]))
        b = Vec(T.x0 + (ib[k] + 0.5) * NAV_CELL, T.y0 + (jb[k] + 0.5) * NAV_CELL, float(zb[k]))
        if T._node(a)[0] == la[k] and not T.can_step(a, b):
            bad += 1
    if not len(pick) or bad:
        fails.append(f"graph steps up over MAX_RISE: {bad} of {len(pick)} refused by can_step (want none, and some found)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"nav_z forge OK ({len(FALLS)} fall frames stay on the canvas; {len(pick)} stair steps up walkable)")


if __name__ == "__main__":
    main()
