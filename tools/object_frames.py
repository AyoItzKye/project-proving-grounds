"""Objects near a point in the running Halo: Reach match, with their type, tag and orientation (forward +0x50, up +0x5C
after the position +0x44): to check how a placement's rotation (yaw, pitch, roll) turns into the object's axes
(brain/placed.py frame) against the game itself.

usage: python -I object_frames.py x y z [radius=3]
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))


def main():
    x, y, z = (float(v) for v in sys.argv[1:4])
    r = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
    from brain.live import LiveReach
    live = LiveReach()
    live.players()
    ents, mx, _ = live._array(live.OBJECTS_AT)
    b = live.g.read(ents, mx * 0x18)
    for i in range(mx):
        if not struct.unpack_from("<H", b, i * 0x18)[0]:
            continue
        typ = b[i * 0x18 + 4]
        o = struct.unpack_from("<Q", b, i * 0x18 + 0x10)[0]
        try:
            head = live.g.read(o, 0x70)
        except OSError:
            continue
        pos = struct.unpack_from("<3f", head, 0x44)
        if math.dist(pos, (x, y, z)) > r:
            continue
        fwd, up = struct.unpack_from("<3f", head, 0x50), struct.unpack_from("<3f", head, 0x5C)
        tag = struct.unpack_from("<I", head, 0)[0]
        print(f"type {typ} tag {tag:#010x} pos {[round(v, 2) for v in pos]} fwd {[round(v, 3) for v in fwd]} "
              f"up {[round(v, 3) for v in up]}")


if __name__ == "__main__":
    main()
