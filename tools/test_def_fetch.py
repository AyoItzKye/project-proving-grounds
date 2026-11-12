"""CTF, a defender fetches our carrier (Director.defender_fetch, DEF_FETCH; the player's rule, Nov 12: if a defender has a
vehicle and the attack does not, the defender goes and brings the flag carrier back in it). Sandtrap:

1. our carrier on foot 60 u from home, nobody driving, a defender 5 u from an empty Warthog: the defender is sent to drive it
2. no vehicle near the defender: nobody sent
3. switch off: nobody sent

usage: python -I test_def_fetch.py      -> "defender fetch OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.director as DD  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_shrine")
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def run(hog_at):
    home = M["flags"][0]
    car = PlayerState(1, 0, "carrier", home + Vec(0.0, 60.0, 0.0), has_flag=True)
    dfn = PlayerState(2, 0, "defender", home + Vec(4.0, 0.0, 0.0))
    bots = {k: Bot(k, 0, make_profile("top", "flanker", random.Random(k)), M, random.Random(k)) for k in (1, 2)}
    d = Director(0, M, bots, random.Random(1))
    bots[2].order = Order("defender", home)
    bots[1].order = Order("runner", home)
    hog = dict(handle=900, kind="warthog", pos=(hog_at.x, hog_at.y, hog_at.z), occupied=False, riders=0, team=0)
    sn = Snapshot(30.0, [car, dfn], mode="ctf", vehicles=[hog])
    d.ferry_orders(30.0, sn, list(bots.values()), {1: car, 2: dfn})
    return bots[2].order


home = M["flags"][0]
o = run(home + Vec(9.0, 0.0, 0.0))
check("1. a defender 5 u from an empty Warthog is sent to drive it", o.role == "drive" and o.target == 900, o)
o = run(home + Vec(60.0, 60.0, 0.0))
check("2. no vehicle near: the defender stays", o.role == "defender", o)
DD.DEF_FETCH = False
o = run(home + Vec(9.0, 0.0, 0.0))
DD.DEF_FETCH = True
check("3. switch off: the defender stays", o.role == "defender", o)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("defender fetch OK")
