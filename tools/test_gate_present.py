"""Offline check: an Invasion gate stands while ITS object stands at it, not any object (live Boneyard 20261105-033712: a
danger zone marker 0.3 u from the laser field by the drop to the core kept that gate on the nav all phase 3; the
attackers' way down went round it and no core run happened). LiveReach.present on fake memory.

usage: python -I test_gate_present.py      -> "gate present OK"
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.live import LiveReach  # noqa: E402


class Mem:
    def __init__(s):
        s.b = {}

    def put(s, at, data):
        s.b[at] = data

    def read(s, at, n):
        for a, d in s.b.items():
            if a <= at < a + len(d):
                return d[at - a:at - a + n]
        raise OSError(at)


def live_with(objs, names):
    """A LiveReach over fake memory: objs [(tag index, (x, y, z))]; names: the map's tag names."""
    lv = object.__new__(LiveReach)
    m = Mem()
    ents = bytearray(0x18 * len(objs))
    for k, (tag, pos) in enumerate(objs):
        o = 0x10000 + k * 0x1000
        struct.pack_into("<H", ents, k * 0x18, 1)
        struct.pack_into("<Q", ents, k * 0x18 + 0x10, o)
        head = bytearray(0x60)
        struct.pack_into("<I", head, LiveReach.TAG_AT, tag)
        struct.pack_into("<3f", head, LiveReach.POS_AT, *pos)
        m.put(o, bytes(head))
    m.put(0x1000, bytes(ents))
    lv.g = m
    lv._array = lambda ptr: (0x1000, len(objs), 0x18)
    lv._tag_name_list = names
    return lv


def main():
    names = ["objects\\multi\\danger_zone\\danger_zone", "objects\\frigate_laser_field_med\\frigate_laser_field_med"]
    gate = Vec(266.24, 89.4, -5.0)
    marker_only = live_with([(0, (266.31, 89.38, -4.71))], names)
    both = live_with([(0, (266.31, 89.38, -4.71)), (1, (266.24, 89.4, -5.0))], names)
    assert marker_only.present([gate], names=["frigate_laser_field_med"]) == set(), "a marker by the gate is no gate"
    assert both.present([gate], names=["frigate_laser_field_med"]) == {0}, "the laser field itself is"
    assert marker_only.present([gate]) == {0}, "no names: any object, as before"
    no_tags = live_with([(0, (266.31, 89.38, -4.71))], [])
    assert no_tags.present([gate], names=["frigate_laser_field_med"]) == {0}, "the map's names not read: any object"
    print("gate present OK")


if __name__ == "__main__":
    main()
