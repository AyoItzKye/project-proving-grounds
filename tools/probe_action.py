"""Read-only: show each player's remote-action slot (+0x8f0 queue, +0x910 flag, +0x914 last action)
and the 4 local input slots (halo1+0x2b776fc, 0x30 each), as floats/ints.

usage: python -I probe_action.py          dump the action slots
       python -I probe_action.py pos      each player's unit position, facing (object +0x18, +0x30)
"""
import struct
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memread import Game  # noqa: E402

PLAYERS_PTR = 0x1C40480
LOCAL_INPUT = 0x2B776FC
OBJECT_HEADERS_PTR = 0x1C42248   # data array of 0xC-byte object headers (+8 = offset in the pool)
OBJECT_POOL_PTR = 0x2D9CDF8      # object = [this] + 0x34 + offset (halo1+0xB389A4)


def unit_pos(g, handle):
    if handle == 0xFFFFFFFF:
        return None
    oh = g.u64(g.base + OBJECT_HEADERS_PTR)
    rel = struct.unpack("<i", g.read(oh + 0x34, 4))[0]
    off = struct.unpack("<i", g.read(oh + rel + (handle & 0xFFFF) * 0xC + 8, 4))[0]
    o = g.u64(g.base + OBJECT_POOL_PTR) + 0x34 + off
    return struct.unpack("<3f", g.read(o + 0x18, 12)), struct.unpack("<3f", g.read(o + 0x30, 12))


def show(tag, b):
    u = struct.unpack("<12I", b)
    f = struct.unpack("<12f", b)
    print(tag, " ".join(f"{x:08x}" for x in u))
    print(" " * len(tag), " ".join(f"{x:8.3f}" if abs(x) < 1e4 and x == x else "    ----" for x in f))


g = Game()
hdr = g.u64(g.base + PLAYERS_PTR)
mx, size = struct.unpack("<hh", g.read(hdr + 0x20, 4))
rel = struct.unpack("<i", g.read(hdr + 0x34, 4))[0]
for i in range(16):
    p = hdr + rel + i * size
    salt = struct.unpack("<H", g.read(p, 2))[0]
    if not salt:
        continue
    if sys.argv[1:2] == ["pos"]:
        unit = struct.unpack("<I", g.read(p + 0x64, 4))[0]
        r = unit_pos(g, unit)
        print(i, f"unit {unit:08x}", "dead" if not r else
              "pos %.2f %.2f %.2f  fwd %.2f %.2f %.2f" % (*r[0], *r[1]))
        continue
    q = g.read(p + 0x8f0, 0x18)
    print(f"player {i} salt {salt:04x} queue ptr {struct.unpack_from('<Q', q, 8)[0]:x} "
          f"tail {struct.unpack_from('<i', q, 0x10)[0]} head {struct.unpack_from('<i', q, 0x14)[0]} "
          f"has_last {g.read(p + 0x910, 1)[0]}")
    show("  last", g.read(p + 0x914, 0x30))
for k in range(2 if sys.argv[1:2] != ["pos"] else 0):
    show(f"local{k}", g.read(g.base + LOCAL_INPUT + k * 0x30, 0x30))
