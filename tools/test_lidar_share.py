"""LiDAR scans shared between players (tools/lidar_share.py, GitHub #19).

1. merge: floor counts added per cell (an old scan's 4-field cells read as a bot's), deaths appended, an exact duplicate
   jump link dropped while a near variant of it (another take-off angle) stays, cover and teleports joined
2. a scan made on another grid is refused
3. export -> import round trip on a scratch map folder: the zip has a manifest (map, game) and the scan; importing it
   into a PC with its own scan of that map adds to it and keeps the old one as lidar.json.before-import-*
4. a zip naming a path ("../x") or an unknown map is refused before anything is written
5. a game's bundle (every scan of that game) imports in one go; importing it again adds nothing; a map this version
   lacks is skipped and said
6. export works in a player's install (no tools/make_release.py there: 0.2.2 builds 0929 / 1306 failed on it), and a
   scan holding an e-mail address is refused
7. the launcher's LiDAR scans card: the author's scans of a game downloaded and added, a shared zip's bytes added
   (nothing twice), a wrong game / not a zip / empty / no download each said
8. the same over HTTP through the launcher's own handler (raw zip bytes; a post without the page's header refused)

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
    # 5. a game's bundle: every scan of that game, imported in one go; again: nothing twice; a map this version lacks
    os.makedirs(os.path.join(maps, "h3_othermap"))
    json.dump(theirs, open(os.path.join(maps, "h3_othermap", "lidar.json"), "w"))
    os.makedirs(os.path.join(maps, "beavercreek"))
    json.dump(theirs, open(os.path.join(maps, "beavercreek", "lidar.json"), "w"))
    bpath, names = L.bundle("halo-3", out)
    check("5. the Halo 3 bundle holds its two scans, not CE's", names == ["h3_othermap", "h3_testmap"], names)
    before = json.load(open(os.path.join(maps, "h3_othermap", "lidar.json")))
    got = L.import_any(bpath)
    after = json.load(open(os.path.join(maps, "h3_othermap", "lidar.json")))
    check("5. bundle imported", [r for _, r, *_ in got] == ["merged", "merged"], got)
    again = L.import_any(bpath)
    check("5. importing it again adds nothing", [r for _, r, *_ in again] == ["already imported"] * 2
          and json.load(open(os.path.join(maps, "h3_othermap", "lidar.json"))) == after, again)
    check("5. floors added once", sum(w[-1] for w in after["walk"]) == 2 * sum(w[-1] for w in before["walk"]))
    shutil.rmtree(os.path.join(maps, "h3_othermap"))
    check("5. a map this version lacks: skipped, said", [r for _, r, *_ in L.import_any(bpath)][0] == "not in this version")
    # 6. export in a player's install: no tools/make_release.py there (0.2.2 builds 0929 / 1306 failed on its import)
    saved = sys.modules.get("make_release")
    sys.modules["make_release"] = None                     # (import make_release -> ImportError)
    try:
        ok = os.path.exists(L.export("h3_testmap", out))
    except Exception as e:
        ok = repr(e)
    finally:
        if saved is not None:
            sys.modules["make_release"] = saved
        else:
            sys.modules.pop("make_release", None)
    check("6. export without the developer tools", ok is True, ok)
    check("6. an e-mail address in a scan is refused", L.private('{"x": "someone@example.com"}') != [])
    # 7. the launcher's LiDAR scans card: the author's scans of a game (downloaded) and a shared zip (its bytes)
    import pathlib
    import launcher
    launcher.ROOT = tmp
    saved_url = L.BUNDLES
    L.BUNDLES = pathlib.Path(out).as_uri() + "/lidar-maps-{slug}.zip"
    try:
        os.makedirs(os.path.join(maps, "h3_othermap"))
        json.dump(theirs, open(os.path.join(maps, "h3_othermap", "lidar.json"), "w"))
        bpath, _ = L.bundle("halo-3", out)                 # (both scans changed since case 5: both new here)
        r = launcher.lidar_fetch("halo-3")
        check("7. the author's scans of a game", r["ok"] and r["message"].startswith("2 maps added"), r)
        check("7. not a game: refused", launcher.lidar_fetch("../x")["ok"] is False)
        r = launcher.lidar_import(open(bpath, "rb").read())
        check("7. a shared zip: nothing twice", r["ok"] and r["message"].startswith("Nothing new: 2 maps already imported"), r)
        r = launcher.lidar_import(b"not a zip")
        check("7. not a zip: said", not r["ok"] and r["message"].startswith("Not a LiDAR scan zip"), r)
        check("7. empty: said", not launcher.lidar_import(None)["ok"])
        L.BUNDLES = pathlib.Path(out).as_uri() + "/missing-{slug}.zip"
        r = launcher.lidar_fetch("halo-3")
        check("7. no connection / no file: said", not r["ok"] and "try again" in r["message"], r)
        # 8. over HTTP, as the launcher's page sends them: a zip's raw bytes (Import a shared zip), the game as JSON
        import threading
        import urllib.request
        srv = launcher.Server(("127.0.0.1", 0), launcher.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}"

        def post(path, data, ctype, page=True):
            req = urllib.request.Request(url + path, data=data, method="POST",
                                         headers=dict({"Content-Type": ctype}, **({"X-Launcher": "1"} if page else {})))
            try:
                return json.loads(urllib.request.urlopen(req, timeout=30).read())
            except urllib.error.HTTPError as e:
                return {"code": e.code}
        try:
            r = post("/lidar/import", open(bpath, "rb").read(), "application/zip")
            check("8. a zip's bytes over HTTP", r.get("ok") and r["message"].startswith("Nothing new"), r)
            check("8. not from the launcher's page: refused", post("/lidar/import", b"x", "application/zip", False)
                  == {"code": 403})
            r = post("/lidar/fetch", json.dumps({"game": "nope"}).encode(), "application/json")
            check("8. the game as JSON", r == {"ok": False, "message": "Choose a game."}, r)
        finally:
            srv.shutdown()
            srv.server_close()
    finally:
        L.BUNDLES = saved_url
finally:
    shutil.rmtree(tmp, ignore_errors=True)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("lidar share OK")
