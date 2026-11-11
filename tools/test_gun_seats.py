"""Gun seats (Bot.crew_target, Bot.fire_gate), live Spire 20261110-201813:

1. a Falcon's left side gun with a man seen only on the right: no target (it fired across the Falcon at its stop: the
   view on its man on 93-95% of the side guns' firing rows, "Falcon gunners miss like crazy"); a man on its left, or
   straight behind (its half reaches front to back): him
2. a Warthog chaingun spraying where a man just went (spin) with open air to that spot: the fire gate lets it fire
   (it held every round: 39% of the seat's time spinning, firing on 1%); with a wall in between, no

usage: python -I test_gun_seats.py      -> "gun seats OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_riverworld")
T = terrain(M)


def bot():
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b._terrain, b.notes, b.seat = T, [], "gunner"
    return b


def main():
    fails = []
    at = Vec(80.0, -100.0, 10.0)
    falcon = dict(handle=5, kind="falcon", pos=(at.x, at.y, at.z), fwd=(1.0, 0.0, 0.0), riders=2, occupied=True)
    me = PlayerState(1, 0, "g", at, vehicle=5, gunner_seat=True, turret="falcon_side_gun_left")
    for label, off, want in (("on its right", Vec(0.0, -15.0, 0.0), None), ("on its left", Vec(0.0, 15.0, 0.0), 2),
                             ("straight behind", Vec(-15.0, 0.0, 0.0), 2)):
        b = bot()
        b.per.beliefs[2] = Belief(at + off, Vec(), 10.0, True, "eyes")
        got = b.crew_target(me, Snapshot(10.0, [me, PlayerState(2, 1, "x", at + off)]), falcon, {2}, own=True)
        if got != want:
            fails.append(f"1. a left side gun, the man {label}: target {got}, want {want}")
    # 2. the spin's spray: a clear line, then one through a wall (a spot under the map's floor)
    base = M["flags"][0]
    me = PlayerState(1, 0, "g", Vec(base.x, base.y, base.z + 1.0), vehicle=6, gunner_seat=True, turret="warthog_chaingun")
    for label, spot, want in (("open air", Vec(base.x + 3.0, base.y, base.z + 1.0), True),
                              ("a wall between", Vec(base.x + 3.0, base.y, base.z - 30.0), False)):
        b = bot()
        b.att, b.spin_at = ["spin", 2, round(spot.x, 1), round(spot.y, 1)], spot
        act = Action()
        act.fire = True
        b.fire_gate(10.0, me, act, Snapshot(10.0, [me]))
        if act.fire != want:
            fails.append(f"2. the chaingun spraying where he went through {label}: fire {act.fire}, want {want}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("gun seats OK (a side gun shoots its own half only; the chaingun sprays where he went through open air)")


if __name__ == "__main__":
    main()
