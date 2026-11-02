"""Floor players walked that the nav lacks (live Spire Invasion: the ramp onto the phase 2 territories' platform, y -397
from x -181.5 at -61.0 up to x -173.3 at -58.8, was walked by bots in three matches but the nav had no way up it:
attackers stood 18 u off for 150 bot-seconds and the nav's way in was a lift to the spire's top and a drop).

From live traces' world rows (4 a second): a position is walked ground when its height is a straight line over +-1 row
(tools/lidar.py's test: vertical acceleration under AIR_ACC, climbing no steeper than STEEP), the player moved 0.5-8 u/s
and no vehicle is within 2 u. Half-unit cells walked by 2+ players, 3+ times, with no walkable nav floor within 0.35 u of
the height, are printed as patches; --add <id> stores them in maps/<map>/moves_review.json as one reviewed floor
(brain/maps.py joins approved floors to the nav).

usage: python -I walked_floor.py <map> <trace.jsonl> [...] [--box x0 x1 y0 y1 z0 z1 [--raw]] [--add id --why text]
"""
import collections
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from lidar import AIR_ACC, STEEP  # noqa: E402

CELL = 0.5


def harvest(paths, raw=False):
    """{(cx, cy, round z): [samples, set of player keys, heights]}"""
    cells = collections.defaultdict(lambda: [0, set(), []])
    for path in paths:
        hist = collections.defaultdict(list)
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if "world" not in r:
                continue
            t = r["t"]
            veh = [(v[2], v[3], v[4]) for v in r.get("vehicles") or []]
            for w in r["world"]:
                h = hist[w[0]]
                if not w[2]:
                    h.clear()
                    continue
                h.append((t, (w[3], w[4], w[5])))
                if len(h) < 3:
                    continue
                del h[:-3]
                (tb, pb), (tc, pc), (ta, pa) = h
                if not (0.15 < tc - tb < 0.4 and 0.15 < ta - tc < 0.4):
                    continue
                acc = 2 * ((pa[2] - pc[2]) / (ta - tc) - (pc[2] - pb[2]) / (tc - tb)) / (ta - tb)
                vz = (pa[2] - pb[2]) / (ta - tb)
                vh = math.dist(pa[:2], pb[:2]) / (ta - tb)
                if not raw and (abs(acc) > AIR_ACC or abs(vz) > vh * STEEP + 0.4 or not 0.5 < vh < 8.0):
                    continue
                if any(math.dist(pc, q) < 2.0 for q in veh):
                    continue
                c = cells[(round(pc[0] / CELL), round(pc[1] / CELL), round(pc[2]))]   # (by height: floors over floors)
                c[0] += 1
                c[1].add((path, w[0]))
                c[2].append(pc[2])
    return cells


def missing(T, cells, box=None, only_box=False):
    """Walked cells with no walkable nav floor at their height; inside box (x0 x1 y0 y1 z0 z1) every walked cell (2+
    samples): the nav's floor there may be cut off by wall bits (Spire's top: the lift's landing and the core ramp's
    side were apart in the nav, 3 u apart in the game)."""
    import numpy as np
    out = []
    for (cx, cy, _), (n, who, zs) in cells.items():
        zs.sort()
        z = zs[len(zs) // 2]
        x, y = cx * CELL, cy * CELL
        if box and box[0] <= x <= box[1] and box[2] <= y <= box[3] and box[4] <= z <= box[5]:
            if n >= 2:
                out.append((x, y, round(z, 2), n, len(who)))
            continue
        if n < 3 or len(who) < 2 or only_box:
            continue
        j, i = T._ij(np.array(x), np.array(y))
        j, i = int(j), int(i)
        if any(T.lwalk[l, j, i] and abs(T.lz[l, j, i] - z) < 0.35 for l in range(T.L)):
            continue
        out.append((x, y, round(z, 2), n, len(who)))
    return out


def patches(pts):
    """Connected groups of cells (8-neighbours, heights within 0.6 u)."""
    left, groups = set(range(len(pts))), []
    while left:
        k = left.pop()
        g, todo = [k], [k]
        while todo:
            a = pts[todo.pop()]
            near = [b for b in left if abs(pts[b][0] - a[0]) <= CELL + 1e-6 and abs(pts[b][1] - a[1]) <= CELL + 1e-6
                    and abs(pts[b][2] - a[2]) < 0.6]
            for b in near:
                left.discard(b)
                g.append(b)
                todo.append(b)
        groups.append([pts[b] for b in g])
    return sorted(groups, key=len, reverse=True)


def main():
    args = sys.argv[1:]
    add = args[args.index("--add") + 1] if "--add" in args else None
    why = args[args.index("--why") + 1] if "--why" in args else ""
    box = [float(v) for v in args[args.index("--box") + 1:args.index("--box") + 7]] if "--box" in args else None
    skip = {k + 1 for k, a in enumerate(args) if a in ("--add", "--why")}
    if box:
        skip |= set(range(args.index("--box") + 1, args.index("--box") + 7))
    pos = [a for k, a in enumerate(args) if not a.startswith("--") and k not in skip]
    name, paths = pos[0], pos[1:]
    from brain.maps import get_map, terrain
    T = terrain(get_map(name))
    pts = missing(T, harvest(paths, "--raw" in args), box, only_box="--raw" in args)   # (raw: air too, the box only)
    groups = [g for g in patches(pts) if len(g) >= 3]
    for g in groups:
        xs, ys, zs = [p[0] for p in g], [p[1] for p in g], [p[2] for p in g]
        print(f"{len(g):4d} cells  x {min(xs)}..{max(xs)}  y {min(ys)}..{max(ys)}  z {min(zs)}..{max(zs)}  "
              f"samples {sum(p[3] for p in g)}  players {max(p[4] for p in g)}")
    if add:
        path = os.path.join(ROOT, "maps", name, "moves_review.json")
        d = json.load(open(path)) if os.path.exists(path) else {"reviews": []}
        d["reviews"] = [r for r in d["reviews"] if r.get("id") != add]
        # each half-unit cell as the nav's cells under it (T.cell 0.25: points 0.5 apart left the nav cells between
        # them floorless, Spire's top)
        offs = [k * T.cell for k in range(-int(CELL / 2 / T.cell), int(CELL / 2 / T.cell) + 1)]
        cells = sorted({(round(p[0] + dx, 3), round(p[1] + dy, 3), p[2]) for g in groups for p in g
                        for dx in offs for dy in offs})
        d["reviews"].append(dict(id=add, kind="floor", ok=True, cells=[list(c) for c in cells],
                                 by="claude", at=time.strftime("%Y-%m-%d %H:%M"), why=why))
        json.dump(d, open(path, "w"), indent=1)
        print(f"added {add}: {sum(len(g) for g in groups)} walked cells, {len(cells)} nav cells")


if __name__ == "__main__":
    main()
