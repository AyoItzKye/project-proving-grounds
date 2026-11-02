"""Taking a loose Invasion core (the player's Spire game: it lay on the ground 176 s after it fell and no attacker came
within 4.6 u of it, their runners fighting, taking guns and handing the run to the guards round it;, "Red team overall
still fucking uncoordinated"; the sim with it dropped where it fell: 0 pickups in 8 x 150 s, the run changing hands
14-27 times):

1. the whole attacking team runs for it (the director's slots), not two runners and guards round it
2. a runner keeps to its line to the core: a fight or a gun 20 u off it loses weight, the core gains it
3. near it and contested, a runner with one teammate by it waits for a second; with two they go in together; with the
   core clear one teammate is enough

usage: python -I test_loose_core.py      -> "loose core OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("reach_35_island")
CORE = Vec(-177.69, -420.52, -61.0)                    # where it lay, live
DELIVER = Vec(-163.05, -432.09, -58.37)


def bot(i, team=1):
    b = Bot(i, team, make_profile("top", "objector", random.Random(i)), M, rng=random.Random(i))
    b.notes = []
    return b


def snap(players, t=50.0):
    return Snapshot(t, players, mode="invasion", inv_phase=3, inv_attackers=1, inv_core=CORE, inv_core_carrier=None,
                    inv_delivery=DELIVER, inv_zones=[CORE])


def main():
    fails = []
    # 1
    att = [PlayerState(10 + k, 1, f"a{k}", Vec(-180.0 + k, -361.0, -54.7), is_bot=True) for k in range(7)]
    d = Director(1, M, {p.id: bot(p.id) for p in att}, random.Random(1))
    slots = d.invasion_slots(50.0, snap(att), 7)[:7]
    runners = sum(1 for r, p, _ in slots if r == "runner" and (p - CORE).flat() < 0.5)
    if runners < 7:
        fails.append(f"the loose core: {runners} of 7 attackers run for it ({[r for r, p, _ in slots]})")
    # 2
    b = bot(1)
    b.order, b.grab_point = Order("runner", CORE), CORE
    me = PlayerState(1, 1, "a", CORE + Vec(0.0, 30.0, 0.0))          # 30 u off: no staging yet
    foe_at = me.pos + Vec(20.0, -5.0, 0.0)                         # a man 20 u off the line to it
    b.per.beliefs[7] = Belief(foe_at, Vec(), 50.0, True, "eyes")
    gun = me.pos + Vec(-18.0, 0.0, 0.0)
    sc = {("fight", 7): 1.9, ("item", gun): 1.5, ("objective", CORE): 0.5}
    b.keep_role(sc, me, snap([me, PlayerState(7, 0, "d", foe_at)]), [7])
    if sc[("fight", 7)] >= 1.0 or sc[("item", gun)] >= 1.0 or sc.get(("objective", CORE), 0.0) < 1.2:
        fails.append(f"a runner 30 u from the loose core, a fight and a gun 20 u off its line: {sc} (want the core first)")
    # 3
    def held(n_mates, dead=0):
        b = bot(2)
        b.order, b.grab_point = Order("runner", CORE), CORE
        me = PlayerState(2, 1, "a", CORE + Vec(0.0, 10.0, 0.0))
        mates = [PlayerState(20 + k, 1, f"m{k}", me.pos + Vec(2.0 + k, 0.0, 0.0), is_bot=True) for k in range(n_mates)]
        camper = PlayerState(7, 0, "d", CORE + Vec(1.0, 0.0, 0.0))
        dead_men = [PlayerState(30 + k, 0, f"x{k}", CORE, alive=False) for k in range(dead)]
        b.per.beliefs[7] = Belief(camper.pos, Vec(), 49.5, True, "eyes")
        sc = {("objective", CORE): 1.4}
        b.keep_role(sc, me, snap([me, camper] + mates + dead_men), [7])
        return max(sc, key=sc.get)[0] == "hold"
    for n, dead, want in ((1, 0, True), (2, 0, False), (1, 2, False)):
        if held(n, dead) != want:
            fails.append(f"10 u from the core, {n} teammate(s) by, {dead} defenders dead: "
                         f"{'waits' if not want else 'goes in'} (want it to {'wait' if want else 'go in'})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("loose core OK (the whole team runs for it, the line to it kept, a group of three goes in)")


if __name__ == "__main__":
    main()
