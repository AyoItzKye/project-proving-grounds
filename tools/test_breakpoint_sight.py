"""Breakpoint (reach_dlc_invasion): sight from the tower ledge to the bridge below. The exported level has no ground in the
gap between them, only a thin sloped strip 16-26 u overhead, and the sight rays read the air under it as inside a hill:
bots on the bridge never saw a person on the ledge while his DMR hit them (BTB 20261105-192945, 171-213 s; ported from
the collaborator's fork, 1aa3339). maps/reach_dlc_invasion/sight_open.json opens it for
sight and shots (Terrain.set_open_under); walking, falls and aircraft keep the old floor; nothing else opens.

usage: python -I test_breakpoint_sight.py      -> "breakpoint sight OK"   (SKIP without the map's heightmap)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import maps  # noqa: E402
from brain.core import Vec  # noqa: E402

PAIRS = [(Vec(-2.47, 19.99, -3.74), Vec(11.46, 23.06, -8.65)), (Vec(-2.47, 19.99, -3.74), Vec(13.03, 17.63, -8.04)),
         (Vec(-2.47, 19.99, -3.74), Vec(19.62, 4.82, -7.37)), (Vec(-1.80, 19.38, -4.06), Vec(23.41, -3.21, -7.08))]


def main():
    if not os.path.exists(os.path.join(HERE, "..", "maps", "reach_dlc_invasion", "heightmap.npz")):
        print("breakpoint sight SKIP (no heightmap)")
        return
    T = maps.terrain(maps.get_map("reach_dlc_invasion"))
    opened = [T.sees(b, a) or T.sees(a, b) for a, b in PAIRS]
    keep = T.ray_low
    T.ray_low = None                                    # (the old ground: what the bots had)
    closed = [T.sees(b, a) or T.sees(a, b) for a, b in PAIRS]
    T.ray_low = keep
    assert all(opened), opened
    assert not any(closed), ("the fix is not what opens them", closed)
    changed = np.isfinite(T.low) & ~np.isfinite(T.ray_low)
    assert int(changed.sum()) > 100, int(changed.sum())
    assert not (changed & np.isfinite(T.floors).any(axis=0)).any(), "a cell with a floor was opened"
    ys, xs = np.nonzero(changed)
    X, Y = T.x0 + (xs + 0.5) * T.cell, T.y0 + (ys + 0.5) * T.cell
    assert ((X > 1.0) & (X < 7.5) & (Y > 10.0) & (Y < 24.0)).all(), "opened outside the strip's box"
    a, b = Vec(8.0, 21.0, -11.7), Vec(8.0, 13.0, -11.7)  # a line under the real ground beside the strip: still shut
    assert not T.sees(a, b)
    other = maps.terrain(maps.get_map("reach_35_island"))
    assert getattr(other, "ray_low", None) is None      # (no other map is touched)
    print(f"breakpoint sight OK ({int(changed.sum())} cells opened, {len(PAIRS)} lines now open, shut before)")


if __name__ == "__main__":
    main()
