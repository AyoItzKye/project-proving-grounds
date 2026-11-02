"""Vehicle roles from the research, checked on the driver's commands:

1. artillery (Wraith): a man 4 u off is a boarder, it backs off; at 30 u it holds its range and keeps moving side on;
   at 60 u it closes in
2. splatter (Ghost): a man on foot with a rifle 10 u off is run down, full throttle at him; one with a rocket launcher
   is not (a strafing gun run instead)

usage: python -I test_vehicle_roles.py      -> "vehicle roles OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("bloodgulch")
T = terrain(M)
A = Vec(60.0, -100.0, T.ground(60.0, -100.0))


def driver(kind, seed=1):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(seed)), M, random.Random(seed))
    b._terrain = T
    b.seat_for, b.seat_since, b.seat = 5, 0.0, "driver"
    return b


def drive_once(b, kind, foe_at, foe_weapon="assault_rifle", t=10.0, me_pos=A):
    me = PlayerState(1, 0, "d", me_pos, yaw=0.0, vehicle=5)
    foe = PlayerState(2, 1, "f", foe_at, weapon=foe_weapon, weapons=[foe_weapon])
    b.per.beliefs[2] = Belief(foe_at, Vec(), t, True, "eyes")
    b.per.recognized.add(2)
    a = Action(yaw=0.0)
    b.drive(t, 1 / 30, me, Snapshot(t, [me, foe], vehicles=[dict(handle=5, kind=kind, pos=(me_pos.x, me_pos.y, me_pos.z),
                                                                     riders=1, occupied=True, fwd=(1.0, 0.0, 0.0))]),
            a, lambda p, q, **k: q)
    return a


def main():
    fails = []
    # 1. artillery
    w = driver("wraith")
    near, mid, far = (drive_once(w, "wraith", A + Vec(d, 0.0, 0.0), t=10.0 + k) for k, d in enumerate((4.0, 30.0, 60.0)))
    if not near.forward < -0.3:
        fails.append(f"Wraith, a man 4 u off: forward {near.forward:.2f} (want backing off a boarder)")
    if abs(mid.forward) > 0.25 or abs(mid.strafe) < 0.3:
        fails.append(f"Wraith, a man 30 u off: forward {mid.forward:.2f}, strafe {mid.strafe:.2f} (want holding range, moving)")
    if not far.forward > 0.5:
        fails.append(f"Wraith, a man 60 u off: forward {far.forward:.2f} (want closing in)")
    # 2. splatter
    g = driver("ghost", seed=2)
    run = drive_once(g, "ghost", A + Vec(10.0, 0.0, 0.0))
    to = 0.0
    if not (run.forward > 0.9 and abs(run.strafe) < 0.1 and abs(math.atan2(math.sin(run.yaw - to), math.cos(run.yaw - to))) < 0.3):
        fails.append(f"Ghost, a rifleman 10 u off: forward {run.forward:.2f}, strafe {run.strafe:.2f}, yaw {run.yaw:.2f} "
                     f"(want running him down)")
    g2 = driver("ghost", seed=3)
    rk = drive_once(g2, "ghost", A + Vec(10.0, 0.0, 0.0), foe_weapon="rockets")
    if abs(rk.strafe) < 0.3:
        fails.append(f"Ghost, a rocket man 10 u off: strafe {rk.strafe:.2f} (want a side-on gun run, not a charge)")
    # 3. a wedged Ghost whose exits never happen (live: 9 of 12 bot seats ended only in death, parked drivers held
    #    Use 35-64% of their seat time): after its third try, no Use for the next 25 s, driving on instead
    p = driver("ghost", seed=4)
    p.drive_to = A + Vec(40.0, 0.0, 0.0)
    tries, was, third, held, driving = 0, False, None, 0, 0
    for k in range(3000):                    # up to 100 s, never moving and never out
        t = 50.0 + k / 30
        me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
        a = Action(yaw=0.0)
        p.drive(t, 1 / 30, me, Snapshot(t, [me], vehicles=[dict(handle=5, kind="ghost", pos=(A.x, A.y, A.z), riders=1,
                                                                 occupied=True, fwd=(1.0, 0.0, 0.0))]),
                a, lambda q, r, **kw: r)
        if a.action and not was:
            tries += 1
            if tries == 3:
                third = t
        was = bool(a.action)
        if third is not None and third + 1.0 < t < third + 26.0:
            held += bool(a.action)
            driving += abs(a.forward) > 0.5
        if third is not None and t > third + 26.0:
            break
    if third is None or held > 0 or driving < 300:
        fails.append(f"wedged, exits not happening: third try at {third}, then Use on {held} ticks in 25 s, throttle on "
                     f"{driving} (want no Use, driving on)")
    # 4. a wedged Banshee (live Spire: a pilot 252 s at full throttle and full climb under the spire, 3% of
    #    it moving; aircraft were left out of the stuck rule): within 8 s it backs off and turns, or gets out low down
    bn = driver("banshee", seed=5)
    bn.drive_to = A + Vec(40.0, 0.0, 0.0)
    backed = out = False
    for k in range(240):                     # 8 s, never moving
        t = 200.0 + k / 30
        me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
        a = Action(yaw=0.0)
        bn.drive(t, 1 / 30, me, Snapshot(t, [me], vehicles=[dict(handle=5, kind="banshee", pos=(A.x, A.y, A.z), riders=1,
                                                                  occupied=True, fwd=(1.0, 0.0, 0.0))]),
                 a, lambda q, r, **kw: r)
        backed |= a.forward < -0.5
        out |= bool(a.action)
    if not (backed or out):
        fails.append("a Banshee wedged 8 s at full throttle: never backed off or got out")
    # 4b. a Banshee circling under a place it cannot get to (Spire, the player: "Guy driving the banshee is glitching
    #     the hell out": its goal on the spire's top 20 u above, it circled 10 s under the overhang): gives it up in 6 s
    cb = driver("banshee", seed=6)
    goal = A + Vec(2.0, 0.0, 20.0)
    cb.drive_to = goal
    for k in range(180):                     # 6 s going round under it, 3 u out
        t = 300.0 + k / 30
        at = A + Vec(3.0 * math.cos(k / 15), 3.0 * math.sin(k / 15), 5.0)
        me = PlayerState(1, 0, "d", at, yaw=0.0, vehicle=5)
        cb.drive(t, 1 / 30, me, Snapshot(t, [me], vehicles=[dict(handle=5, kind="banshee", pos=(at.x, at.y, at.z),
                                                                  riders=1, occupied=True, fwd=(1.0, 0.0, 0.0))]),
                 Action(yaw=0.0), lambda q, r, **kw: r)
    if cb.drive_to is goal or (cb.drive_to is not None and (cb.drive_to - goal).flat() < 1.0):
        fails.append("a Banshee circling 6 s under a place 20 u above it never gave that place up")
    # 5. out where the vehicles' ground ends (live Boneyard: a driver got out 10 u from the Elite spawn
    #    twice, each time to walk back to the next vehicle for the same trip): it walks on, no vehicle for 25 s
    gd = driver("warthog", seed=6)
    gd.drive_to = A + Vec(60.0, 0.0, 0.0)
    gd._terrain = type("Ground", (), {"vnav": staticmethod(lambda a, b: a)})()   # the vehicle ground goes no further
    t = 400.0
    me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
    a = Action(yaw=0.0)
    gd.drive(t, 1 / 30, me, Snapshot(t, [me], vehicles=[dict(handle=5, kind="warthog", pos=(A.x, A.y, A.z), riders=1,
                                                              occupied=True, fwd=(1.0, 0.0, 0.0))]), a, lambda q, r, **kw: r)
    if not (a.action and getattr(gd, "vehicle_retry_at", 0.0) >= t + 25.0):
        fails.append(f"out where the vehicle ground ends: Use {a.action}, next vehicle allowed at "
                     f"{getattr(gd, 'vehicle_retry_at', 0.0) - t:+.1f} s (want out, none for 25 s)")
    # 6. a Warthog with its gunner circles at the player's range (match 221404: the nearest enemy 3.6-13.9 u for
    #    80% of his 234 s fight, median 7.8 u, side on): a man 9 u off is circled side on, not turned from (12-25 u
    #    turned away from every man under 12); one 25 u off is closed on; one 2.5 u off has the range opened
    for d, lo, hi, what in ((9.0, 1.3, 1.85, "side on"), (25.0, 0.0, 1.0, "closing in"), (2.5, 2.2, 3.2, "opening the range")):
        b = driver("warthog", seed=7)
        me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
        gun = PlayerState(3, 0, "g", A, vehicle=5, gunner_seat=True, turret="warthog_chaingun")
        foe_at = A + Vec(d, 0.0, 0.0)
        foe = PlayerState(2, 1, "f", foe_at, weapon="assault_rifle", weapons=["assault_rifle"])
        b.per.beliefs[2] = Belief(foe_at, Vec(), 10.0, True, "eyes")
        b.per.recognized.add(2)
        a = Action(yaw=0.0)
        hog = dict(handle=5, kind="warthog", pos=(A.x, A.y, A.z), riders=2, occupied=True, gunner=True,
                   fwd=(1.0, 0.0, 0.0), turrets=["warthog_chaingun"], manned=["warthog_chaingun"])
        b.drive(10.0, 1 / 30, me, Snapshot(10.0, [me, gun, foe], vehicles=[hog]), a, lambda p, q, **k: q)
        off = abs(math.atan2(math.sin(a.yaw), math.cos(a.yaw)))      # from the way to him (0)
        if not lo <= off <= hi or b.att[0] != "circle":
            fails.append(f"Warthog with a gunner, a man {d} u off: heading {math.degrees(off):.0f} deg off him, {b.att} "
                         f"(want {what})")
    banshee_runs(fails)
    banshee_guard(fails)
    tiers(fails)
    fuel_rod(fails)
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("vehicle roles OK")


def tiers(fails):
    """9. vehicle skill by difficulty"""
    def bot(kind, tier, seed=3, role="free"):
        b = Bot(1, 0, make_profile(tier, "rusher", random.Random(seed)), M, random.Random(seed))
        b._terrain, b.order = T, Order(role)
        b.seat_for, b.seat_since, b.seat = 5, 0.0, "driver"
        b.drive_to = A + Vec(-60.0, 0.0, 0.0)        # its trip: west
        return b
    # a. a Ghost, a man with a rifle 10 u ahead (east): Legendary runs him down; Easy drives on west, shooting him while
    # he is in front of its nose
    for tier, want in (("top", "splatter"), ("novice", "path")):
        b = bot("ghost", tier)
        got = drive_once(b, "ghost", A + Vec(10.0, 0.0, 0.0))
        if b.att[0] != want or (tier == "novice" and not got.fire):
            fails.append(f"{tier} Ghost, a rifleman 10 u ahead: {b.att[0]}, fire {got.fire} (want {want}"
                         f"{', shooting him' if tier == 'novice' else ''})")
    # b. an Easy Banshee 20 u from a man, 12 u over him: no attack run, never the second weapon, 2 s closing
    e = bot("banshee", "novice")
    fired2, runs = False, set()
    for k in range(60):
        t = 10.0 + k / 30
        at = A + Vec(20.0 - 5.0 * (t - 10.0), 0.0, 12.0)
        me = PlayerState(1, 0, "d", at, yaw=math.pi, vehicle=5)
        foe = PlayerState(2, 1, "f", A, weapon="assault_rifle", weapons=["assault_rifle"])
        e.per.beliefs[2] = Belief(A, Vec(), t, True, "eyes")
        e.per.recognized.add(2)
        a = Action(yaw=math.pi)
        e.drive(t, 1 / 30, me, Snapshot(t, [me, foe], vehicles=[dict(handle=5, kind="banshee", pos=(at.x, at.y, at.z),
                                                                    riders=1, occupied=True, fwd=(-1.0, 0.0, 0.0))]),
                a, lambda p, q, **kw: q)
        fired2 |= a.fire2
        runs.add(e.att[0])
    if fired2 or runs & {"run", "pass"}:
        fails.append(f"Easy Banshee closing on a man: states {sorted(runs)}, second weapon {fired2} (want no runs, no bomb)")
    # c. a Warthog with no gunner yet, the director's "ride" role: Normal waits for him, Easy drives off
    for tier, moving in (("average", False), ("novice", True)):
        b = bot("warthog", tier, role="ride")
        me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
        a = Action(yaw=0.0)
        b.drive(2.0, 1 / 30, me, Snapshot(2.0, [me], vehicles=[dict(handle=5, kind="warthog", pos=(A.x, A.y, A.z),
                                                                   riders=1, occupied=True, fwd=(1.0, 0.0, 0.0))]),
                a, lambda p, q, **kw: q)
        if (a.forward > 0.0) != moving:
            fails.append(f"{tier} Warthog driver, its gunner called: forward {a.forward} (want "
                         f"{'driving off' if moving else 'waiting'})")
    # d. the ram's heading error: Normal within 20 deg and not always none, Heroic within 12, Legendary none
    for tier, most in (("average", 20.0), ("strong", 12.0), ("top", 0.0)):
        errs = []
        for seed in range(1, 7):
            b = bot("ghost", tier, seed=seed)
            drive_once(b, "ghost", A + Vec(10.0, 0.0, 0.0))
            r = getattr(b, "ram", None)
            errs.append(None if r is None else math.degrees(r[2]) if len(r) > 2 else 0.0)
        if None in errs or max(abs(x) for x in errs) > most + 1e-6 or (most and max(abs(x) for x in errs) < 2.0):
            fails.append(f"{tier} rams, heading error {[None if x is None else round(x, 1) for x in errs]} deg (want "
                         f"within {most:.0f}{', not all none' if most else ''})")


def fuel_rod(fails):
    """10. Reach's Banshee fuel rod, cycled to like a secondary: closing on a man from 16 u, the cycle pressed, one shot
    0.67 s on, the cycle back 0.44 s after it, no cannon fire between; not again within 15 s. Halo CE has no cycle; Easy
    never (vehicles as transport)"""
    def run(game, tier="top", seconds=4.0):
        b = Bot(1, 0, make_profile(tier, "rusher", random.Random(11)), M, random.Random(11))
        b._terrain, b.game = T, game
        b.seat_for, b.seat_since, b.seat = 5, 0.0, "driver"
        ticks, view = [], {"pitch": 0.0}
        for k in range(int(seconds * 30)):
            t = 10.0 + k / 30
            at = A + Vec(16.0 - 1.0 * (t - 10.0), 0.0, 8.0)       # (slow, so the man stays 10-31 u off)
            me = PlayerState(1, 0, "d", at, yaw=math.pi, pitch=view["pitch"], vehicle=5)
            foe = PlayerState(2, 1, "f", A, weapon="assault_rifle", weapons=["assault_rifle"])
            b.per.beliefs[2] = Belief(A, Vec(), t, True, "eyes")
            b.per.recognized.add(2)
            a = Action(yaw=math.pi)
            b.drive(t, 1 / 30, me, Snapshot(t, [me, foe], vehicles=[dict(handle=5, kind="banshee", pos=(at.x, at.y, at.z),
                                                                        riders=1, occupied=True, fwd=(-1.0, 0.0, 0.0))]),
                    a, lambda p, q, **kw: q)
            view["pitch"] = a.pitch
            ticks.append((t, a.cycle, a.fire))
        return ticks
    ticks = run("reach")
    cyc = [t for t, c, f in ticks if c]
    if len(cyc) != 2 or not 1.15 <= cyc[1] - cyc[0] <= 1.4:
        fails.append(f"Reach Banshee from 16 u: cycle presses at {[round(t - 10.0, 2) for t in cyc]} s (want two, "
                     f"1.26 s apart: to the fuel rod and back)")
    else:
        shots = [round(t - cyc[0], 2) for t, c, f in ticks if f and cyc[0] < t < cyc[1]]
        if not shots or not 0.6 <= shots[0] <= 0.75 or shots[-1] - shots[0] > 0.2:
            fails.append(f"Reach fuel rod: fire between the cycles at {shots} s after the first (want one shot at 0.67 s)")
    for game, tier in (("ce", "top"), ("reach", "novice")):
        if any(c for t, c, f in run(game, tier, 2.0)):
            fails.append(f"{game} {tier} Banshee pressed the weapon cycle (want never)")
    # Reach's boost: the player's right button, sent as the +0x3C float (the vertical input) while the hold is
    # on
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(11)), M, random.Random(11))
    for game, want in (("reach", 1.0), ("h3", 0.0)):
        b.game, a = game, Action()
        a.fire2 = True
        b.boost(a)
        if a.vertical != want:
            fails.append(f"{game} Banshee boost hold: vertical {a.vertical} (want {want})")


def banshee_guard(fails):
    """8. a Banshee defending the core from the air: over the core in phase 3 it does not land, it holds 6 u over the
    core's height and goes round it 15 u out; in phase 2 the same pilot lands at its destination"""
    core = A + Vec(0.0, 0.0, 20.0)
    for phase in (3, 2):
        b = driver("banshee", seed=9)
        b.team = 1
        b.drive_to = core
        at = core + Vec(5.0, 0.0, 6.0)
        me = PlayerState(1, 1, "d", at, yaw=0.0, vehicle=5)
        a = Action(yaw=0.0)
        sn = Snapshot(20.0, [me], mode="invasion", inv_phase=phase, inv_attackers=0, inv_core=core,
                      vehicles=[dict(handle=5, kind="banshee", pos=(at.x, at.y, at.z), riders=1, occupied=True,
                                     fwd=(1.0, 0.0, 0.0))])
        b.drive(20.0, 1 / 30, me, sn, a, lambda p, q, **k: q)
        out = (b.drive_to - core).flat() if b.drive_to is not None else 0.0
        if phase == 3 and (not 14.0 <= out <= 16.0 or a.pitch < -0.1):
            fails.append(f"a Banshee over the core in phase 3: next point {out:.1f} u from it, pitch {a.pitch:.2f} "
                         f"(want round it 15 u out, no landing dive)")
        if phase == 2 and a.pitch > -0.1:
            fails.append(f"a Banshee at its destination in phase 2: pitch {a.pitch:.2f} (want down to land)")


def banshee_runs(fails):
    """7. a Banshee's attack runs, a skilled player's (Spire 232250: runs from 15-30 u out, the cannons inside 28 u, the
    second weapon held ~2.4 s from 12-36 u about every 6 s, past him on straight to 20-28 u, then back): never a hover
    or a side-to-side gun run"""
    man = A + Vec(0.0, 0.0, 0.0)
    b = driver("banshee", seed=8)
    view = {"pitch": 0.0}                             # (the game turns the view to the last command: the next tick's)
    presses = []                                      # (t, second weapon held) every tick

    def fly(at, yaw, t, foe_at=man):
        me = PlayerState(1, 0, "d", at, yaw=yaw, pitch=view["pitch"], vehicle=5)
        foe = PlayerState(2, 1, "f", foe_at, weapon="assault_rifle", weapons=["assault_rifle"])
        b.per.beliefs[2] = Belief(foe_at, Vec(), t, True, "eyes")
        b.per.recognized.add(2)
        a = Action(yaw=yaw)
        b.drive(t, 1 / 30, me, Snapshot(t, [me, foe], vehicles=[dict(handle=5, kind="banshee", pos=(at.x, at.y, at.z),
                                                                     riders=1, occupied=True, fwd=(math.cos(yaw), math.sin(yaw), 0.0))]),
                a, lambda p, q, **k: q)
        view["pitch"] = a.pitch
        presses.append((t, a.fire2))
        return a
    west = math.pi                                   # (it starts 20 u east of him, flying west at him)
    start = man + Vec(20.0, 0.0, 12.0)
    a = fly(start, west, 10.0)
    off = abs(math.atan2(math.sin(a.yaw - west), math.cos(a.yaw - west)))
    if b.att[0] != "run" or off > 0.4 or a.forward < 0.5 or abs(a.strafe) > 0.01:
        fails.append(f"Banshee 20 u out: {b.att}, yaw {math.degrees(off):.0f} deg off him, forward {a.forward}, strafe "
                     f"{a.strafe} (want a run at him, no side-to-side)")
    fired2, yaw = [], west
    for k in range(60):                               # 2 s closing in from 20 u: the second weapon goes once, held
        t = 10.0 + k / 30
        at = man + Vec(20.0 - 5.0 * (t - 10.0), 0.0, 12.0)
        a = fly(at, yaw, t)
        yaw = a.yaw
        fired2.append(a.fire2)
    if not any(fired2):
        fails.append("Banshee closing from 20 u, 12 u over him: never used its second weapon")
    over = fly(man + Vec(-2.0, 0.0, 6.0), west, 12.5)          # over him and past: on, straight, climbing
    if b.att[0] != "pass" or abs(math.atan2(math.sin(over.yaw - west), math.cos(over.yaw - west))) > 0.2 or over.pitch <= 0:
        fails.append(f"Banshee past him: {b.att}, yaw {over.yaw:.2f}, pitch {over.pitch:.2f} (want on west, climbing)")
    mid = fly(man + Vec(-15.0, 0.0, 9.0), west, 14.5)
    if b.att[0] != "pass" or mid.fire:
        fails.append(f"Banshee 15 u past him: {b.att}, fire {mid.fire} (want still extending, not turned back)")
    low = fly(man + Vec(-23.0, 0.0, 9.0), west, 15.0)          # far enough but 9.6 u up (no flying learned here: 9 u)
    if b.att[0] != "pass" or low.pitch <= 0:
        fails.append(f"Banshee 23 u past him, 9.6 u up: {b.att}, pitch {low.pitch:.2f} (want still climbing: the owner's "
                     f"runs start 10-35 u up, PASS_START_MIN 12)")
    yaw = west
    for k in range(45):                               # 23 u past him: the turn back east, over 1.5 s
        back = fly(man + Vec(-23.0, 0.0, 11.0), yaw, 15.5 + k / 30)
        yaw = back.yaw
    off = abs(math.atan2(math.sin(yaw - 0.0), math.cos(yaw - 0.0)))
    if b.att[0] != "run" or off > 0.5:
        fails.append(f"Banshee 23 u past him, 1.5 s on: {b.att}, yaw {yaw:.2f} (want turned back east into the next run)")
    starts = [t for (t, f), (_, was) in zip(presses[1:], presses) if f and not was] + \
        ([presses[0][0]] if presses and presses[0][1] else [])
    starts.sort()
    held = [t for t, f in presses if f]
    if any(b2 - a2 < 6.0 for a2, b2 in zip(starts, starts[1:])) or (held and not 2.0 <= held[-1] - held[0] or False):
        fails.append(f"the second weapon pressed at {starts} (want held ~2.4 s, again no sooner than 6 s)")


if __name__ == "__main__":
    main()
