"""The LiDAR Simulator starts its bots inside a Forge layout's area (GitHub #10, "Bots spawn outside Forge World Creations
while in LiDAR SIM"): for every map variant here, each spawn the simulator would use lies inside the variant's nav window
and on reachable floor; a base map keeps its own spawns.

usage: python -I tools/test_sim_spawns.py      -> "sim spawns OK (...)"
"""
import glob
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.maps import get_map, terrain  # noqa: E402


def sim_spawns(m, T):
    """The simulator's spawn rule (tools/lidar_sim.py run_map), kept in step by the check below."""
    wx0, wy0, wx1, wy1 = getattr(T, "window", (-1e9, -1e9, 1e9, 1e9))
    inside = lambda p: wx0 + 1 <= p.x <= wx1 - 1 and wy0 + 1 <= p.y <= wy1 - 1
    sp = [T._center(*T._reachable_node(*T._node(p), p.z)) for mode in m["spawns"].values() for team in mode.values()
          for p in team if inside(p)]
    sp = [(c.x, c.y, c.z) for c in sp if not math.isnan(c.z)]
    if not sp:
        cells = np.argwhere(T.lwalk & T.reach)
        mid = np.array([T.lz.shape[1] / 2, T.lz.shape[2] / 2])
        picks = cells[np.argsort(np.abs(cells[:, 1:] - mid).sum(axis=1))[:16]]
        sp = [(c.x, c.y, c.z) for c in (T._center(*map(int, k)) for k in picks)]
    return sp


def main():
    src = open(os.path.join(HERE, "lidar_sim.py"), encoding="utf-8").read()
    fails, seen = [], 0
    if "for p in team if inside(p)]" not in src:
        fails.append("tools/lidar_sim.py no longer keeps its spawns inside the nav window")
    roots = (sorted(glob.glob(os.path.join(HERE, "..", "maps", "reach_forge_halo", "variants", "v*")))[:3]   # (Forge
             + sorted(glob.glob(os.path.join(HERE, "..", "maps", "*", "variants", "v*")))[:3])           # World: #10)
    for d in roots:
        name = os.path.relpath(d, os.path.join(HERE, "..", "maps")).replace("\\", "/")
        try:
            m = get_map(name)
            T = terrain(m)
        except Exception:
            continue
        seen += 1
        wx0, wy0, wx1, wy1 = T.window
        for x, y, z in sim_spawns(m, T):
            if not (wx0 + 0.75 <= x <= wx1 - 0.75 and wy0 + 0.75 <= y <= wy1 - 0.75):   # (clamped to its edge: outside)
                fails.append(f"{name}: a spawn at ({x:.1f}, {y:.1f}) outside its window {T.window}")
                break
    if fails:
        print("sim spawns FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print(f"sim spawns OK ({seen} variants)")


if __name__ == "__main__":
    main()
