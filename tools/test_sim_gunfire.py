"""The sim's players carry their gun's magazine (brain/sim.py Sim.gun_fired, SIM_GUNFIRE), as live games show every
player's: a shot takes a round, so another bot's Perception.fired hears it. Before, nobody in the sim ever heard a shot
(no magazine to go down): hearing gunfire (Bot aware) was dead in every sim.

1. a shot is heard by an enemy bot's Perception; no shot, nothing heard
2. the rounds left stay unknown (ammo -1): no reload, never dry, as before
3. switch off: never heard

usage: python -I test_sim_gunfire.py      -> "sim gunfire OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.sim as S  # noqa: E402
from brain.bot import Bot  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def heard(on):
    S.SIM_GUNFIRE = on
    s = S.Sim("slayer", per_team=1, seed=1, map_name="h3_guardian")
    a, b = s.players
    per = s.bots[b.id].per
    first = per.fired(a)                     # (the first look only records his magazine)
    quiet = per.fired(a)
    s.shoot(a)
    loud = per.fired(a)
    return first, quiet, loud, a


first, quiet, loud, a = heard(True)
check("1. a shot is heard", loud is True, loud)
check("1. no shot: nothing heard", quiet is False and first is False, (first, quiet))
check("2. rounds left unknown: never dry", a.ammo == [-1] and not Bot.dry(a), a.ammo)
check("3. switch off: never heard", heard(False)[2] is False)
S.SIM_GUNFIRE = True
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("sim gunfire OK")
