"""On an urgent objective the man who just shot a bot is fought off its way only within HIT_BACK_R (Bot.keep_role):

1. Invasion phase 2, a defender sent at a territory being taken (hunter), 40 u from it: hit by a man 120 u off (a
   DMR across the map, in sight), the fight loses to the territory; hit by one 12 u off, the fight is kept
2. the same for an attacker taking a territory (pressing), the shooter 120 u vs 12 u off
3. a CTF defender (not urgent) still turns on whoever just shot it, near or far (unchanged)

usage: python -I test_hit_back.py      -> "hit back OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import bot as B  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_riverworld")
ME, FOE = 1, 20


def scores_after(order, mode, team, shooter_off, **snapkw):
    b = Bot(ME, team, make_profile("top", "objector", random.Random(1)), M, random.Random(1))
    b.posture, b.notes, b.order = 0.5, [], order
    pos = Vec(80.0, -100.0, 5.0)
    foe = pos + shooter_off
    b.per.beliefs[FOE] = Belief(foe, Vec(), 10.0, True, "eyes")
    b.per.last_seen[FOE] = 10.0
    b.per.attacker_id, b.per.attacker_t = FOE, 9.5
    me = PlayerState(ME, team, "me", pos)
    snap = Snapshot(10.0, [me, PlayerState(FOE, 1 - team, "foe", foe)], snapkw.pop("flags", {}), mode=mode, **snapkw)
    scores = {("fight", FOE): 2.0, ("objective", order.point): 1.0}
    b.keep_role(scores, me, snap, {FOE})
    return scores[("fight", FOE)]


def main():
    fails = []
    zone = Vec(80.0, -140.0, 5.0)
    inv = dict(inv_phase=2, inv_zones=[zone], inv_zone_r=[4.0])
    for label, order, team, kw in (
            ("defender sent at a territory", Order("hunter", zone), 0, dict(inv_attackers=1, **inv)),
            ("attacker taking a territory", Order("defender", zone), 1, dict(inv_attackers=1, **inv))):
        far = scores_after(order, "invasion", team, Vec(0.0, 120.0, 0.0), **kw)
        near = scores_after(order, "invasion", team, Vec(0.0, 12.0, 0.0), **kw)
        if not far < 1.0:
            fails.append(f"{label}: shot from 120 u, the fight kept {far:.2f} over the objective's 1.0")
        if near != 2.0:
            fails.append(f"{label}: shot from 12 u, the fight cut to {near:.2f}")
    home = M["flags"][0]
    ctf = dict(flags={0: FlagState(0, home, home), 1: FlagState(1, M["flags"][1], M["flags"][1])})
    far = scores_after(Order("defender", home), "ctf", 0, Vec(0.0, 120.0, 0.0), **ctf)
    if far != 2.0:
        fails.append(f"CTF defender shot from 120 u: the fight cut to {far:.2f} (no urgent objective, unchanged)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"hit back OK (urgent: a shooter past {B.HIT_BACK_R:.0f} u loses to the objective, a near one is fought; "
          "CTF unchanged)")


if __name__ == "__main__":
    main()
