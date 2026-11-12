r"""Share LiDAR map scans between players (GitHub #19; the repository's lidar-maps/ folder keeps them by game).

export: one map's scan (maps/<map>/lidar.json: the floor walked, the jumps people landed, lifts, teleporters, cover,
        weapons) into a small zip, lidar-share/<map>_<date>.zip beside the mod, with a manifest (map, game, build,
        what is in it). Nothing about the player goes in: no names (people are "human", bots "bot"), no folders, and
        the zip is scanned for private data before it is written (tools/make_release.py scan_text).
import: a shared zip merged into this PC's scan of that map, never replacing it: floor counts added, deaths and jump
        heights appended (the scan's own limits), jump links, teleporters, cover spots and weapons joined with exact
        duplicates dropped and every distinct variant kept (two people's jumps from nearly the same spot both stay).
        The scan before the import is kept as lidar.json.before-import-<date>.

usage: python -I lidar_share.py export <map>           (e.g. h3_construct, reach_20_sword_slayer, beavercreek)
       python -I lidar_share.py import <file.zip>
       python -I lidar_share.py list                   maps with a scan on this PC
"""
import json
import os
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MAPS = os.path.join(ROOT, "maps")
OUT = os.path.join(ROOT, "lidar-share")
GAMES = (("h2a_", "Halo 2 Anniversary"), ("h2_", "Halo 2"), ("h3_", "Halo 3"), ("odst_", "Halo 3: ODST"),
         ("reach_", "Halo: Reach"), ("h4_", "Halo 4"))
LIMITS = {"deaths": 3000, "jumps": 2000}          # tools/lidar.py Recorder.save keeps the same tails


def game_of(name):
    return next((g for p, g in GAMES if name.startswith(p)), "Halo: CE")


def scans():
    return sorted(d for d in os.listdir(MAPS) if os.path.exists(os.path.join(MAPS, d, "lidar.json")))


def export(name, out=OUT):
    """The zip's path. Refuses a map with no scan, or a scan the privacy scan flags."""
    src = os.path.join(MAPS, name, "lidar.json")
    if not os.path.exists(src):
        raise SystemExit(f"no LiDAR scan of {name} on this PC (play it, or run the LiDAR Simulator on it first)")
    text = open(src, encoding="utf-8").read()
    sys.path.insert(0, HERE)
    import make_release
    found, quotes = make_release.scan_text(text, make_release.load_terms())
    if found or quotes:
        raise SystemExit(f"{name}: the scan holds something private ({found}); not exported")
    d = json.loads(text)
    build = open(os.path.join(ROOT, "BUILD"), encoding="utf-8").read().strip() if os.path.exists(os.path.join(ROOT, "BUILD")) else ""
    manifest = dict(map=name, game=game_of(name), build=build, made=time.strftime("%Y-%m-%d"),
                    human_minutes=d.get("human_minutes", 0), bot_minutes=d.get("bot_minutes", 0),
                    counts={k: len(v) for k, v in d.items() if isinstance(v, (list, dict))})
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"{name}_{manifest['made']}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=1))
        z.writestr("lidar.json", text)
    return path


def _key(x):
    return json.dumps(x, sort_keys=True)


def _join(a, b):
    """a then the items of b not already in a (exact duplicates only)."""
    seen = {_key(x) for x in a}
    return a + [x for x in b if _key(x) not in seen and not seen.add(_key(x))]


def merge(mine, theirs):
    """Their scan joined into mine (a new dict). Floors: counts added per cell (cell, height step, kind); deaths and jump
    heights appended to the scan's limits; links, teleports, cover, weapons, holds and objectives joined."""
    if (mine.get("cell"), mine.get("zstep")) != (theirs.get("cell"), theirs.get("zstep")) and mine:
        raise SystemExit("the shared scan uses another grid (cell / height step): made by a different version")
    walk = {}
    for w in mine.get("walk", []) + theirs.get("walk", []):
        k = tuple(w[:3]) + ((w[3],) if len(w) == 5 else (0,))     # (an old scan's cell has no kind: a bot's, 0, as lidar.py)
        walk[k] = walk.get(k, 0) + w[-1]
    out = dict(mine)
    out.update(cell=theirs.get("cell", mine.get("cell")), zstep=theirs.get("zstep", mine.get("zstep")),
               runs=mine.get("runs", 0) + theirs.get("runs", 0),
               bot_minutes=round(mine.get("bot_minutes", 0) + theirs.get("bot_minutes", 0), 1),
               human_minutes=round(mine.get("human_minutes", 0) + theirs.get("human_minutes", 0), 1),
               walk=[[*k, n] for k, n in sorted(walk.items())])
    for k, cap in LIMITS.items():
        out[k] = (mine.get(k, []) + theirs.get(k, []))[-cap:]
    for k in ("links", "teleports", "cover", "weapons", "objectives"):
        if k in mine or k in theirs:
            out[k] = _join(mine.get(k, []), theirs.get(k, []))
    if "holds" in mine or "holds" in theirs:
        holds = dict(mine.get("holds", {}))
        for h, v in theirs.get("holds", {}).items():
            holds[h] = _join(holds.get(h, []), v) if isinstance(v, list) else holds.get(h, v)
        out["holds"] = holds
    return out


def import_zip(path):
    """(map, links before, links after)."""
    with zipfile.ZipFile(path) as z:
        manifest = json.loads(z.read("manifest.json"))
        theirs = json.loads(z.read("lidar.json"))
    name = str(manifest.get("map", ""))
    if not name or any(c in name for c in "/\\:.") or not os.path.isdir(os.path.join(MAPS, name)):
        raise SystemExit(f"{name}: no such map in this version of the mod")
    dst = os.path.join(MAPS, name, "lidar.json")
    mine = json.load(open(dst, encoding="utf-8")) if os.path.exists(dst) else {}
    out = merge(mine, theirs)
    if mine:
        os.replace(dst, f"{dst}.before-import-{time.strftime('%Y%m%d-%H%M%S')}")
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f)
    os.replace(tmp, dst)
    return name, len(mine.get("links", [])), len(out.get("links", []))


def main(argv):
    if not argv or argv[0] not in ("export", "import", "list"):
        raise SystemExit(__doc__)
    if argv[0] == "list":
        for d in scans():
            print(f"{d:32} {game_of(d)}")
    elif argv[0] == "export" and len(argv) > 1:
        print("written", export(argv[1]))
    elif argv[0] == "import" and len(argv) > 1:
        name, a, b = import_zip(argv[1])
        print(f"{name}: merged; jump and ride links {a} -> {b}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
