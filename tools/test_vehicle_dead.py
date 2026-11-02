"""Wrecks and duds (The Pit the same night: two Warthogs behind the map's fences took 15-18% of both teams' bot time,
13,921 rows 2-4 u off them, nobody ever in):

1. each game's reader calls a vehicle dead from its body field (Live.VEH_VITAL: health left in CE / Halo 2 / Halo 3 /
   ODST, damage taken in Reach / Halo 4 / H2A), only once it was read alive this match (a field that reads 0 from the
   start keeps it usable); live_bots.vehicle_dead and vehicle_left (the trace's health left) never raise
2. vehicles.usable: a wreck, a vehicle on its side and a dud are no ride; ride_score is 0 for a wreck
3. the director sends no driver to a wreck (crew_orders) and a bot's own trip pick skips it (decide)
4. a bot standing by a vehicle it cannot get into gives it up after DUD_S, and then nobody goes for it (the team's crew
   orders and the bots' own picks) for DUD_FOR; never a teammate's occupied vehicle (a person's: a seat that did not take)

usage: python -I test_vehicle_dead.py      -> "vehicle dead OK"
"""
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain import vehicles  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.live import Live, LiveH2, LiveH3, LiveH4F, LiveODST, LiveReach  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
import live_bots  # noqa: E402


class Mem:
    def __init__(s, off):
        s.off, s.val = off, {}

    def read(s, a, n):
        b = bytearray(0x200)
        struct.pack_into("<f", b, s.off, s.val.get(a >> 16, 1.0))
        return bytes(b[a & 0xFFFF:(a & 0xFFFF) + n])


def reader(cls):
    r = object.__new__(cls)
    r.g = Mem(cls.VEH_VITAL[0])
    r.object = lambda h: h << 16
    return r


def main():
    fails = []
    # 1. the readers
    for cls, off, dmg in ((Live, 0x9C, False), (LiveH2, 0xEC, False), (LiveH3, 0xF4, False), (LiveODST, 0xE8, False),
                          (LiveReach, 0x128, True), (LiveH4F, 0x15C, True)):
        if cls.VEH_VITAL != (off, dmg):
            fails.append(f"{cls.__name__}: VEH_VITAL {cls.VEH_VITAL}, want {(off, dmg)}")
            continue
        r = reader(cls)
        alive, gone = (0.0, 1.0) if dmg else (1.0, 0.0)
        r.g.val[1] = alive
        a = r.vehicle_dead(1)
        r.g.val[1] = gone
        b = r.vehicle_dead(1)
        r.g.val[2] = gone                     # never read alive: kept usable
        c = r.vehicle_dead(2)
        if (a, b, c) != (False, True, False):
            fails.append(f"{cls.__name__}: alive {a}, after its death {b}, read dead from the start {c} "
                         f"(want False, True, False)")
    r = reader(LiveH3)
    r.object = lambda h: (_ for _ in ()).throw(OSError("read failed"))
    if live_bots.vehicle_dead(r, 1) is not False or live_bots.vehicle_dead(object(), 1) is not False:
        fails.append("live_bots.vehicle_dead raised or did not answer False on a failed read / a reader without it")
    if live_bots.vehicle_left(r, 1) is not None or live_bots.vehicle_left(object(), 1) is not None:
        fails.append("live_bots.vehicle_left raised or did not answer None on a failed read / a reader without it")
    r = reader(LiveReach)                     # the trace's health left: Reach's field is damage taken
    r.g.val[1] = 0.25
    if live_bots.vehicle_left(r, 1) != 0.75:
        fails.append(f"live_bots.vehicle_left: Reach damage 0.25 read {live_bots.vehicle_left(r, 1)} left (want 0.75)")
    # 2. usable
    ok = dict(handle=7, kind="warthog", pos=(0.0, 0.0, 0.0), occupied=False, riders=0, up=(0.0, 0.0, 1.0))
    wreck, side = dict(ok, dead=True), dict(ok, up=(0.0, 1.0, 0.0))
    if not vehicles.usable(ok) or vehicles.usable(wreck) or vehicles.usable(side) or \
            vehicles.usable(ok, 5.0, {7: 10.0}) or not vehicles.usable(ok, 11.0, {7: 10.0}):
        fails.append("vehicles.usable: want a standing vehicle yes; a wreck, one on its side, a dud no (and after it)")
    me = PlayerState(1, 0, "b", Vec(5.0, 0.0, 0.0))
    if vehicles.ride_score(wreck, me, Vec(80.0, 0.0, 0.0), 80.0) != 0.0:
        fails.append("ride_score: a wreck scored as a ride")
    # 3. the team's driver pick, and a bot's own trip
    M = get_map("bloodgulch")
    home = M["flags"][0]
    for name, v, want in (("wreck", dict(ok, pos=(home.x + 6, home.y, home.z), dead=True), False),
                          ("standing one", dict(ok, pos=(home.x + 6, home.y, home.z)), True)):
        b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
        d = Director(0, M, {1: b}, random.Random(1))
        snap = Snapshot(10.0, [PlayerState(1, 0, "b", home + Vec(2.0, 0.0, 0.0))], vehicles=[v], mode="slayer")
        d.roles = {1: "free"}
        d.crew_orders(10.0, snap, {1: snap.player(1)}, [b])
        sent = b.order.role == "drive"
        if sent != want:
            fails.append(f"crew_orders, a {name} 4 u off: driver sent {sent}, want {want}")
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(2)), M, random.Random(2))
    far = M["flags"][1]
    snap = Snapshot(10.0, [PlayerState(1, 0, "b", home)], vehicles=[dict(ok, pos=(home.x + 3, home.y, home.z), dead=True)],
                    mode="slayer")
    b.order = Order("mid", far)
    picks = 0
    for k in range(40):
        b.next_decide, b.vehicle_retry_at, b.goal = 0.0, 0.0, ("roam", None)
        g = b.decide(10.0 + k, snap.player(1), snap)
        picks += g[0] == "vehicle"
    if picks:
        fails.append(f"a bot's own trip pick took a wreck {picks} of 40 decisions")
    # 4. a dud: stood by 12 s without getting in
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(3)), M, random.Random(3))
    v = dict(ok, pos=(home.x + 3, home.y, home.z))
    me = PlayerState(1, 0, "b", home)
    gave_up = None
    for k in range(int(12 / (1 / 30))):
        t = 20.0 + k / 30
        if not b.dud_check(t, 1 / 30, me, v):
            gave_up = t - 20.0
            break
    if gave_up is None or not vehicles.DUD_S - 0.1 <= gave_up <= vehicles.DUD_S + 0.2:
        fails.append(f"dud: gave up after {gave_up} s by it, want about {vehicles.DUD_S}")
    duds = M.get("_vehicle_duds", {})
    if not duds.get(7, 0.0) > 30.0:
        fails.append(f"dud: not shared on the map ({duds})")
    # (a teammate's vehicle, a person's, is never shunned: a seat that did not take is no dud)
    b3 = Bot(3, 0, make_profile("top", "rusher", random.Random(5)), M, random.Random(5))
    mine = dict(ok, handle=8, pos=(home.x + 3, home.y, home.z), occupied=True, riders=1, team=0)
    if not all(b3.dud_check(20.0 + k / 30, 1 / 30, me, mine) for k in range(int(15 / (1 / 30)))) or 8 in duds:
        fails.append("dud: a teammate's occupied vehicle was shunned after 15 s by it")
    b2 = Bot(2, 0, make_profile("top", "rusher", random.Random(4)), M, random.Random(4))
    d = Director(0, M, {2: b2}, random.Random(2))
    snap = Snapshot(40.0, [PlayerState(2, 0, "c", home + Vec(1.0, 0.0, 0.0))], vehicles=[v], mode="slayer")
    d.roles = {2: "free"}
    d.crew_orders(40.0, snap, {2: snap.player(2)}, [b2])
    if b2.order.role == "drive":
        fails.append("dud: the director still sent a driver to it")
    later = Snapshot(20.0 + vehicles.DUD_FOR + 15.0, snap.players, vehicles=[v], mode="slayer")
    d.crew_orders(later.time, later, {2: later.player(2)}, [b2])
    if b2.order.role != "drive":
        fails.append("dud: still shunned after DUD_FOR")
    M.pop("_vehicle_duds", None)
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("vehicle dead OK (6 readers, usable, crew and trip picks, dud after "
          f"{gave_up:.1f} s, shared, over after {vehicles.DUD_FOR:.0f} s)")


if __name__ == "__main__":
    main()
