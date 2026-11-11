"""The LiDAR director covers the play area only (tools/lidar_director.py play_area, PLAY_MARGIN), on Narrows:

1. the hull of every spawn and placed feature: no floor left out (an ordinary map loses nothing)
2. the hull of three points round one base, 5 u margin: the floor far from it is not floor to cover, the base's is
3. no play points: the whole map, as before
And the simulator's --max-real bounds a command-line run again (o.window False), not the window's (True).

usage: python -I test_lidar_play.py      -> "lidar play OK"
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jumpphys as J  # noqa: E402
import lidar  # noqa: E402
import lidar_director as LD  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


class Rec:
    def explored_many(s, x, y, z):
        return np.zeros(len(x), bool)


def want(T, sp, play):
    d = LD.LidarDirector(T, Rec(), sp, play=play)
    d.plan(0.0, {})
    return d


def main():
    fails = []
    m = get_map("h3_chill")
    T = J.prepare(terrain(m))
    sp = [p for mode in m["spawns"].values() for team in mode.values() for p in team]
    sp = [Vec(p.x, p.y, p.z) for p in sp]
    feats = lidar.load_features("h3_chill").get("features", [])
    every = [(p.x, p.y) for p in sp] + [tuple(f["pos"][:2]) for f in feats if len(f.get("pos") or ()) >= 2]
    whole = want(T, sp, ())
    full = want(T, sp, every)
    if int(full.want.sum()) != int(whole.want.sum()):
        fails.append(f"1. spawns and features: {int(full.want.sum())} samples to cover, {int(whole.want.sum())} without")
    base = m["flags"][0]
    tri = [(base.x + 3, base.y), (base.x - 3, base.y + 3), (base.x - 3, base.y - 3)]
    old = LD.PLAY_MARGIN
    LD.PLAY_MARGIN = 5.0
    try:
        small = LD.LidarDirector(T, Rec(), sp, play=tri)
        small.plan(0.0, {})
    finally:
        LD.PLAY_MARGIN = old
    near = np.hypot(small.x - base.x, small.y - base.y)
    if (small.want & (near > 20)).any():
        fails.append("2. floor 20 u from the play area still to cover")
    if not (small.want & (near < 4)).any():
        fails.append("2. the floor inside the play area is not to cover")
    import lidar_sim
    import inspect
    src = inspect.getsource(lidar_sim.run_map)
    if 'ran < o.max_real or getattr(o, "window", True)' not in src:
        fails.append("--max-real: run_map does not bound a command-line run (o.window)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"lidar play OK (Narrows: {int(full.want.sum())} samples, none left out; a 5 u play area round red's base keeps "
          f"{int(small.want.sum())})")


if __name__ == "__main__":
    main()
