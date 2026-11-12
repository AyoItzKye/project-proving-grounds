"""The player's three flagged games of Nov 11 evening (Shrine and Narrows CTF, Zanzibar Oddball; logs/tmp/play_nov11b):

1. Oddball, two teams, the person holds the ball (he held it 136-0; his hunters' objective scored 0.7-1.1 under guns at
   1.6-2.05 and fights with his teammates at 3): the hunter's live point is the carrier, its objective scores as a flag
   return over a gun 10 u off it; his teammate in view 10 u off the hunter is still fought (ODD_FIGHT_SEEN: the sims'
   hunters walked past his guards without); switch off: the gun (as before)
2. the loose ball in a two-team lobby: no leash (the sims' pickups, 228 -> 178 with one)
3. our person carries the ball, a "mid" watcher 30 u off him with a gun 8 u off it: back to its overlook by him
4. shots (Narrows): a man whose chest has no round's line but his head has: no shot this tick, the aim goes to his
   head (head_only), the next tick fires; both blocked (as the learned spots let through): no shot; clear: shot
5. learning a shoot-through spot (Bot.corner_hit): a hit where a line ran between the two 0.3 s before is a corner,
   not learned; blocked all along: learned; too short a trail: not
6. the speedometer (Bot.move_watch): running free, then pushing on 0.8 s going nowhere marks the way blocked, and the
   next step into it slides along the face; running free marks nothing; in a fight a strafe into it goes the other way;
   a body that never moved (a test world holding it still) is not judged
7. a gunner's trigger (Bot.gun_seat_trigger): down 0.6 u off a man 12 u away, held 1.2 u off, held through a 0.2 s
   swing off him, let go after 0.5 s; the mounted gun's aim error is half the hand's (steady)
8. the learned shoot-through file is shots_learned.json; the old walls_learned.json is not read
9. Oddball, the loose ball (Triplicate, Nov 11 late: a bot 2.4 u off it chose a gun 2.6 over it 1.84): 2.4 u off it,
   with a gun 2.6 and a fight 3.2 with a man 10 u off, the ball first; a man of theirs at arm's length: him first; a
   teammate nearer and the ball 8 u off: left to him; switch off: the gun
10. Oddball, eight teams, a hunter on their carrier: a third team's man in view 6 u off (a committed fight 3.2) and a
    gun 3 u off us far from the carrier lose to the carrier; a third team's man at 2 u is still fought
11. Oddball, a bot carrier's escort 20 u off him: a third team's man 6 u off the escort (a committed fight) loses to
    the way back

usage: python -I test_owner_flags_nov11b.py      -> "owner flags nov11b OK"
"""
import json
import math
import os
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.bot as BB  # noqa: E402
import brain.maps as MP  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def bot(m, team, role, point, target=-1, pid=1):
    b = Bot(pid, team, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    b.order = Order(role, point, target=target)
    b.notes = []
    return b


def best(scores):
    return max(scores, key=scores.get)


# 1-2. Oddball on Sandtrap, two teams: the person (team 0) carries the ball at (0, -8); we hunt for team 1
M = get_map("h3_shrine")
Z = -22.0
person = PlayerState(0, 0, "person", Vec(0.0, -8.0, Z), has_flag=True, is_bot=False)
mate = PlayerState(3, 0, "mate", Vec(0.0, -40.0, Z))
me = PlayerState(1, 1, "hunter", Vec(0.0, -30.0, Z))
gun = Vec(10.0, -30.0, Z)
snap = Snapshot(50.0, [person, mate, me], mode="oddball")
snap.ball, snap.ball_carrier = person.pos, 0


def hunt(leash):
    BB.OWNER_LEASH = leash
    try:
        b = bot(M, 1, "hunter", person.pos)
        b.per.beliefs = {3: Belief(mate.pos, Vec(0, 0, 0), 50.0, True, "eyes")}
        live = b.live_point(me, snap)
        pt = live or b.objective_point(me)
        obj = 1.3 + 0.6 * b.p.teamwork if live is not None else 0.5 + 0.7 * b.p.objective   # (decide's two scores)
        scores = {("item", gun): 2.05, ("fight", 3): 1.9, ("objective", pt): obj}
        b.keep_role(scores, me, snap, [3])
        return live, scores
    finally:
        BB.OWNER_LEASH = True


live, scores = hunt(True)
check("1. the hunter's live point is their carrier", live is not None and (live - person.pos).flat() < 0.01, live)
check("1. their carrier beats the gun", scores[("objective", live)] > scores[("item", gun)], scores)
check("1. his teammate in view 10 u off us is still fought (a person shoots who is in front of him)",
      scores[("fight", 3)] == 1.9, scores)
live0, scores0 = hunt(False)
check("1. switch off: the gun, as before", best(scores0) == ("item", gun), scores0)
loose = Snapshot(50.0, [mate, me], mode="oddball")
loose.ball, loose.ball_carrier = Vec(0.0, -8.0, Z), None
b = bot(M, 1, "hunter", loose.ball)
scores = {("item", gun): 2.05, ("objective", loose.ball): 1.0}
b.keep_role(scores, me, loose, [])
check("2. the loose ball, two teams: no leash on the gun", scores[("item", gun)] == 2.05, scores)

# 3. our person carries; our watcher is 30 u off him, its overlook 9 u off him, a gun 8 u off the watcher
watch = PlayerState(2, 0, "watcher", Vec(0.0, -38.0, Z))
post = Vec(0.0, -17.0, Z)
snap3 = Snapshot(50.0, [person, watch], mode="oddball")
snap3.ball, snap3.ball_carrier = person.pos, 0
b = bot(M, 0, "mid", post, pid=2)
scores = {("item", Vec(8.0, -38.0, Z)): 1.9, ("objective", post): 0.5 + 0.7 * b.p.objective}
b.keep_role(scores, watch, snap3, [])
check("3. the watcher goes back to its overlook by our carrier, not to the gun", best(scores)[0] == "objective", scores)

# 4. Narrows: the round's line to the part aimed at (no learned spots: the renamed file)
N = get_map("h3_chill")


def shot(a, e_at, ticks=2):
    b = bot(N, 0, "free", None, pid=1)
    me4 = PlayerState(1, 0, "me", a)
    foe = PlayerState(9, 1, "foe", e_at)
    sn = Snapshot(10.0, [me4, foe], mode="slayer")
    out = []
    for k in range(ticks):
        now = 10.0 + k * 0.033
        b.per.clear_at[9] = now                      # (Perception's sight said so this tick)
        out.append(b.line_clear(now, me4, 9, sn))
    return b, out


b, out = shot(Vec(0.89, 3.03, 60.76), Vec(0.30, 9.10, 62.61))
check("4. head over cover: no shot on the first tick, then one at his head", out == [False, True]
      and getattr(b, "head_only", (None,))[0] == 9, out)
b, out = shot(Vec(-1.11, 2.03, 52.76), Vec(0.30, 9.10, 62.61))
check("4. both blocked (a learned spot's sight): no shot", out == [False, False], out)
b, out = shot(Vec(-1.11, 3.03, 60.76), Vec(0.30, 10.10, 60.39))
check("4. a clear line: shot", out == [True, True], out)
BB.WALL_SHOTS = False
b, out = shot(Vec(-1.11, 2.03, 52.76), Vec(0.30, 9.10, 62.61))
BB.WALL_SHOTS = True
check("4. switch off: Perception's line alone (as before)", out == [True, True], out)

# 5. corner hits
T = terrain(N)
clear_a, clear_b = Vec(-1.11, 3.03, 60.76), Vec(0.30, 10.10, 60.39)
blk_a, blk_b = Vec(-1.11, 2.03, 52.76), Vec(0.30, 9.10, 62.61)
ts = [10.0 + k * 0.033 for k in range(20)]
his = [(t, clear_a if t < 10.3 else blk_a) for t in ts]
mine = [(t, clear_b if t < 10.3 else blk_b) for t in ts]
check("5. a line 0.3 s before the hit: a corner, not learned", Bot.corner_hit(T, his, mine, ts[-1]))
check("5. blocked all along: learned", not Bot.corner_hit(T, [(t, blk_a) for t in ts], [(t, blk_b) for t in ts], ts[-1]))
check("5. a trail too short: not learned", Bot.corner_hit(T, [(t, blk_a) for t in ts[-5:]], [(t, blk_b) for t in ts[-5:]],
                                                         ts[-1]))

# 6. the speedometer, on Narrows' open floor
spot = Vec(-1.11, 3.03, 60.76)


def run(moving, fight=False, ticks=35):
    b = bot(N, 0, "free", None, pid=1)
    b.goal = ("fight", 9) if fight else ("objective", Vec(20.0, 3.0, 60.76))
    sn = Snapshot(10.0, [PlayerState(1, 0, "me", spot)], mode="slayer")
    act = None
    for k in range(ticks):
        now = 10.0 + k * 0.033
        s = 1.9 * min(k, ticks if moving else 10) * 0.033   # (runs free along its push, then the wall)
        p = Vec(spot.x, spot.y + s, spot.z) if fight else Vec(spot.x + s, spot.y, spot.z)
        me6 = PlayerState(1, 0, "me", p)
        b.notes = []
        act = Action(yaw=0.0, forward=0.0 if fight else 1.0, strafe=1.0 if fight else 0.0)
        b.move_watch(now, me6, act, sn)
    return b, act


b, act = run(False)
check("6. pushing into nothing that moves it: marked blocked", getattr(b, "wall_way", None) is not None, b.notes)
check("6. the next step slides along the face", abs(act.forward) < 0.3 and abs(act.strafe) > 0.9,
      (act.forward, act.strafe, b.notes))
b, act = run(True)
check("6. running free: nothing marked", getattr(b, "wall_way", None) is None and act.forward == 1.0, b.notes)
b, act = run(False, fight=True)
check("6. a fight's strafe into it goes the other way", act.strafe < 0 and getattr(b, "strafe_dir", 1) == -1,
      (act.strafe, b.notes))
b0 = bot(N, 0, "free", None, pid=1)
b0.goal = ("objective", Vec(20.0, 3.0, 60.76))
for k in range(30):
    a0 = Action(yaw=0.0, forward=1.0)
    b0.move_watch(10.0 + k * 0.033, PlayerState(1, 0, "me", spot), a0, Snapshot(10.0, [PlayerState(1, 0, "me", spot)]))
check("6. never seen running (a test world's still body): not judged", getattr(b0, "wall_way", None) is None, b0.notes)

# 7. a gunner's trigger: a man 12 u east
g = bot(M, 0, "ride", None, pid=1)
seat = PlayerState(1, 0, "gunner", Vec(0.0, -30.0, Z))
man = Vec(12.0, -30.0, Z)
g.aim.goal = (0.0, 0.0)
off = lambda u: Action(yaw=math.atan2(u, 12.0), pitch=math.atan2(0.35, 12.0) * 0 + g_pitch)
g_pitch = math.atan2((man.z + 0.35) - (seat.pos.z + 0.62), 12.0)
g.seat_fire = False
check("7. 0.6 u off: the trigger goes down", g.gun_seat_trigger(1.0, seat, man, off(0.6)))
g.seat_fire = True
check("7. held: 1.2 u off stays down", g.gun_seat_trigger(1.1, seat, man, off(1.2)))
check("7. a swing off him 0.2 s: still down", g.gun_seat_trigger(1.3, seat, man, off(4.0)))
check("7. off him 0.5 s: let go", not g.gun_seat_trigger(1.6, seat, man, off(4.0)))
g.seat_fire = False
check("7. not firing yet: 1.2 u off does not start it", not g.gun_seat_trigger(5.0, seat, man, off(1.2)))
errs = {}
for steady in (1.0, 0.5):
    a = bot(M, 0, "ride", None, pid=1).aim
    tot = 0.0
    for k in range(400):
        a.next_sample = 0.0
        a.step(k * 1.0, 0.033, seat, 9, man, Vec(0, 0, 0), False, steady=steady)
        tot += abs(a.err[0])
    errs[steady] = tot / 400
check("7. a mounted gun's aim error is half the hand's", abs(errs[0.5] / errs[1.0] - 0.5) < 0.08, errs)

# 8. the learned file's name
tmp = tempfile.mkdtemp()
try:
    root = MP.ROOT
    shutil.copytree(os.path.join(root, "h3_chill"), os.path.join(tmp, "h3_chill"),
                    ignore=shutil.ignore_patterns("*learned*", "lidar*", "source"))
    with open(os.path.join(tmp, "h3_chill", "walls_learned.json"), "w") as f:
        json.dump([[4, 34, 62.5, 63.0, 0]], f)
    MP.ROOT = tmp
    MP._TERRAIN.pop("h3_chill", None)
    old = len(getattr(terrain(MP.load_map("h3_chill")), "walls_learned", []))
    MP._TERRAIN.pop("h3_chill", None)
    with open(os.path.join(tmp, "h3_chill", "shots_learned.json"), "w") as f:
        json.dump([[4, 34, 62.5, 63.0, 0]], f)
    new = len(getattr(terrain(MP.load_map("h3_chill")), "walls_learned", []))
finally:
    MP.ROOT = root
    MP._TERRAIN.pop("h3_chill", None)
    shutil.rmtree(tmp, ignore_errors=True)
check("8. walls_learned.json not read, shots_learned.json read", old == 0 and new == 1, (old, new))

# 9. the loose ball (Sandtrap floor, two teams)
ballp = Vec(0.0, -27.6, Z)
me9 = PlayerState(1, 1, "bot", Vec(0.0, -30.0, Z))
foe9 = PlayerState(9, 0, "foe", Vec(10.0, -30.0, Z))


def loose(me_, others, seen, on=True):
    BB.ODD_BALL_FIRST = on
    try:
        sn = Snapshot(50.0, [me_, foe9] + others, mode="oddball")
        sn.ball, sn.ball_carrier = ballp, None
        b = bot(M, 1, "hunter", ballp)
        b.per.beliefs = {9: Belief(foe9.pos, Vec(0, 0, 0), 50.0, True, "eyes")}
        sc = {("item", Vec(2.0, -31.0, Z)): 2.6, ("fight", 9): 3.2, ("objective", ballp): 1.84}
        b.ball_first(me_, sn, sc, seen)
        return best(sc)
    finally:
        BB.ODD_BALL_FIRST = True


check("9. the loose ball 2.4 u off: first", loose(me9, [], [9]) == ("objective", ballp))
foe9 = PlayerState(9, 0, "foe", Vec(1.5, -30.0, Z))
check("9. a man at arm's length: him first", loose(me9, [], [9]) == ("fight", 9))
foe9 = PlayerState(9, 0, "foe", Vec(10.0, -30.0, Z))
far9 = PlayerState(1, 1, "bot", Vec(0.0, -35.6, Z))
mate9 = PlayerState(4, 1, "mate", Vec(0.0, -25.0, Z))
check("9. a teammate nearer, 8 u off: left to him", loose(far9, [mate9], [9]) != ("objective", ballp))
check("9. switch off: the fight", loose(me9, [], [9], on=False) == ("fight", 9))

# 10. eight teams: team 0 carries; we (team 1) hunt; a team 2 man in view 6 u off us
car = PlayerState(0, 0, "carrier", Vec(0.0, -8.0, Z), has_flag=True, is_bot=False)
me10 = PlayerState(1, 1, "hunter", Vec(0.0, -30.0, Z))
third = PlayerState(5, 2, "third", Vec(6.0, -30.0, Z))
rest = [PlayerState(20 + k, 3 + k, f"x{k}", Vec(60.0 + k, 40.0, Z)) for k in range(5)]
sn10 = Snapshot(50.0, [car, me10, third] + rest, mode="oddball")
sn10.ball, sn10.ball_carrier = car.pos, 0
b = bot(M, 1, "hunter", car.pos)
b.per.beliefs = {5: Belief(third.pos, Vec(0, 0, 0), 50.0, True, "eyes")}
live = b.live_point(me10, sn10)
gun10 = Vec(2.0, -32.0, Z)
sc = {("fight", 5): 3.2, ("item", gun10): 2.6, ("objective", live): 1.3 + 0.6 * b.p.teamwork + BB.ODD_HUNT_ADD}
b.keep_role(sc, me10, sn10, [5])
check("10. eight teams: their carrier over a third team's man 6 u off and a gun beside us", best(sc)[0] == "objective", sc)
third2 = PlayerState(5, 2, "third", Vec(2.0, -30.0, Z))
sn10b = Snapshot(50.0, [car, me10, third2] + rest, mode="oddball")
sn10b.ball, sn10b.ball_carrier = car.pos, 0
b.per.beliefs = {5: Belief(third2.pos, Vec(0, 0, 0), 50.0, True, "eyes")}
sc = {("fight", 5): 3.2, ("objective", live): 1.3 + 0.6 * b.p.teamwork + BB.ODD_HUNT_ADD}
b.keep_role(sc, me10, sn10b, [5])
check("10. a third team's man at 2 u is still fought", sc[("fight", 5)] == 3.2, sc)

# 11. a bot carries for us; our escort 20 u off him, a gun 7 u off the escort
bcar = PlayerState(3, 0, "botcarrier", Vec(0.0, -8.0, Z), has_flag=True, is_bot=True)
esc = PlayerState(2, 0, "escort", Vec(0.0, -28.0, Z))
t11 = PlayerState(6, 2, "third", Vec(6.0, -28.0, Z))
sn11 = Snapshot(50.0, [bcar, esc, t11], mode="oddball")
sn11.ball, sn11.ball_carrier = bcar.pos, 3
b = bot(M, 0, "escort", bcar.pos, target=3, pid=2)
b.per.beliefs = {6: Belief(t11.pos, Vec(0, 0, 0), 50.0, True, "eyes")}
sc = {("fight", 6): 3.2, ("objective", bcar.pos): 1.0}
b.keep_role(sc, esc, sn11, [6])
check("11. a bot carrier's escort goes back to him, not after a man 6 u off it", best(sc)[0] == "objective", sc)

if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("owner flags nov11b OK")
