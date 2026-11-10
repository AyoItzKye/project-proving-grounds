"""Objectives stay in bounds, and the sim's man cannons throw (Nov 9):

1. a map whose kill zones are read from its design data (killzones.json) learns no out of bounds spots and drops the
   ones it had (brain/oob.py Oob.learn): Narrows had two "deaths" 1.4 u from red's flag and 2.3 u from blue's, each a
   soft wall R round it, and the nav moved every runner's goal 2-4 u off the stand
2. on Narrows, with its out of bounds set as the sim and the brain set it, each flag's own floor is the nav's goal
   (Terrain._reachable_node) and a runner 3 u off it gets a way onto it
3. the sim's man cannon (Sim.cannons): a player on Narrows' red pad flies to the landing by blue's base in about the
   live 4.2 s, not steering, and lands there

usage: python -I test_flag_in_bounds.py      -> "flag in bounds OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import oob as O  # noqa: E402
from brain.core import Vec, dist  # noqa: E402
from brain.sim import Sim, TICK  # noqa: E402


def main():
    fails = []
    o = O.Oob("h3_chill")
    if o.learn or o.spots:
        fails.append(f"Narrows (killzones.json read): learn {o.learn}, spots {len(o.spots)} (want none)")
    s = Sim(mode="ctf", per_team=(1, 1), seed=1, map_name="h3_chill")
    for t in (0, 1):
        f = s.m["flags"][t]
        n = s.T._node(f)
        if s.T._reachable_node(*n, f.z) != n:
            fails.append(f"flag {t}: the nav's goal moved off its stand to {s.T._reachable_node(*n, f.z)}")
        a = Vec(f.x + 2.2, f.y + (1.6 if t == 0 else -1.6), f.z)
        w = s.T.nav(a, f)
        if w is None or dist(w, a) < 0.1:
            fails.append(f"flag {t}: a runner 2.7 u off it gets no way on ({w})")
    pads = s.cannons()
    if len(pads) != 2:
        fails.append(f"Narrows' cannons: {len(pads)} pads (want 2)")
    else:
        pad, land = min(pads, key=lambda pl: dist(pl[0], s.m["flags"][0]))
        p = s.players[0]
        p.alive, p.pos = True, pad
        s.state[p.id]["flight"] = None
        s.move(p, 0.01, 0.0)                     # (onto the pad: thrown)
        fl = s.state[p.id].get("flight")
        if fl is None:
            fails.append("onto the red pad: not thrown")
        else:
            secs = fl[3] - fl[2]
            if not 3.5 <= secs <= 5.0:
                fails.append(f"the throw takes {secs:.1f} s (live 4.2 s)")
            t0 = s.now
            while s.state[p.id].get("flight") is not None and s.now - t0 < 8.0:
                s.step()
            if dist(p.pos, land) > 1.0:
                fails.append(f"landed {dist(p.pos, land):.1f} u off the landing")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("flag in bounds OK (no learned out of bounds where kill zones are known; both Narrows flags on the nav; "
          "the cannon throws base to base)")


if __name__ == "__main__":
    main()
