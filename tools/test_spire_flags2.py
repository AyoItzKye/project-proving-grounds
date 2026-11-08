"""the player's Spire Invasion flags of, match 230700, each at its live moment:

1. Man cannons cost their time aloft: the mini base cannon's flight is no longer priced as 1.5x its 24 u, so a bot on the
   mini base by its pad (Sidewinder at 283 s, "just missed man cannon") takes it, and a Conveyor Belt spawn rides a
   cannon up to the core (the middle one, or the left one where the PC's scan makes its walk cheaper); rides start at the cannon's trigger (where people's rides start), not its marker 1.2 u into it
3. A Falcon beside the spire's top, under its level by the core (Moose 337-430 s, "flying into spire, not on top of it"):
   it climbs and does not set down; over the top by the core it sets down
4. The focus rifle is held on the man at 20 u, not burst ("needs to hold it down, not burst fire it")
5. A bot that swapped guns at its feet does not swap back for its own dropped gun (33.7 s: ten swaps in a second,
   "floating knives")
6. Its own grenade: a step toward the spot it just threw at is turned away (88 s: "threw a grenade and ran right into
   it")

usage: python -I test_spire_flags2.py      -> "spire flags 2 OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

M = get_map("reach_35_island/variants/v3977bae2")
T = terrain(M)
STAND = Vec(-178.24, -405.33, -22.9)
CORE = Vec(-172.51, -405.87, -23.88)
MINI_PAD, MID_PAD = (-143.6, -392.1), (-161.0, -380.8)
LEFT_PAD = (-191.25, -389.59)    # the other cannon up to the core's level people rode (twice, features found by them)


def first_link(p):
    """Follow the nav from p toward the core's stand until it answers a link: its take-off (x, y), or None."""
    for _ in range(400):
        w = T.nav(p, STAND, jump=True, human=True, safe=False)
        if hasattr(w, "sx"):
            return (w.sx, w.sy)
        if not hasattr(w, "x") or (Vec(w.x, w.y, w.z) - p).flat() < 0.05:
            return None
        d = Vec(w.x - p.x, w.y - p.y, 0)
        n = d.flat()
        step = min(0.5, n)
        p = Vec(p.x + d.x / n * step, p.y + d.y / n * step, T.nav_z(p.x + d.x / n * step, p.y + d.y / n * step, w.z))
    return None


def bot(seed=1, m=M):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(seed)), m, random.Random(seed))
    b._terrain, b.notes = (T if m is M else terrain(m)), []
    return b


def main():
    testdata.need_lidar("reach_35_island", "reach_35_island/variants/v3977bae2")
    fails = []
    # 1. cannons by time aloft
    near = lambda q, pad: q is not None and math.hypot(q[0] - pad[0], q[1] - pad[1]) < 1.2   # (at its trigger: within 1.2 u of the marker)
    q = first_link(Vec(-143.38, -389.53, -53.65))
    if not near(q, MINI_PAD):
        fails.append(f"on the mini base by its cannon (Sidewinder, 283 s): first link {q} (want the cannon {MINI_PAD})")
    # from Conveyor Belt a cannon up to the core, not the walk or the lift: the middle one, or (this PC's Nov 7 21:32
    # Spire scan made the walk to it cheaper) the left one people rode too, which lands 9.7 u from the core's stand to
    # the middle's 15.6 u; both cost their time aloft (checked below)
    q = first_link(Vec(-180.0, -364.0, -55.0))
    if not (near(q, MID_PAD) or near(q, LEFT_PAD)):
        fails.append(f"from Conveyor Belt: first link {q} (want a cannon up to the core: {MID_PAD} or {LEFT_PAD})")
    for src, dst, k, w in T.hjumps:
        if k.get("ride") and k["land"][2] - k["take_off"][2] > 10 and k.get("air_s"):
            if abs(w - (k["air_s"] * 2.25 + 1.0)) > 0.01:
                fails.append(f"a cannon ride from {k['take_off'][:2]}: cost {w:.1f} (want its {k['air_s']:.1f} s aloft)")
                break

    # (the rides start at the triggers: the Elites' cannon's ride 0.7 u off its marker, where VaporRaven dithered 2 u
    # off; tools/test_spire_flags.py checks every Spire launch starts within 1.2 u of its marker)

    # 3. a Falcon by the spire's top
    def fly(at, seed=5):
        b = bot(seed)
        b.order, b.seat, b.seat_for, b.enter_want, b.enter_riders, b.drive_to = Order("runner", CORE), "driver", None, \
            "driver", 0, CORE
        fal = dict(handle=5, kind="falcon", pos=(at.x, at.y, at.z), riders=1, occupied=True, fwd=(1.0, 0.0, 0.0),
                   turrets=[], manned=[], gunner=False)
        a = Action(yaw=0.0)
        me = PlayerState(1, 0, "moose", at, vehicle=5)
        b.drive(400.0, 1 / 30, me, Snapshot(400.0, [me], vehicles=[fal], mode="invasion", inv_phase=3,
                                            inv_attackers=0, inv_core=CORE), a, lambda p, q, **kw: q)
        return a, b

    a, b = fly(Vec(-171.4, -403.0, -31.0))
    if a.vertical <= 0.5 or getattr(b, "landing", False):
        fails.append(f"a Falcon 7 u under the top's level by the core: vertical {a.vertical}, landing "
                     f"{getattr(b, 'landing', None)} (want a climb, no landing)")
    a, b = fly(Vec(-172.0, -404.5, -19.5))
    if not getattr(b, "landing", False) or a.vertical > 0.0:
        fails.append(f"a Falcon over the top by the core: vertical {a.vertical}, landing {getattr(b, 'landing', None)} "
                     f"(want setting down)")

    # 4. the focus rifle held at 20 u (Blood Gulch's open ground)
    bg = get_map("bloodgulch")
    Tb = terrain(bg)
    at = Vec(70.0, -120.0, Tb.nav_z(70.0, -120.0))
    foe_at = at + Vec(-20.0, 0, 0)
    fb = Bot(1, 0, make_profile("top", "rusher", random.Random(3)), bg, random.Random(3))
    fb.can_pickup = False
    t, yaw, pitch, fires, ticks = 0.0, math.pi, 0.0, 0, 0
    while t < 4.0:
        me = PlayerState(1, 0, "panda", at, yaw=yaw, pitch=pitch, alive=True, weapon="focus_rifle", weapons=["focus_rifle"])
        foe = PlayerState(2, 1, "human", foe_at, alive=True)
        a = fb.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        if t > 1.5:
            ticks, fires = ticks + 1, fires + bool(a.fire)
        t += 1 / 30
    if fires / max(ticks, 1) < 0.9:
        fails.append(f"the focus rifle at 20 u: trigger down {fires / max(ticks, 1):.0%} of the time (want 90%+, held)")

    # 5. no swapping back for its own dropped gun
    sb = bot(7)
    spot = Vec(-132.7, -355.84, -59.29)
    me = PlayerState(1, 0, "moose", spot, weapon="assault_rifle", weapons=["assault_rifle", "magnum"], ammo=[60, 12])
    snap = Snapshot(33.7, [me], mode="invasion", inv_phase=1, inv_attackers=0,
                    ground_weapons=[("needle_rifle", spot + Vec(0.3, 0.1, 0))])
    first = sb.upgrade_point(me, snap)
    # (live: the gun it took read "unknown" in its hands, worth nothing, so its own dropped magnum was the next upgrade)
    me = PlayerState(1, 0, "moose", spot, weapon="unknown", weapons=["assault_rifle", "unknown"], ammo=[60, 20])
    snap = Snapshot(33.9, [me], mode="invasion", inv_phase=1, inv_attackers=0,
                    ground_weapons=[("magnum", spot + Vec(-0.2, 0.2, 0))])
    again = sb.upgrade_point(me, snap)
    if first is None or again is not None:
        fails.append(f"swap at its feet: first {first}, then its own dropped magnum {again} (want the needle rifle, then "
                     f"nothing)")

    # 6. its own grenade
    gb = bot(9)
    me = PlayerState(1, 1, "elite", Vec(-150.0, -360.0, -56.0))
    a = Action(yaw=0.0, forward=1.0)
    a.grenade = True
    gb.att = ["aim", 5, -144.0, -360.0, ]
    gb.own_grenade(87.0, me, a)
    me = PlayerState(1, 1, "elite", Vec(-147.0, -360.0, -56.0))
    a = Action(yaw=0.0, forward=1.0)
    gb.notes = []
    gb.own_grenade(87.6, me, a)
    if a.forward >= 0.0 or not any("own" in str(n) for n in gb.notes):
        fails.append(f"3 u from the spot it threw at, stepping in: forward {a.forward:.2f}, notes {gb.notes} (want turned "
                     f"away)")
    a = Action(yaw=0.0, forward=1.0)
    gb.own_grenade(91.0, me, a)
    if a.forward != 1.0:
        fails.append(f"4 s after the throw: forward {a.forward:.2f} (want free again)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("spire flags 2 OK (cannons by time aloft, rides from their triggers; a Falcon climbs over the top before setting"
          " down; the focus rifle held; no swap back; its own grenade kept clear of)")


if __name__ == "__main__":
    main()
