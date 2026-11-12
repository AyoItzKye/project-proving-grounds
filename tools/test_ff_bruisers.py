"""Firefight melee bruisers (Bot.ff_kite, FF_KITE; the player's ask, Nov 12: keep distance from the Hunter, pick off the
Grunts, juke its wild attacks, get behind it and shoot its back):

1. a Hunter facing us 6 u off: the step backs off from it (the move points away)
2. a Hunter with its back to us 10 u off: Legendary rounds to its back; Easy does not
3. a Grunt and a Hunter both 8 u off: the Hunter facing us ranks under its back-turned self, and its back-turned self
   over the Grunt
4. switch off: no change to the step

usage: python -I test_ff_bruisers.py      -> "firefight bruisers OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.bot as BB  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_construct")
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


me = PlayerState(1, 0, "bot", Vec(0.0, 0.0, 0.0))


def hunter(at, facing_me):
    yaw = math.atan2(-at.y, -at.x) if facing_me else math.atan2(at.y, at.x)
    return PlayerState(50, 1, "ai", at, yaw=yaw, rank="hunter_major")


def step(tier, h):
    b = Bot(1, 0, make_profile(tier, "flanker", random.Random(1)), M, random.Random(1))
    b.order, b.notes = Order("free", None), []
    act = Action(yaw=0.0, forward=1.0)
    b.ff_kite(10.0, me, Snapshot(10.0, [me, h], mode="firefight"), act)
    w = act.yaw + math.atan2(act.strafe, act.forward)
    return Vec(math.cos(w), math.sin(w), 0.0), b.notes


h = hunter(Vec(6.0, 0.0, 0.0), True)
mv, notes = step("top", h)
check("1. facing us 6 u off: backs off", mv.x < -0.3, (mv, notes))
h = hunter(Vec(10.0, 0.0, 0.0), False)
mv, notes = step("top", h)
behind = Vec(14.0, 0.0, 0.0)
check("2. its back to us: Legendary rounds to its back", mv.x > 0.5, (mv, notes))
mv, notes = step("novice", h)
check("2. Easy: no flank", not notes, notes)


def threat(e):
    b = Bot(1, 0, make_profile("top", "flanker", random.Random(1)), M, random.Random(1))
    b.per.beliefs = {e.id: Belief(e.pos, Vec(0, 0, 0), 10.0, True, "eyes")}
    return b.threat(10.0, me, Snapshot(10.0, [me, e], mode="firefight"), e.id)


front, back = threat(hunter(Vec(8.0, 0.0, 0.0), True)), threat(hunter(Vec(8.0, 0.0, 0.0), False))
grunt = threat(PlayerState(51, 1, "ai", Vec(8.0, 0.0, 0.0), yaw=math.pi, rank="grunt_minor"))
check("3. the Hunter facing us ranks under its back-turned self", front < back, (front, back))
check("3. its back is the shot over a Grunt", back > grunt, (back, grunt))
BB.FF_KITE = False
mv, notes = step("top", hunter(Vec(6.0, 0.0, 0.0), True))
BB.FF_KITE = True
check("4. switch off: the step as it was", abs(mv.x - 1.0) < 1e-6, mv)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("firefight bruisers OK")
