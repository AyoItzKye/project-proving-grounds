"""How far a person keeps each vehicle from walls, objects and the ground.

From Data collector files (logs/collect_<map>_<stamp>.jsonl: the person's place and ride each tick) and the map's terrain
(brain/maps.terrain: the level, a Forge layout's pieces), every moving sample in a vehicle (5 a second, his own driving:
over MIN_SPEED) is measured with the aircraft probe the bots use (Terrain.fly_clear): the nearest solid thing round it
(16 headings, flat, at its height for aircraft, 0.8 and 1.4 u over its floor for ground vehicles), how far it is open
along where it goes, the time to reach that at its speed, and an aircraft's height over the floor under it. Per kind:
speeds and the percentiles of each, written as JSON (and a table to stdout).

usage: python -I vehicle_clearance.py <map> <out.json> <collect file> [collect file ...]
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles as V  # noqa: E402
from brain.core import Vec  # noqa: E402

MIN_SPEED = 2.0      # u/s: slower is parking, boarding, a seat tour
RATE = 0.2           # s between measured samples
FAR = 60.0           # u: probes reach this far (a Sabre covers it in about a second)
YAWS = 16


def owner_track(path):
    """[(t, x, y, z, kind, seat)] of the person's rows riding something (column 14 ride: [kind, turret or ""])."""
    out = []
    for line in open(path, encoding="utf-8"):
        if '"p"' not in line:
            continue
        d = json.loads(line)
        me = next((r for r in d["p"] if not r[12]), None)
        if me is not None and len(me) > 14 and me[14] and me[2]:
            out.append((d["t"], me[3], me[4], me[5], me[14][0], me[14][1] or ""))
    return out


def pct(xs, ps=(5, 10, 25, 50, 75, 90)):
    xs = sorted(x for x in xs if x is not None and math.isfinite(x))
    if not xs:
        return {}
    return {f"p{p}": round(xs[min(len(xs) - 1, int(p / 100 * len(xs)))], 2) for p in ps} | {"n": len(xs)}


def wall_dist(T):
    """Per nav cell, the distance (u) to the nearest wall cell of its level (Terrain.near_wall), once per terrain."""
    if getattr(T, "_wall_dist", None) is None:
        import numpy as np
        from scipy import ndimage
        from brain.terrain import NAV_CELL
        T._wall_dist = np.stack([ndimage.distance_transform_edt(~T.near_wall[l]) * NAV_CELL for l in range(T.L)])
    return T._wall_dist


def measure(T, track):
    """Per kind: lists of speed, nearest, ahead, ttc (and height over floor for aircraft)."""
    got = collections.defaultdict(lambda: collections.defaultdict(list))
    last = -1e9
    for k in range(2, len(track) - 2):
        t, x, y, z, kind, seat = track[k]
        if seat or t - last < RATE:
            continue                                   # a gunner's seat does not steer
        a, b = track[k - 2], track[k + 2]
        if a[4] != kind or b[4] != kind or not 0.05 < b[0] - a[0] < 1.0:
            continue
        vx, vy, vz = ((b[i] - a[i]) / (b[0] - a[0]) for i in (1, 2, 3))
        flat = math.hypot(vx, vy)
        if flat < MIN_SPEED:
            continue
        last = t
        sp = V.spec(kind) or {}
        air = sp.get("move") == "air"
        p = Vec(x, y, z)
        over = T.height_over(x, y, z)
        floor = z - over
        if air:
            probe = lambda yaw: T.fly_clear(p, yaw, FAR, dzs=(-0.6, 0.0, 0.8), floor=floor)
        else:
            q = Vec(x, y, floor)
            probe = lambda yaw: T.fly_clear(q, yaw, FAR, dzs=(0.8, 1.4), floor=floor)
        heading = math.atan2(vy, vx)
        g = got[kind]
        g["speed"].append(flat)
        if not air:                                   # the walls the vehicles' ground keeps off (Terrain._build_vnav)
            n = T._node_at(x, y, floor, tol=1.0) if T.inside(x, y) else None
            if n is not None:
                g["wall"].append(float(wall_dist(T)[n]))
        g["nearest"].append(min(probe(heading + 2 * math.pi * i / YAWS) for i in range(YAWS)))
        ahead = probe(heading)
        g["ahead"].append(ahead)
        if ahead < FAR:
            g["ttc"].append(ahead / flat)
        if air:
            g["over_floor"].append(over)
            g["climb"].append(vz)
    return got


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    from brain.maps import get_map, terrain
    T = terrain(get_map(sys.argv[1]))
    got = collections.defaultdict(lambda: collections.defaultdict(list))
    for path in sys.argv[3:]:
        for kind, g in measure(T, owner_track(path)).items():
            for k, xs in g.items():
                got[kind][k] += xs
    out = {kind: {k: pct(xs) for k, xs in g.items()} for kind, g in got.items()}
    json.dump(dict(map=sys.argv[1], files=[os.path.basename(p) for p in sys.argv[3:]], min_speed=MIN_SPEED,
                   far=FAR, kinds=out), open(sys.argv[2], "w", encoding="utf-8"), indent=1)
    for kind, g in sorted(out.items()):
        print(kind, {k: (v.get("p10"), v.get("p50"), v.get("n")) for k, v in g.items()})


if __name__ == "__main__":
    main()
