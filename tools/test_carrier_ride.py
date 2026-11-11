"""Our flag carrier and vehicles (GitHub #16), through the real director passes and Bot.drive, on Avalanche and
Valhalla:

1. a person with the flag gets into the passenger seat of our bot's Warthog mid-map: the driver's trip ends where the
   carrier scores (director.vehicle_jobs taxi to carry_point), and it does not get out in its first 4 s
2. our carrier bot boards our bot's Warthog (ferry / board): seated under the "board" order it stays in (the board
   order's point is the vehicle, which read as "ferried home": out 1 s after getting in)
3. our carrier bot 6 u from a person's Warthog with a seat free is sent to board it (ferry_orders); not an empty one
   (a carrier does not drive)
4. an escort 25 u from our carrier heads straight for him, not its spot behind him (ESCORT_FAR; Valhalla)

usage: python -I test_carrier_ride.py      -> "carrier ride OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

TEAM, H = 1, 9


def check(name, fails):
    M = get_map(name)
    T = terrain(M)
    ours, theirs = M["flags"][TEAM], M["flags"][1 - TEAM]

    def mk(i, pers="objector"):
        b = Bot(i, TEAM, make_profile("top", pers, random.Random(i)), M, random.Random(i))
        b._terrain, b.posture, b.notes = T, 0.5, []
        return b

    def veh(pos, riders, occupied=True):
        return dict(handle=H, kind="warthog", pos=(pos.x, pos.y, pos.z), riders=riders, occupied=occupied, team=TEAM,
                    fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), gunner=False, turrets=[], manned=[])

    def flags(carrier, at):
        return {1 - TEAM: FlagState(1 - TEAM, theirs, at, "carried", carrier), TEAM: FlagState(TEAM, ours, ours)}

    def uses(b, me, others, v, t0, secs, fl):
        for k in range(int(secs * 30)):
            t = t0 + k / 30
            a = Action()
            b.now = t
            b.drive(t, 1 / 30, me, Snapshot(t, [me, *others], fl, mode="ctf", vehicles=[v]), a, lambda p, q, **kw: q)
            if a.action:
                return round(t - t0, 2)
        return None

    # 1. a person carrier aboard our bot's Warthog
    at = theirs + (ours - theirs) * 0.3
    for role in ("mid", "runner"):
        bs = {1: mk(1), 3: mk(3, "camper")}
        d = Director(TEAM, M, bs, random.Random(1))
        drv = bs[1]
        drv.seat, drv.seat_for, drv.seat_since = "driver", H, 0.0
        drv.order = Order(role, theirs if role == "runner" else at, target=H)
        me = PlayerState(1, TEAM, "drv", at, vehicle=H)
        ps = [me, PlayerState(2, TEAM, "player", at, vehicle=H, has_flag=True, is_bot=False), PlayerState(3, TEAM, "c", ours)]
        v = veh(at, 2)
        d.roles[1], d.next_roles = role, 0.0
        d.assign_roles(10.0, Snapshot(10.0, ps, flags(2, at), mode="ctf", vehicles=[v]))
        to = getattr(drv, "drive_to", None)
        if to is None or dist(to, ours) > 12.0:
            fails.append(f"{name} 1 ({role}): the trip ends {dist(to, ours) if to else None} u from our stand, not where "
                         "the carrier scores")
        out = uses(drv, me, ps[1:], v, 10.0, 4.0, flags(2, at))
        if out is not None:
            fails.append(f"{name} 1 ({role}): the driver got out {out} s after the carrier got in")
    # 2. our carrier bot seated under its board order
    at = theirs + (ours - theirs) * 0.25
    vpos = at + Vec(6.0, 5.0, 0.0)
    bs = {1: mk(1), 2: mk(2), 3: mk(3, "camper")}
    d = Director(TEAM, M, bs, random.Random(2))
    drv, car = bs[1], bs[2]
    drv.seat, drv.seat_for, drv.seat_since = "driver", H, 0.0
    ps = [PlayerState(1, TEAM, "drv", vpos, vehicle=H), PlayerState(2, TEAM, "car", at, has_flag=True),
          PlayerState(3, TEAM, "c", ours)]
    d.next_roles = 0.0
    d.assign_roles(20.0, Snapshot(20.0, ps, flags(2, at), mode="ctf", vehicles=[veh(vpos, 1)]))
    if (drv.order.role, car.order.role) != ("ferry", "board"):
        fails.append(f"{name} 2: carrier 8 u from our bot's Warthog: driver {drv.order.role}, carrier {car.order.role}")
    car.seat, car.seat_for, car.seat_since = "passenger", H, 21.0
    out = uses(car, PlayerState(2, TEAM, "car", vpos, vehicle=H, has_flag=True),
               [PlayerState(1, TEAM, "drv", vpos, vehicle=H)], veh(vpos, 2), 21.0, 1.9, flags(2, vpos))
    if out is not None:
        fails.append(f"{name} 2: the carrier got out {out} s after boarding (its board order read as home)")
    # 3. a person's Warthog by our carrier bot; an empty one
    at = theirs + (ours - theirs) * 0.2
    vpos = at + Vec(4.0, 4.0, 0.0)
    for person, want in ((True, "board"), (False, "runner")):
        bs = {2: mk(2), 3: mk(3, "camper")}
        d = Director(TEAM, M, bs, random.Random(3))
        ps = [PlayerState(2, TEAM, "car", at, has_flag=True), PlayerState(3, TEAM, "c", ours)]
        if person:
            ps.append(PlayerState(4, TEAM, "player", vpos, vehicle=H, is_bot=False))
        d.next_roles = 0.0
        d.assign_roles(30.0, Snapshot(30.0, ps, flags(2, at), mode="ctf", vehicles=[veh(vpos, int(person), person)]))
        if bs[2].order.role != want:
            fails.append(f"{name} 3: carrier 6 u from {'a person' if person else 'an empty'} Warthog: order "
                         f"{bs[2].order.role}, want {want}")
    # 4. an escort far from our carrier goes straight to him; near him, to its spot behind him (bot.ESCORT_FAR). The
    # carrier on the floor somewhere between the stands where his spot behind is open ground
    def head(car, off):
        e = mk(5)
        e.order = Order("escort", car, target=2)
        me = PlayerState(5, TEAM, "esc", car + off)
        return e.live_point(me, Snapshot(40.0, [me, PlayerState(2, TEAM, "car", car, has_flag=True)], flags(2, car),
                                         mode="ctf"))
    spots = [theirs + (ours - theirs) * (k / 20) for k in range(3, 18)]
    spots = [Vec(q.x, q.y, T.nav_z(q.x, q.y, q.z)) for q in spots]
    car = next((q for q in spots if dist(head(q, Vec(-6.0, 0.0, 0.0)), q) > 1.0), None)
    if car is None:
        return False            # (Avalanche: the stands' line runs over the river and cliffs)
    if dist(head(car, Vec(-25.0, 0.0, 0.0)), car) > 0.5:
        fails.append(f"{name} 4: escort 25 u from the carrier heads for its spot behind him, not him")
    return True


def main():
    fails = []
    if not any([check(name, fails) for name in ("h3_sidewinder", "h3_riverworld")]):
        fails.append("4: no map with open ground behind the carrier between the stands")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("carrier ride OK (a person carrier driven home, a boarded carrier stays in, a person's Warthog boarded)")


if __name__ == "__main__":
    main()
