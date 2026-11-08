"""Halo 2 Classic's vehicles as a person plays them (the recorded play, Nov 7; brain/vehicles.py use_game, GAME_SEATS,
GAME_BOOST; brain/bot.py SCORPION_MG_R):

1. seats: no gunner on Halo 2's Scorpion or Wraith (the machine gun is the driver's); the Spectre's passengers ask for
   seats 1 and 2 and its gunner for the gun riding on it (seat 0, turret)
2. boosts: the Wraith's short bursts (1.0 s), the Banshee's and Spectre's holds, as recorded
3. the Scorpion driver's machine gun (fire2): on a man on foot within reach, not on one far off, not on a vehicle; and
   no machine gun outside Halo 2 (Halo 3's Scorpion gun is the gunner's)
4. the boost on the way (travel_boost) reaches Halo 2 now (fire2 is its second trigger, h2.cpp)

usage: python -I test_h2_vehicles.py      -> "h2 vehicles OK"   (its own process: use_game changes module tables)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Action, Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("bloodgulch")
T = terrain(M)
A = Vec(60.0, -100.0, T.ground(60.0, -100.0))


def scorpion_shot(game, foe_at, foe_vehicle=-1, seed=1):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(seed)), M, random.Random(seed))
    b._terrain, b.game = T, game
    b.seat_for, b.seat_since, b.seat = 5, 0.0, "driver"
    me = PlayerState(1, 0, "d", A, yaw=0.0, vehicle=5)
    foe = PlayerState(2, 1, "f", foe_at, weapon="smg", weapons=["smg"], vehicle=foe_vehicle)
    vs = [dict(handle=5, kind="scorpion", pos=(A.x, A.y, A.z), riders=1, occupied=True, fwd=(1.0, 0.0, 0.0))]
    if foe_vehicle != -1:
        vs.append(dict(handle=foe_vehicle, kind="ghost", pos=(foe_at.x, foe_at.y, foe_at.z), riders=1, occupied=True,
                       team=1, fwd=(-1.0, 0.0, 0.0)))
    fired = False
    for k in range(90):                      # 3 s: the turret comes round onto him
        t = 10.0 + k / 30
        b.per.beliefs[2] = Belief(foe_at, Vec(), t, True, "eyes")
        b.per.recognized.add(2)
        a = Action(yaw=0.0)
        b.drive(t, 1 / 30, me, Snapshot(t, [me, foe], vehicles=vs), a, lambda p, q, **kw: q)
        fired |= bool(a.fire2)
    return fired


def main():
    fails = []
    vehicles.use_game("h2")
    # 1. seats
    if "gunner" in vehicles.spec("scorpion")["seats"] or "gunner" in vehicles.spec("wraith")["seats"]:
        fails.append(f"Halo 2 Scorpion / Wraith seats {vehicles.spec('scorpion')['seats']} / "
                     f"{vehicles.spec('wraith')['seats']} (want no gunner)")
    if vehicles.reach_seat("scorpion", "gunner") is not None:
        fails.append(f"Halo 2 Scorpion gunner seat {vehicles.reach_seat('scorpion', 'gunner')} (want none)")
    sp = [vehicles.reach_seat("spectre", "passenger", k) for k in range(2)]
    if sp != [(1, False), (2, False)] or vehicles.reach_seat("spectre", "gunner") != (0, True):
        fails.append(f"Spectre passengers {sp}, gunner {vehicles.reach_seat('spectre', 'gunner')} "
                     f"(want seats 1, 2 and the gun's 0)")
    # 2. boosts
    for k, want in (("wraith", (1.0, 5.3)), ("banshee", (5.3, 4.6)), ("spectre", (16.5, 2.0))):
        if vehicles.TRAVEL_BOOST.get(k) != want:
            fails.append(f"Halo 2 {k} boost {vehicles.TRAVEL_BOOST.get(k)} (want {want})")
    if "spectre" not in vehicles.BOOSTS:
        fails.append("the Spectre is not a booster")
    # 3. the Scorpion's machine gun
    if not scorpion_shot("h2", A + Vec(10.0, 0.0, 0.0)):
        fails.append("Halo 2 Scorpion, a man on foot 10 u ahead: no machine gun")
    if scorpion_shot("h2", A + Vec(40.0, 0.0, 0.0)):
        fails.append("Halo 2 Scorpion, a man 40 u off: machine gun (want only the shell out there)")
    if scorpion_shot("h2", A + Vec(10.0, 0.0, 0.0), foe_vehicle=9):
        fails.append("Halo 2 Scorpion, a Ghost 10 u ahead: machine gun (want the shell for a vehicle)")
    if scorpion_shot("h3", A + Vec(10.0, 0.0, 0.0)):
        fails.append("Halo 3 Scorpion driver fired a machine gun (its gun is the gunner's)")
    # 4. the boost on the way
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(7)), M, random.Random(7))
    b._terrain, b.game = T, "h2"
    # (north from A is open for a boost's length on Blood Gulch; east rises 7.8 u on)
    v = dict(handle=5, kind="ghost", pos=(A.x, A.y, A.z), riders=1, occupied=True, fwd=(0.0, 1.0, 0.0))
    me = PlayerState(1, 0, "d", A, yaw=math.pi / 2, vehicle=5)
    a = Action(yaw=math.pi / 2)
    b.travel_boost(10.0, me, v, a, False)
    if not a.fire2:
        fails.append("Halo 2 Ghost on an open straight: no boost on the way")
    # 5. a vehicle that puts its rider out at once with no Use of his (a Ghost on its side) is left alone (put_out)
    for since, used, want in ((10.0, None, True), (10.0, 10.3, False), (5.0, None, False)):
        p = Bot(1, 0, make_profile("top", "rusher", random.Random(8)), M, random.Random(8))
        p.seat_for, p.seat_since = 77, since
        p.duds().clear()                     # (shared by every bot on the map)
        if used is not None:
            p.seat_use_t = used
        p.put_out(10.5)
        if (77 in p.duds()) != want:
            fails.append(f"put out 10.5 s after getting in at {since} (Use at {used}): dud {77 in p.duds()} "
                         f"(want {want})")
    if fails:
        print("FAIL\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("h2 vehicles OK")


if __name__ == "__main__":
    main()
