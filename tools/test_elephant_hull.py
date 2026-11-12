"""The player's Sandtrap CTF, Nov 12 (live 20261112-162033): "they keep trying to shoot enemies through the elephant
despite having no line of sight" (47% of the bots' trigger ticks at a man went through an Elephant's hull) and "they get
conflicted between grabbing the enemy flag and getting in vehicles that are waiting for them to grab it" (the player's
Warthog by their flag called the runners in by its horn, the next role pass sent them back, every 1-2 s for 25 s).

1. vehicles.hull_blocks: a line through an Elephant's side is blocked; along its bay front to back, over its walls, or
   past it, open; the Elephant one of them rides is left out; switched off: open
2. Bot.line_clear: a man behind an Elephant is not shot at (the round's line), one in the open is
3. Perception: a man behind an Elephant is not seen (no clear-line stamp); in the open he is
4. Director.honk_orders / the crew jobs (PULL_FIRST): their flag on its stand, a runner 6 u from it is not called into
   a teammate's honking Warthog; a bot farther off is; once our bot holds the flag, he is called first

usage: python -I test_elephant_hull.py      -> "elephant hull OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.director as BD  # noqa: E402
from brain import vehicles  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.match import Posture  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


# an Elephant at the origin facing +x (its frame: f along x, l along y), z 0
EL = dict(handle=77, kind="behemoth", pos=(0.0, 0.0, 0.0), fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), occupied=False, team=1)
V = [EL]
check("1. through its side (left to right, chest height)", vehicles.hull_blocks(V, Vec(0, 8, 0.6), Vec(0, -8, 0.4)))
check("1. along its bay, rear to front, at the bay floor's height", not vehicles.hull_blocks(V, Vec(-8, 0, 1.1), Vec(8, 0, 1.1)))
check("1. over its walls", not vehicles.hull_blocks(V, Vec(0, 8, 3.5), Vec(0, -8, 3.5)))
check("1. past it, 4 u aside", not vehicles.hull_blocks(V, Vec(-8, 4, 0.6), Vec(8, 4, 0.6)))
check("1. the Elephant one rides: left out", not vehicles.hull_blocks(V, Vec(0, 8, 0.6), Vec(0, -8, 0.4), skip=(77,)))
vehicles.ELEPHANT_SOLID = False
check("1. switched off: open", not vehicles.hull_blocks(V, Vec(0, 8, 0.6), Vec(0, -8, 0.4)))
vehicles.ELEPHANT_SOLID = True

# 2-3. a bot 8 u off its left side, a man 8 u off its right side (behind it) or 8 u ahead of its front corner (open)
M = get_map("h3_shrine")
for where, foe_at, want in (("behind the Elephant", Vec(0, -8, 0), False), ("in the open", Vec(9, 8, 0), True)):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    me = PlayerState(1, 0, "b", Vec(0, 8, 0), yaw=-math.pi / 2 if not want else 0.0, alive=True, weapon="assault_rifle")
    foe = PlayerState(7, 1, "foe", foe_at, alive=True)
    snap = Snapshot(5.0, [me, foe], mode="ctf", vehicles=V)
    b.per.recognized.add(7)
    b.per.beliefs[7] = Belief(foe.pos, Vec(), 5.0, True, "eyes")
    b.per.clear_at[7] = 5.0
    b.notes = []
    got = b.line_clear(5.0, me, 7, snap)
    check(f"2. a man {where}: shot at {want}", bool(got) == want, got)
    b.per.clear_at.pop(7, None)
    me.yaw = math.atan2(foe.pos.y - me.pos.y, foe.pos.x - me.pos.x)
    b.per.update(5.0, me, snap, lambda p, q: True, [])
    check(f"3. a man {where}: seen (a clear line) {want}", (7 in b.per.clear_at) == want, b.per.clear_at)

# 4. the horn by their flag
ctf = get_map("h3_shrine")
red, blue = ctf["flags"][0], ctf["flags"][1]


def honk(runner_off, state="home", holder=False):
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), ctf, random.Random(i)) for i in (1, 2)}
    d = BD.Director(0, ctf, bots, random.Random(0))
    d.posture = Posture(0.5, "even")
    hog_at = blue + Vec(5.0, 0.0, 0.0)
    me1 = PlayerState(1, 0, "runner", blue + Vec(runner_off, 1.0, 0.0), alive=True, has_flag=holder)
    me2 = PlayerState(2, 0, "far", blue + Vec(14.0, 9.0, 0.0), alive=True)
    person = PlayerState(0, 0, "person", hog_at, alive=True, vehicle=900)
    hog = dict(handle=900, kind="warthog", pos=(hog_at.x, hog_at.y, hog_at.z), riders=1, occupied=True, team=0,
               fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0))
    flags = {0: FlagState(0, red, red, "home"),
             1: FlagState(1, blue, me1.pos if holder else blue, "carried" if holder else state, 1 if holder else None)}
    snap = Snapshot(30.0, [person, me1, me2], flags, mode="ctf", vehicles=[hog])
    snap.honks = [900]
    d.roles = {1: "runner", 2: "mid"}
    for b in bots.values():
        b.order = Order(d.roles[b.id], blue)
    d.honk_orders(30.0, snap, list(bots.values()), {1: me1, 2: me2})
    return bots[1].order.role, bots[2].order.role


r1, r2 = honk(6.0)
check("4. a runner 6 u from their flag on its stand: not called into the Warthog", r1 == "runner", (r1, r2))
check("4. a bot of ours farther off: called in", r2 in ("ride", "board"), (r1, r2))
r1, r2 = honk(6.0, holder=True)
check("4. our runner holding their flag: called in", r1 in ("ride", "board"), (r1, r2))
BD.PULL_FIRST = False
r1, r2 = honk(6.0)
check("4. switched off: the runner called in as before", r1 in ("ride", "board"), (r1, r2))
BD.PULL_FIRST = True
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("elephant hull OK")
