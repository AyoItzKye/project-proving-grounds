"""Grenades into the objective (the player throws 2.37 a minute, Legendary 0.56 on Spire Invasion): a short simulated
Spire Invasion (brain/sim.py, fixed seed) where bots on their way to a territory throw at men believed there
("grenade: into the objective"), at least once in its first 30 s.

usage: python -I test_objective_nades.py      -> "objective nades OK"
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.sim import Sim  # noqa: E402


def close_opener():
    """A Grenadier meeting a man 5 u off opens with a grenade (live Spire: 62% of the bots' fight time was under 6
    u, where no opener or pressure grenade was allowed; 1.16 presses a minute to the player's 2.37)."""
    import random
    from brain.bot import Belief, Bot
    from brain.core import PlayerState, Snapshot, Vec
    from brain.maps import get_map
    from brain.profiles import make_profile
    b = Bot(1, 1, make_profile("top", "spammer", random.Random(1)), get_map("reach_35_island"), random.Random(1))
    me, foe = Vec(-176.2, -402.9, -24.1), Vec(-171.2, -402.9, -24.1)
    thrown = False
    for k in range(30):
        t = 50.0 + k / 30
        b.per.beliefs[7] = Belief(foe, Vec(), t, True, "eyes")
        b.per.recognized.add(7)
        sn = Snapshot(t, [PlayerState(1, 1, "g", me), PlayerState(7, 0, "x", foe)], mode="slayer")
        thrown |= bool(b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, []).grenade)
    return thrown


def main():
    if not close_opener():
        sys.exit("FAIL\na Grenadier meeting a man 5 u off: no grenade in its first second")
    sim = Sim("invasion", per_team=6, seed=4, map_name="reach_35_island")
    out = io.StringIO()
    sim.run(30, trace=out)
    n = sum("into the objective" in line for line in out.getvalue().splitlines())
    if n < 1:
        sys.exit(f"FAIL\nno grenade into the objective in 30 s of Spire Invasion (seed 4)")
    print(f"objective nades OK ({n} in 30 s)")


if __name__ == "__main__":
    main()
