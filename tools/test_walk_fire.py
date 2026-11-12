"""The player's Sandtrap CTF, Nov 12 (live 20261112-135123): "bots still struggle with the elephant, more than half the
team isnt attacking the enemy flag ... I literally walked in front of a guys face and he did nothing".

1. Bot.walk_fire (WALK_FIRE): on its way to the objective, a gun in hand, a man in view 4 u ahead is aimed at and fired
   on, and the walk goes on the same way over the ground; a man behind it (150 degrees off the walk), carrying a flag, a
   sword in hand, in a seat, or switched off: nothing (the walk as it was)
2. Bot.blocked_way: an Elephant's middle 1 u ahead is no "vehicle" in the way (its bay and deck are walked by way_in; a
   bot on the deck was turned off it three times in 26 s); a Warthog there still is
3. Director.role_slots, CTF 8 a side, both flags home: one point ahead, the defenders stay at the player's quarter (2);
   two ahead, one more (3), and runners still go (LEAD_KEEPS_SPLIT); switched off: the lead management as it was

usage: python -I test_walk_fire.py      -> "walk fire OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.bot as BB  # noqa: E402
import brain.director as BD  # noqa: E402
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.match import Posture  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []
WALK_NOTES = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


M = get_map("h3_shrine")
T = terrain(M)
BB.WALL_SHOTS = False


def walk(foe_at, seconds=1.5, weapon="assault_rifle", has_flag=False, vehicle=-1):
    """A bot walking east (+x) at full stick; a man seen at foe_at (relative). (fired ticks, aimed ticks, world move ok)"""
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(2)), M, random.Random(2))
    b.order = Order("runner", Vec(60.0, 0.0, 0.0))
    p0 = Vec(4.0, 18.0, T.nav_z(4.0, 18.0))      # (open sand by the red base)
    fired = aimed = 0
    notes = set()
    move_ok = True
    t, yaw = 10.0, 0.0
    while t < 10.0 + seconds:
        me = PlayerState(1, 0, "b1", p0, yaw=yaw, alive=True, weapon=weapon, weapons=[weapon], has_flag=has_flag,
                         vehicle=vehicle)
        foe = PlayerState(7, 1, "foe", p0 + foe_at, alive=True)
        b.per.beliefs[7] = Belief(foe.pos, Vec(), t, True, "eyes")
        b.per.recognized.add(7)
        b.per.last_seen[7] = b.per.clear_at[7] = t      # (Perception.update: seen, a clear line)
        snap = Snapshot(t, [me, foe], mode="ctf")
        act = Action(yaw=yaw, pitch=0.0)
        act.forward, act.strafe = math.cos(yaw), -math.sin(yaw)   # (the walk east the goal's move_to gave)
        b.now, b.notes, b.att, b.vehicles_now, b.shot_now, b.planned_jump = t, [], None, (), False, False   # (think, per tick)
        b.walk_fire(t, 1 / 30, me, snap, act, lambda p, q, **k: q)
        mx = math.cos(act.yaw) * act.forward - math.sin(act.yaw) * act.strafe
        my = math.sin(act.yaw) * act.forward + math.cos(act.yaw) * act.strafe
        move_ok &= abs(mx - 1.0) < 1e-6 and abs(my) < 1e-6
        fired += bool(act.fire)
        att = getattr(b, "att", None)
        aimed += bool(att and att[0] == "aim" and att[1] == 7)
        notes.update(b.notes)
        yaw = act.yaw
        t += 1 / 30
    WALK_NOTES.append(notes)
    return fired, aimed, move_ok


f, a, ok = walk(Vec(4.0, 1.0, 0.0))
check("1. a man 4 u ahead: aimed at and fired on", f > 0 and a > 0, (f, a, WALK_NOTES[-1]))
check("1. the walk goes on east, whatever the bot faces", ok)
f, a, ok = walk(Vec(-4.0, 2.0, 0.0))
check("1. a man behind it: nothing", f == 0 and a == 0, (f, a))
f, a, ok = walk(Vec(4.0, 1.0, 0.0), has_flag=True)
check("1. carrying a flag: nothing", f == 0 and a == 0, (f, a))
f, a, ok = walk(Vec(4.0, 1.0, 0.0), weapon="sword")
check("1. a sword in hand: nothing (that is a run at him)", f == 0 and a == 0, (f, a))
f, a, ok = walk(Vec(4.0, 1.0, 0.0), vehicle=12345)
check("1. in a seat: nothing", f == 0 and a == 0, (f, a))
f, a, ok = walk(Vec(30.0, 1.0, 0.0))
check("1. an AR, a man 30 u ahead not shooting it: nothing (out of reach)", f == 0 and a == 0, (f, a))
BB.WALK_FIRE = False
f, a, ok = walk(Vec(4.0, 1.0, 0.0))
check("1. switched off: nothing", f == 0 and a == 0, (f, a))
BB.WALK_FIRE = True

# 2. the Elephant's middle ahead is not a vehicle in the way
b = Bot(1, 0, make_profile("top", "rusher", random.Random(2)), M, random.Random(2))
me = PlayerState(1, 0, "b1", Vec(0.0, 0.0, -20.0), alive=True)


class OpenT:
    def clearance(self, *a, **k):
        return 9.0


for kind, want in (("behemoth", None), ("warthog", "vehicle")):
    snap = Snapshot(5.0, [me], mode="ctf", vehicles=[dict(handle=1, kind=kind, pos=[1.0, 0.0, -21.0])])
    got = b.blocked_way(OpenT(), me, snap, 0.0)
    check(f"2. a {kind}'s middle 1 u ahead: {want}", got == want, got)

# 3. the defenders when ahead
ctf = get_map("h3_shrine")


def slots(lead, keep=True):
    BD.LEAD_KEEPS_SPLIT = keep
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), ctf, random.Random(i)) for i in range(1, 8)}
    d = BD.Director(0, ctf, bots, random.Random(0))
    d.posture = Posture(0.5, "even")
    d.posture.lead = lead
    d.split, d.split_until = False, 1e9
    red, blue = ctf["flags"][0], ctf["flags"][1]
    players = [PlayerState(i, 0, f"b{i}", red + Vec(i * 0.5, 0, 0)) for i in range(0, 8)]
    players += [PlayerState(20 + k, 1, f"e{k}", blue) for k in range(8)]
    flags = {0: FlagState(0, red, red, "home"), 1: FlagState(1, blue, blue, "home")}
    out = d.role_slots(30.0, Snapshot(30.0, players, flags, mode="ctf"), 7)[:7]
    BD.LEAD_KEEPS_SPLIT = True
    roles = [r[0] for r in out]
    return roles.count("defender"), roles.count("runner")


for lead, want in ((0, 2), (1, 2), (2, 3)):
    dfn, run = slots(lead)
    check(f"3. {lead} ahead: {want} defenders of 8, runners still go", dfn == want and run >= 1, (dfn, run))
dfn, run = slots(1, keep=False)
check("3. switched off, one ahead: the lead management as it was (3)", dfn == 3, (dfn, run))
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("walk fire OK")
