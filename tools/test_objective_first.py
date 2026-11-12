"""An objective job first (Bot.objective_first, OBJ_FIRST; the player, Nov 12: "go grab this DMR even though you are right
next to the objective"). A CTF defender at its post (Sandtrap):

1. a gun 10 u off the post, the other way: weighed down to OBJ_ITEM_K
2. a gun on its way back to the post (detour under OBJ_DETOUR): left as it was
3. out of ammo: every gun left as it was
4. Slayer (no objective): left as it was
5. switch off: left as it was
6. away from the job (over OBJ_NEAR, 40 u off the post), a gun 5 u off the other way: left as it was (the player's
   Invasion rule, test_invasion_pileon 10: a better gun lying close is taken; build 20261112-0058 broke it)

usage: python -I test_objective_first.py      -> "objective first OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.bot as BB  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_shrine")
Z = -22.0
post = Vec(0.0, -40.0, Z)
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def run(gun, mode="ctf", ammo=(60,), role="defender", at=Vec(0.0, -36.0, Z)):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b.order = Order(role, post)
    me = PlayerState(1, 0, "bot", at, weapon="assault_rifle", weapons=["assault_rifle"],
                     ammo=list(ammo))
    sc = {("item", gun): 2.0, ("objective", post): 1.0}
    b.objective_first(me, Snapshot(5.0, [me], mode=mode), sc)
    return sc[("item", gun)]


away, onway = Vec(0.0, -26.0, Z), Vec(0.5, -38.0, Z)
check("1. a gun 10 u the other way: weighed down", run(away) == 2.0 * BB.OBJ_ITEM_K, run(away))
check("2. a gun on the way back to the post: left", run(onway) == 2.0, run(onway))
check("3. out of ammo: left", run(away, ammo=(0,)) == 2.0, run(away, ammo=(0,)))
check("4. Slayer: left", run(away, mode="slayer") == 2.0, run(away, mode="slayer"))
far, near_far = Vec(0.0, 0.0, Z), Vec(0.0, 5.0, Z)             # 40 u off the post, a gun 5 u the other way
check("6. 40 u from the job, a gun 5 u off: left (the Invasion rule: a better gun close by is taken)",
      run(near_far, at=far) == 2.0, run(near_far, at=far))
BB.OBJ_FIRST = False
check("5. switch off: left", run(away) == 2.0, run(away))
BB.OBJ_FIRST = True
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("objective first OK")
