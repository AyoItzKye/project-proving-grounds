"""Add the scenario's placed objects (objects.json "placed": scenery, crates, controls and machines with their rotation,
label and flags, tools/reach_export.py) to the Halo 4 / H2A maps' objects.json, from the scenario XMLs their export kept
(source/*.slim.xml), without exporting the map again: those exports came before "placed", so their navs had none of the
maps' crates (live: bots stuck 40 s against Adrift's stacked crates in CTF). Only "placed" changes.

usage: python -I placed_refresh.py --h4|--h2a [map ...]      (default: every maps/h4_* or maps/h2a_* with source XMLs)
"""
import glob
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reach_export as X  # noqa: E402  (reads and removes the --h4 / --h2a flag)


def refresh(folder):
    src = os.path.join(folder, "source")
    main = os.path.join(src, "scenario.slim.xml")
    objs = os.path.join(folder, "objects.json")
    if not (os.path.exists(main) and os.path.exists(objs)):
        return None
    xmls = [main] + sorted(f for f in glob.glob(os.path.join(src, "scenario_*.slim.xml")))
    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "objects.json")
        X.scenario_objects(xmls, tmp)
        placed = json.load(open(tmp))["placed"]
    o = json.load(open(objs, encoding="utf-8"))
    o["placed"] = placed
    json.dump(o, open(objs, "w"), indent=1)
    return len(placed)


if __name__ == "__main__":
    if X.PREFIX not in ("h4_", "h2a_"):
        sys.exit("usage: placed_refresh.py --h4|--h2a [map ...]")
    names = sys.argv[1:] or sorted(os.path.basename(p)[len(X.PREFIX):] for p in glob.glob(os.path.join(X.ROOT, "maps", X.PREFIX + "*")))
    for n in names:
        print(n, refresh(os.path.join(X.ROOT, "maps", X.PREFIX + n)), flush=True)
