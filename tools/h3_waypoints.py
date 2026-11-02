"""Halo 3's HUD waypoints (the host's, TLS slot 0xF0, 0x74 bytes each; brain/live.py LiveH3.king_hill) in a running
match: every entry that names an object, with its kind (+0x10), scale (+0x14), place (+0x24), shown flag (+0x30), and
the player whose body (unit) the object is. For finding how a mode marks its special player (Juggernaut, VIP).

usage: python -I h3_waypoints.py [--every S --for S]     (once, or every S seconds for a while)
"""
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.live import LiveH3, NONE  # noqa: E402


def dump(L):
    ps = L.players()
    units = {p["unit"]: p for p in ps if p.get("unit") not in (None, NONE)}
    byidx = {p["index"]: p for p in ps}
    base = L.g.u64(L._blk + L.HUD_WAYPOINTS) if L._blk else 0
    b = L.g.read(base, 0x3000) if base else b""
    rows = []
    for o in range(0, len(b) - 0x74, 4):
        h = struct.unpack_from("<I", b, o)[0]
        if h == NONE or not h or (h >> 16) == 0:
            continue
        kind, scale = struct.unpack_from("<I", b, o + 0x10)[0], struct.unpack_from("<f", b, o + 0x14)[0]
        shown = struct.unpack_from("<I", b, o + 0x30)[0]
        if kind > 0xFFFF or not (0.0 < scale < 100.0) or shown > 1:
            continue
        pos = struct.unpack_from("<3f", b, o + 0x24)
        who = units.get(h) or (byidx.get(h & 0xFFFF) if (h >> 16) & 0xFF00 == 0xEC00 else None)   # (a player datum)
        rows.append((o, h, kind, scale, shown, pos, who))
    print(f"t {time.strftime('%H:%M:%S')} players: " + ", ".join(
        f"{p['name']}(team {p.get('team')}, unit {p['unit']:08x})" for p in ps if p.get("unit") not in (None, NONE)))
    for o, h, kind, scale, shown, pos, who in rows:
        print(f"  +{o:04x} obj {h:08x} kind {kind:#x} scale {scale:.2f} shown {shown} at "
              f"({pos[0]:.1f},{pos[1]:.1f},{pos[2]:.1f})" + (f"  = {who['name']} (team {who.get('team')})" if who else ""))


def main():
    a = sys.argv[1:]
    every = float(a[a.index("--every") + 1]) if "--every" in a else 0
    span = float(a[a.index("--for") + 1]) if "--for" in a else 0
    L = LiveH3()
    t0 = time.time()
    while True:
        dump(L)
        if not every or time.time() - t0 > span:
            break
        time.sleep(every)


if __name__ == "__main__":
    main()
