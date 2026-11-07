"""the player's flags in Spire Invasion match 094415:

1. 142 s / 441 s "warthog glitched out threw his weapon away": at a gun lying on the floor, once the swap went through
   (the hands changed) no more Use presses there and the spot is skipped (the gun put down lay on the same spot: the
   two swapped 10 times in 0.7 s)
2. 441 s "too slow with the shotgun ... too much spaced out shots in that close of range": up close the shotgun is
   pressed 0.2-0.24 s apart as the player does (the game fires as soon as it can), not 0.75+
3. 371 s: a Falcon with its pilot in calls a runner 25 u off
   (the call radius is 2.5 x for a transport aircraft); a Warthog does not, at 25 u
4. 410 s "this banshee ... used as transportation. Power vehicles ... used with a purpose": no trip in a Banshee, a
   tank or a Hornet (vehicles.taxi_ok, ride_score 0), a runner in one gets no taxi job; a Warthog and a Ghost still do
5. 519 s "Did elites even haul ass to try to stop core carrier?": they stalled at the spire's foot, a spot that could
   never be learned (Spire's learned spots were at the 300 cap, most of them cells the player stood on): a learned
   spot people stood on is refused, the stall's own spot (never stood on) is learned

usage: python -I test_flags_094415.py      -> "flags 094415 OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

M = get_map("reach_35_island")
T = terrain(M)


def main():
    testdata.need_lidar("reach_35_island")
    fails = []
    # 1. the swap goes through, then no more presses
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b.game, b._terrain = "reach", T
    gun = Vec(-112.4, -327.0, -63.2)
    pos = Vec(-112.7, -327.0, -63.2)
    b.goal, b.next_decide = ("item", gun), 1e9
    presses, after = 0, 0
    for k in range(40):
        t = k / 30
        wpns = ["assault_rifle", "needle_rifle"] if k < 20 else ["unknown", "needle_rifle"]   # (taken at 0.67 s)
        me = PlayerState(1, 0, "bot", pos, alive=True, weapon=wpns[0], weapons=wpns)
        a = b.think(t, 1 / 30, Snapshot(t, [me]), lambda p, q: True, lambda p, q, **k: q, [])
        presses += k < 20 and bool(a.action)
        after += k >= 21 and bool(a.action)
        b.goal, b.next_decide = ("item", gun), 1e9           # (held on the gun: the loop's case)
    skip = getattr(b, "rearm_skip", {}).get((round(gun.x), round(gun.y)), 0.0)
    if not presses or after or skip < 1.0:
        fails.append(f"a gun at its feet: presses before the swap {presses}, after it {after}, spot skipped until "
                     f"{skip:.1f} (want presses, then none, skipped)")
    # 2. the shotgun up close
    gaps = [b.fire_gap("shotgun", 2.0) for _ in range(20)]
    if max(gaps) > 0.25:
        fails.append(f"shotgun at 2 u: gaps up to {max(gaps):.2f} s (want 0.2-0.24, the playtest cadence)")
    # 3. a Falcon calls a runner 25 u off; a Warthog does not
    for kind, seats, want in (("falcon", 3, True), ("warthog", 3, False)):
        drv = Bot(10, 0, make_profile("top", "rusher", random.Random(2)), M, random.Random(2))
        run = Bot(11, 0, make_profile("top", "rusher", random.Random(3)), M, random.Random(3))
        d = Director(0, M, {10: drv, 11: run}, random.Random(4))
        vp = Vec(-112.7, -327.0, -63.2)
        drv.seat = "driver"
        run.set_order(Order("runner", Vec(-178.0, -405.0, -23.0)), sure=True)
        d.roles = {10: "drive", 11: "runner"}
        p_drv = PlayerState(10, 0, "drv", vp, alive=True, vehicle=99)
        p_run = PlayerState(11, 0, "run", vp + Vec(25.0, 0.0, 0.0), alive=True)
        v = dict(handle=99, kind=kind, pos=(vp.x, vp.y, vp.z), team=0, riders=1, gunner=False, occupied=True)
        snap = Snapshot(10.0, [p_drv, p_run], mode="invasion", vehicles=[v])
        d.rider_calls(10.0, snap, [drv, run], {10: p_drv, 11: p_run})
        got = run.order.role in ("ride", "board") and run.order.target == 99
        if got != want:
            fails.append(f"{kind} with its pilot in, a runner 25 u off: called {got} (want {want})")
    # 4. power vehicles are no taxi
    me = PlayerState(1, 0, "bot", Vec(0.0, 0.0, 0.0), alive=True)
    for kind, want in (("banshee", False), ("scorpion", False), ("hornet", False), ("warthog", True), ("ghost", True),
                       ("mongoose", True)):
        sc = vehicles.ride_score(dict(handle=1, kind=kind, pos=(3.0, 0.0, 0.0)), me, Vec(60.0, 0.0, 0.0), 60.0)
        ok = getattr(vehicles, "taxi_ok", lambda k: True)(kind)
        if (sc > 0) != want or ok != want:
            fails.append(f"a trip in a {kind}: score {sc:.2f}, taxi_ok {ok} (want {want})")
    # 5. learned spots: never on a cell people stood on; the stall's spot (never stood on) learned
    pw = getattr(T, "people_walked", None) or {(round(-112.7 / 0.25), round(-327.0 / 0.25), round(-63.2 / 0.1))}
    stood = next(iter(pw))
    p_stood = Vec(stood[0] * 0.25, stood[1] * 0.25, stood[2] * 0.1)
    n0 = len(T.stuck)
    T.learn_stuck(p_stood, sure=True)
    stall = Vec(-187.5, -384.0, -59.0)
    T.learn_stuck(stall, sure=True)
    keys = {(round(p.x, 1), round(p.y, 1), round(p.z, 1)) for p in (p_stood, stall)}
    if keys & set(T.stuck) != {(round(stall.x, 1), round(stall.y, 1), round(stall.z, 1))} or n0 >= T.STUCK_MAX:
        fails.append(f"learned spots: {n0} at the start (cap {T.STUCK_MAX}); a stood-on cell learned "
                     f"{(round(p_stood.x, 1), round(p_stood.y, 1), round(p_stood.z, 1)) in T.stuck}, the stall's "
                     f"{(round(stall.x, 1), round(stall.y, 1), round(stall.z, 1)) in T.stuck} (want refused, learned)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"flags 094415 OK (no presses after the swap; shotgun {min(gaps):.2f}-{max(gaps):.2f} s up close; the Falcon "
          f"calls from 25 u; no Banshee / tank / Hornet trips; Spire's learned spots {n0} under the cap, stood-on "
          f"cells refused)")


if __name__ == "__main__":
    main()
