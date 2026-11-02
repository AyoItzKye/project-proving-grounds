"""Boarding and anti-tank play (at 603.3 s in his Scorpion). On h3_cyberdyne:

1. a Normal bot on foot, an enemy's Scorpion 4 u off side on and slow: it goes to board it (over the fight with its
   driver); the same Scorpion running at it nose first at 6 u/s, or one 9 u off: no
2. Easy never boards (it never plans); CE has no boarding
3. going to board: it walks to the driver's seat and presses Use beside it
4. aboard an enemy's vehicle: melee and one grenade, no driving
5. an enemy Scorpion 20 u off: a Normal non-Grenadier with rockets goes after it; with none, it fetches a launcher lying
   10 u off, not one 40 u off

usage: python -I test_boarding.py      -> "boarding OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_cyberdyne")
T = terrain(M)
A = M["points"]["mid"]


def bot(tier="average", pers="rusher", m=M, seed=1):
    b = Bot(1, 0, make_profile(tier, pers, random.Random(seed)), m, random.Random(seed))
    b._terrain = terrain(m)
    b.order = Order("mid", A)
    b.posture, b.notes = 0.5, []
    return b


def tank_at(off, fwd=(0.0, 1.0, 0.0)):
    q = A + off
    return dict(handle=31, kind="scorpion", pos=(q.x, q.y, q.z), riders=1, occupied=True, team=1, fwd=fwd,
                up=(0.0, 0.0, 1.0))


def see(b, pid, pos, t):
    b.per.beliefs[pid] = Belief(pos, Vec(), t, True, "eyes")
    b.per.recognized.add(pid)
    b.per.last_seen[pid] = t


def decide(b, t, me, v, drv, n=10):
    got = []
    for k in range(n):
        see(b, 7, drv.pos, t + k * 0.01)
        b.goal, b.next_decide = ("roam", None), 0.0
        got.append(b.decide(t + k * 0.01, me, Snapshot(t, [me, drv], vehicles=[v], mode="slayer"))[0])
    return max(set(got), key=got.count)


def main():
    fails = []
    me = PlayerState(1, 0, "b", A, weapon="assault_rifle", weapons=["assault_rifle"])
    for name, off, vel, want in (("4 u off side on, slow", Vec(4.0, 0.0, 0.0), Vec(0.0, 1.0, 0.0), "board"),
                                 ("running at it nose first", Vec(4.0, 0.0, 0.0), Vec(-6.0, 0.0, 0.0), None),
                                 ("9 u off", Vec(9.0, 0.0, 0.0), Vec(), None)):
        fwd = (-1.0, 0.0, 0.0) if vel.x < 0 else (0.0, 1.0, 0.0)
        v = tank_at(off, fwd)
        drv = PlayerState(7, 1, "drv", A + off, vehicle=31, vel=vel)
        got = decide(bot(), 10.0, me, v, drv)
        if (got == "board") != (want == "board"):
            fails.append(f"an enemy Scorpion {name}: chose {got} (want {'board' if want else 'not board'})")
    v, drv = tank_at(Vec(4.0, 0.0, 0.0)), PlayerState(7, 1, "drv", A + Vec(4.0, 0.0, 0.0), vehicle=31)
    if decide(bot("novice"), 20.0, me, v, drv) == "board":
        fails.append("Easy boarded")
    ce = get_map("bloodgulch")
    b = bot(m=ce)
    q = ce["points"]["mid"]
    vce = dict(tank_at(Vec()), pos=(q.x + 4, q.y, q.z))
    got = decide(b, 30.0, PlayerState(1, 0, "b", q), vce, PlayerState(7, 1, "drv", q + Vec(4, 0, 0), vehicle=31))
    if got == "board":
        fails.append("CE: boarded")
    # 3. to the seat, Use beside it
    b = bot()
    b.goal, b.next_decide = ("board", 31), 1e9
    pressed, start = 0, None
    pos = A
    for k in range(90):
        t = 40.0 + k / 30
        me = PlayerState(1, 0, "b", pos)
        a = b.think(t, 1 / 30, Snapshot(t, [me, drv], vehicles=[v], mode="slayer"), T.los, T.nav, [])
        start = start or a
        pos = pos + Vec(a.forward * math.cos(a.yaw) - a.strafe * math.sin(a.yaw),
                        a.forward * math.sin(a.yaw) + a.strafe * math.cos(a.yaw), 0.0) * (2.25 / 30)
        pressed += a.action
    if not pressed or abs(start.forward) + abs(start.strafe) < 0.3:
        fails.append(f"going to board: moved {abs(start.forward) + abs(start.strafe):.2f}, pressed Use {pressed} ticks")
    # 4. aboard theirs
    b = bot()
    melee = nades = 0
    for k in range(60):
        t = 50.0 + k / 30
        me = PlayerState(1, 0, "b", A + Vec(4, 0, 0), vehicle=31)
        a = Action()
        b.drive(t, 1 / 30, me, Snapshot(t, [me, drv], vehicles=[dict(v, riders=2)]), a, lambda p, q, **kw: q)
        melee += a.melee
        nades += a.grenade
        if a.forward or a.fire:
            fails.append("aboard an enemy's Scorpion: drove or fired")
            break
    if not melee or nades != 1:
        fails.append(f"aboard an enemy's Scorpion: melee {melee} ticks, grenades {nades} (want melee, one grenade)")
    # 5. anti-tank: a launcher in hand, or one lying close
    far = PlayerState(7, 1, "drv", A + Vec(20.0, 0.0, 0.0), vehicle=31)
    vt = tank_at(Vec(20.0, 0.0, 0.0))
    for name, weapons, ground, want in (("rockets in hand", ["assault_rifle", "rockets"], [], True),
                                        ("a launcher 10 u off", ["assault_rifle"], [("rockets", A + Vec(-10.0, 0, 0))], True),
                                        ("a launcher 40 u off", ["assault_rifle"], [("rockets", A + Vec(-40.0, 0, 0))], False)):
        b = bot(pers="camper", seed=5)
        b.map = dict(M, items=[])
        see(b, 7, far.pos, 60.0)
        me = PlayerState(1, 0, "b", A, weapon=weapons[0], weapons=weapons, ammo=[60] * len(weapons))
        snap = Snapshot(60.0, [me, far], vehicles=[vt], mode="slayer", ground_weapons=ground)
        scores = {}
        b.vehicle_mission(60.0, me, snap, scores)
        if bool(b.mission_keys) != want:
            fails.append(f"an enemy Scorpion 20 u off, {name}: mission {b.mission_keys} (want {'one' if want else 'none'})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("boarding OK (boards a slow tank beside it, not one running at it; to the seat and Use; melee and a grenade"
          " aboard; anyone Normal+ after an enemy tank with a launcher)")


if __name__ == "__main__":
    main()
