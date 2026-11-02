"""Every object in the running match (a Forge map's pieces among them), for LiveR's Forge support in every game with Forge.
Like Reach (brain/forge.py), a placed piece is an ordinary object: its tag id, type, position and axes. The object table
and the header's layout differ per game: found here, not assumed: the TLS slot whose table holds valid entries, and the
header offset where a position is followed by two unit, perpendicular axes.

Writes logs/forge/<game>_<map>_<time>.json: {"game", "map", "slot", "pos_at", "objects": [{index, type, tag, pos, fwd,
up}]} (tag: the 32-bit tag id; its low 16 bits are the tag index, named by tools/forge_tags.py).

usage: python -I forge_dump.py <h3|reach|h4|h2a>
"""
import json
import math
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
from brain import live as L  # noqa: E402

SLOTS = (0x10, 0x18, 0x20, 0x38, 0x40)
# position offsets tried: the axes (forward, up) follow the position (Reach +0x44 / +0x50 / +0x5C; Halo 4 +0x64 /
# +0x70 / +0x7C, live on Forge Island: 400 of 400 objects; its +0x40 holds the position too)
POS_AT = tuple(range(0x20, 0x90, 4))
TAG_AT = {"h4": 8, "h2a": 8}   # the object's tag id (Reach +0; Halo 4 +8: all 499 on Forge Island name a tag)


def reader(game):
    if game == "h3":
        return L.LiveH3()
    if game == "reach":
        return L.LiveReach()
    return L.LiveH4F({"h4": "halo4.dll", "h2a": "groundhog.dll"}[game])


def unit(v):
    return abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 0.02


def axes_ok(head, at):
    if not head or at + 36 > len(head):
        return False
    p = struct.unpack_from("<3f", head, at)
    f = struct.unpack_from("<3f", head, at + 12)
    u = struct.unpack_from("<3f", head, at + 24)
    return (all(math.isfinite(x) and abs(x) < 5000 for x in p) and unit(f) and unit(u)
            and abs(sum(a * b for a, b in zip(f, u))) < 0.02)


def table(live, slot):
    try:
        ents, mx, size = live._array(slot)
        if not 0 < mx <= 8192:
            return None
        b = live.g.read(ents, mx * 0x18)
    except Exception:
        return None
    rows = []
    for i in range(mx):
        salt = struct.unpack_from("<H", b, i * 0x18)[0]
        addr = struct.unpack_from("<Q", b, i * 0x18 + 0x10)[0]
        if salt and 0x10000 < addr < 0x7FFFFFFFFFFF:
            rows.append((i, b[i * 0x18 + 3], b[i * 0x18 + 4], addr))
    return rows


def main():
    game = sys.argv[1]
    live = reader(game)
    live.players()                                    # (sets up the TLS block the arrays hang from)
    best = None
    for slot in SLOTS:
        rows = table(live, slot)
        if not rows:
            continue
        heads = {}
        for i, t3, t4, addr in rows:
            try:
                heads[i] = live.g.read(addr, 0xB0)
            except OSError:
                pass
        for at in POS_AT:
            ok = sum(axes_ok(h, at) for h in heads.values())
            if best is None or ok > best[0]:
                best = (ok, slot, at, rows, heads)
    if not best or best[0] < 5:
        sys.exit(f"no object table found ({best[0] if best else 0} objects with axes)")
    ok, slot, at, rows, heads = best
    type_at = 3 if game == "h3" else 4
    objs = []
    for i, t3, t4, addr in rows:
        h = heads.get(i)
        if h is None or not axes_ok(h, at):
            continue
        objs.append(dict(index=i, type=t3 if type_at == 3 else t4, tag=struct.unpack_from("<I", h, TAG_AT.get(game, 0))[0],
                         pos=[round(x, 4) for x in struct.unpack_from("<3f", h, at)],
                         fwd=[round(x, 5) for x in struct.unpack_from("<3f", h, at + 12)],
                         up=[round(x, 5) for x in struct.unpack_from("<3f", h, at + 24)]))
    try:
        mp = live.map_name() if hasattr(live, "map_name") else ""
    except Exception:
        mp = ""
    out_dir = os.path.join(ROOT, "logs", "forge")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{game}_{(mp or 'map').replace(chr(92), '_')}_{time.strftime('%Y%m%d-%H%M%S')}.json")
    json.dump(dict(game=game, map=mp, slot=hex(slot), pos_at=hex(at), objects=objs), open(out, "w"), indent=0)
    types = {}
    for o in objs:
        types[o["type"]] = types.get(o["type"], 0) + 1
    print(f"{len(objs)} objects (table slot {hex(slot)}, position +{hex(at)}), types {dict(sorted(types.items()))} -> {out}")


if __name__ == "__main__":
    main()
