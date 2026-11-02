"""Boneyard Invasion respawns by the player's spawn screen names ("T1 Spartan Bulkheads; Bridge Approach the only T1
Elite; T2 Elite Middle Approach and Bulkheads; T2 Spartan Shop and Vehicle Depot"; Elites had spawned on the tier 2
side in tier 1). brain/invasion.py honor_spawn, maps/reach_70_boneyard/inv_spawns.json "named":

1. phase 1: every Elite (attacker) respawn is Bridge Approach's (west, x under 235), every Spartan's Bulkheads'
2. phase 2: Elites at Middle Approach or Bulkheads (x 250-275), Spartans at Shop or Vehicle Depot (x over 300)

usage: python -I test_boneyard_spawns.py      -> "boneyard spawns OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import PlayerState, Vec  # noqa: E402
from brain.invasion import honor_spawn, honor_spawns  # noqa: E402


class NoMates:
    """A terrain stub: nobody is clear to spawn on (named spawns only)."""

    def los(self, a, b):
        return True

    def ground_ok(self, *a, **k):
        return False


def main():
    fails = []
    spawns = honor_spawns("reach_70_boneyard")
    if spawns is None:
        print("FAIL\nno named spawns for Boneyard")
        raise SystemExit(1)
    rng = random.Random(1)
    want = {(1, "att"): ({"Bridge Approach"}, lambda p: p.x < 235.0), (1, "def"): ({"Bulkheads"}, lambda p: 255 < p.x < 270),
            (2, "att"): ({"Middle Approach", "Bulkheads"}, lambda p: 250 < p.x < 275),
            (2, "def"): ({"Shop", "Vehicle Depot"}, lambda p: p.x > 300)}
    for (phase, side), (names, where) in want.items():
        me = PlayerState(5, 1 if side == "att" else 0, "b", Vec(0.0, 0.0, 0.0), alive=False)
        got = [honor_spawn(spawns, phase, side, me, [me], rng, NoMates()) for _ in range(40)]
        bad = [(g["name"], round(g["pos"].x)) for g in got if g is None or g["name"] not in names or not where(g["pos"])]
        if bad or not got:
            fails.append(f"phase {phase} {side}: {sorted(set(bad))[:5]} (want only {sorted(names)})")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("boneyard spawns OK (each side's spawn screen names, per phase)")


if __name__ == "__main__":
    main()
