r"""The player's own Forge maps (MCC LocalFiles\<xuid>\<Halo3|Halo4|Halo2A>\Map\*.mvar, saved in Forge) filed as variants
of their base maps (maps/<base>/variants/<id>/variant.json; its pieces read from the .mvar: brain/mvar.read_h3,
read_h4), so the LiDAR simulator lists them and the nav stands their Forge pieces up (maps/_shapes/<game>.json,
tools/object_shapes.py). Halo 3 has no live piece reader, so the file is its only source; a Halo 4 / H2A layout seen
live already (brain/variants.identify: no file behind it) sharing SAME of its objects is that folder, given the file's
pieces (a live read can miss some), else a new folder by the file's own id (two of the player's Halo 3 maps sharing
their spawns came out as one variant when matched by layout). Run by the LiDAR simulator at its start
(tools/lidar_sim.py); safe to run again (a filed one is rewritten from its file).

usage: python -I h3_forge_import.py      -> one line a variant
"""
import hashlib
import os
import sys
import time

if __name__ == "__main__":     # (run as a script: tools/ off the path; imported, the caller's path stays: live_bots
    # and lidar import tls and variant_strategy from tools/ after it)
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from brain import forge, maps, mvar, variants  # noqa: E402
from brain.callouts import read_json  # noqa: E402

READERS = {"h3": mvar.read_h3, "h4": mvar.read_h4, "h2a": mvar.read_h4}


def pieces_of(v):
    """[(name, pos, (forward, left, up))] of a read variant's placed, named objects."""
    out = []
    for o in v["objects"]:
        if not o["placed"] or not o["name"]:
            continue
        up, fw = tuple(o.get("up") or (0, 0, 1)), tuple(o.get("forward") or (1, 0, 0))
        left = (up[1] * fw[2] - up[2] * fw[1], up[2] * fw[0] - up[0] * fw[2], up[0] * fw[1] - up[1] * fw[0])
        out.append((o["name"], tuple(o["pos"]), (fw, left, up)))
    return out


def seen_live(base, keys, fname):
    """The id of a filed variant of base with this very layout (keys, from any file: MCC copies the running variant to
    Temporary\\UserContent under a new name at every match start), else one with no file behind it (or this file)
    sharing SAME of keys, the best; None."""
    d = os.path.join(maps.ROOT, base, variants.SUB)
    best = None
    for vid in sorted(os.listdir(d)) if os.path.isdir(d) else ():
        old = read_json(os.path.join(d, vid, "variant.json"))
        theirs = {tuple(k) for k in (old or {}).get("objects", [])}
        if theirs == keys:
            return vid
        if not old or (old.get("mvar") or {}).get("file", fname) != fname:
            continue
        share = len(keys & theirs) / max(1, min(len(keys), len(theirs)))
        if share >= variants.SAME and (best is None or share > best[0]):
            best = (share, vid)
    return best and best[1]


def file_one(path, game="h3"):
    """File one .mvar; (title, base, map name, pieces, solid pieces) or None (unreadable, no base map here)."""
    v = READERS[game](path)
    base = v["map"]
    if not v.get("ok") or not base or not os.path.isdir(os.path.join(maps.ROOT, base)):
        return None
    pieces = pieces_of(v)
    objs = read_json(os.path.join(maps.ROOT, base, "objects.json"))
    mine = variants.own([(n, p) for n, p, _ in pieces], variants.base_placed(objs))
    if len(mine) < variants.MIN_OWN:
        return None
    keys = {variants._key(n, p) for n, p in mine}
    fname = os.path.basename(path)
    vid = seen_live(base, keys, fname) or "v" + hashlib.sha1(fname.encode()).hexdigest()[:8]
    name = f"{base}/{variants.SUB}/{vid}"
    old = variants.info(name) or {}
    now = time.strftime("%Y-%m-%d %H:%M")
    data = dict(old, id=vid, base=base, game=game, name=v["title"], first_seen=old.get("first_seen", now),
                last_seen=now, objects=[list(k) for k in sorted(keys)], count=len(keys),
                window=list(variants.union(old.get("window"), variants.window_of(
                    [p for _, p in mine] + list(variants.base_area(objs))))),
                pieces=[[n] + [round(c, 4) for c in tuple(p) + tuple(x for ax in a for x in ax)] for n, p, a in pieces],
                mvar=dict(file=fname, title=v["title"]))
    variants.save(name, data)
    solid = sum(1 for n, p, a in pieces if forge.block(n, p, a, game=game))
    return v["title"], base, name, len(pieces), solid


def main():
    for game in READERS:
        for f in mvar.library(game):
            if "LocalFiles" not in f:
                continue
            try:
                got = file_one(f, game)
            except Exception as e:                  # (one unreadable file never stops the rest)
                print(f"{os.path.basename(f)}: {type(e).__name__}: {e}")
                continue
            if got:
                print(f"{got[0]!r} on {got[1]}: {got[3]} pieces, {got[4]} solid -> {got[2]}")


if __name__ == "__main__":
    main()
