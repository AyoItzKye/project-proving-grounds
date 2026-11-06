"""Your line of sight, crosshair and buttons for the Observer:

1. Terrain.aim_hit on Forge World: a look down meets the floor at your feet; a look up from open ground meets
   nothing (sky); a level look stops where the brain's own line of sight (_ray) stops: clear just short, blocked past;
   on a made-up flat level a look meets nothing past the map's edge
2. tracefmt.crosshair: on a player in front (his id), on a vehicle ("v<handle>"); in a vehicle, the vehicle, its gun
   and who rides with you are passed over; nothing ahead and no level: None; dead: None
3. Everyone.rows: your row gets your crosshair and ride (15, 16), a bot's row stays 15 long
4. observer.aim_text says it in words; the Observer has no key reader (no keys are recorded)

usage: python -I test_crosshair.py      -> "crosshair OK"
"""
import math
import os
import sys
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import PlayerState, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import EYE, Terrain  # noqa: E402
from brain.tracefmt import Everyone, crosshair, seat_of  # noqa: E402
import observer  # noqa: E402

M = get_map("reach_forge_halo")
T = terrain(M)


def ray_dir(yaw, pitch):
    return Vec(math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))


def main():
    fails = []
    # 1. the level
    open_ground = [z.center for z in M["zones"].zones if abs(float(T.top_at(z.center.x, z.center.y)) - z.center.z) < 0.5]
    if not open_ground:
        fails.append("1. no zone centre on open ground to look up from")
    for c in open_ground:
        o = c + Vec(0.0, 0.0, EYE)
        down = T.aim_hit(o, 0.0, -1.2)
        if down is None or (down - c).length() > 1.0:
            fails.append(f"1. a look down from {c}: {down} (want the floor at the feet)")
        up = T.aim_hit(o, 0.0, 1.4)
        if up is not None:
            fails.append(f"1. a look up from open ground at {c}: {up} (want the sky, None)")
    c = M["zones"].zones[0].center
    o, checked = c + Vec(0.0, 0.0, EYE), 0
    feet = Vec(o.x, o.y, o.z - EYE)
    for k in range(8):
        yaw = k * math.pi / 4
        h = T.aim_hit(o, yaw, 0.0)
        if h is None:
            continue
        L, d = (h - o).length(), ray_dir(yaw, 0.0)
        if L < 1.0:
            continue
        checked += 1
        short, past = o + d * (L - 0.4), o + d * (L + 0.6)
        if not T._ray(feet, short, 0.0, "see") or T._ray(feet, past, 0.0, "see"):   # (the view line: windows pass)
            fails.append(f"1. a level look at yaw {math.degrees(yaw):.0f}: stops {L:.1f} u out; the brain's line of sight "
                         f"short of it {T._ray(feet, short, 0.0, 'see')}, past it {T._ray(feet, past, 0.0, 'see')} (want clear, blocked)")
    if not checked:
        fails.append("1. no level look met anything to check against")
    # the map's edge: a made-up 10 x 10 u flat level; a look sloping down to meet its ground 3 u past the edge meets
    # nothing (the cells past the edge are not there: read clipped, they would be the edge's own ground)
    flat = types.SimpleNamespace(x0=0.0, y0=0.0, w=40, h=40, cell=0.25, low=np.zeros((40, 40)),
                                 floors=np.full((1, 40, 40), np.nan), walls=np.zeros((40, 40, 1), np.uint64),
                                 wall_z0=-10.0, wall_bin=1.0)
    flat._ij = types.MethodType(Terrain._ij, flat)
    flat._wall_bit = types.MethodType(Terrain._wall_bit, flat)
    past = Terrain.aim_hit(flat, Vec(5.0, 5.0, 3.0), 0.0, -math.atan2(3.0, 8.0))
    inside = Terrain.aim_hit(flat, Vec(5.0, 5.0, 3.0), 0.0, -math.atan2(3.0, 4.0))
    if past is not None or inside is None or abs(inside.x - 9.0) > 0.3:
        fails.append(f"1. a flat 10 u level: a look down to its ground 3 u past the edge {past} (want None), 1 u short "
                     f"of it {inside} (want x 9)")
    # 2. players and vehicles under the crosshair (no level: T None)
    me = PlayerState(0, 0, "you", Vec(0.0, 0.0, 0.0), is_bot=False)
    foe = PlayerState(1, 1, "bot", Vec(10.0, 0.0, 0.0))
    hog = dict(handle=7, kind="warthog", pos=(6.0, 0.0, 0.6))
    got = crosshair(me, [me, foe], [], None)
    if not got or got[3] != 1 or abs(got[0] - 10.0) > 0.7:
        fails.append(f"2. a man 10 u ahead: {got} (want on #1, 10 u out)")
    got = crosshair(me, [me, foe], [hog], None)
    if not got or got[3] != "v7":
        fails.append(f"2. a Warthog 6 u ahead of him: {got} (want on the Warthog, v7: it is nearer)")
    rider = PlayerState(0, 0, "you", Vec(0.0, 0.0, 0.0), is_bot=False, vehicle=7, gunner_seat=True, turret="warthog_gauss")
    mine = dict(handle=7, kind="warthog", pos=(0.5, 0.0, 0.0))
    gun = dict(handle=8, kind="warthog_gauss", pos=(1.5, 0.0, 0.6))
    driver = PlayerState(2, 0, "mate", Vec(1.0, 0.0, 0.0), vehicle=7)
    got = crosshair(rider, [rider, driver, foe], [mine, gun], None)
    if not got or got[3] != 1:
        fails.append(f"2. on a Warthog's gun, a man 10 u ahead: {got} (want on #1: the Warthog, its gun and its driver "
                     "passed over)")
    if seat_of(rider, [mine, gun]) != ["warthog", "warthog_gauss"] or seat_of(me, [mine]) is not None:
        fails.append(f"2. rides: {seat_of(rider, [mine, gun])}, {seat_of(me, [mine])} (want warthog on its gauss gun, "
                     "None on foot)")
    away = PlayerState(0, 0, "you", Vec(0.0, 0.0, 0.0), yaw=math.pi, is_bot=False)
    if crosshair(away, [away, foe], [hog], None) is not None:
        fails.append("2. looking away from everyone with no level: not None")
    if crosshair(PlayerState(0, 0, "you", Vec(), alive=False, is_bot=False), [foe], [], None) is not None:
        fails.append("2. dead: not None")
    with_level = crosshair(PlayerState(0, 0, "you", c, pitch=-1.2, is_bot=False), [], [], T)
    if not with_level or with_level[3] is not None or math.dist(with_level[:3], (c.x, c.y, c.z)) > 1.0:
        fails.append(f"2. looking down on Forge World: {with_level} (want the level at the feet, on None)")
    # 3. the world rows
    rows = Everyone().rows(1.0, [me, foe], {1}, lambda p, q: True, {0: ([10.0, 0.0, 0.4, 1], None)})
    if len(rows[0]) != 17 or rows[0][15:] != [[10.0, 0.0, 0.4, 1], None] or len(rows[1]) != 15:
        fails.append(f"3. world rows {rows} (want your crosshair and ride at 15, 16; the bot's row 15 long)")
    # 4. in words; no key reader
    if hasattr(observer, "key_events") or hasattr(observer, "held_at"):
        fails.append("4. the Observer still reads keys")
    words = observer.aim_text([0, 0, 1, 0.0, 0.0, 0.0, 1, 1, 0, 0, 0, 0, 0, [], 1, [10.0, 0.0, 0.4, 1],
                               ["warthog", "warthog_gauss"]])
    if "crosshair on #1" not in words or "10.0 u off" not in words or "riding warthog on its warthog_gauss" not in words:
        fails.append(f"4. in words: {words!r}")
    if fails:
        sys.exit("crosshair FAILED:\n  " + "\n  ".join(fails))
    print("crosshair OK")


if __name__ == "__main__":
    main()
