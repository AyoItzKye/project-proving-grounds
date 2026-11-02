"""Rides into the map's LiDAR data:

1. drive mesh: a Warthog driven through ground the vehicle nav left out (beside a wall) makes it the vehicles' ground
2. air mesh: a Banshee flight gives one take-off, one landing, a turn-back, the strafing and travelling heights from
   its own height over the floor, and flown cells in the low and high layers
3. a pilot travels at the learned height
4. a LiDAR save with weapons in it
5. a Forge layout's notes go straight into logs/ (its map name has slashes: the run died on the player's first pickup)

usage: python -I test_rides.py      -> "rides OK"
"""
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain, rides_layers  # noqa: E402
import lidar  # noqa: E402


def main():
    fails = []
    m = get_map("bloodgulch")
    T = terrain(m)
    T._build_vnav()
    import numpy as np
    # 1. walkable ground beside a wall, left out of the vehicles' ground: a strip of 6 cells next to its edge
    ls, js, is_ = np.nonzero(T.lwalk & ~T.vroomy & T.reach)
    strip = None
    for k in range(0, len(ls), 97):
        l, j, i = int(ls[k]), int(js[k]), int(is_[k])
        cells = [(l, j, i + d) for d in range(6)]
        if all(0 <= c[2] < T.nw and T.lwalk[c] and not T.vroomy[c] and np.isfinite(T.lz[c]) for c in cells) \
                and abs(float(T.lz[cells[-1]]) - float(T.lz[cells[0]])) < 0.3:
            strip = cells
            break
    if strip is None:
        fails.append("no strip of left-out walkable ground found on Blood Gulch")
    else:
        rw = lidar.RideWatch("bloodgulch", T=T, path=os.path.join(tempfile.mkdtemp(), "rides.json"))
        for k, c in enumerate(strip * 2):                 # driven along it, a person at the wheel
            p = T._center(*c)
            v = [dict(handle=7, kind="warthog", pos=(p.x, p.y, p.z), riders=1)]
            rw.update(10.0 + k * 0.1, v, [PlayerState(0, 0, "you", p, vehicle=7)], set())
        rw.save()
        drive, air, heights, marks = rides_layers([os.path.dirname(rw.path)], T, files=[rw.path])
        T.add_rides(drive, air, heights, marks)
        T._build_vnav()
        got = sum(bool(T.vroomy[c]) for c in strip)
        if got < 5:
            fails.append(f"drive mesh: {got} of 6 driven cells beside the wall are vehicle ground after the drive")
    # 2. a Banshee flight over the canyon: on the ground, up to 3 u, along at 3 u, up to 12 u, along, a turn back,
    #    down, landed
    x0, y0 = 60.0, -100.0
    g = lambda x, y: T.ground(x, y)
    rw = lidar.RideWatch("bloodgulch", T=T, path=os.path.join(tempfile.mkdtemp(), "rides.json"))
    t, x, y = 20.0, x0, y0
    plan = [(0.0, 3)] + [(min(3.0, 0.5 * k), 1.5) for k in range(1, 8)] + [(3.0, 1.5)] * 30 + \
           [(3.0 + 0.9 * k, 1.5) for k in range(1, 11)] + [(12.0, 1.5)] * 30
    path = []
    for h, step in plan:                                  # out along +x
        x += step
        path.append((x, y, h))
    for k in range(12):                                   # the turn back (a half circle)
        a = math.pi * (k + 1) / 12
        path.append((x + 2.0 * math.sin(a), y + 2.0 - 2.0 * math.cos(a), 12.0))
    x, y = path[-1][0], path[-1][1]
    for k in range(30):                                   # back along -x, then down onto the ground
        x -= 1.5
        h = 12.0 if k < 18 else max(0.0, 12.0 - (k - 17) * 1.2)
        path.append((x, y, h))
    path += [(x, y, 0.0)] * 5
    for (px, py, h) in path:
        t += 0.25
        z = g(px, py) + h
        v = [dict(handle=9, kind="banshee", pos=(px, py, z), riders=1)]
        rw.update(t, v, [PlayerState(0, 0, "you", Vec(px, py, z), vehicle=9)], set())
    rw.save()
    drive, air, heights, marks = rides_layers([os.path.dirname(rw.path)], T, files=[rw.path])
    if len(marks.get("takeoff", [])) != 1 or len(marks.get("landing", [])) != 1 or not marks.get("turnback"):
        fails.append(f"flight marks: take-offs {len(marks.get('takeoff', []))}, landings {len(marks.get('landing', []))}, "
                     f"turn-backs {len(marks.get('turnback', []))} (want 1, 1, 1+)")
    if heights is None or not (2.0 <= heights[0] <= 4.5 and 10.5 <= heights[1] <= 13.5):
        fails.append(f"flight heights {heights} (want strafing about 3, travelling about 12 over the floor)")
    if not air.get("low") or not air.get("high"):
        fails.append(f"air cells: low {len(air.get('low', {}))}, high {len(air.get('high', {}))} (want both)")
    # 3. a pilot with those heights climbs toward 12 u when travelling (6 u over the floor now)
    from brain.bot import Action, Bot
    from brain.profiles import make_profile
    T.add_rides({}, {}, (3.0, 12.0), {})
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    b._terrain = T
    p = Vec(x0, y0, g(x0, y0) + 6.0)
    me = PlayerState(1, 0, "b", p, vehicle=5)
    b.seat_for, b.seat_since, b.seat, b.drive_to = 5, 0.0, "driver", Vec(x0 + 60.0, y0, g(x0, y0))
    a = Action()
    b.drive(5.0, 1 / 30, me, Snapshot(5.0, [me], vehicles=[dict(handle=5, kind="banshee", pos=(p.x, p.y, p.z), riders=1,
                                                                        occupied=True, fwd=(1.0, 0.0, 0.0))]),
            a, lambda q, r, **k: r)
    if not a.pitch > 0.2:
        fails.append(f"pilot 6 u over the floor, travelling height 12: pitch {a.pitch:.2f} (want climbing)")
    # ... and 5 u from where it goes, it comes down to land (it held its height and circled there, Spire)
    b.drive_to, a = Vec(x0 + 5.0, y0, g(x0, y0)), Action()
    b.drive(6.0, 1 / 30, me, Snapshot(6.0, [me], vehicles=[dict(handle=5, kind="banshee", pos=(p.x, p.y, p.z), riders=1,
                                                                        occupied=True, fwd=(1.0, 0.0, 0.0))]),
            a, lambda q, r, **k: r)
    if not a.pitch < -0.2:
        fails.append(f"pilot 5 u from its destination, 6 u up: pitch {a.pitch:.2f} (want coming down to land)")
    # 3b. a Falcon climbs on its vertical input, not its pitch (live, tools/falcon_probe.py: pitch and forward moved
    #     a landed Falcon 0.00 u; +1 at Reach's +0x3C climbed it 6.8 u in 6 s, 0 sank it, +0.5 held it): on the ground it
    #     goes up, at its travelling height it holds, by where it goes it comes down
    def falcon(h, to, t):
        q = Vec(x0, y0, g(x0, y0) + h)
        fm = PlayerState(1, 0, "b", q, vehicle=6)
        b.seat_for, b.seat_since, b.seat, b.drive_to = 6, 0.0, "driver", to
        fa = Action()
        b.drive(t, 1 / 30, fm, Snapshot(t, [fm], vehicles=[dict(handle=6, kind="falcon", pos=(q.x, q.y, q.z), riders=1,
                                                                 occupied=True, fwd=(1.0, 0.0, 0.0))]),
                fa, lambda q1, r, **k: r)
        return fa.vertical
    far, near = Vec(x0 + 60.0, y0, g(x0, y0)), Vec(x0 + 5.0, y0, g(x0, y0))
    for h, to, want, what in ((0.0, far, 1.0, "on the ground, going 60 u: up"), (12.0, far, 0.5, "at its 12 u: holding"),
                              (6.0, near, -1.0, "6 u up, 5 u from where it goes: down")):
        got = falcon(h, to, 10.0 + h)
        if got != want:
            fails.append(f"Falcon {what}: vertical {got} (want {want})")
    # 4. a LiDAR save with weapons in it (since 7f95635 its copy did dict() on the list of weapon records and every save
    #    on a map with weapons stored failed: the player's Lockout match of kept nothing)
    rec = lidar.Recorder("bloodgulch", count_run=False, path=os.path.join(tempfile.mkdtemp(), "lidar.json"))
    rec.found_weapon("rockets", (1.0, 2.0, 3.0), "seen")
    try:
        rec.save()
        got = lidar.load(rec.path).get("weapons", [])
        if not (isinstance(got, list) and got and got[0].get("name") == "rockets"):
            fails.append(f"LiDAR save: weapons stored as {got!r} (want the list of records)")
    except Exception as e:
        fails.append(f"LiDAR save with a weapon found failed: {type(e).__name__}: {e}")
    # 5. a Forge layout's file names (in a Forge session the run died
    #    on his first pickup, its note sent to logs/owner_pickups_reach_forge_halo/variants/..., a folder not there)
    for name in ("reach_forge_halo/variants/v4f12d627", "bloodgulch"):
        p = lidar.pickups_path(name)
        if os.path.dirname(os.path.abspath(p)) != os.path.abspath(os.path.join(lidar.ROOT, "logs")):
            fails.append(f"pickup notes of {name} go to {p} (want straight into logs/)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"rides OK (heights {heights[0]:.1f} / {heights[1]:.1f}, {len(air['low'])} low and {len(air['high'])} high cells)")


if __name__ == "__main__":
    main()
