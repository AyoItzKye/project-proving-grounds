"""The getaway ride (live Avalanche 064500: the one carrier walked home from blue's stand, the nearest Mongoose 57-84 u off
and outside the ferry's 45 u until 549 s). On Avalanche's data (h3_sidewinder), as in trace 070402 (team 1 by its base
with a Mongoose):

1. both flags home, our bot driving a Mongoose (the team's crew): its job is the getaway, parked GETAWAY_D u from their
   stand on our side, on ground a vehicle drives; a Wraith's driver is never the getaway
2. parked there: it waits, engine off, seat free, and does not get out
3. our carrier has their flag on their stand, the getaway 55 u off (past the old 45 u): it is sent for him (ferry),
   and he boards once it is within 10 u
4. ferried home: the carrier gets out on our stand to score
5. no vehicle route read (vnav None): the spot falls back to the drivable ground nearest the line, and the ferry drives
   straight at its man. Passes with and without the live-learned files (maps/h3_sidewinder lidar.json, rides.json,
   nav_learned.json, untracked in the main repo: there the route from the stand first drops 3.6 u under the platform)

usage: python -I test_getaway.py      -> "getaway OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.bot import Action, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

M = get_map("h3_sidewinder")
T = terrain(M)
OURS, THEIRS = M["flags"][1], M["flags"][0]          # team 1 (as #6 in trace 070402): its stand (-27, -32), theirs (27, -32)
START = Vec(-24.9, -26.7, -4.56)                     # by team 1's base on the drive mesh (stalls.py places)


def bots():
    out = {i: Bot(i, 1, make_profile("top", "objector", random.Random(i)), M, random.Random(i)) for i in (1, 2, 3)}
    for b in out.values():
        b._terrain = T
    return out


def veh(kind, pos, riders=1, handle=9):
    return dict(handle=handle, kind=kind, pos=(pos.x, pos.y, pos.z), riders=riders, occupied=True, team=1,
                fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), gunner=False, turrets=[], manned=[])


def flags(carried_by=None, at=None):
    f0 = FlagState(0, THEIRS, at, "carried", carried_by) if carried_by is not None else FlagState(0, THEIRS, THEIRS)
    return {0: f0, 1: FlagState(1, OURS, OURS)}


def main():
    testdata.need_lidar("h3_sidewinder")
    fails = []
    # 1. the job
    for kind, want in (("mongoose_snow", "getaway"), ("wraith", None)):
        bs = bots()
        d = Director(1, M, bs, random.Random(1))
        bs[1].seat, bs[1].order = "driver", Order("drive", START, target=9)
        bs[2].order, bs[3].order = Order("runner", THEIRS), Order("defender", OURS)
        ps = [PlayerState(1, 1, "drv", START, vehicle=9), PlayerState(2, 1, "run", START + Vec(5, 0, 0)),
              PlayerState(3, 1, "dfd", OURS)]
        snap = Snapshot(30.0, ps, flags(), mode="ctf", vehicles=[veh(kind, START)])
        d.vehicle_jobs(30.0, snap, list(bs.values()), {b.id: snap.player(b.id) for b in bs.values()})
        job, park = getattr(bs[1], "vjob", None), getattr(bs[1], "drive_to", None)
        if (job == "getaway") != (want == "getaway"):
            fails.append(f"a {kind} driver by our base, both flags home: job {job} (want {want})")
        if want and (park is None or not 14.0 <= dist(park, THEIRS) <= 30.0 or dist(park, OURS) >= dist(THEIRS, OURS)
                     or not (T.vnav(park, park), T.vroomy[T._node(park)])[1]):
            fails.append(f"the getaway's spot {park}: want 16+ u from their stand on our side, on drivable ground")
    # 2. parked
    bs = bots()
    b = bs[1]
    park = Director(1, M, bs, random.Random(1)).getaway_park(Snapshot(0.0, [], flags(), mode="ctf"), START)
    b.seat, b.seat_for, b.seat_since, b.crew_ride, b.vjob, b.drive_to = "driver", 9, 0.0, 9, "getaway", park
    b.order = Order("drive", park, target=9)
    moved = out = 0
    for k in range(60):
        t = 40.0 + k / 30
        me = PlayerState(1, 1, "drv", park + Vec(1.0, 0.0, 0.0), vehicle=9)
        a = Action()
        b.drive(t, 1 / 30, me, Snapshot(t, [me], flags(), mode="ctf", vehicles=[veh("mongoose_snow", me.pos)]), a,
                lambda p, q, **kw: q)
        moved += abs(a.forward) > 0.1
        out += a.action
    if moved or out:
        fails.append(f"parked as the getaway: throttle {moved} ticks, get-out {out} ticks (want it waiting)")
    # 3. our carrier on their stand, the getaway 55 u off
    bs = bots()
    d = Director(1, M, bs, random.Random(2))
    bs[1].seat, bs[1].vjob, bs[1].order = "driver", "getaway", Order("drive", park, target=9)
    far = THEIRS + (OURS - THEIRS) * (55.0 / dist(OURS, THEIRS))
    ps = [PlayerState(1, 1, "drv", far, vehicle=9), PlayerState(2, 1, "car", THEIRS, has_flag=True),
          PlayerState(3, 1, "dfd", OURS)]
    snap = Snapshot(50.0, ps, flags(2, THEIRS), mode="ctf", vehicles=[veh("mongoose_snow", far)])
    d.ferry_orders(50.0, snap, list(bs.values()), {x.id: snap.player(x.id) for x in bs.values()})
    if bs[1].order.role != "ferry" or bs[1].order.target != 2:
        fails.append(f"our carrier 55 u from the getaway: its order {bs[1].order.role} (want ferry to him)")
    near = THEIRS + (OURS - THEIRS) * (6.0 / dist(OURS, THEIRS))
    ps[0] = PlayerState(1, 1, "drv", near, vehicle=9)
    snap = Snapshot(55.0, ps, flags(2, THEIRS), mode="ctf", vehicles=[veh("mongoose_snow", near)])
    d.ferry_orders(55.0, snap, list(bs.values()), {x.id: snap.player(x.id) for x in bs.values()})
    if bs[2].order.role != "board":
        fails.append(f"the getaway 6 u from our carrier: he is {bs[2].order.role} (want board)")
    # 4. home with the flag
    c = bs[2]
    c.seat, c.seat_for, c.seat_since, c.order = "passenger", 9, 0.0, Order("runner", OURS)
    me = PlayerState(2, 1, "car", OURS + Vec(2.0, 0.0, 0.0), vehicle=9, has_flag=True)
    a = Action()
    c.drive(60.0, 1 / 30, me, Snapshot(60.0, [me, PlayerState(1, 1, "drv", me.pos, vehicle=9)], flags(2, me.pos),
                                       mode="ctf", vehicles=[veh("mongoose_snow", me.pos, riders=2)]), a,
            lambda p, q, **kw: q)
    if not a.action:
        fails.append("ferried home: the carrier stayed in his seat on our stand")
    # 5. no vehicle route read (vnav answering None): the spot is the drivable ground nearest the line, and a ferry
    # drive steers straight at its man instead of failing
    real = T.vnav
    T.vnav = lambda a, b, **kw: None
    try:
        dd = Director(1, M, bots(), random.Random(3))
        spot = dd.getaway_park(Snapshot(0.0, [], flags(), mode="ctf"), START)
        T.vnav = real
        ok_ground = spot is not None and (T.vnav(spot, spot), bool(T.vroomy[T._node(spot)]))[1]
        T.vnav = lambda a, b, **kw: None
        if not ok_ground or not 10.0 <= dist(spot, THEIRS) <= 30.0:
            fails.append(f"no vehicle route: the getaway's spot {spot} (want drivable ground 16-19 u from their stand)")
        fb = bots()[1]
        fb.seat, fb.seat_for, fb.seat_since, fb.order = "driver", 9, 0.0, Order("ferry", OURS, target=2)
        me = PlayerState(1, 1, "drv", START, yaw=0.0, vehicle=9)
        man = START + Vec(20.0, 0.0, 0.0)
        a = Action()
        fb.drive(70.0, 1 / 30, me, Snapshot(70.0, [me, PlayerState(2, 1, "car", man, has_flag=True)], flags(2, man),
                                            mode="ctf", vehicles=[veh("mongoose_snow", START)]), a,
                 lambda p, q, **kw: None)
        if a.forward < 0.5 or abs(a.yaw) > 0.2:
            fails.append(f"no vehicle route: the ferry drove forward {a.forward:.2f} yaw {a.yaw:.2f} (want at its man)")
    except Exception as e:                 # (a route that can be None must not break a getaway step)
        fails.append(f"no vehicle route: {type(e).__name__}: {e}")
    finally:
        T.vnav = real
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"getaway OK (parked {dist(park, THEIRS):.0f} u from their stand on our side; sent for the carrier 55 u off; "
          f"he boards, and gets out home)")


if __name__ == "__main__":
    main()
