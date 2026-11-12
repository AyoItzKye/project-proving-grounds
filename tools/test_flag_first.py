"""CTF: a runner within RUN_GRAB_R of their flag on its stand takes it before anything else (Bot.flag_first, RUN_GRAB).
Live High Ground Multi Flag, Nov 12: within 15 u of their flag at home the runners chose it in 3% of their decisions
(fights 66%, boarding the base turret 18%); with it, 17% and the match's first capture.

1. a runner 8 u from their flag at home with a teammate beside it, a fight scored 3.2: the flag scores over it
2. a man of theirs at arm's length (2 u): the fight stays first; alone with a guard in view: the fight first too
   (grab_ok: a carrier cannot shoot back, test_ctf_grab 3b)
3. their flag carried, or 20 u off, or a defender, or Slayer, or switched off: scores as they were
4. the stage's wait this tick (staged_at): left to the wait

usage: python -I test_flag_first.py      -> "flag first OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.bot as BB  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_deadlock")
FLAG = M["flags"][1]
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def run(off=8.0, foe_off=10.0, state="home", role="runner", mode="ctf", staged=False, mate=True):
    b = Bot(1, 0, make_profile("average", "rusher", random.Random(1)), M, random.Random(1))
    b.order = Order(role, FLAG)
    me = PlayerState(1, 0, "b1", FLAG + Vec(off, 0.0, 0.0))
    foe = PlayerState(7, 1, "foe", me.pos + Vec(0.0, foe_off, 0.0))
    b.per.beliefs[7] = Belief(foe.pos, Vec(), 5.0, True, "eyes")
    mates = [PlayerState(2, 0, "b2", me.pos + Vec(1.5, 0.0, 0.0))] if mate else []
    snap = Snapshot(5.0, [me, foe] + mates, flags={1: FlagState(1, FLAG, FLAG, state)}, mode=mode)
    if staged:
        b.staged_at = snap.time
    sc = {("fight", 7): 3.2, ("objective", FLAG): 1.86, ("board", Vec(0, 0, 0)): 2.0}
    b.flag_first(me, snap, sc, [7])
    return sc[("objective", FLAG)] > sc[("fight", 7)], sc[("objective", FLAG)]


check("1. 8 u from their flag at home: the flag first", run()[0], run())
check("2. a man at arm's length: the fight first", not run(foe_off=2.0)[0])
check("2. alone, a guard in view by the flag: the fight first", not run(mate=False, foe_off=6.0)[0])
check("3. their flag carried: as it was", run(state="carried")[1] == 1.86)
check("3. 20 u off: as it was", run(off=20.0)[1] == 1.86)
check("3. a defender: as it was", run(role="defender")[1] == 1.86)
check("3. Slayer: as it was", run(mode="slayer")[1] == 1.86)
BB.RUN_GRAB = False
check("3. switch off: as it was", run()[1] == 1.86)
BB.RUN_GRAB = True
check("4. the stage's wait this tick: as it was", run(staged=True)[1] == 1.86)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("flag first OK")
