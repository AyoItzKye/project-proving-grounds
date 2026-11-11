"""Passive LiDAR (tools/lidar.py HumanWatch) learns the map's lifts, man cannons and teleporters from people in every
match: a ride from (or onto) a lift's or cannon's pad counts without a jump press (H2A and Halo 4 read the press, and
nobody presses jump on a man cannon: 0 rides were kept there), a teleport (moved TELE_JUMP+ in one step, alive, on
foot) is kept per direction in the map's LiDAR data, one-way until someone goes the other way, and the bots' nav gets
every teleport direction people used that the map's own data lacks (brain/maps.py people_teleports).

usage: python -I test_passive_devices.py      -> "passive devices OK"
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from lidar import HumanWatch, Recorder, teleport_ways  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import people_teleports  # noqa: E402

fails = []


def check(what, ok):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        fails.append(what)


DT = 1 / 30


def launch(x0=0.0, z0=0.0, vz=7.0, vx=3.0, g=4.1, land_dz=4.0):
    """A man cannon's throw: 1 s walking onto the pad, the arc, down onto a ledge land_dz up, 6 s standing there."""
    pts = [(x0 - 1.0 + k * DT, 0.0, z0) for k in range(30)]
    t = 0.0
    while True:
        t += DT
        z = z0 + vz * t - g * t * t / 2
        if t > vz / g and z <= z0 + land_dz:
            break
        pts.append((x0 + vx * t, 0.0, z))
    end = (x0 + vx * t, 0.0, z0 + land_dz)
    return pts + [end] * 180


def feed(hw, pts, jump=False, t0=0.0, index=0):
    for k, p in enumerate(pts):
        hw.update(t0 + k * DT, [(index, p, True, False, jump, False)])
    return t0 + len(pts) * DT


tmp = tempfile.mkdtemp()
# 1. a cannon ride with no jump press (H2A / Halo 4 read the press): kept when it starts at a cannon's pad
hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False, path=os.path.join(tmp, "a.json")))
hw.rec.links = []
feed(hw, launch())
check("no pads known: a ride without a jump press is left out (as a push)", not hw.rec.links and hw.skipped == 1)
hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False, path=os.path.join(tmp, "b.json")),
                pads=[(0.0, 0.0, 0.0)])
hw.rec.links = []
feed(hw, launch())
check("from a cannon's pad: the ride is kept without a jump press", len(hw.rec.links) == 1 and hw.skipped == 0)

# 2. teleports: moved 20 u in one step, alive and on foot: kept, counted per direction; the way back makes it two-way
hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False, path=os.path.join(tmp, "c.json")))
a, b = (0.0, 0.0, 0.0), (20.0, 5.0, 2.0)
t = feed(hw, [a] * 10 + [b] * 10)
hw.update(t, [(0, None, False, False, False, False)])      # dies there, respawns by the entrance: no teleport back
t = feed(hw, [(0.3, 0.2, 0.0)] * 10 + [(20.2, 5.1, 2.0)] * 10, t0=t + 3.0)
tp = hw.rec.teleports
check(f"a teleport is kept with its count (got {tp})", len(tp) == 1 and tp[0][2] == 2)
check("one direction only: one-way", teleport_ways(tp) == [(tp[0][0], tp[0][1], "one-way", 2)])
feed(hw, [b] * 10 + [a] * 10, t0=t)
ways = teleport_ways(hw.rec.teleports)
check(f"used both ways: two-way ({ways})", len(ways) == 1 and ways[0][2] == "two-way")
# 3. not teleports: a respawn (dead in between), a vehicle's seat, slow moves
hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False, path=os.path.join(tmp, "d.json")))
hw.update(0.0, [(0, a, True, False, False, False)])
hw.update(DT, [(0, None, False, False, False, False)])
hw.update(2 * DT, [(0, b, True, False, False, False)])
hw.update(3 * DT, [(0, a, True, False, False, True)])
hw.update(4 * DT, [(0, b, True, False, False, True)])
check("a respawn or a ride in a seat is no teleport", not hw.rec.teleports)
# 4. saved with the map's LiDAR data and read back
hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False, path=os.path.join(tmp, "e.json")))
feed(hw, [a] * 5 + [b] * 5)
hw.save()
back = Recorder("_selftest", count_run=False, path=os.path.join(tmp, "e.json"))
check("teleports saved and read back", back.teleports and back.teleports[0][2] == 1)
# 5. the nav: people's teleports the map's data lacks, each direction people used; the map's own pairs not doubled
known = [(Vec(0.0, 0.0, 0.0), Vec(20.0, 5.0, 2.0))]
seen = [[[0.3, 0.2, 0.0], [20.2, 5.1, 2.0], 4], [[20.0, 5.0, 2.0], [0.0, 0.0, 0.0], 1], [[50.0, 0.0, 0.0], [60.0, 0.0, 0.0], 1]]
add = people_teleports(known, seen)
check(f"the nav gets the two directions the map lacks ({add})",
      len(add) == 2 and all(isinstance(p, Vec) for pair in add for p in pair)
      and any(abs(x.x - 20.0) < 0.1 and abs(y.x) < 0.1 for x, y in add) and any(abs(x.x - 50.0) < 0.1 for x, _ in add))
check("and none twice", people_teleports(known + add, seen) == [])

if fails:
    sys.exit(f"FAIL {len(fails)}")
print("passive devices OK")
