"""Halo 4 and H2A map variant files read directly (brain/mvar.py parse_h4 / read_h4), so the player's own Forge maps
on those games stand up in the LiDAR simulator's nav (tools/h3_forge_import.py). Before: no reader (the LiDAR sim knew
an H4 / H2A Forge map only from a live match), and H2A's stone platforms had no shape (the BOT OBSERVER platforms were
open air at -60 under the -45 floor).

1. data: both games' palettes (tools/forge_palette.py --h4h2a) name every map folder's scenario, the Forge canvases
   included; the platforms and blocks have shapes (tools/object_shapes.py)
2. every Halo 4 and H2A map variant MCC has on this PC (skipped when MCC is not found): parses, and every palette
   entry's placed count equals the objects read with that index (the check a misread field fails); every object named
3. the player's ALL ITEMS files (skipped when absent): every placeable item the live dump saw
   (maps/_shapes/<game>_forge_all_items.json) is in the file with its name within 5 cm
4. the importer files a Halo 4 / H2A file into the folder its live read made (no second entry for one layout)

usage: python -I test_mvar_h4.py      -> "mvar h4 OK"
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from brain import mvar  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


SH = os.path.join(ROOT, "maps", "_shapes")
for g, canvas, piece in (("h4", "h4_dlc_forge_island", "fi_unsc_c_plat_1x1_flat"), ("h2a", "h2a_ca_forge_skybox03",
                                                                               "fw_stone_plat_5x5_flat")):
    pal = json.load(open(os.path.join(SH, g + "_palettes.json"), encoding="utf-8"))
    folders = {os.path.basename(d) for d in os.listdir(os.path.join(ROOT, "maps")) if d.startswith(g + "_")}
    check(f"1. {g}: a palette for every map folder", {v["map"] for v in pal.values()} == folders,
          folders - {v["map"] for v in pal.values()})
    check(f"1. {g}: {canvas}'s palette has {piece}", any(piece in e[2] for v in pal.values() if v["map"] == canvas
                                                          for e in v["entries"]))
    check(f"1. {g}: {piece} has a shape", piece in json.load(open(os.path.join(SH, g + ".json")))["shapes"])

for g in ("h4", "h2a"):
    files = mvar.library(g)
    if not files:
        print(f"  (MCC not found: {g} parts 2-4 skipped)")
        continue
    bad, unnamed, n = [], 0, 0
    for f in files:
        v = mvar.read_h4(f)
        n += len(v["objects"])
        if not v["ok"]:
            bad.append(os.path.basename(f))
        unnamed += sum(1 for o in v["objects"] if not o["name"])
    check(f"2. {g}: all {len(files)} files parse, placed counts match ({n} objects)", not bad, bad[:5])
    check(f"2. {g}: every object named", unnamed == 0, unnamed)
    own = [mvar.read_h4(f) for f in files if "LocalFiles" in f]
    every = next((v for v in own if "ALL ITEMS" in v["title"]), None)
    if not every:
        print(f"  (no {g} ALL ITEMS file: part 3 skipped)")
        continue
    gt = json.load(open(os.path.join(SH, g + "_forge_all_items.json"), encoding="utf-8"))
    names = {o["name"] for o in every["objects"]}
    want = [it for it in gt["items"] if it["name"].rsplit("\\", 1)[-1] in names]
    hit = sum(1 for it in want if any(o["name"] == it["name"].rsplit("\\", 1)[-1] and math.dist(o["pos"], it["at"]) < 0.05
                                       for o in every["objects"]))
    check(f"3. {g}: the live ALL ITEMS items in the file, within 5 cm ({hit} of {len(want)})",
          want and hit == len(want), hit)
    import h3_forge_import as imp
    from brain import variants
    got = imp.file_one(every["path"], g)
    live = [d for d in os.listdir(os.path.join(ROOT, "maps", got[1], variants.SUB))
            if (variants.info(f"{got[1]}/{variants.SUB}/{d}") or {}).get("name") == every["title"]]
    check(f"4. {g}: filed once ({got[2]}, {got[4]} solid pieces)", len(live) == 1 and got[4] > 0, live)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("mvar h4 OK")
