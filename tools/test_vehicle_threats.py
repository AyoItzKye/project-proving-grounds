"""Rams and threats (docs/research/17-vehicle-tactics-guide.md §4.3, §4.6), checked on the driver's commands:

1. Armor Lock: a Warthog never runs at a man locked in it (Reach: the rammer dies; REACH-CTF-04, KOTH-02, ASS-02); the
   same man unlocked is run down
2. head on: a Warthog runs at an enemy Ghost (Halo 2 on), never at a Scorpion; in CE not at the Ghost either
3. a Ghost (its own gun) commits only with the man within 12 degrees of its nose; at 40 degrees a gun run
4. the rocket hog and the transport hog never run men down
5. a man who sidestepped 1.5 u off the nose 4 u ahead: on through (the heading kept), not swerved into
6. a man run down: on at full throttle 1.5 s, not stopped beside him
7. a rocket aimed at a Warthog 20 u off: after the tier's reaction it turns across his line at full throttle; Easy
   never dodges
8. a plasma pistol 4 u off (Reach): full throttle away; in CE (no EMP) nothing
9. a Scorpion's barrel on us: a Ghost slides out of its line nose kept, a Banshee climbs over it
10. a Falcon breaks off from an enemy Banshee 30 u off (away and down); a Scorpion holds under a rocket

usage: python -I test_vehicle_threats.py      -> "vehicle threats OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("bloodgulch")
R = dict(M, name="reach_35_island")               # Reach's rules on the same ground (s.game "reach")
T = terrain(M)
A = Vec(60.0, -100.0, T.ground(60.0, -100.0))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def driver(game=R, tier="top", seed=1):
    b = Bot(1, 0, make_profile(tier, "rusher", random.Random(seed)), game, random.Random(seed))
    b._terrain = T
    b.seat_for, b.seat_since, b.seat = 5, 0.0, "driver"
    b.drive_to = A + Vec(0.0, 80.0, 0.0)              # a trip north
    return b


def veh(kind, at=A, h=5, fwd=(1.0, 0.0, 0.0), riders=1):
    return dict(handle=h, kind=kind, pos=(at.x, at.y, at.z), riders=riders, occupied=True, fwd=fwd, turrets=[],
                manned=[], gunner=False, team=0)


def run(b, kind, foes, t=10.0, n=1, extra=(), fwd=(1.0, 0.0, 0.0), me_yaw=0.0, vel=Vec()):
    """n ticks; foes: PlayerStates in sight. The last tick's Action."""
    a = None
    for k in range(n):
        tk = t + k / 30
        for f in foes:
            b.per.beliefs[f.id] = Belief(f.pos, f.vel, tk, True, "eyes")
            b.per.recognized.add(f.id)
        me = PlayerState(1, 0, "d", A, vel, yaw=me_yaw, vehicle=5)
        a = Action(yaw=me_yaw)
        b.drive(tk, 1 / 30, me, Snapshot(tk, [me] + list(foes), vehicles=[veh(kind, fwd=fwd)] + list(extra)), a,
                lambda p, q, **kw: q)
    return a


def man(pid=2, at=A + Vec(8.0, 0.0, 0.0), weapon="assault_rifle", yaw=math.pi, **kw):
    return PlayerState(pid, 1, f"m{pid}", at, weapon=weapon, weapons=[weapon], yaw=yaw, **kw)


def main():
    fails = []
    # 1. Armor Lock
    b = driver()
    run(b, "warthog", [man(equipment="armor_lock", ability_on=True)])
    if b.att and b.att[0] == "splatter":
        fails.append("Warthog ran at a man in Armor Lock")
    b = driver()
    run(b, "warthog", [man(equipment="armor_lock")])
    if not b.att or b.att[0] != "splatter":
        fails.append(f"Warthog did not run down a man not locked ({b.att})")
    # 2. head on: a Ghost yes, a Scorpion no, CE no
    for game, kind, want in ((R, "ghost", True), (R, "scorpion", False), (M, "ghost", False)):
        b = driver(game=game)
        g = man(at=A + Vec(12.0, 0.0, 0.0), vehicle=7)
        run(b, "warthog", [g], extra=[veh(kind, A + Vec(12.0, 0.0, 0.0), h=7, fwd=(-1.0, 0.0, 0.0))])
        ran = bool(b.att) and b.att[0] == "splatter"
        if ran != want:
            fails.append(f"Warthog ({game['name']}) at an enemy {kind} head on: ran {ran} (want {want})")
    # 3. a Ghost's run needs him on its nose
    for deg, want in ((5.0, True), (40.0, False)):
        b = driver()
        q = A + Vec(10.0 * math.cos(math.radians(deg)), 10.0 * math.sin(math.radians(deg)), 0.0)
        run(b, "ghost", [man(at=q)])
        ran = bool(b.att) and b.att[0] == "splatter"
        if ran != want:
            fails.append(f"Ghost, a man {deg:.0f} degrees off its nose: ran {ran} (want {want})")
    # 4. rocket hog and transport hog: no runs
    for kind in ("rwarthog", "thog"):
        b = driver()
        run(b, kind, [man()])
        if b.att and b.att[0] == "splatter":
            fails.append(f"the {kind} ran a man down")
    # 5. a sidestep close in: on through
    b = driver()
    run(b, "warthog", [man(at=A + Vec(7.0, 0.3, 0.0))])                  # the run starts
    a = run(b, "warthog", [man(at=A + Vec(4.0, 1.5, 0.0))], t=11.0)       # he stepped aside 1 s on
    a2 = run(b, "warthog", [man(at=A + Vec(4.0, 1.5, 0.0))], t=11.1)
    if abs(wrap(a2.yaw)) > 0.05 or a2.forward < 0.99:
        fails.append(f"Warthog swerved into a man who sidestepped: yaw {a2.yaw:.2f} (want 0, on through)")
    # 6. post hit: on 1.5 s
    b = driver()
    run(b, "warthog", [man(at=A + Vec(3.0, 0.0, 0.0))])
    dead = man(at=A + Vec(1.0, 0.0, 0.0), alive=False)
    b.per.beliefs.pop(2, None)
    a = Action()
    me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
    b.drive(10.5, 1 / 30, me, Snapshot(10.5, [me, dead], vehicles=[veh("warthog")]), a, lambda p, q, **kw: q)
    a2 = Action()
    b.drive(11.5, 1 / 30, me, Snapshot(11.5, [me, dead], vehicles=[veh("warthog")]), a2, lambda p, q, **kw: q)
    if a.forward < 0.99 or a2.forward < 0.99 or a.action or a2.action:
        fails.append(f"Warthog after running a man down: forward {a.forward:.1f} / {a2.forward:.1f} (want on, 1.5 s)")
    # 7. a rocket aimed at us 20 u off (due east, aiming west at us): across his line; Easy holds its course
    rk = man(at=A + Vec(20.0, 0.0, 0.0), weapon="rockets", yaw=math.pi)
    b = driver()
    a = run(b, "warthog", [rk], n=12, me_yaw=math.pi / 2, fwd=(0.0, 1.0, 0.0))   # driving north
    if not (b.att and b.att[0] == "evade") or abs(abs(wrap(a.yaw - math.pi)) - math.pi / 2) > 0.2 or a.forward < 0.99:
        fails.append(f"Warthog, a rocket aimed at it: yaw {math.degrees(a.yaw):.0f} forward {a.forward:.1f} "
                     f"({b.att}; want across his line, full throttle)")
    e = driver(tier="novice")
    run(e, "warthog", [rk], n=30, me_yaw=math.pi / 2, fwd=(0.0, 1.0, 0.0))
    if e.att and e.att[0] == "evade":
        fails.append("Easy dodged a rocket in a Warthog (it never dodges)")
    # 8. EMP gun 4 u off: away (Reach), nothing in CE
    for game, want in ((R, True), (M, False)):
        b = driver(game=game)
        a = run(b, "mongoose", [man(at=A + Vec(4.0, 0.0, 0.0), weapon="plasma_pistol")], n=12)
        away = bool(b.att) and b.att[0] == "evade" and abs(wrap(a.yaw - math.pi)) < 0.2
        if away != want:
            fails.append(f"Mongoose ({game['name']}), a plasma pistol 4 u off: drove away {away} (want {want})")
    # 9. a Scorpion's barrel on us: the Ghost slides across nose kept, the Banshee climbs
    tank = man(at=A + Vec(30.0, 0.0, 0.0), yaw=math.pi, vehicle=7)
    sc = veh("scorpion", A + Vec(30.0, 0.0, 0.0), h=7, fwd=(-1.0, 0.0, 0.0))
    for nose in (math.pi / 2, 0.2):               # facing north (across is ahead), nearly facing the tank (a slide)
        b = driver()
        a = run(b, "ghost", [tank], n=12, extra=[sc], me_yaw=nose, fwd=(math.cos(nose), math.sin(nose), 0.0))
        move = a.yaw + math.atan2(a.strafe, a.forward)
        if (not (b.att and b.att[0] == "evade") or abs(wrap(a.yaw - nose)) > 0.05
                or abs(abs(wrap(move - math.pi)) - math.pi / 2) > 0.1 or math.hypot(a.forward, a.strafe) < 0.9):
            fails.append(f"Ghost facing {math.degrees(nose):.0f} under a Scorpion's barrel: yaw {math.degrees(a.yaw):.0f}"
                         f" moving {math.degrees(move):.0f} ({b.att}; want across the barrel's line, nose kept)")
    b = driver()
    a = run(b, "banshee", [tank], n=12, extra=[sc])
    if not (b.att and b.att[0] == "evade") or a.pitch < 0.3:
        fails.append(f"Banshee under a Scorpion's barrel: pitch {a.pitch:.2f} ({b.att}; want climbing over it)")
    # 10. a Falcon and an enemy Banshee 30 u off: away and down; a Scorpion holds under a rocket
    bn = man(at=A + Vec(30.0, 0.0, 6.0), vehicle=8)
    b = driver()
    a = run(b, "falcon", [bn], n=12, extra=[veh("banshee", A + Vec(30.0, 0.0, 6.0), h=8)])
    if not (b.att and b.att[0] == "evade") or abs(wrap(a.yaw - math.pi)) > 0.2 or a.vertical > -0.5:
        fails.append(f"Falcon, an enemy Banshee 30 u off: yaw {math.degrees(a.yaw):.0f} vertical {a.vertical} "
                     f"({b.att}; want away and down)")
    b = driver()
    run(b, "scorpion", [rk], n=12)
    if b.att and b.att[0] == "evade":
        fails.append("a Scorpion dodged a rocket (tanks hold)")
    # 11. a man on foot 1.8 u behind a Ghost, not aiming at it (a rocket: no run at him): full throttle away after the
    #     tier's reaction, also from a radar dot of him 0.5 s old (not 1.5 s); Easy does not react
    bd = man(at=A + Vec(-1.8, 0.0, 0.0), weapon="rockets", yaw=math.pi / 2)
    b = driver()
    a = run(b, "ghost", [bd], n=12)
    if not (b.att and b.att[0] == "evade") or abs(wrap(a.yaw)) > 0.2 or a.forward < 0.99:
        fails.append(f"Ghost, a man 1.8 u behind it: yaw {math.degrees(a.yaw):.0f} forward {a.forward:.1f} "
                     f"({b.att}; want away from him, full throttle)")
    e = driver(tier="novice")
    run(e, "ghost", [bd], n=30)
    if e.att and e.att[0] == "evade":
        fails.append("Easy drove away from a boarder (it does not react)")
    # ... a Banshee hovering 2.7 u over a man goes away (10 m for a hovering aircraft); one on its run over him at 12 u/s
    #     flies on
    for vel, want in ((Vec(), True), (Vec(12.0, 0.0, 0.0), False)):
        b = driver()
        run(b, "banshee", [man(at=A + Vec(1.0, 0.0, -2.5), yaw=math.pi / 2)], n=12, vel=vel)
        if (bool(b.att) and b.att[0] == "evade") != want:
            fails.append(f"Banshee at {vel.flat():.0f} u/s 2.7 u over a man: {b.att} (want away {want})")
    for age, want in ((0.5, True), (1.5, False)):
        b = driver()
        for k in range(12):
            tk = 10.0 + k / 30
            b.per.beliefs[2] = Belief(bd.pos, Vec(), tk - age, False, "radar")
            me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
            b.drive(tk, 1 / 30, me, Snapshot(tk, [me, bd], vehicles=[veh("ghost")]), Action(), lambda p, q, **kw: q)
        got = bool(b.att) and b.att[0] == "evade"
        if got != want:
            fails.append(f"Ghost, a radar dot {age} s old 1.8 u behind it: away {got} (want {want})")
    # 12. Halo 3, the driver's shield broken and a man in view 12 u off (guide 17 §4.1 driver_shield_down): a Warthog
    #     drives to the teammate 20 u north, full throttle; not in Reach, not Easy, not with its shield up
    H3 = dict(M, name="h3_bloodgulch")
    mate = PlayerState(3, 0, "t", A + Vec(0.0, 20.0, 0.0))
    for game, tier, shield, want in ((H3, "strong", 0.0, True), (R, "strong", 0.0, False), (H3, "novice", 0.0, False),
                                     (H3, "strong", 0.8, False)):
        b = driver(game=game, tier=tier)
        f = man(at=A + Vec(12.0, 0.0, 0.0))
        for k in range(3):
            tk = 10.0 + k / 30
            b.per.beliefs[2] = Belief(f.pos, Vec(), tk, True, "eyes")
            b.per.recognized.add(2)
            me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5, shield=shield)
            a = Action()
            b.drive(tk, 1 / 30, me, Snapshot(tk, [me, f, mate], vehicles=[veh("warthog")]), a, lambda p, q, **kw: q)
        got = bool(b.att) and b.att[0] == "retreat"
        if got != want or (want and (getattr(b, "retreat_to", None) != mate.pos or a.forward < 0.99 or a.fire)):
            fails.append(f"Warthog ({game['name']}, {tier}, shield {shield}) with a man in view: {b.att}, to "
                         f"{getattr(b, 'retreat_to', None)}, forward {a.forward} (want a retreat to the teammate {want})")
    if fails:
        print("vehicle threats FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("vehicle threats OK")


if __name__ == "__main__":
    main()
