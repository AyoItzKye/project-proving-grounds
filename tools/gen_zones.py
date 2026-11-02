"""Generate maps/<map>/callouts.json for a map without hand-made callouts, from its own data:
landmark zones (bases, roofs, teleporters, power weapons and powerups), side areas (Red side,
Mid, Blue side), the mid and high-ground points, defender holds and attack lanes. Names are
landmark names until the map's community callouts are researched (docs/research/06 did that
for Blood Gulch).

usage: python -I gen_zones.py <map>
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from brain.core import Vec  # noqa: E402
from brain.terrain import Terrain  # noqa: E402

ITEM_NAMES = {"rocket launcher": "Rockets", "sniper rifle": "Sniper", "plasma_cannon": "Fuel rod",
              "powerup super shield": "Overshield", "powerup invisibility": "Camo",
              "shield-invisibility": "Powerup", "flame thrower": "Flamethrower", "shotgun": "Shotgun",
              "rockets": "Rockets", "sniper": "Sniper", "sword": "Sword"}


def circle(c, r, n=12):
    return [[round(c[0] + r * math.cos(2 * math.pi * k / n), 2), round(c[1] + r * math.sin(2 * math.pi * k / n), 2)]
            for k in range(n)]


def clip(poly, a, b):
    """Keep the part of a convex polygon closer to point a than to point b."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    nx, ny = a[0] - b[0], a[1] - b[1]
    side = lambda p: (p[0] - mx) * nx + (p[1] - my) * ny
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t])
    return out


def snap(T, x, y, z=None, reach_from=None, r=6.0):
    """Nearest walkable point (and, if given, reachable from reach_from) within r."""
    best = None
    for rr in np.arange(0, r, 0.25):
        for k in range(max(1, int(rr * 8))):
            a = 2 * math.pi * k / max(1, int(rr * 8))
            p = Vec(x + rr * math.cos(a), y + rr * math.sin(a), z if z is not None else 0.0)
            if not T.walkable(p):
                continue
            q = Vec(p.x, p.y, T.nav_z(p.x, p.y, z))
            if reach_from is not None and not np.isfinite(T._field(reach_from)[T._node(q)]):
                continue
            return q
    return best


def main(name):
    d = os.path.join(ROOT, "maps", name)
    objs = json.load(open(os.path.join(d, "objects.json")))
    spots = {0: [], 1: []}
    for f in objs["netgame_flags"]:
        if f["type"] == "ctf - flag" and f["id"] in spots:
            spots[f["id"]].append(f["pos"])
    if not spots[0] or not spots[1]:
        sys.exit(f"{name}: no CTF flags, cannot place bases")
    # Halo 3 maps place several flags per team (symmetric and asymmetric setups): the bases are
    # the red / blue pair farthest apart
    red, blue = max(((a, b) for a in spots[0] for b in spots[1]), key=lambda ab: math.dist(ab[0][:2], ab[1][:2]))
    T = Terrain(os.path.join(d, "heightmap.npz"), [])
    xmin, ymin = T.x0, T.y0
    xmax, ymax = T.x0 + T.w * T.cell, T.y0 + T.h * T.cell
    zones = {}

    # bases (inside, below roof height) and roofs if the base has walkable ground above the flag
    roof_z = max(red[2], blue[2]) + 2.0
    for team, (fname, f) in enumerate((("Red", red), ("Blue", blue))):
        zones[f"{fname} base"] = {"poly": circle(f, 5.0), "side": fname.lower(), "priority": 40,
                                 "full": f"{fname} flag and the area around it", "aka": [fname.lower()],
                                 "area": False, "zmax": f[2] + 1.2}
        j, i = T._cell(Vec(f[0], f[1]))
        hi = T.lz[1][max(0, j - 12):j + 12, max(0, i - 12):i + 12]
        if np.isfinite(hi).any():
            top = float(np.nanmax(hi))
            roof_z = min(roof_z, top) if team else top
            zones[f"{fname} top"] = {"poly": circle(f, 6.0), "side": fname.lower(), "priority": 35,
                                    "full": f"on top of the {fname.lower()} base", "aka": [], "area": False,
                                    "zmin": f[2] + 1.2}

    # teleporters, by the nearer base
    tele = [f for f in objs["netgame_flags"] if f["type"] == "teleport from"]
    for f in tele:
        p = f["pos"]
        side = "Red" if math.dist(p[:2], red[:2]) < math.dist(p[:2], blue[:2]) else "Blue"
        n = f"{side} tele"
        k = 2
        while n in zones:
            n, k = f"{side} tele {k}", k + 1
        zones[n] = {"poly": circle(p, 2.5, 8), "side": side.lower(), "priority": 30, "full": "teleporter entrance",
                    "aka": ["port", "portal"], "area": False}

    # power weapons and powerups
    for e in objs["equipment"]:
        key = e["item"].split("\\")[-1]
        if key not in ITEM_NAMES:
            continue
        p = e["pos"]
        n = ITEM_NAMES[key]
        if n in zones or sum(ITEM_NAMES.get(x["item"].split("\\")[-1]) == n for x in objs["equipment"]) > 1:
            side = "Red" if math.dist(p[:2], red[:2]) < math.dist(p[:2], blue[:2]) else "Blue"
            n = f"{side} {n.lower()}"
        if n in zones:
            continue
        zones[n] = {"poly": circle(p, 3.5, 10), "side": "mid", "priority": 30, "full": f"{n} spawn",
                    "aka": [], "area": False}

    # side areas: slabs across the red-blue axis
    mid = [(red[0] + blue[0]) / 2, (red[1] + blue[1]) / 2]
    seeds = {"Red side": red[:2], "Mid": mid, "Blue side": blue[:2]}
    box = [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
    for n, s in seeds.items():
        poly = box
        for m, o in seeds.items():
            if m != n:
                poly = clip(poly, s, o)
        zones[n] = {"poly": [[round(p[0], 2), round(p[1], 2)] for p in poly], "side": n.split()[0].lower(),
                    "priority": 10, "full": f"{n.lower()} of the map", "aka": [], "area": True}

    # points: mid (walkable, reachable from both bases) and the highest reachable ground near it
    rv, bv = Vec(*red), Vec(*blue)
    mid_p = snap(T, mid[0], mid[1], reach_from=rv, r=15) or Vec(mid[0], mid[1], 0)
    best = mid_p
    span = math.dist(red[:2], blue[:2])
    field = T._field(rv)
    for a in range(0, 360, 15):
        for rr in np.arange(2, max(6, span * 0.3), 1.5):
            p = Vec(mid_p.x + rr * math.cos(math.radians(a)), mid_p.y + rr * math.sin(math.radians(a)), 0)
            if not T.walkable(p):
                continue
            for l in (0, 1):
                j, i = T._cell(p)
                if T.lwalk[l, j, i] and np.isfinite(field[l, j, i]) and T.lz[l, j, i] > best.z + 0.3:
                    best = Vec(p.x, p.y, float(T.lz[l, j, i]))
    points = {"mid": [round(mid_p.x, 2), round(mid_p.y, 2), round(mid_p.z, 2)],
              "mid_hill": [round(best.x, 2), round(best.y, 2), round(best.z, 2)]}

    # defender holds: the flag and two spots 6 units out toward mid, 50 degrees apart
    holds = {}
    for team, f in (("red", red), ("blue", blue)):
        fv = Vec(*f)
        ang = math.atan2(mid[1] - f[1], mid[0] - f[0])
        hs = [list(f)]
        for da in (-0.9, 0.9):
            p = snap(T, f[0] + 6 * math.cos(ang + da), f[1] + 6 * math.sin(ang + da), f[2], reach_from=fv, r=4)
            if p:
                hs.append([round(p.x, 2), round(p.y, 2), round(p.z, 2)])
        holds[team] = [[round(v, 2) for v in h] for h in hs]

    # attack lanes: mid and two lanes across the axis at a third of the map width each side
    ux, uy = (blue[0] - red[0]) / span, (blue[1] - red[1]) / span
    lanes = [points["mid"]]
    for side in (-1, 1):
        p = snap(T, mid_p.x - uy * side * span * 0.3, mid_p.y + ux * side * span * 0.3, reach_from=rv, r=10)
        if p:
            lanes.append([round(p.x, 2), round(p.y, 2), round(p.z, 2)])

    out = {"map": name, "generated": True, "base_radius": 5.0, "roof_z": round(roof_z, 2), "points": points,
           "holds": holds, "lanes": lanes, "sneak": {}, "zones": zones}
    json.dump(out, open(os.path.join(d, "callouts.json"), "w"), indent=1)
    print(name, len(zones), "zones", points, "lanes", len(lanes))


if __name__ == "__main__":
    main(sys.argv[1])
