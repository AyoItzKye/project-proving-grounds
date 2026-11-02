"""Vehicles keep the player's distance from walls and objects (his Forge World runs measured by tools/vehicle_clearance.py
into brain/vehicles.py CLEARANCE, TAKE_OFF, TRAVEL_BOOST and Bot's CHAINGUN_HEAT), on Halo 3's Sidewinder:

1. the look ahead goes by his seconds, not a fixed 12 u: a Sabre at 20 u/s sees a wall 30-45 u off and turns or
   climbs; a Banshee at 4 u/s does not react to it yet
2. take-offs: a Falcon just in climbs straight up (no throttle) until 2.5 u over its floor; a Sabre just in has its
   nose up and, facing a wall close ahead, launches toward a heading open for its 3 s
3. room at the sides: a Banshee at speed 4 u off a wall beside it eases away from it; 8+ u off anything, untouched
4. height: a Banshee at speed under 6.8 u over the floors ahead pulls up; one 12 u over open ground does not
5. Reach's chaingun: held on, a gunner fires 13.5 s, is off 3.3 s, fires again
6. the travel boost: a Ghost on a long open leg holds it 1.7 s, is off 3.6 s, holds it again; facing a wall close
   ahead it does not
7. the vehicles' ground keeps off walls: a long drive's route points stand farther from walls with the wall cost
   (Terrain.VEH_WALL_COST) than without, and it still arrives

usage: python -I test_vehicle_clearance.py      -> "vehicle clearance OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain import vehicles  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import Terrain  # noqa: E402
import vehicle_clearance as VC  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
OPEN = Vec(-43.0, 42.0, 21.59)        # 10 u over the floor, every heading 12 u clear (test_air_stuck)


def pilot(kind, since=-10.0, game="h3"):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, rng=random.Random(1))
    b._terrain, b.seat, b.seat_since, b.game = T, "driver", since, game
    return b


def guard(b, kind, pos, yaw, speed, now=0.0, act=None):
    """One air_guard tick; (act, its notes)."""
    b.now, b.notes, b.landing = now, [], False
    me = PlayerState(1, 0, "pilot", pos, vel=Vec(math.cos(yaw) * speed, math.sin(yaw) * speed, 0.0), yaw=yaw,
                     alive=True, vehicle=9)
    act = act or Action(yaw=yaw)
    if act.forward == 0.0:
        act.forward = 1.0
    snap = Snapshot(now, [me], vehicles=[dict(handle=9, kind=kind, pos=(pos.x, pos.y, pos.z), occupied=True, riders=1,
                                              team=0, fwd=(math.cos(yaw), math.sin(yaw), 0.0))])
    b.air_guard(me, act, snap)
    return act, " / ".join(b.notes)


def main():
    fails = []
    floor = OPEN.z - T.height_over(OPEN.x, OPEN.y, OPEN.z)
    # the spots (logs/tmp/find_spots.py): WALL44, 10 u over the floor, a wall 44 u off due east and every heading 12 u
    # clear; PAD, on the ground with a wall 0.8 u off at 310 deg, open 60 u another way; SIDE, 10 u over the floor, open
    # 30 u at 140 deg with a wall 3.6 u off its right
    WALL44, PAD, SIDE = Vec(-52.0, -32.0, 16.82), Vec(-52.0, -44.0, 10.99), Vec(-52.0, -40.0, 10.0)
    over = lambda p: p.z - T.height_over(p.x, p.y, p.z)
    # 1. the look ahead
    d = T.fly_clear(WALL44, 0.0, 60.0, floor=over(WALL44))
    a, n = guard(pilot("sabre"), "sabre", WALL44, 0.0, 20.0)
    if not 30.0 <= d <= 45.0 or "wall ahead" not in n:
        fails.append(f"1. a Sabre at 20 u/s, a wall {d:.0f} u ahead: {n or 'no reaction'} (want a reaction)")
    a, n = guard(pilot("banshee"), "banshee", WALL44, 0.0, 4.0)
    if "wall ahead" in n:
        fails.append(f"1. a Banshee at 4 u/s reacted to a wall {d:.0f} u ahead ({n})")
    # 2. take-offs, just in, on the ground
    gz = over(PAD)
    a, n = guard(pilot("falcon", since=0.0), "falcon", PAD, 0.0, 0.0, now=0.5)
    if not (a.forward == 0.0 and a.strafe == 0.0 and a.vertical == 1.0 and "straight up" in n):
        fails.append(f"2. a Falcon just in: forward {a.forward}, vertical {a.vertical} ({n}; want straight up)")
    blocked = math.radians(310.0)
    a, n = guard(pilot("sabre", since=0.0), "sabre", PAD, blocked, 0.0, now=0.2, act=Action(yaw=blocked))
    need = vehicles.clearance("sabre")["ttc"] * vehicles.spec("sabre")["speed"]
    was, now_ = T.fly_clear(PAD, blocked, need, floor=gz), T.fly_clear(PAD, a.yaw, need, floor=gz)
    if a.pitch < 0.1 or "toward open air" not in n or now_ <= was + 5.0:         # (nose up: his 1-13 deg)
        fails.append(f"2. a Sabre just in facing a wall {was:.1f} u off: pitch {a.pitch:.2f}, launched toward {now_:.1f} u "
                     f"of open air ({n}; want its nose up and a more open heading)")
    # 3. room at the sides
    y = math.radians(140.0)
    a, n = guard(pilot("banshee"), "banshee", SIDE, y, 6.0)
    turned = math.atan2(math.sin(a.yaw - y), math.cos(a.yaw - y))
    if "too near" not in n or turned <= 0.0:          # (the wall on its right: away is left, a positive turn)
        fails.append(f"3. a Banshee with a wall 3.6 u to its right: turned {math.degrees(turned):+.0f} deg ({n}; want left)")
    a, n = guard(pilot("banshee"), "banshee", OPEN + Vec(0, 0, 4.0), 0.0, 6.0)
    if "too near" in n:
        fails.append(f"3. a Banshee in open air eased off ({n})")
    ground = PAD
    # 4. height
    low = Vec(OPEN.x, OPEN.y, floor + 5.0)
    a, n = guard(pilot("banshee"), "banshee", low, 0.0, 6.0)
    if "pull up" not in n:
        fails.append(f"4. a Banshee 5 u over the floor at speed: no pull up ({n or 'no notes'})")
    # 5. the chaingun
    b, dt, fired, t = pilot("warthog", game="reach"), 1.0 / 30.0, [], 0.0
    while t < 40.0:
        fired.append((t, b.chaingun_heat(dt, True)))
        t += dt
    on = [x for x in fired if x[1]]
    first_off = next(x[0] for x in fired if not x[1])
    back_on = next(x[0] for x in fired if x[1] and x[0] > first_off)
    if not (13.3 <= first_off <= 13.7 and 3.1 <= back_on - first_off <= 3.5):
        fails.append(f"5. the chaingun fired to {first_off:.1f} s, off {back_on - first_off:.1f} s (want 13.5, 3.3)")
    # 6. the travel boost: a Ghost on the open ground by the blue side (the open spot's floor), on a long open leg
    leg = next((y for y in (k * math.pi / 18 for k in range(36))
                if T.fly_clear(Vec(OPEN.x, OPEN.y, floor), y, 20.0, dzs=(0.8, 1.4), floor=floor) >= 20.0), None)
    if leg is None:
        fails.append("6. no open leg on the ground (the test's spot)")
    else:
        g = pilot("ghost")
        v = dict(handle=9, kind="ghost", fwd=(math.cos(leg), math.sin(leg), 0.0))
        me = PlayerState(1, 0, "driver", Vec(OPEN.x, OPEN.y, floor), vel=Vec(math.cos(leg) * 6, math.sin(leg) * 6, 0),
                         yaw=leg, alive=True, vehicle=9)
        held = []
        for k in range(int(8.0 * 30)):
            g.notes, act = [], Action(yaw=leg)
            act.forward = 1.0
            g.travel_boost(k / 30.0, me, v, act, False)
            held.append(act.fire2)
        ons = [k / 30.0 for k, h in enumerate(held) if h]
        first_off = next((k / 30.0 for k, h in enumerate(held) if not h), None)
        again = next((k / 30.0 for k, h in enumerate(held) if h and first_off is not None and k / 30.0 > first_off), None)
        if not ons or first_off is None or again is None or not (1.6 <= first_off <= 1.8 and 5.2 <= again <= 5.4):
            fails.append(f"6. a Ghost's travel boost: off at {first_off}, again at {again} (want 1.7 and 5.3)")
        wall = min((k * math.pi / 18 for k in range(36)),
                   key=lambda y: T.fly_clear(Vec(ground.x, ground.y, gz), y, 20.0, dzs=(0.8, 1.4), floor=gz))
        g2 = pilot("ghost")
        act = Action(yaw=wall)
        act.forward = 1.0
        me2 = PlayerState(1, 0, "driver", Vec(ground.x, ground.y, gz), vel=Vec(math.cos(wall) * 6, math.sin(wall) * 6, 0),
                          yaw=wall, alive=True, vehicle=9)
        g2.travel_boost(0.0, me2, dict(handle=9, kind="ghost", fwd=(math.cos(wall), math.sin(wall), 0.0)), act, False)
        if act.fire2:
            fails.append("6. a Ghost facing a wall close ahead boosted")
    # 7. the vehicles' ground: a long drive across the map, with and without the wall cost
    W = VC.wall_dist(T)
    a0, b0 = Vec(-40.0, 40.0, 0.0), Vec(30.0, -30.0, 0.0)
    a0 = Vec(a0.x, a0.y, a0.z + T.ground(a0.x, a0.y))
    b0 = Vec(b0.x, b0.y, b0.z + T.ground(b0.x, b0.y))
    med = {}
    for cost in (0.0, Terrain.VEH_WALL_COST):
        T.VEH_WALL_COST = cost
        T.__dict__.pop("graph_v", None)
        T._vfields = {}
        p, near = a0, []
        for _ in range(80):
            q = T.vnav(p, b0)
            if (q - p).flat() < 0.3:
                break
            n = T._node_at(q.x, q.y, q.z, tol=1.0) if T.inside(q.x, q.y) else None
            if n is not None:
                near.append(float(W[n]))
            p = q
        near.sort()
        med[cost] = (near[len(near) // 2] if near else 0.0, (p - b0).flat())
    del T.VEH_WALL_COST
    T.__dict__.pop("graph_v", None)
    T._vfields = {}
    (m0, end0), (m1, end1) = med[0.0], med[Terrain.VEH_WALL_COST]
    if not (m1 > m0 and end1 < 6.0):
        fails.append(f"7. the drive's route median {m1:.2f} u from walls with the cost, {m0:.2f} without; ended {end1:.1f} u "
                     f"short (want farther, and arriving)")
    if fails:
        print("\n".join(fails))
        sys.exit(1)
    print(f"vehicle clearance OK (route median from walls {m0:.2f} -> {m1:.2f} u; chaingun 13.5 / 3.3 s; boosts 1.7 / 3.6 s)")


if __name__ == "__main__":
    main()
