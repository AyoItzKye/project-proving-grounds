"""Vehicle regression checks, built from the owner's Spire Invasion of Nov 5 (install 0.2.1 = 4031edb, trace
reach_35_island_20261105-201917; his flags at 322-348 s: "they dont touch the fucking banshee at all", "the falcon
asshole is still flying to the soft kill top of the fucking map and not trying to pick up any teammates", "teammates
still fucking ignore my empty gun on my warthog", "the flying bots no longer use object detection"). One assert-based
check per behavior; each failed on the code before its fix (fix-vehicles branch):

1. banshee_taken: an empty Banshee 1 u from an attacker on his objective job is taken (director.crew_orders, busy pool;
   280.9 s: runner #5 1 u off it, nobody ever got in); a phase 3 defender beside one stays on the core (Bot.urgent)
2. person_gun: a person's Warthog with its gun empty calls the defender beside it onto the gun, whatever his post
   (director.rider_calls; 142.6 s: #7 6 u off, his post 56 u away)
3. pilot_pickup: a runner pilot taking off alone fetches a teammate on his way to the core, the way measured flat
   (director.gunner_pickup; 298.1 s: #9 on the pad, #? at the spire's foot 100 u off, under the core)
4. roof: a pilot over the map's roof (Spire's safe zone top, -16.2) goes down, a Falcon sinks (Bot.air_roof_guard;
   333-341 s: #9 at -14.8 in the soft kill till it died)
5. falcon_core_flight: a Falcon flown from its pad to the core on the spire's top (closed loop, the level's walls):
   no strike on the spire's side under the top, never over the roof (Bot.air_guard's face rule; 310.5 s: #9 into the
   spire's side at -30.8, 13.7 u/s; 21316aa's zmax took the top's deck out of the floor rule)

usage: python -I test_reg_vehicles.py [name]      -> "reg vehicles OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import oob  # noqa: E402
from brain.bot import Action, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = "reach_35_island"
M = get_map(MAP)
T = terrain(M)
T.set_oob([], None, oob.volumes(MAP))           # (live_bots: Oob.set_phase)
CORE = Vec(-178.2, -405.3, -22.9)               # the core on the spire's top
PAD = Vec(-128.6, -313.5, -60.6)                # the Falcon's pad
BANSHEE = (-189.24, -387.58, -57.17)            # the Banshees' pad


def bot(i, team=0, pers="rusher"):
    b = Bot(i, team, make_profile("top", pers, random.Random(i)), M, random.Random(i))
    b._terrain = T
    return b


def inv_snap(t, players, vehicles, attackers=0):
    snap = Snapshot(t, players, mode="invasion", vehicles=vehicles, inv_phase=3, inv_attackers=attackers)
    snap.inv_core, snap.inv_delivery, snap.inv_core_carrier = CORE, Vec(-130.0, -330.0, -60.0), None
    return snap


def vdict(h, kind, pos, riders=0, team=-1, **kw):
    pos = (pos.x, pos.y, pos.z) if isinstance(pos, Vec) else tuple(pos)
    return dict(dict(handle=h, kind=kind, pos=pos, riders=riders, occupied=riders > 0, team=team, gunner=False,
                     turrets=[], manned=[], fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), left=1.0, dead=False), **kw)


def banshee_taken():
    # 280.9 s: runner #5 1 u off the empty Banshee, #1 / #3 / #7 8 u off; team 0 attacking phase 3
    bots = {i: bot(i) for i in (1, 3, 5, 7)}
    d = Director(0, M, bots, random.Random(1))
    at = {1: (-182.4, -385.1, -57.4), 3: (-186.9, -380.2, -57.0), 5: (-189.9, -387.1, -57.2), 7: (-195.1, -381.6, -57.3)}
    ps = [PlayerState(i, 0, f"b{i}", Vec(*p), is_bot=True) for i, p in at.items()]
    for b in bots.values():
        b.order = Order("runner", CORE)
        d.roles[b.id] = "runner"
    v = vdict(4063559896, "banshee", BANSHEE)
    d.vehicle_orders(280.9, inv_snap(280.9, ps, [v]), list(bots.values()))
    took = [b.id for b in bots.values() if b.order.role == "drive" and b.order.target == v["handle"]]
    assert took == [5], f"the Banshee by the attackers: taken by {took} (want #5, 1 u off it)"
    # (a phase 3 defender beside it stays on the core: live 221404, Elites went for a Banshee as the core was taken)
    dfd = {i: bot(i, 1) for i in (2, 4)}
    d1 = Director(1, M, dfd, random.Random(2))
    ps = [PlayerState(2, 1, "d2", Vec(-189.0, -386.0, -57.2), is_bot=True),
          PlayerState(4, 1, "d4", Vec(-185.0, -388.0, -57.2), is_bot=True)]
    for b in dfd.values():
        b.order = Order("defender", CORE)
        d1.roles[b.id] = "defender"
    d1.vehicle_orders(281.0, inv_snap(281.0, ps, [v]), list(dfd.values()))
    assert all(b.order.role == "defender" for b in dfd.values()), "a phase 3 defender left the core for the Banshee"


def person_gun():
    # 142.6 s: the owner (id 0) at the wheel of his Warthog, #7 a defender 6 u off (post 56 u away), #5 22 u off
    H = 3890610684
    hog = (-152.2, -350.7, -55.4)
    bots = {i: bot(i) for i in (5, 7)}
    d = Director(0, M, bots, random.Random(3))
    post = Vec(-171.5, -403.3, -58.7)
    for b in bots.values():
        b.order = Order("defender", post)
        d.roles[b.id] = "defender"
    ps = [PlayerState(0, 0, "owner", Vec(*hog), vehicle=H, is_bot=False),
          PlayerState(7, 0, "b7", Vec(-147.3, -347.6, -56.3), is_bot=True),
          PlayerState(5, 0, "b5", Vec(-171.0, -362.0, -55.0), is_bot=True)]
    snap = Snapshot(142.6, ps, mode="invasion", vehicles=[vdict(H, "warthog", hog, riders=1, team=0)], inv_phase=2,
                    inv_attackers=1)
    d.rider_calls(142.6, snap, list(bots.values()), {b.id: snap.player(b.id) for b in bots.values()})
    assert (bots[7].order.role, bots[7].order.target) == ("ride", H), \
        f"the defender 6 u from the owner's empty gun: {bots[7].order.role} (want ride)"
    assert bots[5].order.role == "defender", "a defender 22 u off was called (CALL_R 12)"


def pilot_pickup():
    # 298.1 s: #9 at the Falcon's wheel on its pad, runner to the core; #3 a runner at the spire's foot (under the core)
    H = 4063101084
    bots = {9: bot(9), 3: bot(3)}
    d = Director(0, M, bots, random.Random(4))
    p = bots[9]
    p.seat_for, p.seat_since, p.seat = H, 296.7, "driver"
    for b in bots.values():
        b.order = Order("runner", CORE)
        d.roles[b.id] = "runner"
    mate = Vec(-181.0, -366.0, -55.8)
    ps = [PlayerState(9, 0, "pilot", PAD, vehicle=H, is_bot=True), PlayerState(3, 0, "b3", mate, is_bot=True)]
    v = vdict(H, "falcon", PAD, riders=1, team=0, turrets=["falcon_side_gun_left", "falcon_side_gun_right"])
    snap = inv_snap(298.1, ps, [v])
    d.vehicle_jobs(298.1, snap, list(bots.values()), {b.id: snap.player(b.id) for b in bots.values()})
    assert p.vjob == "pickup" and p.drive_to is not None and (p.drive_to - mate).flat() < 1.0, \
        f"the lone Falcon pilot's job: {p.vjob} to {p.drive_to} (want a pickup of #3 under the core)"


def roof():
    # 333.4-341.8 s: #9's Falcon at -14.8 over the spire's top, 1.5 u over the safe zone's top, till it died
    H = 4063101084
    p = bot(9)
    p.seat_for, p.seat_since, p.seat = H, 296.7, "driver"
    pos = Vec(-181.2, -407.2, -14.8)
    me = PlayerState(9, 0, "pilot", pos, vehicle=H, is_bot=True)
    a = Action(yaw=0.6)
    a.pitch, a.vertical = 0.45, 1.0
    p.air_roof_guard(me, a, Snapshot(333.4, [me], vehicles=[vdict(H, "falcon", pos, riders=1, team=0)]))
    assert a.vertical < 0 and a.pitch <= -0.3, f"over the roof: vertical {a.vertical}, pitch {a.pitch} (want down)"


def falcon_core_flight():
    for pid in (1, 9):                          # (two pilots: their dice differ)
        fly_to_core(pid)


def fly_to_core(pid, seconds=22.0):
    """Closed loop from the pad to the core: a point mass flown by Bot.think, 16 u/s at full stick (live 15-18), the
    vertical input 3 u/s (+1 up, 0.5 holds, 0 sinks), stopped by what the level has solid at its body (centre and 2 u
    to each side, -1.2 / 0 / +1 u)."""
    HZ, H = 30, 0x7777
    b = bot(pid)
    b.order = Order("runner", CORE)
    b.seat = "driver"
    pos, vel, yaw, pitch = PAD, Vec(), math.atan2(CORE.y - PAD.y, CORE.x - PAD.x), 0.0
    side_hits, over = [], 0.0
    for k in range(int(seconds * HZ)):
        t = 100.0 + k / HZ
        me = PlayerState(pid, 0, "pilot", pos, vel, yaw, pitch, vehicle=H, weapon="none")
        snap = Snapshot(t, [me], vehicles=[vdict(H, "falcon", (pos.x, pos.y, pos.z), riders=1, team=0,
                                                 fwd=(math.cos(yaw), math.sin(yaw), 0.0))], mode="slayer")
        if k == 0:
            b.seat_for, b.seat_since = H, t - 0.5
        b.drive_to, b.vjob = CORE, "taxi"
        act = b.think(t, 1 / HZ, snap, T.los, T.nav, [])
        yaw, pitch = act.yaw, act.pitch
        vert = getattr(act, "vertical", 0.0) or 0.0
        want = Vec(math.cos(yaw) * act.forward - math.sin(yaw) * act.strafe,
                   math.sin(yaw) * act.forward + math.cos(yaw) * act.strafe, 0.0) * 16.0
        want = Vec(want.x, want.y, max(-3.0, min(3.0, 6.0 * vert - 3.0)))
        dv = want - vel
        m = dv.length()
        vel = vel + (dv * (0.2 / m) if m > 0.2 else dv)
        step = vel * (1 / HZ)
        fl = step.flat()
        if fl > 1e-4:
            hy = math.atan2(step.y, step.x)
            floor = pos.z - T.height_over(pos.x, pos.y, pos.z)
            d = min(T.fly_clear(pos + Vec(-math.sin(hy) * o, math.cos(hy) * o, step.z), hy, fl + 0.6, dzs=(-1.2, 0.0, 1.0),
                                floor=floor, start=0.1) for o in (0.0, 2.0, -2.0))
            if d < fl + 0.6:
                if pos.z < CORE.z - 2.0 and (pos - CORE).flat() > 6.0:
                    side_hits.append((round(k / HZ, 1), round(pos.x, 1), round(pos.y, 1), round(pos.z, 1)))
                vel, step = Vec(0, 0, vel.z), Vec(0, 0, step.z)
        pos = pos + step
        fz = pos.z - T.height_over(pos.x, pos.y, pos.z)
        if pos.z < fz + 0.5:
            pos, vel = Vec(pos.x, pos.y, fz + 0.5), Vec(vel.x, vel.y, max(0.0, vel.z))
        if pos.z > T.air_roof(pos.x, pos.y) if hasattr(T, "air_roof") else pos.z > -16.2:
            over += 1 / HZ
    near_spire = [h for h in side_hits if (Vec(h[1], h[2], 0) - CORE).flat() < 20.0]
    assert not near_spire, f"the Falcon struck the spire's side under its top: {near_spire[:3]}"
    assert over == 0.0, f"the Falcon flew {over:.1f} s over the map's roof (the soft kill)"


CHECKS = [banshee_taken, person_gun, pilot_pickup, roof, falcon_core_flight]


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else None
    fails = []
    for c in CHECKS:
        if want and c.__name__ != want:
            continue
        try:
            c()
        except AssertionError as e:
            fails.append(f"{c.__name__}: {e}")
        except Exception as e:                  # (the old code lacks a method: that is a failure too)
            fails.append(f"{c.__name__}: {type(e).__name__}: {e}")
    if fails:
        print("FAIL\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("reg vehicles OK")


if __name__ == "__main__":
    main()
