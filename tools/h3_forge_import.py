"""The player's own Halo 3 map variants (MCC LocalFiles\\<xuid>\\Halo3\\Map\\*.mvar, saved in Forge) filed as variants of their
base maps (maps/<base>/variants/v<id of the file>/variant.json; its pieces read from the .mvar, brain/mvar.read_h3), so
the LiDAR simulator lists them and the nav stands their Forge pieces up (maps/_shapes/h3.json, tools/object_shapes.py
h3). Halo 3 has no live piece reader (brain/forge.py reads Reach, Halo 4 and H2A), so the file is the source. Filed by
the file's own id, not matched by layout (two of the player's maps sharing their spawns came out as one variant). Run by
the LiDAR simulator at its start (tools/lidar_sim.py); safe to run again (a filed one is rewritten from its file).

usage: python -I h3_forge_import.py      -> one line a variant
"""
import hashlib
import os
import sys
import time

sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from brain import forge, maps, mvar, variants  # noqa: E402
from brain.callouts import read_json  # noqa: E402


def pieces_of(v):
    """[(name, pos, (forward, left, up))] of a read_h3 variant's placed, named objects."""
    out = []
    for o in v["objects"]:
        if not o["placed"] or not o["name"]:
            continue
        up, fw = tuple(o.get("up") or (0, 0, 1)), tuple(o.get("forward") or (1, 0, 0))
        left = (up[1] * fw[2] - up[2] * fw[1], up[2] * fw[0] - up[0] * fw[2], up[0] * fw[1] - up[1] * fw[0])
        out.append((o["name"], tuple(o["pos"]), (fw, left, up)))
    return out


def file_one(path):
    """File one .mvar; (title, base, map name, pieces, solid pieces) or None (not Halo 3, no base map here)."""
    v = mvar.read_h3(path)
    base = v["map"]
    if not v.get("ok") or not os.path.isdir(os.path.join(maps.ROOT, base)):
        return None
    pieces = pieces_of(v)
    objs = read_json(os.path.join(maps.ROOT, base, "objects.json"))
    mine = variants.own([(n, p) for n, p, _ in pieces], variants.base_placed(objs))
    if len(mine) < variants.MIN_OWN:
        return None
    vid = "v" + hashlib.sha1(os.path.basename(path).encode()).hexdigest()[:8]
    name = f"{base}/{variants.SUB}/{vid}"
    old = variants.info(name) or {}
    now = time.strftime("%Y-%m-%d %H:%M")
    keys = sorted({variants._key(n, p) for n, p in mine})
    data = dict(old, id=vid, base=base, game="h3", name=v["title"], first_seen=old.get("first_seen", now),
                last_seen=now, objects=[list(k) for k in keys], count=len(keys),
                window=list(variants.union(old.get("window"), variants.window_of(
                    [p for _, p in mine] + list(variants.base_area(objs))))),
                pieces=[[n] + [round(c, 4) for c in tuple(p) + tuple(x for ax in a for x in ax)] for n, p, a in pieces],
                mvar=dict(file=os.path.basename(path), title=v["title"]))
    variants.save(name, data)
    solid = sum(1 for n, p, a in pieces if forge.block(n, p, a, game="h3"))
    return v["title"], base, name, len(pieces), solid


def main():
    for f in mvar.library("h3"):
        if "LocalFiles" not in f:
            continue
        try:
            got = file_one(f)
        except Exception as e:                  # (one unreadable file never stops the rest)
            print(f"{os.path.basename(f)}: {type(e).__name__}: {e}")
            continue
        if got:
            print(f"{got[0]!r} on {got[1]}: {got[3]} pieces, {got[4]} solid -> {got[2]}")


if __name__ == "__main__":
    main()
