"""The see-through faces of a map (glass, windows, fog volumes: bsp2obj --glass) as quarter-unit
cells with the height range they cover: maps/<map>/glass.json. LiDAR does not paint these as walls
(they break, or bullets pass), so bots never take cover behind them.

usage: python -I glass_mask.py <glass.txt> <map folder name>
       python -I glass_mask.py --all <h2a|h4|odst>      (runs bsp2obj for every map of that game)
"""
import json
import math
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MCC = paths.mcc()
GAME_DIR = {"h2a": "groundhog", "h4": "halo4", "odst": "halo3odst"}
STEP = 0.1                     # sample spacing on each triangle (cells are 0.25)


def mask(glass_txt):
    cells = {}
    for line in open(glass_txt):
        v = [float(x) for x in line.split()]
        if len(v) != 9:
            continue
        a, b, c = v[0:3], v[3:6], v[6:9]
        n = max(1, int(max(math.dist(a, b), math.dist(b, c), math.dist(c, a)) / STEP))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, w = i / n, j / n
                p = [a[k] + (b[k] - a[k]) * u + (c[k] - a[k]) * w for k in range(3)]
                key = (round(p[0] * 4), round(p[1] * 4))
                lo, hi = cells.get(key, (p[2], p[2]))
                cells[key] = (min(lo, p[2]), max(hi, p[2]))
    return [[x, y, round(lo, 2), round(hi, 2)] for (x, y), (lo, hi) in sorted(cells.items())]


def build(glass_txt, map_name):
    out = mask(glass_txt)
    json.dump(dict(cell=0.25, cells=out), open(os.path.join(ROOT, "maps", map_name, "glass.json"), "w"))
    return len(out)


def build_all(game):
    exe = paths.need(paths.map_tool("bsp2obj"), "bsp2obj.exe (the map tools: tools/map_tools)")
    tmp = tempfile.mkdtemp(prefix="glass_")
    for d in sorted(os.listdir(os.path.join(ROOT, "maps"))):
        if not d.startswith(game + "_") or not os.path.isdir(os.path.join(ROOT, "maps", d)):
            continue
        stem = d[len(game) + 1:]
        mp = os.path.join(MCC, GAME_DIR[game], "maps", stem + ".map")
        if not os.path.exists(mp):
            print(d, "no .map file")
            continue
        g = os.path.join(tmp, stem + ".txt")
        r = subprocess.run([exe, mp, os.path.join(tmp, "mesh.obj"), "--glass", g], capture_output=True, text=True)
        n = build(g, d) if r.returncode == 0 and os.path.exists(g) else None
        print(d, f"{n} glass cells" if n is not None else "bsp2obj failed: " + r.stdout[-200:], flush=True)
        for f in (g, os.path.join(tmp, "mesh.obj")):
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    if sys.argv[1] == "--all":
        build_all(sys.argv[2])
    else:
        print(build(sys.argv[1], sys.argv[2]), "glass cells")
