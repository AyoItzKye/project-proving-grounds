r"""Halo 3 Forge pieces read live (brain/forge.py live_pieces with LiveH3: TAG_GAME "h3", scenery 6 and crates 10,
position +0x50, forward +0x5C, up +0x68) and the running layout known by the variant file placing them
(brain/mvar.py find_h3; tools/live_bots.py and tools/lidar.py file it with h3_forge_import, so the match's nav has its
pieces). Before: Halo 3 read no pieces live (forge.py knew Reach, Halo 4 and H2A only), so a Halo 3 Forge match ran on
the bare map's nav.

1. a Halo 3 object table in memory (fake reader): scenery and crates come out named by tag index with their position
   and axes; machines (doors, lifts) and markers left out
2. find_h3 (skipped when MCC is not found): the live pieces of a Sandbox variant (the player's ALL ITEMS when here, else
   a built-in one) pick that file, not another Sandbox file; with a third of them moved 2 m (edited since) still that
   file; the bare map (no Forge pieces, or only the map's own scenery) none
3. filing the found file gives the variant folder with its pieces (h3_forge_import.file_one); MCC's copy of the
   running variant (Temporary\UserContent, a new name each match) loses a tie to the player's own file and files
   into the same folder

usage: python -I test_h3_live_pieces.py      -> "h3 live pieces OK"
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from brain import forge, mvar  # noqa: E402
from brain.live import LiveH3  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


class Mem:
    def __init__(s):
        s.blobs = {}

    def read(s, a, n):
        for base, b in s.blobs.items():
            if base <= a and a + n <= base + len(b):
                return b[a - base:a - base + n]
        raise OSError("unmapped")


class FakeH3:
    TAG_GAME, TAG_AT, TYPE_AT, OBJECTS_AT = LiveH3.TAG_GAME, LiveH3.TAG_AT, LiveH3.TYPE_AT, LiveH3.OBJECTS_AT
    _blk = 1

    def __init__(s, objs, names):
        s.g, s._tag_name_list = Mem(), names
        ents = bytearray(0x18 * len(objs))
        for i, (typ, tag, pos, fw, up) in enumerate(objs):
            addr = 0x100000 + i * 0x1000
            struct.pack_into("<HxB", ents, i * 0x18, 1, typ)
            struct.pack_into("<Q", ents, i * 0x18 + 0x10, addr)
            o = bytearray(0x80)
            struct.pack_into("<I", o, 0, 0xE0000000 | tag)
            struct.pack_into("<3f3f3f", o, 0x50, *pos, *fw, *up)
            s.g.blobs[addr] = bytes(o)
        s.g.blobs[0x10] = bytes(ents)
        s.n = len(objs)

    def _array(s, off):
        return 0x10, s.n, 0x18


names = ["", "objects\\levels\\shared\\golf_ball\\block_large", "objects\\levels\\shared\\barricade_large",
         "objects\\levels\\shared\\door_large", "objects\\multi\\spawning\\respawn_point"]
fake = FakeH3([(6, 1, (1.0, 2.0, 3.0), (0, 1, 0), (0, 0, 1)), (10, 2, (4.0, 5.0, 6.0), (1, 0, 0), (0, 0, 1)),
               (7, 3, (0.0, 0.0, 0.0), (1, 0, 0), (0, 0, 1)), (6, 4, (9.0, 9.0, 9.0), (1, 0, 0), (0, 0, 1))], names)
got = forge.live_pieces(fake)
check("1. scenery and crates read, named, machines and markers out",
      [p[0] for p in got] == ["block_large", "barricade_large"], got)
check("1. position and axes from +0x50 / +0x5C / +0x68",
      got and got[0][1] == (1.0, 2.0, 3.0) and got[0][2][0] == (0, 1, 0) and got[0][2][1] == (-1, 0, 0), got[:1])

files = [f for f in mvar.library("h3")]
if not files:
    print("  (MCC not found: parts 2-3 skipped)")
else:
    import h3_forge_import as imp
    sand = []
    for f in files:
        try:
            v = mvar.read_h3(f)
        except Exception:
            continue
        if v["ok"] and v["map"] == "h3_sandbox":
            sand.append(v)
    kinds = mvar.json.load(open(mvar.H3_PALETTES))
    pal = next(v for v in kinds.values() if v["map"] == "h3_sandbox")
    forge_names = {n for k in mvar.H3_FORGE_KINDS for n in pal["kinds"].get(k, [])}
    with_pieces = [v for v in sand if sum(1 for o in v["objects"] if o["placed"] and o["name"] in forge_names) >= 10]
    pick = next((v for v in with_pieces if v["title"] == "H3 ALL ITEMS"), with_pieces[0] if with_pieces else None)
    check("2. a Sandbox file with Forge pieces on this PC", pick is not None, len(sand))
    if pick:
        live = imp.pieces_of(pick)
        v, share = mvar.find_h3("h3_sandbox", live, files=[s["path"] for s in sand])
        check(f"2. its live pieces pick its file ({pick['title']!r}, {len(sand)} Sandbox files)",
              v is not None and v["path"] == pick["path"], (v and v["title"], share))
        moved = [(n, (p[0] + 2.0, p[1], p[2]) if k % 3 == 0 else p, a) for k, (n, p, a) in enumerate(live)]
        v2, s2 = mvar.find_h3("h3_sandbox", moved, files=[s["path"] for s in sand])
        check("2. a third moved 2 m (edited since): still that file", v2 is not None and v2["path"] == pick["path"],
              (v2 and v2["title"], s2))
        own = [n for k in ("8",) for n in pal["kinds"].get(k, []) if n not in forge_names][:3]
        bare = [(n, (0.0, 0.0, 0.0), ((1, 0, 0), (0, 1, 0), (0, 0, 1))) for n in own]
        check("2. the bare map: no file", mvar.find_h3("h3_sandbox", [])[0] is None
              and mvar.find_h3("h3_sandbox", bare, files=[s["path"] for s in sand])[0] is None)
        filed = imp.file_one(pick["path"], "h3")
        check("3. filed as a variant with its pieces", filed is not None and "/variants/" in filed[2] and filed[4] > 0,
              filed)
        # MCC copies the running variant to Temporary\UserContent under a new name at every match start: live, the copy
        # won the tie (newer) and filed a second folder for the same layout
        copies = [s["path"] for s in sand if s["title"] == pick["title"] and s["path"] != pick["path"]
                  and "LocalFiles" in pick["path"]]
        if copies:
            v3, _ = mvar.find_h3("h3_sandbox", live, files=copies + [pick["path"]])
            check("3. a tie goes to the player's own file, not MCC's match copy", v3 and v3["path"] == pick["path"],
                  v3 and v3["path"])
            check("3. the match copy files into the same folder", imp.file_one(copies[0], "h3")[2] == filed[2])
            imp.file_one(pick["path"], "h3")
        else:
            print("  (no match copy of the player's file: the tie checks skipped)")
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("h3 live pieces OK")
