"""Every live Halo: Reach object near a point, by its exact tag name (tools/reach_tag_names.py): what blocks a bot where
the map's exported data has nothing (live, Boneyard Invasion: four attackers stuck at 250.7, 56.5).

usage: python -I objects_near.py <x> <y> <z> [radius 4] [--weapons: every weapon object too]
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.live import LiveReach  # noqa: E402
import reach_tag_names  # noqa: E402


def main():
    x, y, z = (float(v) for v in sys.argv[1:4])
    r = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("-") else 4.0
    live = LiveReach()
    names = reach_tag_names.cached(live.map_name())
    weapons_anywhere = "--weapons" in sys.argv     # every weapon object, wherever (a flag hung under a marker)
    for handle, typ, _, pos in live.objects():
        d = math.dist(pos, (x, y, z))
        if d > r and not (weapons_anywhere and typ == 2):
            continue
        ptr = live.object(handle)
        head = live.g.read(ptr, 0x18) if ptr else bytes(0x18)
        tag, parent = struct.unpack_from("<I", head, 0)[0], struct.unpack_from("<I", head, 0x14)[0]
        name = names[tag & 0xFFFF] if (tag & 0xFFFF) < len(names) else "?"
        print(f"{d:5.2f} type {typ:2d} handle {handle:08x} parent {parent:08x} pos {tuple(round(v, 2) for v in pos)} {name}")


if __name__ == "__main__":
    main()
