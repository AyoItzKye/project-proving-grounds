"""People's moves off the nav, for review.

The watcher (tools/lidar.py HumanWatch, in every bot match) already records where people walk, crouch and land
jumps (maps/<map>/lidar.json); a landed jump between two nav floors is used by every bot at once. What the nav
cannot use without help is floor it lacks: a crate top, a ledge, a rail. This tool finds the patches people
walked (and survived) with no nav floor at that height, with the evidence and a hint for each, draws a review
sheet, and records the decision in maps/<map>/moves_review.json; brain/maps.py adds approved floor to the nav
(Terrain extra_floor), and the jumps people landed onto it then join the nav too.

usage: python -I review_moves.py [map ...]                      candidates + logs/review/moves_<map>.png
       python -I review_moves.py --approve <map> <id> [...] --why "<reason>"
       python -I review_moves.py --reject <map> <id> [...] --why "<reason>"
"""
import datetime
import json
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
from brain.maps import get_map, read_json, reviewed_moves, terrain  # noqa: E402

HUMAN_KINDS = (1, 3)          # lidar.py KIND_HUMAN, KIND_CROUCH: floor a person stood on
ON_FLOOR = 0.5                # a walked cell this close to a nav floor is on the nav
MIN_CELLS = 4                 # smaller patches are position noise (a cell is 0.25 units)
SHEET = os.path.join(ROOT, "logs", "review")


def patches(name, T=None, data=None, reviews=None):
    """[{id, cells [(x, y, z)], visits, rise, top_gap, jumps, deaths, hint}] not reviewed yet."""
    T = T or terrain(get_map(name))
    data = data if data is not None else read_json(os.path.join(ROOT, "maps", name, "lidar.json"))
    done = {tuple(round(v, 2) for v in c[:2]) for r in (reviews if reviews is not None else reviewed_moves(name))
            for c in r.get("cells", [])}
    off = {}
    for x, y, z, k, n in data.get("walk", []):
        if k not in HUMAN_KINDS:
            continue
        x, y, z = x * 0.25, y * 0.25, z * 0.1
        j, i = (int(v) for v in T._ij(np.asarray(x), np.asarray(y)))
        col = T.floors[:, j, i]
        fin = col[np.isfinite(col)]
        if (fin.size and np.min(np.abs(fin - z)) <= ON_FLOOR) or (round(x, 2), round(y, 2)) in done:
            continue
        c = off.setdefault((j, i), [x, y, z, 0])
        c[3] += n
    out, seen = [], set()
    for start in off:
        if start in seen:
            continue
        stack, grp = [start], []
        seen.add(start)
        while stack:
            a = stack.pop()
            grp.append(a)
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    b = (a[0] + dj, a[1] + di)
                    if b in off and b not in seen and abs(off[b][2] - off[a][2]) <= 0.3:
                        seen.add(b)
                        stack.append(b)
        if len(grp) < MIN_CELLS:
            continue
        cells = [tuple(off[g][:3]) for g in grp]
        cx, cy, cz = (float(np.mean([c[k] for c in cells])) for k in range(3))
        below = [float(np.nanmax(np.where(T.floors[:, j, i] < off[(j, i)][2] - ON_FLOOR, T.floors[:, j, i], np.nan)))
                 if np.any(T.floors[:, j, i] < off[(j, i)][2] - ON_FLOOR) else np.nan for j, i in grp]
        rise = cz - float(np.nanmedian(below)) if np.any(np.isfinite(below)) else float("inf")
        top_gap = float(np.median([off[(j, i)][2] - T.top[j, i] for j, i in grp]))
        near = lambda p, r: any(abs(p[0] - c[0]) < r and abs(p[1] - c[1]) < r and abs(p[2] - c[2]) < 1.0 for c in cells)
        jumps = sum(1 for l in data.get("links", []) if l.get("human") and (near(l["land"], 0.5) or near(l["take_off"], 0.5)))
        deaths = sum(1 for d in data.get("deaths", []) if d.get("who") == "human" and near(d["pos"], 1.5))
        # no cell with all 8 neighbours in the patch (under 3 x 3 anywhere): a trail, not floor. Seen in the first
        # review: Zanzibar's long curves 0.8 over open ground were vehicle seats (rides, before HumanWatch skipped
        # them), Boardwalk's strips hugged the rim of floor at the same height (the player's centre over the edge, feet
        # on it)
        g = set(grp)
        wide = sum(1 for a in grp if sum((a[0] + dj, a[1] + di) in g for dj in (-1, 0, 1) for di in (-1, 0, 1)) == 9)
        hint = ("a 1-cell trail: a vehicle seat, a lift or a ledge rim, not floor" if not wide else
                "a step or slope edge (nav floor under 0.6 below)" if rise < 0.6 else
                "the level has a surface here (too small or steep for the floor data)" if abs(top_gap) <= 0.4 else
                "nothing in the level data under it: an object (crate, rock, vehicle) or the air" if top_gap > 0.4 else
                "under the level's top surface (an overhang or a tunnel)")
        pid = "p%06x" % (zlib.crc32(f"{cx:.0f},{cy:.0f},{cz:.0f}".encode()) & 0xFFFFFF)
        out.append(dict(id=pid, cells=[[round(v, 2) for v in c] for c in cells], center=(cx, cy, cz),
                        visits=sum(off[g][3] for g in grp), rise=rise, top_gap=top_gap, jumps=jumps, deaths=deaths, hint=hint))
    return sorted(out, key=lambda p: -len(p["cells"]))


def sheet(name, cands, T, path):
    """A tile per candidate: the level's top surface around it (brighter = higher, relative to the patch), the
    patch in red, nav floor at the patch's height in green, its text."""
    from PIL import Image, ImageDraw
    tile, half = 300, 32                      # 64 x 64 cells = 16 x 16 units around the patch
    cols = 4
    rows = max(1, (len(cands) + cols - 1) // cols)
    img = Image.new("RGB", (cols * tile, rows * (tile + 70)), (20, 20, 20))
    d = ImageDraw.Draw(img)
    for n, p in enumerate(cands):
        cx, cy, cz = p["center"]
        j0, i0 = (int(v) for v in T._ij(np.asarray(cx), np.asarray(cy)))
        js, is_ = np.arange(j0 - half, j0 + half), np.arange(i0 - half, i0 + half)
        J, I = np.clip(js, 0, T.h - 1)[:, None], np.clip(is_, 0, T.w - 1)[None, :]
        top = np.nan_to_num(T.top[J, I], nan=cz + 3)
        g = np.clip(128 + (top - cz) * 40, 0, 255).astype(np.uint8)
        rgb = np.stack([g, g, g], -1)
        flo = T.floors[:, J, I]
        same = np.any(np.isfinite(flo) & (np.abs(flo - cz) <= ON_FLOOR), axis=0)
        rgb[same] = (rgb[same] * 0.5 + np.array([0, 110, 0])).astype(np.uint8)
        for x, y, z in p["cells"]:
            j, i = (int(v) for v in T._ij(np.asarray(x), np.asarray(y)))
            if abs(j - j0) < half and abs(i - i0) < half:
                rgb[j - j0 + half, i - i0 + half] = (230, 40, 40)
        im = Image.fromarray(rgb[::-1]).resize((tile, tile), Image.NEAREST)   # north up
        ox, oy = (n % cols) * tile, (n // cols) * (tile + 70)
        img.paste(im, (ox, oy))
        d.text((ox + 4, oy + tile + 2), f"{p['id']}  {len(p['cells'])} cells, {p['visits']} visits, z {cz:.1f}", fill=(255, 255, 255))
        d.text((ox + 4, oy + tile + 16), f"above floor {p['rise']:.1f}, above level top {p['top_gap']:.1f}", fill=(220, 220, 220))
        d.text((ox + 4, oy + tile + 30), f"jumps {p['jumps']}, deaths near {p['deaths']}", fill=(220, 220, 220))
        d.text((ox + 4, oy + tile + 44), p["hint"][:48], fill=(255, 210, 120))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def decide(name, ids, ok, why, cands=None):
    """Record the review of candidates `ids` on map `name`; returns the reviews written."""
    cands = {p["id"]: p for p in (cands if cands is not None else patches(name))}
    if "trails" in ids:                          # every 1-cell trail on the map at once
        ids = [i for i in ids if i != "trails"] + [i for i, p in cands.items() if p["hint"].startswith("a 1-cell trail")]
    missing = [i for i in ids if i not in cands]
    if missing:
        raise SystemExit(f"not candidates now (re-run the list): {missing}")
    path = os.path.join(ROOT, "maps", name, "moves_review.json")
    data = read_json(path) if os.path.exists(path) else {"reviews": []}
    new = [dict(id=i, kind="floor", ok=ok, cells=cands[i]["cells"], why=why, hint=cands[i]["hint"], by="claude",
                at=datetime.date.today().isoformat()) for i in ids]
    data["reviews"] = [r for r in data["reviews"] if r["id"] not in ids] + new
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    return new


def selftest():
    """A crate top (z 1.0 over floor 0.0) walked 3 x 3 cells: a candidate; approved, the nav gets that floor."""
    from brain.terrain import Terrain
    import tempfile
    d = tempfile.mkdtemp()
    n = 40
    floors = np.full((1, n, n), 0.0, np.float32)
    top = np.zeros((n, n), np.float32)
    top[20:23, 20:24] = 1.0                          # the crate is in the top surface, not in the floor data
    np.savez(os.path.join(d, "h.npz"), top=top, low=np.zeros((n, n), np.float32), floors=floors,
             walls=np.zeros((n, n, 1), np.uint64), wall_z0=-10.0, wall_bin=0.5, x0=0.0, y0=0.0, cell=0.25)
    T = Terrain(os.path.join(d, "h.npz"), [])
    walk = [[i, j, 10, 1, 2] for j in range(20, 23) for i in range(20, 23)]       # 9 cells (3 x 3) at z 1.0
    walk += [[5, 5, 0, 1, 9], [30, 30, 11, 1, 1]]                                  # on the floor; a lone blip
    found = patches("x", T, {"walk": walk}, reviews=[])
    assert len(found) == 1 and len(found[0]["cells"]) == 9, found
    p = found[0]
    assert p["rise"] > 0.9 and abs(p["top_gap"]) < 0.01 and "surface" in p["hint"], p
    T2 = Terrain(os.path.join(d, "h.npz"), [], extra_floor=p["cells"])
    from brain.core import Vec
    node = T2._node(Vec(5.25, 5.25, 1.0))
    assert T2.lwalk[node] and abs(T2.lz[node] - 1.0) < 0.05, (node, T2.lz[node])
    assert not patches("x", T2, {"walk": walk}, reviews=[]), "approved floor is a candidate again"
    assert not patches("x", T, {"walk": walk}, reviews=[{"cells": p["cells"]}]), "a rejected patch came back"
    trail = [[i, 8, 8, 1, 3] for i in range(5, 15)]                               # a seat 0.8 up, one cell wide
    t = patches("x", T, {"walk": trail}, reviews=[])
    assert len(t) == 1 and t[0]["hint"].startswith("a 1-cell trail"), t


def main():
    selftest()
    args = sys.argv[1:]
    why = args[args.index("--why") + 1] if "--why" in args else ""
    for flag, ok in (("--approve", True), ("--reject", False)):
        if flag in args:
            k = args.index(flag)
            name, ids = args[k + 1], [a for a in args[k + 2:] if not a.startswith("--") and a != why]
            for r in decide(name, ids, ok, why):
                print(("approved" if ok else "rejected"), name, r["id"], len(r["cells"]), "cells")
            return
    names = args or sorted(n for n in os.listdir(os.path.join(ROOT, "maps"))
                           if os.path.exists(os.path.join(ROOT, "maps", n, "lidar.json"))
                           and os.path.exists(os.path.join(ROOT, "maps", n, "heightmap.npz")))
    for name in names:
        try:
            T = terrain(get_map(name))
        except Exception as e:                       # a map without full map data
            print(f"{name}: no terrain ({type(e).__name__})")
            continue
        cands = patches(name, T)
        if not cands:
            continue
        path = os.path.join(SHEET, f"moves_{name}.png")
        sheet(name, cands[:24], T, path)
        print(f"{name}: {len(cands)} candidates -> {path}")
        for p in cands:
            print(f"  {p['id']} {len(p['cells']):3} cells, {p['visits']:3} visits, z {p['center'][2]:.1f}, above floor "
                  f"{p['rise']:.1f}, above level top {p['top_gap']:.1f}, jumps {p['jumps']}, deaths {p['deaths']}: {p['hint']}")


if __name__ == "__main__":
    main()
