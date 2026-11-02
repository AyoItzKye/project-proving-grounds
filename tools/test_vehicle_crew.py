"""Vehicle crews, checked on the bots' commands:

1. a Reach multiplayer Falcon has no pilot gun (guide 17, REACH-PUR-03): its lone pilot never fires, and goes on with its
   trip past a man it sees (live: it fired on 1179 of 1402 ticks and hurt nobody)
2. a Falcon with one side gun manned hovers with that side to the man (§4.5: the driver keeps the gunner's arc)
3. the Forge nose-gun Falcon's pilot does shoot (the chin gun rides on it)
4. a side gunner holds a mounted gun's trigger while it tracks a strafing man 16 u off (live: 34% of its ticks), and not
   while still swinging onto him
5. a passenger shoots his own gun at the man our gunner's view is on, and not at all while carrying the objective (§4.5)
6. a seat that is not one of the guns riding on the vehicle is a passenger's (a Falcon's troop seat read as its gun)
7. a chaingun stays spun up for 2 s on where a man went out of sight (§4.4), then stops
8. Reach variants by the gun riding on the body (gauss, rocket, troop bed), what each gunner shoots, who is armed
9. the snapshot: a turret's name and the vehicle's variant, its guns and the manned sides

usage: python -I test_vehicle_crew.py      -> "vehicle crews OK"
"""
import math
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain import vehicles  # noqa: E402
from brain.bot import Action, Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("bloodgulch")
T = terrain(M)
A = Vec(60.0, -100.0, T.ground(60.0, -100.0) + 4.0)
FALCON = dict(handle=5, kind="falcon", pos=(A.x, A.y, A.z), riders=1, occupied=True, fwd=(1.0, 0.0, 0.0), turrets=[],
              manned=[], gunner=False)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def crew(seat, tier="strong", seed=1):
    b = Bot(1, 0, make_profile(tier, "rusher", random.Random(seed)), M, random.Random(seed))
    b._terrain = T
    b.seat_for, b.seat_since, b.seat = 5, 0.0, seat
    return b


def see(b, pid, pos, t, seen=True):
    b.per.beliefs[pid] = Belief(pos, Vec(), t, seen, "eyes")
    b.per.recognized.add(pid)


def tick(b, t, v, me, others, yaw=0.0):
    a = Action(yaw=yaw)
    b.drive(t, 1 / 30, me, Snapshot(t, [me] + others, vehicles=[v]), a, lambda p, q, **k: q)
    return a


def main():
    fails = []
    foe = PlayerState(2, 1, "f", A + Vec(12.0, 0.0, -4.0), weapon="assault_rifle", weapons=["assault_rifle"])
    # 1. the lone pilot of a multiplayer Falcon: no shots, its trip goes on
    p = crew("driver")
    p.drive_to = A + Vec(0.0, 60.0, 0.0)
    fired = 0
    for k in range(30):
        t = 10.0 + k / 30
        see(p, 2, foe.pos, t)
        me = PlayerState(1, 0, "p", A, yaw=0.0, vehicle=5)
        a = tick(p, t, FALCON, me, [foe])
        fired += a.fire
    if fired or p.att[0] != "path":
        fails.append(f"lone Falcon pilot, a man 12 u off: fired {fired} of 30 ticks, doing {p.att[0]} (want no shots, "
                     f"its trip on)")
    # 2. one side gun manned: that side to him (he is due east: heading -90 deg puts him on the left)
    for side, want in (("left", -math.pi / 2), ("right", math.pi / 2)):
        p = crew("driver", seed=2)
        v = dict(FALCON, riders=2, gunner=True, turrets=["falcon_side_gun_left", "falcon_side_gun_right"],
                 manned=[f"falcon_side_gun_{side}"])
        me = PlayerState(1, 0, "p", A, yaw=0.0, vehicle=5)
        g = PlayerState(3, 0, "g", A, yaw=0.0, vehicle=5, gunner_seat=True, turret=f"falcon_side_gun_{side}")
        see(p, 2, foe.pos, 10.0)
        a = tick(p, 10.0, v, me, [foe, g])
        if abs(wrap(a.yaw - want)) > 0.15:
            fails.append(f"Falcon, {side} gun manned, a man due east: heading {math.degrees(a.yaw):.0f} deg "
                         f"(want {math.degrees(want):.0f}: the manned side to him)")
    # 3. the nose-gun Falcon's pilot shoots
    p = crew("driver", seed=3)
    v = dict(FALCON, turrets=["falcon_chin_gun"])
    fired = 0
    yaw = 0.0
    for k in range(45):
        t = 10.0 + k / 30
        see(p, 2, foe.pos, t)
        me = PlayerState(1, 0, "p", A, yaw=yaw, pitch=-0.3, vehicle=5)
        a = tick(p, t, v, me, [foe], yaw)
        yaw = a.yaw
        fired += a.fire
    if not fired:
        fails.append("nose-gun Falcon pilot, a man 12 u ahead: never fired (the chin gun is the pilot's)")
    # 4. a side gunner on a man strafing 16 u off, its view following its hand (Normal)
    g = crew("gunner", tier="average", seed=4)
    v = dict(FALCON, riders=2, gunner=True, turrets=["falcon_side_gun_left"], manned=["falcon_side_gun_left"],
             fwd=(0.0, -1.0, 0.0))                     # facing south: due east is its left side
    yaw, pitch, fired, first = math.pi / 2, 0.0, 0, None
    for k in range(90):
        t = 20.0 + k / 30
        q = A + Vec(16.0, 1.5 * math.sin(t * 1.5), -4.0)          # a Spartan's strafe, up to 2.25 u/s
        see(g, 2, q, t)
        g.per.beliefs[2].vel = Vec(0.0, 2.25 * math.cos(t * 1.5), 0.0)
        me = PlayerState(1, 0, "g", A, yaw=yaw, pitch=pitch, vehicle=5, gunner_seat=True, turret="falcon_side_gun_left")
        a = tick(g, t, v, me, [PlayerState(2, 1, "f", q)], yaw)
        if first is None:
            first = a.fire                             # still 90 degrees off him
        yaw, pitch = a.yaw, a.pitch
        fired += a.fire and k >= 45
    if first:
        fails.append("side gunner fired while still 90 degrees off its man")
    if fired < 0.8 * 45:
        fails.append(f"side gunner on a man strafing 16 u off: fired {fired} of its last 45 ticks (want 80%+; the hand "
                     f"gun's window gave 34% live)")
    # 5. a passenger: the man our gunner looks at (east, 14 u), not the closer one (west, 8 u); none with the flag
    for flag in (False, True):
        ps = crew("passenger", seed=5)
        v = dict(FALCON, riders=3, gunner=True, turrets=["falcon_side_gun_left"], manned=["falcon_side_gun_left"])
        east, west = A + Vec(14.0, 0.0, -4.0), A + Vec(-8.0, 0.0, -4.0)
        see(ps, 2, east, 10.0)
        see(ps, 4, west, 10.0)
        me = PlayerState(1, 0, "ps", A, yaw=0.0, vehicle=5, weapon="dmr", has_flag=flag)
        gun = PlayerState(3, 0, "g", A, yaw=0.02, vehicle=5, gunner_seat=True, turret="falcon_side_gun_left")
        ps.att = None
        a = tick(ps, 10.0, v, me, [PlayerState(2, 1, "e", east), PlayerState(4, 1, "w", west), gun])
        if not flag and (not ps.att or ps.att[1] != 2):
            fails.append(f"passenger: shot at {ps.att and ps.att[1]} (want 2, the man the gunner's view is on)")
        if flag and (a.fire or ps.att):
            fails.append("passenger carrying the objective aimed or fired (want neither)")
    # 6. into a Reach Falcon with its pilot in, not in one of its guns: a passenger
    sb = crew("driver", seed=6)
    sb.seat_for, sb.enter_riders = None, 1
    tick(sb, 10.0, dict(FALCON, riders=2, turrets=["falcon_side_gun_left", "falcon_side_gun_right"]),
         PlayerState(1, 0, "s", A, vehicle=5), [])
    if sb.seat != "passenger":
        fails.append(f"a Reach Falcon's troop seat read as {sb.seat} (want passenger)")
    # 6b. H2A: botcore seats a bot by the seat it asked for, so that is its seat whoever was inside (H2A Bloodline:
    # the first one into a Warthog's passenger seat "drove" it, one at the wheel behind its gunner only aimed)
    h2a = get_map("h2a_ca_coagulation")
    h2a_hog = dict(handle=5, kind="h2a_warthog", pos=(A.x, A.y, A.z), riders=1, occupied=True, fwd=(1.0, 0.0, 0.0),
                   turrets=["h2a_warthogchaingun"], manned=[], gunner=False)
    for asked, inside, want in (("passenger", 0, "passenger"), ("driver", 1, "driver")):
        hb = Bot(1, 0, make_profile("strong", "rusher", random.Random(8)), h2a, random.Random(8))
        hb._terrain = T
        hb.seat_for, hb.enter_riders, hb.enter_want = None, inside, asked
        tick(hb, 10.0, dict(h2a_hog, riders=inside + 1), PlayerState(1, 0, "h", A, vehicle=5), [])
        if hb.seat != want:
            fails.append(f"H2A Warthog, asked for {asked} with {inside} inside: seat read as {hb.seat} (want {want})")
    # 6c. a Warthog wedged just off its drivable ground (Bloodline, its edge 0.25 u away): it counted as "arrived" every
    # tick and was sent on again, never stuck, 0.35 throttle into the rock for 30 s (live); it backs off within 4 s
    from brain.bot import Order
    wb = Bot(1, 0, make_profile("top", "rusher", random.Random(3)), h2a, random.Random(3))
    wb.order, wb.seat_for, wb.enter_want, wb.enter_riders = Order("drive"), None, "driver", 0
    wedge = Vec(24.60, 16.69, 0.19)
    stuck_hog = dict(h2a_hog, pos=(wedge.x, wedge.y, wedge.z), fwd=(math.cos(-1.22), math.sin(-1.22), 0.0))
    back_at = None
    for k in range(150):
        t = 10.0 + k / 30
        wme = PlayerState(1, 0, "w", wedge, yaw=-1.22, vehicle=5)
        a = Action(yaw=-1.22)
        wb.drive(t, 1 / 30, wme, Snapshot(t, [wme], vehicles=[stuck_hog]), a, lambda p, q, **kw: q)
        if a.forward < 0 and back_at is None:
            back_at = t - 10.0
    if back_at is None or back_at > 4.0:
        fails.append(f"a wedged Warthog at the edge of its ground: first reverse {back_at} s (want within 4 s)")
    ce = crew("driver", seed=9)                   # elsewhere the game picks the seat: still told by who is inside
    ce.seat_for, ce.enter_riders, ce.enter_want = None, 0, "passenger"
    tick(ce, 10.0, dict(h2a_hog, kind="warthog", riders=1), PlayerState(1, 0, "c", A, vehicle=5), [])
    if ce.seat != "driver":
        fails.append(f"CE Warthog, empty when it got in: seat read as {ce.seat} (want driver)")
    # 6d. a gunner and a passenger in a Warthog with nobody at the wheel stayed in to the end (H2A Bloodline: the rule
    # asked for one rider only). Out (Use held) after 5 s still; never with a person aboard (he may have parked to
    # fight) or while it moves
    def first_use(seat, human=False, moving=False):
        rb = crew(seat, seed=11)
        others = [PlayerState(3, 0, "g", A, vehicle=5, gunner_seat=True)] if seat == "passenger" else \
            [PlayerState(3, 0, "p", A, vehicle=5)]
        if human:
            others.append(PlayerState(4, 0, "you", A, vehicle=5, is_bot=False))
        hog = dict(h2a_hog, riders=len(others) + 1, gunner=True, manned=["h2a_warthogchaingun"])
        for k in range(240):
            t = 10.0 + k / 30
            me = PlayerState(1, 0, "r", A + Vec(t - 10.0 if moving else 0.0, 0.0, 0.0), vehicle=5,
                             gunner_seat=seat == "gunner", turret="h2a_warthogchaingun" if seat == "gunner" else "")
            if tick(rb, t, hog, me, others).action:
                return t - 10.0
        return None
    for seat in ("passenger", "gunner"):
        out = first_use(seat)
        if out is None or not 5.0 <= out <= 5.5:
            fails.append(f"H2A Warthog, {seat} with nobody driving: first Use at {out} s (want 5-5.5 s)")
        for how in ("human", "moving"):
            out = first_use(seat, **{how: True})
            if out is not None:
                fails.append(f"H2A Warthog, {seat}, {'a person aboard' if how == 'human' else 'moving'}: Use at {out} s "
                             "(want none)")
    # 6e. out of a Warthog's gun (nobody drove), back in at its wheel: a new seat, read again (H2A Bloodline s133: it
    # kept "gunner" and its old seat clock and was out again at once, 162 exits in 9 minutes)
    lb = Bot(1, 0, make_profile("strong", "rusher", random.Random(12)), h2a, random.Random(12))
    lb._terrain = T
    lb.seat_for, lb.seat_since, lb.seat = 5, 0.0, "gunner"
    foot = PlayerState(1, 0, "l", A + Vec(3.0, 0.0, 0.0))
    lb.think(20.0, 1 / 30, Snapshot(20.0, [foot], vehicles=[dict(h2a_hog, riders=0, occupied=False)]), T.los,
             lambda p, q, **k: q, [])
    lb.enter_want, lb.enter_riders = "driver", 0
    tick(lb, 20.5, dict(h2a_hog, riders=1), PlayerState(1, 0, "l", A, vehicle=5), [])
    if lb.seat != "driver" or lb.seat_since != 20.5:
        fails.append(f"back in the same Warthog at its wheel: seat {lb.seat}, seat clock from {lb.seat_since} "
                     "(want driver, 20.5)")
    # 6f. a teammate's Warthog on its roof is no ride (Halo 4 Exile: an upturned Warthog boarded 20 times, each time
    # out again a second later): no press for its gun beside it; standing, the press comes

    def joins(upz):
        jb = Bot(1, 0, make_profile("strong", "rusher", random.Random(14)), h2a, random.Random(14))
        jb._terrain = T
        jb.order, jb.goal, jb.next_decide = Order("ride"), ("vehicle", 5), 1e9
        hog = dict(h2a_hog, riders=1, occupied=True, team=0, up=(0.0, (1 - upz * upz) ** 0.5, upz))
        mate = PlayerState(3, 0, "m", A, vehicle=5)
        for k in range(30):
            t = 30.0 + k / 30
            me = PlayerState(1, 0, "j", A + Vec(1.0, 0.0, 0.0))
            a = jb.think(t, 1 / 30, Snapshot(t, [me, mate], vehicles=[hog]), T.los, lambda p, q, **kw: q, [])
            if a.seat >= 0 or a.action:
                return True
        return False
    for upz, want in ((1.0, True), (-1.0, False), (0.2, False)):
        if joins(upz) != want:
            fails.append(f"a teammate's Warthog with up z {upz}: pressed to join {not want} (want {want})")
    # 6g. a driver just in waits for a teammate coming for a free seat, 8 s at most; nobody near, a full vehicle, shot
    # at, an enemy close or a flag aboard: off at once
    G = Vec(60.0, -100.0, T.ground(60.0, -100.0))

    def waits(kind="warthog", riders=1, mate=(6.0, -5.0), t=1.0, shot=False, enemy=None, flag=False):
        db = crew("driver", seed=21)
        db.seat_vitals, db.notes = 2.0, []
        car = dict(handle=5, kind=kind, pos=(G.x, G.y, G.z), riders=riders, occupied=True, team=0, fwd=(1.0, 0.0, 0.0),
                   turrets=[], manned=[], gunner=False)
        me = PlayerState(1, 0, "d", G, vehicle=5, shield=0.5 if shot else 1.0, has_flag=flag)
        others = [] if mate is None else [PlayerState(3, 0, "m", G + Vec(mate[0], 0.0, 0.0), vel=Vec(mate[1], 0.0, 0.0))]
        if enemy is not None:
            see(db, 9, G + Vec(0.0, enemy, 0.0), t)
        tick(db, t, car, me, others)
        return "vehicle: waiting for crew" in db.notes
    for name, kw, want in (("a teammate running to its Warthog", {}, True), ("to its Mongoose", dict(kind="mongoose"), True),
                           ("nobody near", dict(mate=None), False), ("8 s on", dict(t=9.0), False),
                           ("a teammate running off", dict(mate=(6.0, 5.0)), False),
                           ("a teammate at the door, 1 s in", dict(mate=(2.0, 0.0)), True),
                           ("a teammate at the door, 4 s in", dict(mate=(2.0, 0.0), t=4.0), False),
                           ("every seat taken", dict(riders=3), False), ("shot since getting in", dict(shot=True), False),
                           ("an enemy 12 u off", dict(enemy=12.0), False), ("the flag aboard", dict(flag=True), False)):
        if waits(**kw) != want:
            fails.append(f"a driver just in, {name}: waits {not want} (want {want})")
    # 7. a chaingun: a man gone out of sight 0.5 s ago, spun up on where he went; 3 s on, quiet
    w = crew("gunner", seed=7)
    hog = dict(handle=5, kind="warthog", pos=(A.x, A.y, A.z), riders=2, occupied=True, fwd=(1.0, 0.0, 0.0),
               turrets=["warthog_chaingun"], manned=["warthog_chaingun"], gunner=True)
    see(w, 2, A + Vec(12.0, 3.0, -4.0), 9.5, seen=False)
    me = PlayerState(1, 0, "w", A, vehicle=5, gunner_seat=True, turret="warthog_chaingun")
    spun = tick(w, 10.0, hog, me, []).fire
    late = tick(w, 12.5, hog, me, []).fire
    if not spun or late:
        fails.append(f"chaingun: 0.5 s after losing its man fired {spun} (want True), 3 s after {late} (want False)")
    # 7b. a Reach chaingun aims from where its shot leaves, 0.92 over the gunner's place (the Warthog's height), not
    # from the eye's 0.62
    ag = crew("gunner", tier="top", seed=8)
    man = A + Vec(6.0, 0.0, 0.0)
    see(ag, 2, man, 20.0)
    tick(ag, 20.0, hog, PlayerState(1, 0, "w", A, vehicle=5, gunner_seat=True, turret="warthog_chaingun"),
         [PlayerState(2, 1, "x", man)])
    want = math.atan2(0.35 - 0.92, 6.0)
    got = ag.aim.goal[1] - ag.aim.err[1] if getattr(ag.aim, "goal", None) else None
    if got is None or abs(got - want) > 0.01:
        fails.append(f"chaingun aim pitch {got} (want {want:.3f}: from the gun's 0.92, not the eye's 0.62)")
    # 7c. a rider with nobody in sight looks for someone: a left side gun turns to its side and sweeps it; one that knew
    # a man 3 s ago turns there
    def looks(knew):
        lb = crew("gunner", seed=9)
        if knew:
            see(lb, 2, A + Vec(-10.0, 0.0, 0.0), 27.0, seen=False)
        yaws, yaw = [], 0.0
        for k in range(90):
            me = PlayerState(1, 0, "l", A, yaw=yaw, vehicle=5, gunner_seat=True, turret="falcon_side_gun_left")
            yaw = tick(lb, 30.0 + k / 30, dict(FALCON, riders=2, gunner=True, turrets=["falcon_side_gun_left"],
                                               manned=["falcon_side_gun_left"]), me, [], yaw=yaw).yaw
            yaws.append(yaw)
        return yaws
    side, back = looks(False), looks(True)
    if abs(wrap(side[-1] - math.pi / 2)) > 0.9 or max(side) - min(side) < 0.5:
        fails.append(f"a left side gunner with nobody in sight ended at yaw {side[-1]:.2f} (want its side, 1.57 +-0.9)")
    if abs(wrap(back[-1] - math.pi)) > 0.2:
        fails.append(f"a rider that knew a man behind it 3 s ago ended at yaw {back[-1]:.2f} (want 3.14)")
    # 8. Reach variants
    checks = [(vehicles.variant("warthog", ["warthog_gauss"]), "gauss"),
              (vehicles.variant("warthog", ["warthog_rocket"]), "rwarthog"),
              (vehicles.variant("warthog", ["warthog_chaingun"]), "warthog"),
              (vehicles.variant("warthog", ["warthog_troop"]), "thog"),
              (vehicles.variant("falcon", ["falcon_sensor", "falcon_side_grenade_left"]), "falcon"),
              (vehicles.variant("banshee_mp", []), "banshee_mp"),
              (vehicles.spec("thog")["gun"], None),
              (vehicles.gunner_gun(dict(kind="falcon"), "falcon_side_grenade_right"), "grenade_launcher"),
              (vehicles.gunner_gun(dict(kind="falcon"), "falcon_side_gun_right"), "assault_rifle"),
              (vehicles.gunner_gun(dict(kind="gauss"), "warthog_gauss"), "sniper"),
              (vehicles.gunner_gun(dict(kind="mp_warthog"), ""), "assault_rifle"),
              (vehicles.driver_armed(dict(kind="falcon", turrets=["falcon_side_gun_left"])), False),
              (vehicles.driver_armed(dict(kind="falcon", turrets=["falcon_chin_gun"])), True),
              (vehicles.driver_armed(dict(kind="warthog")), False),
              (vehicles.driver_armed(dict(kind="ghost")), True),
              (vehicles.gun_sides(dict(manned=["falcon_side_gun_left", "falcon_side_grenade_right"])), {"left", "right"})]
    for k, (got, want) in enumerate(checks):
        if got != want:
            fails.append(f"vehicles table check {k}: {got!r} (want {want!r})")
    # 9. the snapshot of a Falcon with a man in its left gun
    import live_bots

    class Reader:
        def __init__(s, mem):
            s.mem = mem

        def read(s, a, n):
            return s.mem.get(a, b"\xff" * n)

    class FakeLive:
        PARENT_AT = 0x14

        def __init__(s):
            s.g = Reader({0x1000 + 0x14: struct.pack("<I", 0xE0010001), 0x2000 + 0x14: struct.pack("<I", 0xE0010001)})

        def players(s):
            return [dict(index=1, name="Bot", team=0, unit=1, pos=(1.0, 2.0, 3.0), aim=(1, 0, 0), health=1.0, shield=1.0,
                         weapon="dmr", weapons=["dmr"], vehicle=0xE0020002)]

        def objects(s, types=None):
            return [(0xE0010001, 1, "objects\\vehicles\\human\\falcon\\falcon", (1.0, 2.0, 3.0)),
                    (0xE0020002, 1, "objects\\vehicles\\human\\falcon\\turrets\\falcon_side_gun_left\\falcon_side_gun_left",
                     (1.0, 2.5, 3.0)),
                    (0xE0030003, 1, "objects\\vehicles\\human\\falcon\\turrets\\falcon_side_gun_right\\falcon_side_gun_right",
                     (1.0, 1.5, 3.0))]

        def object(s, h):
            return {0xE0020002: 0x1000, 0xE0030003: 0x2000}.get(h, 0x9000)

        def flags(s, players, stands=None):
            return []

    live_bots.MAP = M
    snap = live_bots.snapshot(FakeLive(), 0.0, {}, {1})
    me = snap.player(1)
    v = snap.vehicles[0] if len(snap.vehicles) == 1 else None
    if not (v and v["kind"] == "falcon" and me.vehicle == 0xE0010001 and me.gunner_seat
            and me.turret == "falcon_side_gun_left" and v["manned"] == ["falcon_side_gun_left"]
            and sorted(v["turrets"]) == ["falcon_side_gun_left", "falcon_side_gun_right"]
            and vehicles.gun_sides(v) == {"left"}):
        fails.append(f"snapshot: vehicles {snap.vehicles}, rider vehicle {me.vehicle:#x} gun {me.gunner_seat} "
                     f"turret {me.turret!r}")
    fails += crew_order_checks()
    if fails:
        print("vehicle crews FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("vehicle crews OK")


def crew_order_checks():
    """10-14: the team picks its vehicles by role."""
    from brain.director import Director
    fails = []
    B = Vec(60.0, -100.0, T.ground(60.0, -100.0))

    def bots(n, tier="strong"):
        out = {}
        for i in range(1, n + 1):
            b = Bot(i, 0, make_profile(tier, "rusher", random.Random(i)), M, random.Random(i))
            b.p.teamwork = 1.0                   # (no rogue moments: the orders themselves are checked)
            out[i] = b
        return out

    def veh(h, kind, at, occupied=False, team=-1):
        return dict(handle=h, kind=kind, pos=(at.x, at.y, at.z), occupied=occupied, riders=int(occupied), team=team,
                    fwd=(1.0, 0.0, 0.0), turrets=[], manned=[], gunner=False)

    def orders(mode, people, vs, t=10.0, crews=None):
        bs = bots(len(people))
        d = Director(0, M, bs, random.Random(1))
        if crews:
            d.crews = dict(crews)
        snap = Snapshot(t, [PlayerState(i, 0, f"b{i}", q) for i, q in people.items()], vehicles=vs, mode=mode)
        players = {i: snap.player(i) for i in bs}
        d.crew_orders(t, snap, players, list(bs.values()))
        return {i: (b.order.role, b.order.target) for i, b in bs.items()}, d

    # 10. one of each: anti-air, anti-vehicle, transport, and the harasser after them
    people = {1: B + Vec(10, 0, 0), 2: B + Vec(0, 40, 0), 3: B + Vec(-40, 0, 0), 4: B + Vec(0, -40, 0)}
    vs = [veh(11, "banshee", B + Vec(20, 0, 0)), veh(12, "scorpion", B + Vec(0, 52, 0)),
          veh(13, "warthog", B + Vec(-48, 0, 0)), veh(14, "ghost", B + Vec(0, -49, 0)),
          veh(15, "mongoose", B + Vec(70, 70, 0))]
    got, _ = orders("slayer", people, vs)
    want = {1: ("drive", 11), 2: ("drive", 12), 3: ("drive", 13), 4: ("drive", 14)}
    if got != want:
        fails.append(f"crew orders, one bot by each vehicle: {got} (want {want})")
    # 11. one bot between a Banshee (20 u) and a Warthog (25 u): Slayer takes the anti-air, CTF the transport first
    one = {1: B}
    two = [veh(11, "banshee", B + Vec(20, 0, 0)), veh(13, "warthog", B + Vec(-25, 0, 0))]
    for mode, h in (("slayer", 11), ("ctf", 13)):
        got, _ = orders(mode, one, two)
        if got[1] != ("drive", h):
            fails.append(f"crew orders, {mode}: {got[1]} (want driving {h})")
    # 12. too far (60 u): no order
    got, _ = orders("slayer", one, [veh(11, "banshee", B + Vec(60, 0, 0))])
    if got[1][0] == "drive":
        fails.append(f"crew orders: sent 60 u to a Banshee ({got[1]})")
    # 13. a teammate already flies a Banshee: the second empty one is not an anti-air job; the Ghost is still a harasser's
    got, _ = orders("slayer", one, [veh(11, "banshee", B + Vec(20, 0, 0)), veh(16, "banshee", B + Vec(5, 5, 0), True, 0),
                                    veh(14, "ghost", B + Vec(-30, 0, 0))])
    if got[1] != ("drive", 14):
        fails.append(f"crew orders, our Banshee flying: {got[1]} (want the Ghost, 14)")
    # 14. a job kept 30 s, then dropped (and that vehicle not offered to that bot for 60 s)
    got, d = orders("slayer", one, [veh(11, "banshee", B + Vec(20, 0, 0))], t=50.0, crews={11: (1, 10.0)})
    if got[1][0] == "drive" or d.crew_skip.get((1, 11), 0) < 100.0:
        fails.append(f"crew orders: a 40 s old job still {got[1]}, skip {d.crew_skip}")
    # 15. the bot takes the job from 40 u (a seat call reaches 30 u)
    b = bots(1)[1]
    b._terrain = T
    b.order = __import__("brain.bot", fromlist=["Order"]).Order("drive", B + Vec(40, 0, 0), target=11)
    me = PlayerState(1, 0, "b1", B)
    snap = Snapshot(10.0, [me], vehicles=[veh(11, "banshee", B + Vec(40, 0, 0))], mode="slayer")
    g = b.decide(10.0, me, snap)
    if g != ("vehicle", 11):
        fails.append(f"a bot sent 40 u to drive a Banshee chose {g}")
    # 16. a role's driver at its destination keeps driving (no getting out), on to the next place
    w = crew("driver", seed=8)
    w.crew_ride, w.drive_to = 5, B + Vec(2.0, 0.0, 0.0)
    gh = dict(handle=5, kind="ghost", pos=(B.x, B.y, B.z), riders=1, occupied=True, fwd=(1.0, 0.0, 0.0))
    me = PlayerState(1, 0, "w", B, vehicle=5)
    a = tick(w, 30.0, gh, me, [])
    if a.action or now_exit(w, 30.0):
        fails.append("a role's Ghost got out at its destination")
    return fails


def now_exit(b, t):
    return t < getattr(b, "exit_until", 0.0)


if __name__ == "__main__":
    main()
