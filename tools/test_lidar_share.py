"""LiDAR scans shared between players (tools/lidar_share.py, GitHub #19).

1. merge: floor counts added per cell (an old scan's 4-field cells read as a bot's), deaths appended, an exact duplicate
   jump link dropped while a near variant of it (another take-off angle) stays, cover and teleports joined
2. a scan made on another grid is refused
3. export -> import round trip on a scratch map folder: the zip has a manifest (map, game) and the scan; importing it
   into a PC with its own scan of that map adds to it and keeps the old one as lidar.json.before-import-*
4. a zip naming a path ("../x") or an unknown map is refused before anything is written

usage: python -I test_lidar_share.py      -> "lidar share OK"
"""
import glob
import json
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lidar_share as L  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


jump = {"kind": "jump", "take_off": [1.0, 2.0, 3.0], "land": [4.0, 2.0, 3.5], "human": True}
variant = dict(jump, take_off=[1.1, 2.0, 3.0])
mine = dict(cell=0.25, zstep=0.1, runs=1, bot_minutes=1.0, human_minutes=2.0, walk=[[1, 2, 3, 0, 5], [7, 7, 7, 4]],
            deaths=[{"who": "human", "pos": [0, 0, 0]}], jumps=[1.0], links=[jump], cover=[[1, 1, 1, 0, 0]], teleports=[])
theirs = dict(cell=0.25, zstep=0.1, runs=2, bot_minutes=0.5, human_minutes=1.0, walk=[[1, 2, 3, 0, 4], [9, 9, 9, 1, 1]],
              deaths=[{"who": "human", "pos": [1, 1, 1]}], jumps=[1.2], links=[jump, variant],
              cover=[[1, 1, 1, 0, 0], [2, 2, 2, 0, 0]], teleports=[{"from": [0, 0, 0], "to": [5, 5, 5]}])
m = L.merge(mine, theirs)
walk = {tuple(w[:4]): w[4] for w in m["walk"]}
check("1. floor counts added", walk.get((1, 2, 3, 0)) == 9 and walk.get((9, 9, 9, 1)) == 1, walk)
check("1. an old 4-field cell read as a bot's", walk.get((7, 7, 7, 0)) == 4, walk)
check("1. deaths and jump heights appended", len(m["deaths"]) == 2 and m["jumps"] == [1.0, 1.2])
check("1. the duplicate jump dropped, its variant kept", m["links"] == [jump, variant], m["links"])
check("1. cover and teleports joined", len(m["cover"]) == 2 and len(m["teleports"]) == 1)
check("1. minutes and runs added", (m["runs"], m["human_minutes"]) == (3, 3.0))
try:
    L.merge(mine, dict(theirs, cell=0.5))
    check("2. another grid refused", False)
except SystemExit:
    check("2. another grid refused", True)

tmp = tempfile.mkdtemp()
maps, out = os.path.join(tmp, "maps"), os.path.join(tmp, "share")
os.makedirs(os.path.join(maps, "h3_testmap"))
json.dump(theirs, open(os.path.join(maps, "h3_testmap", "lidar.json"), "w"))
L.MAPS, L.ROOT = maps, tmp
try:
    path = L.export("h3_testmap", out)
    with zipfile.ZipFile(path) as z:
        man = json.loads(z.read("manifest.json"))
    check("3. the zip's manifest", man["map"] == "h3_testmap" and man["game"] == "Halo 3", man)
    json.dump(mine, open(os.path.join(maps, "h3_testmap", "lidar.json"), "w"))
    name, a, b = L.import_zip(path)
    now = json.load(open(os.path.join(maps, "h3_testmap", "lidar.json")))
    check("3. imported into this PC's scan", (name, a, b) == ("h3_testmap", 1, 2) and len(now["walk"]) == 3, (a, b))
    check("3. the old scan kept", len(glob.glob(os.path.join(maps, "h3_testmap", "lidar.json.before-import-*"))) == 1)
    for bad in ("../h3_testmap", "h3_nosuchmap"):
        evil = os.path.join(tmp, "evil.zip")
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("manifest.json", json.dumps({"map": bad}))
            z.writestr("lidar.json", json.dumps(theirs))
        try:
            L.import_zip(evil)
            check(f"4. {bad!r} refused", False)
        except SystemExit:
            check(f"4. {bad!r} refused", True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("lidar share OK")
