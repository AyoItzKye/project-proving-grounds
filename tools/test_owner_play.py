"""The player's flagged games, Nov 11 (logs/tmp/play_nov11/ANALYSIS.md): bots stay on the job the way he plays it.
Bot.keep_role on scores as decide builds them, on Sandtrap (h3_shrine):

1. Oddball, five teams: a hunter sent at their ball carrier (he held it 199-0; the 12 hunters fought a third team in
   74% of their fights) with a third team's man in view 11 u off, a gun 15 u off and a Mongoose: the carrier first
   (a fight with him, or the way to him), the third team's man, the gun and the Mongoose behind it
2. a man of the third team shooting the hunter right now is still fought (on us)
3. the person's escort (his two escorts were a median 33 u off him, 18% of their time on vehicles): a vehicle 25 u off
   him loses to the way back to him
4. a ferry on foot (High Ground 141.8 s: it walked to a gun while our carrier waited): the carrier, not the gun
5. Oddball holds (he held the ball 71% of the match in one covered spot): Passive LiDAR sums where a person holds the
   ball per 2 u cell (HumanWatch.holding, Recorder.held), maps.people_holds reads spots held 10 s+, and our bot carrier
   goes to the longest-held one no enemy is on (Director.carry_point), else the old pick
6. vehicles by his rules (director.OWNER_VEHICLES): six bots free in CTF beside 3 Mongooses, 2 Warthogs, a Ghost and an
   Elephant: no crew job on a Mongoose or the Elephant, both Warthogs crewed (attack and defence), one Ghost; off: the
   Mongooses get drivers (the play before)

usage: python -I test_owner_play.py      -> "owner play OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_shrine")
Z = -22.0
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def bot(team, role, point, target=-1):
    b = Bot(1, team, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b.order = Order(role, point, target=target)
    return b


def best(scores):
    return max(scores, key=scores.get)


# 1-2. Oddball, five teams: we are team 1; team 0's man 0 carries the ball at (0, -8); team 2's bot 5 is in view
carrier = PlayerState(0, 0, "carrier", Vec(0.0, -8.0, Z), has_flag=True, is_bot=False)
me = PlayerState(1, 1, "hunter", Vec(0.0, -30.0, Z))
third = PlayerState(5, 2, "third", Vec(10.0, -35.0, Z))
others = [PlayerState(20 + k, 3 + k % 2, f"x{k}", Vec(60.0 + k, 40.0, Z)) for k in range(2)]
gun, mongoose = Vec(15.0, -30.0, Z), dict(handle=777, kind="mongoose", pos=(-12.0, -32.0, Z), occupied=False)
snap = Snapshot(50.0, [carrier, me, third] + others, mode="oddball", vehicles=[mongoose])
snap.ball, snap.ball_carrier = carrier.pos, 0
b = bot(1, "hunter", carrier.pos)
b.per.beliefs = {0: Belief(carrier.pos, Vec(0, 0, 0), 50.0, True, "eyes"),
                 5: Belief(third.pos, Vec(0, 0, 0), 50.0, True, "eyes")}
base = {("fight", 5): 1.9, ("fight", 0): 1.7, ("item", gun): 1.3, ("vehicle", 777): 1.6,
        ("objective", carrier.pos): 1.0}
scores = dict(base)
b.keep_role(scores, me, snap, [0, 5])
top = best(scores)
check("1. the hunter goes for their carrier, not the third team, the gun or the Mongoose",
      top in (("fight", 0), ("objective", carrier.pos)) or (top[0] == "objective" and top[1] == carrier.pos), f"{top}: {scores}")
check("1. the third team's man is weighed down", scores[("fight", 5)] < 0.7 * base[("fight", 5)], scores[("fight", 5)])
b.per.attacker_id, b.per.attacker_t = 5, 49.5
scores = dict(base)
b.keep_role(scores, me, snap, [0, 5])
check("2. the third team's man shooting us now is fought", scores[("fight", 5)] == base[("fight", 5)], scores[("fight", 5)])

# 3. the person carries the ball; our escort is 22 u off him with a vehicle 25 u off him
person = PlayerState(0, 0, "person", Vec(0.0, -8.0, Z), has_flag=True, is_bot=False)
esc = PlayerState(2, 0, "escort", Vec(0.0, -30.0, Z))
snap = Snapshot(50.0, [person, esc], mode="oddball", vehicles=[mongoose])
snap.ball, snap.ball_carrier = person.pos, 0
b = bot(0, "escort", person.pos, target=0)
scores = {("vehicle", 777): 2.0, ("objective", person.pos): 1.0}
b.keep_role(scores, esc, snap, [])
check("3. the escort heads back to the person, not to the Mongoose", best(scores)[0] == "objective", scores)

# 4. a ferry on foot: our carrier 14 u off, a gun 18 u off him
carry = PlayerState(3, 0, "carrier", Vec(-18.0, -8.0, Z), has_flag=True)
ferry = PlayerState(4, 0, "ferry", Vec(-20.0, 6.0, Z))
snap = Snapshot(50.0, [carry, ferry], mode="ctf")
b = bot(0, "ferry", carry.pos, target=3)
far_gun = Vec(-28.0, 9.0, Z)
scores = {("item", far_gun): 1.5}
b.keep_role(scores, ferry, snap, [])
check("4. the ferry goes to our carrier, not to the gun", best(scores)[0] == "objective", scores)

# 5. ball holds
import json  # noqa: E402
import tempfile  # noqa: E402
sys.path.insert(0, HERE)
from lidar import HumanWatch, Recorder  # noqa: E402
from brain import maps as MP  # noqa: E402
from brain.director import Director  # noqa: E402
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "h3_shrine"))
hw = HumanWatch("_selftest", Recorder("_selftest", count_run=False, path=os.path.join(tmp, "h3_shrine", "lidar.json")))
for k in range(60):                       # 30 s holding at (0.3, -8.4), 5 s at (20, 30)
    hw.holding(k * 0.5, "oddball", (0.3, -8.4, Z))
for k in range(10):
    hw.holding(40.0 + k * 0.5, "oddball", (20.0, 30.0, Z))
hw.rec.save()
saved = json.load(open(os.path.join(tmp, "h3_shrine", "lidar.json")))["holds"]["oddball"]
check("5. holding time summed per 2 u cell and saved", abs(sum(saved.values()) - 34.5) < 0.6 and len(saved) == 2, saved)
root0 = MP.ROOT
MP.ROOT = tmp
try:
    holds = MP.people_holds(M, "oddball")
finally:
    MP.ROOT = root0
check("5. the spot held 10 s+ is a people's hold, the 5 s one not", len(holds) == 1 and abs(holds[0][0].y + 8.0) < 0.1, holds)
d = Director(0, M, {}, random.Random(0))
d._odd_people = holds
far_foes = Snapshot(50.0, [PlayerState(9, 1, "f", Vec(40.0, 40.0, Z))], mode="oddball")
check("5. our carrier goes to the people's spot", d.carry_point(far_foes) == holds[0][0], d.carry_point(far_foes))
on_it = Snapshot(50.0, [PlayerState(9, 1, "f", Vec(1.0, -7.0, Z))], mode="oddball")
check("5. an enemy on it: the old pick", d.carry_point(on_it) != holds[0][0], d.carry_point(on_it))

# 6. crew jobs
import brain.director as Dmod  # noqa: E402
kinds = ["mongoose", "mongoose", "mongoose", "warthog", "warthog", "ghost", "elephant"]
vehs = [dict(handle=100 + k, kind=kd, pos=(4.0 * k, 20.0, Z), occupied=False, team=0, riders=0, up=(0, 0, 1))
        for k, kd in enumerate(kinds)]
for owner_rules in (True, False):
    Dmod.OWNER_VEHICLES = owner_rules
    try:
        bots = {i: Bot(i, 0, make_profile("top", "rusher", random.Random(i)), M, random.Random(i)) for i in range(1, 7)}
        dd = Dmod.Director(0, M, bots, random.Random(0))
        ps = [PlayerState(i, 0, f"b{i}", Vec(4.0 * i, 24.0, Z)) for i in bots]
        sn = Snapshot(60.0, ps, mode="ctf", vehicles=vehs)
        dd.crew_orders(60.0, sn, {p.id: p for p in ps}, list(bots.values()))
        got = sorted(kinds[b.order.target - 100] for b in bots.values() if b.order.role == "drive")
    finally:
        Dmod.OWNER_VEHICLES = True
    if owner_rules:
        check("6. crews by his rules: no Mongoose or Elephant, two Warthogs, one Ghost",
              got.count("mongoose") == 0 and "elephant" not in got and got.count("warthog") == 2 and got.count("ghost") <= 1, got)
    else:
        check("6. off: the play before crews Mongooses", got.count("mongoose") >= 1, got)

if fails:
    sys.exit(f"FAIL {len(fails)}")
print("owner play OK")
