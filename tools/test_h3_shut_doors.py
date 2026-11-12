"""Halo 3 doors and gates that open only by a switch and start shut are walls in the nav (brain/placed.py static_boxes,
tools/h3_machines.py; brain/maps.py gives Halo 3 maps their static boxes). Live High Ground Multi Flag, Nov 12: the base
gate (deadlock_gate_v3) was open floor to the nav; red's runners pressed into it 14 minutes ("step down", "unstuck
wiggle" at (-6, 4, 12)), 0-0, one pickup.

1. High Ground: the gate is a static box; a path from red's base to blue's flag keeps 2 u+ off it (it went through, 0.74)
2. Orbital: its two shut large doors are boxes; Last Resort's bridge (a walkway, shut too) is not
3. a door that opens by itself (no "does not operate automatically") stays out, as before

usage: python -I test_h3_shut_doors.py      -> "h3 shut doors OK"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.placed import static_boxes  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


m = get_map("h3_deadlock")
names = [b[4] for b in static_boxes(m["objects"], "h3")]
check("1. High Ground's gate is a wall", names == ["deadlock_gate_v3"], names)
T = terrain(m)
gate = Vec(-6.1533, 4.2729, 11.5875)
path = T.path_ahead(Vec(-6.0, 9.0, T.nav_z(-6.0, 9.0)), m["flags"][1], n=400)
near = min(math.dist((q.x, q.y), (gate.x, gate.y)) for q in path) if path else 0.0
check("1. red's way out to blue's flag keeps off the gate", bool(path) and near > 2.0, round(near, 2))
orbital = [b[4] for b in static_boxes(get_map("h3_spacecamp")["objects"], "h3")]
check("2. Orbital's shut doors are walls", orbital.count("spacecamp_door_large") == 2, orbital)
docks = [b[4] for b in static_boxes(get_map("h3_docks")["objects"], "h3")]
check("2. Last Resort's bridge is no wall", "bridge00" not in docks, docks)
auto = dict(kind="machines", name="tunnel_door", pos=[0, 0, 0], rot=[0, 0, 0], flags="")
check("3. a door that opens by itself stays out", static_boxes({"placed": [auto]}, "h3") == [])
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("h3 shut doors OK")
