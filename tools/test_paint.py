"""Hand painting, roofless views and the LiDAR Roombas (the player: "these bots are just too dumb ... they just plant
their faces in the walls", "the 'paint' feature and drive and fly mesh", "a roofless view of the maps", "two types of
fly meshes One low altitude ... and high altitude"). Checks:
1. tools/paint.py: cells snapped to the floor under the cut, one per spot and floor, saved heights kept, bad names out
2. tools/roofless.py: levels from floors, a roof hides the floor only in the top view
3. Terrain.apply_paint on Rat's Nest (h3_armory): a block band across the middle corridor lengthens the flag-to-flag
   walk; painted high air routes a pilot along it and low air is separate; painted drive cells join the vehicles'
   ground
4. tools/lidar.py selftest, with a Roomba held by a wall it cannot see (no level data): it gives that goal up

usage: python -I test_paint.py      -> "paint OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import lidar  # noqa: E402
import paint  # noqa: E402
import roofless  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


def walk_len(T, a, b):
    p, n = a, 0.0
    for _ in range(400):
        w = T.nav(p, b)
        q = Vec(w.x, w.y, w.z)
        if (q - p).length() < 0.05:
            break
        n, p = n + (q - p).length(), q
    return n, (p - b).length()


def main():
    fails = []
    paint.selftest()
    roofless.selftest()
    m = get_map("h3_armory")
    T = terrain(m)
    red, blue = m["flags"][0], m["flags"][1]
    before, _ = walk_len(T, red, blue)
    band = [[x * 0.5, y * 0.5, z] for x in range(0, 29) for y in range(-2, 3) for z in (-9.6, -9.0, -8.2, -7.6, -6.7)]
    high = [[-14.0, y * 0.5, -9.0] for y in range(-50, 51)]
    drive = [[x * 0.5, -20.0, -8.3] for x in range(0, 20)]
    T.apply_paint({"block": band, "fly_high": high, "drive_m": drive})
    after, left = walk_len(T, red, blue)
    if not (after > before + 2.0 and left < 0.5):
        fails.append(f"a block band across the middle: walk {before:.1f} -> {after:.1f} (end {left:.1f} off)")
    f = T.fly_way(Vec(-14, -20, -2), Vec(-14, 20, -2), "high")
    if f is None or abs(f.x + 14) > 0.01 or not -17.5 <= f.y <= -16.5:
        fails.append(f"high air: next point {f} (want 6 cells along the strip, about (-14, -17))")
    if T.fly_way(Vec(-14, -20, -2), Vec(-14, 20, -2), "low") is not None:
        fails.append("low air answered with nothing painted low")
    if T.fly_way(Vec(10, 0, -2), Vec(-14, 20, -2), "high") is not None:
        fails.append("high air answered for a start far off the painted air")
    if not T.drive_paint:
        fails.append("no painted drive cell on the floor")
    else:
        T.vnav(Vec(0, -20, -8.3), Vec(9, -20, -8.3))
        if not all(T.vroomy[l, j, i] or not T.lwalk[l, j, i] for l, j, i in T.drive_paint):
            fails.append("painted drive cells not in the vehicles' ground")
    lidar.selftest()
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("paint OK")


if __name__ == "__main__":
    main()
