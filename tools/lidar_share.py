r"""Share LiDAR map scans between players (GitHub #19; the repository's lidar-maps/ folder keeps them by game).

export: one map's scan (maps/<map>/lidar.json: the floor walked, the jumps people landed, lifts, teleporters, cover,
        weapons) into a small zip, lidar-share/<map>_<date>.zip beside the mod, with a manifest (map, game, build,
        what is in it). Nothing about the player goes in: no names (people are "human", bots "bot"), no folders, and
        the scan is checked for anything private before it is written (private()).
bundle: every scan of one game on this PC in one zip, lidar-maps-<game>.zip (bundle.json + <map>/manifest.json +
        <map>/lidar.json): the author's scans, a download per game on the releases page (tag lidar-maps).
import: a shared zip (one map's, or a game's bundle) merged into this PC's scans, never replacing them: floor counts
        added, deaths and jump heights appended (the scan's own limits), jump links, teleporters, cover spots and
        weapons joined with exact duplicates dropped and every distinct variant kept (two people's jumps from nearly the
        same spot both stay). The scan before is kept as lidar.json.before-import-<date>. A scan already imported
        (maps/<map>/lidar_imported.json) is skipped, so importing twice adds nothing twice. A map this version of the
        mod does not have is skipped.
fetch:  a game's author bundle downloaded from the releases page and imported (the launcher's Import LiDAR scans).

usage: python -I lidar_share.py export <map>           (e.g. h3_construct, reach_20_sword_slayer, beavercreek)
       python -I lidar_share.py bundle <game>          (halo-ce halo-2 halo-2-anniversary halo-3 halo-3-odst halo-reach
                                                         halo-4)
       python -I lidar_share.py import <file.zip>
       python -I lidar_share.py fetch <game>
       python -I lidar_share.py list                   maps with a scan on this PC
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MAPS = os.path.join(ROOT, "maps")
OUT = os.path.join(ROOT, "lidar-share")
GAMES = (("h2a_", "Halo 2 Anniversary"), ("h2_", "Halo 2"), ("h3_", "Halo 3"), ("odst_", "Halo 3: ODST"),
         ("reach_", "Halo: Reach"), ("h4_", "Halo 4"))
SLUGS = {"Halo: CE": "halo-ce", "Halo 2": "halo-2", "Halo 2 Anniversary": "halo-2-anniversary", "Halo 3": "halo-3",
         "Halo 3: ODST": "halo-3-odst", "Halo: Reach": "halo-reach", "Halo 4": "halo-4"}
BUNDLES = "https://github.com/AyoItzKye/project-proving-grounds/releases/download/lidar-maps/lidar-maps-{slug}.zip"
LIMITS = {"deaths": 3000, "jumps": 2000}          # tools/lidar.py Recorder.save keeps the same tails
# private data a scan must never carry (make_release's own scan is a developer tool, not in a player's install: export
# there failed on its import, 0.2.2 builds 0929 / 1306)
PRIVATE = (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}",                       # an e-mail address
           r"(?i)[A-Z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+",                           # a user folder
           r"(?i)(?<![0-9a-f.])(?:0x)?0009[0-9a-f]{12}(?![0-9a-f])")                # an Xbox user id


def game_of(name):
    return next((g for p, g in GAMES if name.startswith(p)), "Halo: CE")


def scans():
    return sorted(d for d in os.listdir(MAPS) if os.path.exists(os.path.join(MAPS, d, "lidar.json")))


def private(text):
    """What private a scan's text holds ([] when nothing): the patterns above, and on a developer copy the release
    scan (tools/make_release.py: its personal terms too)."""
    found = [p for p in PRIVATE if re.search(p, text)]
    try:
        sys.path.insert(0, HERE)
        import make_release
        hit, quotes = make_release.scan_text(text, make_release.load_terms())
        found += list(hit) + (["a note on the tester"] if quotes else [])
    except ImportError:
        pass
    return found


def _scan(name):
    """(manifest, text) of a map's scan, privacy-checked."""
    src = os.path.join(MAPS, name, "lidar.json")
    if not os.path.exists(src):
        raise SystemExit(f"no LiDAR scan of {name} on this PC (play it, or run the LiDAR Simulator on it first)")
    text = open(src, encoding="utf-8").read()
    hit = private(text)
    if hit:
        raise SystemExit(f"{name}: the scan holds something private ({hit}); not exported")
    d = json.loads(text)
    b = os.path.join(ROOT, "BUILD")
    manifest = dict(map=name, game=game_of(name), build=open(b, encoding="utf-8").read().strip() if os.path.exists(b) else "",
                    made=time.strftime("%Y-%m-%d"), human_minutes=d.get("human_minutes", 0),
                    bot_minutes=d.get("bot_minutes", 0),
                    counts={k: len(v) for k, v in d.items() if isinstance(v, (list, dict))})
    return manifest, text


def export(name, out=OUT):
    """The zip's path. Refuses a map with no scan, or a scan holding something private."""
    manifest, text = _scan(name)
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"{name}_{manifest['made']}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=1))
        z.writestr("lidar.json", text)
    return path


def bundle(slug, out=OUT, kind="author"):
    """Every scan of one game in one zip: (path, maps)."""
    game = next((g for g, s in SLUGS.items() if s == slug), None)
    if game is None:
        raise SystemExit(f"{slug}: not a game (one of {', '.join(SLUGS.values())})")
    names = [d for d in scans() if game_of(d) == game]
    if not names:
        raise SystemExit(f"no {game} scans on this PC")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"lidar-maps-{slug}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            manifest, text = _scan(n)
            z.writestr(f"{n}/manifest.json", json.dumps(manifest, indent=1))
            z.writestr(f"{n}/lidar.json", text)
        z.writestr("bundle.json", json.dumps(dict(game=game, slug=slug, kind=kind, maps=names,
                                                  made=time.strftime("%Y-%m-%d")), indent=1))
    return path, names


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


def _ok_name(name):
    return bool(name) and not any(c in name for c in "/\\:.") and os.path.isdir(os.path.join(MAPS, name))


def _import_one(name, text):
    """Merge one scan's text into maps/<name>: ("merged" | "already imported", links before, links after)."""
    sig = hashlib.sha1(text.encode()).hexdigest()
    seen_path = os.path.join(MAPS, name, "lidar_imported.json")
    seen = json.load(open(seen_path, encoding="utf-8")) if os.path.exists(seen_path) else []
    dst = os.path.join(MAPS, name, "lidar.json")
    mine = json.load(open(dst, encoding="utf-8")) if os.path.exists(dst) else {}
    if sig in seen:
        return "already imported", len(mine.get("links", [])), len(mine.get("links", []))
    out = merge(mine, json.loads(text))
    if mine:
        os.replace(dst, f"{dst}.before-import-{time.strftime('%Y%m%d-%H%M%S')}")
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f)
    os.replace(tmp, dst)
    json.dump(seen + [sig], open(seen_path, "w", encoding="utf-8"))
    return "merged", len(mine.get("links", [])), len(out.get("links", []))


def import_any(path):
    """A map's zip or a game's bundle: [(map, result, links before, links after)]; maps this version lacks are
    reported as "not in this version" and skipped. Raises SystemExit on a zip that is neither."""
    out = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "bundle.json" in names:
            maps = json.loads(z.read("bundle.json")).get("maps", [])
            items = [(m, f"{m}/lidar.json") for m in maps if isinstance(m, str)]
        elif {"manifest.json", "lidar.json"} <= names:
            items = [(str(json.loads(z.read("manifest.json")).get("map", "")), "lidar.json")]
        else:
            raise SystemExit("not a LiDAR scan zip (no manifest.json / bundle.json)")
        for m, member in items:
            if not _ok_name(m) or member not in names:
                out.append((m, "not in this version", 0, 0))
                continue
            out.append((m, *_import_one(m, z.read(member).decode("utf-8"))))
    return out


def import_zip(path):
    """One map's zip: (map, links before, links after) (kept for its callers); refuses a map this version lacks."""
    got = import_any(path)
    if len(got) != 1 or got[0][1] == "not in this version":
        raise SystemExit(f"{got[0][0] if got else '?'}: no such map in this version of the mod")
    return got[0][0], got[0][2], got[0][3]


def fetch(slug, url=None, dest=None):
    """Download a game's author bundle from the releases page and import it: import_any's list."""
    if slug not in SLUGS.values():
        raise SystemExit(f"{slug}: not a game")
    dest = dest or os.path.join(ROOT, "user", "downloads")
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, f"lidar-maps-{slug}.zip")
    req = urllib.request.Request(url or BUNDLES.format(slug=slug), headers={"User-Agent": "ProjectProvingGrounds-launcher"})
    with urllib.request.urlopen(req, timeout=60) as r, open(path + ".part", "wb") as f:
        f.write(r.read())
    os.replace(path + ".part", path)
    return import_any(path)


def summary(got):
    merged = [m for m, r, *_ in got if r == "merged"]
    old = [m for m, r, *_ in got if r == "already imported"]
    missing = [m for m, r, *_ in got if r == "not in this version"]
    new_links = sum(b - a for _, r, a, b in got if r == "merged")
    if not merged:
        return ("Nothing new: " + (f"{len(old)} map{'s' if len(old) != 1 else ''} already imported" if old else
                                    "none of its maps are in this version")
                + (f", {len(missing)} not in this version" if old and missing else ""))
    return (f"{len(merged)} map{'s' if len(merged) != 1 else ''} added to your scans ({new_links} new jumps and rides)"
            + (f", {len(old)} already imported" if old else "") + (f", {len(missing)} not in this version" if missing else ""))


def main(argv):
    if not argv or argv[0] not in ("export", "bundle", "import", "fetch", "list"):
        raise SystemExit(__doc__)
    if argv[0] == "list":
        for d in scans():
            print(f"{d:32} {game_of(d)}")
    elif argv[0] == "export" and len(argv) > 1:
        print("written", export(argv[1]))
    elif argv[0] == "bundle" and len(argv) > 1:
        path, names = bundle(argv[1])
        print(f"written {path}: {len(names)} maps")
    elif argv[0] == "import" and len(argv) > 1:
        print(summary(import_any(argv[1])))
    elif argv[0] == "fetch" and len(argv) > 1:
        print(summary(fetch(argv[1])))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
