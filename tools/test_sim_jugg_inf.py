"""Juggernaut and Infection in the offline sim (brain/sim_modes.py side_start / on_kill, Sim.switch_team): they scored
nothing before (no side change in the sim: the baseline of Nov 12, 0 points in 4 x 300 s each).

1. Juggernaut, 4v4 on Construct, 120 s: one Juggernaut on team 1, the rest team 0, both sides score, his bot is in team
   1's director and nobody else's; the snapshot marks him (snap.vips)
2. Infection, 120 s: points both ways, a survivor killed by a zombie came back a zombie (zombies grew past the start),
   zombies hold swords; the snapshot says which side is infected
3. a sword does not hit past its reach (Sim.shoot, MELEE_REACH)

usage: python -I test_sim_jugg_inf.py      -> "sim juggernaut infection OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.sim import Sim  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


s = Sim("juggernaut", per_team=4, seed=1, map_name="h3_construct")
s.limit = 999
s.run(120.0)
j = s.objmodes.jugg
teams = {t: [p.id for p in s.players if p.team == t] for t in (0, 1)}
check("1. one Juggernaut, team 1 alone", teams[1] == [j], teams)
check("1. both sides score", s.score[0] > 0 and s.score[1] > 0, dict(s.score))
check("1. his bot in team 1's director only", j in s.directors[1].bots and j not in s.directors[0].bots)
check("1. the snapshot marks him", s.snapshot().vips == (j,), s.snapshot().vips)

s = Sim("infection", per_team=4, seed=2, map_name="h3_construct")
s.limit = 999
peak = 0
for _ in range(4):
    s.run(30.0)
    peak = max(peak, sum(1 for p in s.players if p.team == 1))
check("2. points both ways", s.score[0] > 0 and s.score[1] > 0, dict(s.score))
check("2. the infected grew past the first zombie", peak > 1, peak)
check("2. zombies hold swords", all(p.weapon == "sword" for p in s.players if p.team == 1 and p.alive))
check("2. the snapshot says who is infected", s.snapshot().infected == 1)

z = next(p for p in s.players if p.team == 1)
v = next(p for p in s.players if p.team == 0)
z.pos, v.pos, v.alive, z.alive = Vec(0.0, 0.0, 0.0), Vec(6.0, 0.0, 0.0), True, True
s.target_in_crosshair = lambda p: v
hits = s.stats[z.id]["hits"]
z.weapon = "sword"
s.shoot(z)
check("3. a sword misses past its reach", s.stats[z.id]["hits"] == hits)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("sim juggernaut infection OK")
