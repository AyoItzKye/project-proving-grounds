"""People's walks under a lone floor win (brain/terrain.py walked_under). The report 20261105-161417 (live
Boneyard B28, 436.8 s): Elites kept getting stuck on this staircase. The level data had a flat -9.0 slab over
x 254.5-255.5, y 54-55.5 where people (and every bot) stood at -10.0: the nav put bots on the slab and sent them up a
route into the stair's side (spells 9-22 s at (253.3-255.6, 53.3-54.8), B27 / B28).

1. Boneyard (the variant): the nav has a floor within 0.3 of -10.0 under the slab, and the stair's own treads
   (253.7, 53.5, -9.7) and (257.6, 55.8, -7.9) keep theirs.
2. A crate (a 1 u box on the ground) with a person walked beside it, in its edge cell: the crate top stays.

usage: python -I test_walked_under.py      -> "walked_under OK (...)"
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import walked_under  # noqa: E402


def near(T, x, y, z, tol=0.3):
    j, i = T._cell(Vec(x, y, z))
    col = T.floors[:, j, i]
    return bool((np.abs(col[np.isfinite(col)] - z) <= tol).any())


def main():
    fails = []
    T = terrain(get_map("reach_70_boneyard/variants/v86d95e85"))
    under = [(x, y) for x in (254.6, 254.9, 255.2) for y in (54.2, 54.6, 55.0) if near(T, x, y, -10.0)]
    if len(under) < 6:
        fails.append(f"1. ground at -10 under the slab in {len(under)} of 9 spots (want 6+)")
    for x, y, z in ((253.7, 53.5, -9.7), (257.6, 55.8, -7.9)):
        if not near(T, x, y, z):
            fails.append(f"1. the stair's tread at ({x}, {y}, {z}) lost")
    # 2. a 1 u crate over x 2-3, y 2-3 on ground at 0; a person stood at the crate's edge cell (in its 0.25 cell)
    fl = np.full((2, 20, 20), np.nan)
    fl[0] = 0.0
    fl[0, 8:12, 8:12] = 1.0
    walked = {(round(2.0 / 0.25), round(2.0 / 0.25), 0)}
    n = walked_under(fl, 0.0, 0.0, 0.25, walked)
    if n or not (fl[0, 8:12, 8:12] == 1.0).all():
        fails.append(f"2. a crate top beside a walk was taken ({n} cells)")
    if fails:
        sys.exit("walked_under FAIL: " + "; ".join(fails))
    print(f"walked_under OK (Boneyard ground under the slab at {len(under)} of 9 spots)")


if __name__ == "__main__":
    main()
