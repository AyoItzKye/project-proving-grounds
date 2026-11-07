"""A pilot gets gunners as people do, built from a bug report (live Spire Invasion 20261105-143525, 1040 s: a Spartan
pilot never tried to get gunners on its Falcon; team 1, phase 3, the pilot Needler502 #14):

1. a pilot waiting for the teammate called to its gun sets down for him (1031-1035 s: the Falcon sat 2 u over the
   ground, the floors rule climbed it to 5-7 u over Cyber117 #6 walking under it at 1 u, and he never got in); and lifts
   straight up again once the wait is over (the take-off after it)
2. a rider called last pass keeps the call while the pilot waits, past his role pass and a rogue roll (1033.3 s: #6, 6 u
   from the Falcon, made a runner 17 u from the core and never called again); nobody coming any more: no waiting
   for them (1033-1040 s: the Falcon sat 7 s more for #6); the kept call lasts only the pilot's wait (12 s in the air)
3. a runner alone at the wheel of a gun he cannot fire goes for a gunner on his way first (963-1024 s: #14 flew alone
   100 u to the core with AtomicBeast #15 37-48 u off his way); not one far off that way (PICKUP_DETOUR), not with an
   armed driver's seat (a Revenant: taxi), not Easy
4. the same for every multi-seat gun vehicle the brain drives: Warthogs (Halo 3 / Reach / Halo 4 / H2A), the Spectre,
   the Prowler, the Elephant (gunner_pickup), and the set-down for every aircraft with crew seats (the Hornet)

usage: python -I test_falcon_crew.py      -> "falcon crew OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Action, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("reach_35_island")
T = terrain(M)
H = 2488074763
CORE = Vec(-161.7, -422.5, -60.1)            # the core, loose on the ground 1013-1046 s
SPIRE_TOP = Vec(-178.2, -405.3, -22.9)       # the core on its stand, 961-971 s
PAD = Vec(-128.6, -313.5, -60.6)             # the Falcon's pad


def bot(i, tier="top", seed=None):
    b = Bot(i, 1, make_profile(tier, "objector", random.Random(seed or i)), M, random.Random(seed or i))
    b._terrain = T
    return b


def falcon(pos, kind="falcon", riders=1, **kw):
    return dict(dict(handle=H, kind=kind, pos=(pos.x, pos.y, pos.z), riders=riders, occupied=True, team=1, gunner=False,
                     turrets=["falcon_side_gun_left", "falcon_side_gun_right"] if kind == "falcon" else [], manned=[],
                     fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0)), **kw)


def main():
    fails = []
    # 1. 1031.4-1035.5 s: the Falcon down by the spire's foot, #6 called to its gun at 1029.3 s walking in from 10 u
    fpos = Vec(-178.9, -416.2, -57.9)
    p = bot(14)
    p.seat_for, p.seat_since, p.seat, p.order = H, 961.2, "driver", Order("runner", CORE)
    p.drive_to = CORE
    p.called_aboard = {H: ((6,), 1029.3)}
    climbed, held = [], 0
    for k in range(30):
        t = 1031.4 + k * 0.1
        me = PlayerState(14, 1, "p", fpos, vehicle=H)
        walker = PlayerState(6, 1, "g", Vec(-171.0 - 0.15 * k, -417.0, -60.0), vel=Vec(-6.0, 0.0, 0.0))
        a = Action(yaw=1.36)
        p.notes = []
        p.now = t
        p.drive(t, 0.1, me, Snapshot(t, [me, walker], vehicles=[falcon(fpos)], mode="invasion"), a, lambda q, r, **kw: r)
        p.air_guard(me, a, Snapshot(t, [me, walker], vehicles=[falcon(fpos)], mode="invasion"))
        held += "vehicle: waiting for crew" in p.notes
        if a.vertical > 0.0 or a.forward or a.strafe:
            climbed.append((round(t, 1), a.vertical, sorted(p.notes)))
        p.notes = []
    if held < 30 or climbed:
        fails.append(f"1. Falcon waiting for its called gunner by the spire's foot: waited {held} of 30 ticks, lifted or "
                     f"moved on {len(climbed)} (want: set down, still), first {climbed[:2]}")
    # ... and the wait over (12 s from the call), set down (its origin reads 0.02 u over the floor landed on its pad):
    # straight up first, as just in
    down = Vec(fpos.x, fpos.y, -60.85)
    t = 1042.0
    me = PlayerState(14, 1, "p", down, vehicle=H)
    a = Action(yaw=1.36)
    p.notes = []
    p.now = t
    snap = Snapshot(t, [me], vehicles=[falcon(down)], mode="invasion")
    p.drive(t, 0.1, me, snap, a, lambda q, r, **kw: r)
    p.air_guard(me, a, snap)
    if "air: taking off, straight up" not in p.notes:
        fails.append(f"1. the wait over, on the ground: no straight-up take-off ({sorted(p.notes)})")
    # the Hornet (crew seats, no vtol lift): set down too
    p = bot(14, seed=3)
    p.seat_for, p.seat_since, p.seat, p.order = H, 1020.0, "driver", Order("runner", CORE)
    p.called_aboard = {H: ((6,), 1029.3)}
    me = PlayerState(14, 1, "p", fpos, vehicle=H)
    walker = PlayerState(6, 1, "g", Vec(-171.0, -417.0, -60.0), vel=Vec(-6.0, 0.0, 0.0))
    a = Action(yaw=1.36)
    p.notes = []
    p.now = 1031.4
    snap = Snapshot(1031.4, [me, walker], vehicles=[falcon(fpos, kind="hornet")], mode="invasion")
    p.drive(1031.4, 0.1, me, snap, a, lambda q, r, **kw: r)
    p.air_guard(me, a, snap)
    if a.pitch > 0.0 or "air: a structure by us, pull up" in p.notes:
        fails.append(f"1. Hornet waiting for crew: pitch {a.pitch:.2f}, {sorted(p.notes)} (want: set down)")

    # 2. 1033.3 s: the role pass made #6 a runner 17 u from the core, 6 u from the Falcon, after his call at 1029.3 s
    def pass_at(t, six_pos, called_at=1029.3, teamwork=0.05):
        drv, six = bot(14), bot(6, seed=11)
        six.p.teamwork = teamwork               # (a rogue roll on any fresh choice)
        drv.seat, drv.order, drv.called_aboard = "driver", Order("runner", CORE), {H: ((6,), called_at)}
        six.order = Order("runner", CORE)
        d = Director(1, M, {14: drv, 6: six}, random.Random(1))
        d.roles, d.aboard_calls = {14: "runner", 6: "runner"}, {H: (6,)}
        pl = [PlayerState(14, 1, "p", fpos, vehicle=H), PlayerState(6, 1, "g", six_pos)]
        snap = Snapshot(t, pl, vehicles=[falcon(fpos)], mode="invasion", inv_phase=3, inv_attackers=1, inv_core=CORE)
        d.rider_calls(t, snap, [drv, six], {x.id: snap.player(x.id) for x in (drv, six)})
        return drv, six
    drv, six = pass_at(1033.3, Vec(-172.9, -416.6, -60.0))
    if six.order.role != "ride" or H not in getattr(drv, "called_aboard", {}):
        fails.append(f"2. #6 called at 1029.3, 6 u from the Falcon at 1033.3 s: order {six.order.role}, the pilot "
                     f"waits for {getattr(drv, 'called_aboard', {})} (want: still on the gun, the pilot waiting)")
    drv, six = pass_at(1033.3, Vec(-140.0, -416.6, -60.0))         # 39 u off: not coming any more
    if H in getattr(drv, "called_aboard", {}):
        fails.append(f"2. nobody coming any more (#6 39 u off): the pilot still waits for {drv.called_aboard[H]}")
    drv, six = pass_at(1043.0, Vec(-172.9, -416.6, -60.0))         # past the pilot's 12 s wait: no kept call
    if six.order.role == "ride":
        fails.append("2. 13.7 s after the call (the pilot's wait over): #6 kept on the gun")

    # 3. 963.6 s: #14 alone in the Falcon on the pad, a runner for the core on the spire's top; #15 a runner 37 u off
    def jobs(kind, mate_pos, tier="top", armed_turrets=None):
        drv, mate = bot(14, tier=tier), bot(15)
        drv.seat, drv.order = "driver", Order("runner", SPIRE_TOP)
        mate.order = Order("runner", SPIRE_TOP)
        d = Director(1, M, {14: drv, 15: mate}, random.Random(1))
        d.roles = {14: "runner", 15: "runner"}
        v = falcon(PAD, kind=kind, **({"turrets": armed_turrets} if armed_turrets is not None else {}))
        pl = [PlayerState(14, 1, "p", PAD, vehicle=H), PlayerState(15, 1, "r", mate_pos)]
        snap = Snapshot(963.6, pl, vehicles=[v], mode="invasion", inv_phase=3, inv_attackers=1, inv_core=SPIRE_TOP)
        d.vehicle_jobs(963.6, snap, [drv, mate], {x.id: snap.player(x.id) for x in (drv, mate)})
        return drv
    on_way = Vec(-138.0, -351.5, -58.4)
    drv = jobs("falcon", on_way)
    if drv.vjob != "pickup" or dist2(drv.drive_to, on_way) > 1.0:
        fails.append(f"3. lone Falcon pilot on the pad, #15 37 u off its way: job {drv.vjob} to {drv.drive_to} (want: "
                     f"pickup at #15)")
    for kind in ("warthog", "rwarthog", "gauss", "spectre", "prowler", "elephant"):
        if jobs(kind, on_way).vjob != "pickup":
            fails.append(f"4. lone {kind} driver, a gunner 37 u off his way: job {jobs(kind, on_way).vjob} (want pickup)")
    if jobs("falcon", Vec(-100.0, -280.0, -60.0)).vjob != "taxi":
        fails.append("3. a mate 44 u behind the pad (63 u off the way): fetched (want taxi: PICKUP_DETOUR)")
    if jobs("revenant", on_way).vjob == "pickup":
        fails.append("3. a Revenant (its driver's gun): went for a gunner")
    if jobs("falcon", on_way, armed_turrets=["falcon_chin_gun"]).vjob != "taxi":
        fails.append("3. the nose-gun Falcon (its pilot's gun): went for a gunner (want taxi)")
    if jobs("falcon", on_way, tier="novice").vjob != "taxi":
        fails.append("3. Easy: went for a gunner (want taxi: it never plans)")
    if fails:
        print("FAIL")
        for f in fails:
            print(" ", f)
        sys.exit(1)
    print("falcon crew OK")


def dist2(a, b):
    return 99.0 if a is None else ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


if __name__ == "__main__":
    main()
