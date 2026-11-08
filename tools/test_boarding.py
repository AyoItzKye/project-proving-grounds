"""Boarding and anti-tank play (at 603.3 s in a player's Scorpion). On h3_cyberdyne:

1. a Normal bot on foot, an enemy's Scorpion 4 u off side on and slow: it goes to board it (over the fight with its
   driver); the same Scorpion running at it nose first at 6 u/s, or one 9 u off looking at it: no; 9 u off, slow, its
   driver looking away: yes (a Boneyard playtest board), not at 3 u/s nor 13 u off
2. Easy never boards (it never plans); CE has no boarding
3. going to board: it walks to the tank's front and presses Use beside it
4. aboard an enemy's vehicle: melee and one grenade, no driving; in Reach melee alone, a press every 0.55 s
6. the plasma launcher on a vehicle is held until every bomb locked (PL_LOCK_S on it), on foot CHARGE's hold
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
from brain import vehicles  # noqa: E402
from brain.bot import CHARGE, PL_LOCK_S, Action, Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, angles_to, eye  # noqa: E402
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
    # (yaw: where its driver looks; pi: at us. The player's board: walked up on from 11 u while its driver looked away)
    for name, off, vel, yaw, want in (("4 u off side on, slow", Vec(4.0, 0.0, 0.0), Vec(0.0, 1.0, 0.0), math.pi, "board"),
                                      ("running at it nose first", Vec(4.0, 0.0, 0.0), Vec(-6.0, 0.0, 0.0), math.pi, None),
                                      ("9 u off, its driver on us", Vec(9.0, 0.0, 0.0), Vec(), math.pi, None),
                                      ("9 u off, its driver looking away", Vec(9.0, 0.0, 0.0), Vec(), 0.0, "board"),
                                      ("9 u off looking away, at 3 u/s", Vec(9.0, 0.0, 0.0), Vec(0.0, 3.0, 0.0), 0.0, None),
                                      ("13 u off, its driver looking away", Vec(13.0, 0.0, 0.0), Vec(), 0.0, None)):
        fwd = (-1.0, 0.0, 0.0) if vel.x < 0 else (0.0, 1.0, 0.0)
        v = tank_at(off, fwd)
        drv = PlayerState(7, 1, "drv", A + off, vehicle=31, vel=vel, yaw=yaw)
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
    # (Reach boards into the vehicle's boarding seats, a second each: live the driver's seat beside an enemy Wraith
    # never took; Halo 3 keeps seat 0)
    got = [vehicles.reach_seat(k, "board", n) for k, n in (("scorpion", 0), ("scorpion", 1), ("scorpion", 3),
                                                          ("wraith", 0), ("ghost", 2))]
    if got != [(5, False), (6, False), (5, False), (1, False), (3, False)]:
        fails.append(f"Reach boarding seats: {got}")
    front = A + Vec(4.0, 0.0, 0.0) + Vec(0.0, 2.0, 0.0)          # its facing +y, BOARD_FRONT ahead
    if (pos - front).flat() > 1.0:
        fails.append(f"going to board a tank: ended {(pos - front).flat():.1f} u from its front (want under 1)")
    # 3b. never in Use reach (a ledge over it: live Beachhead Firefight Nov 8, 70 s over a Ghost 2.9 u under it): left
    #     alone after BOARD_REACH_S, banned BOARD_BAN s
    from brain.bot import BOARD_REACH_S
    b = bot()
    b.goal, b.next_decide = ("board", 31), 1e9
    stay = PlayerState(1, 0, "b", A + Vec(4.0, 0.0, 3.0))       # (held 3 u over it: it never gets there)
    for k in range(int((BOARD_REACH_S + 2.0) * 30)):
        t = 60.0 + k / 30
        b.think(t, 1 / 30, Snapshot(t, [stay, drv], vehicles=[v], mode="slayer"), T.los, T.nav, [])
        b.goal, b.next_decide = (("board", 31), 1e9) if getattr(b, "board_ban", {}).get(31, 0.0) <= t else (b.goal, 1e9)
    if getattr(b, "board_ban", {}).get(31, 0.0) <= 60.0 + BOARD_REACH_S:
        fails.append(f"boarding a vehicle it cannot reach: not given up after {BOARD_REACH_S + 2.0:.0f} s")
    # 4. aboard theirs (it boarded: board_try names the vehicle)
    b = bot()
    b.board_try = (31, 49.0)
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
    # (Reach, the player's board: melee alone, a press every BOARD_MELEE_EVERY)
    b = bot(m=get_map("reach_70_boneyard"))
    b.board_try = (31, 49.0)
    presses = nades = 0
    was = False
    for k in range(66):
        t = 50.0 + k / 30
        me = PlayerState(1, 0, "b", A + Vec(4, 0, 0), vehicle=31)
        a = Action()
        b.drive(t, 1 / 30, me, Snapshot(t, [me, drv], vehicles=[dict(v, riders=2)]), a, lambda p, q, **kw: q)
        presses += a.melee and not was
        was, nades = a.melee, nades + a.grenade
    if presses != 4 or nades:
        fails.append(f"aboard an enemy's Scorpion in Reach, 2.2 s: {presses} melee presses, grenades {nades} (want 4, none)")
    # (the driver an enemy boarded is no boarder: live Boneyard 183101 every boarded driver stopped and meleed too)
    b = bot(m=get_map("reach_70_boneyard"))
    hit = 0
    for k in range(30):
        t = 60.0 + k / 30
        me = PlayerState(1, 0, "b", A + Vec(4, 0, 0), vehicle=31)
        a = Action()
        b.drive(t, 1 / 30, me, Snapshot(t, [me, drv], vehicles=[dict(v, riders=2)]), a, lambda p, q, **kw: q)
        hit += a.melee
    if hit or any("aboard theirs" in n for n in b.notes):
        fails.append(f"a driver an enemy boarded beat at its own vehicle ({hit} melee ticks)")
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
    # 6. the plasma launcher (the player's Banshee kill): on a vehicle let go only once every bomb locked (PL_LOCK_S of the
    # reticle within the vehicle's size, PL_LOCK_R; the clock again after a slip off it over PL_SLIP), whatever the
    # man-sized "on" says (live Breakpoint 181702: on flickered, a 12 s hold on a Banshee never let go); on foot CHARGE's
    for name, veh, flicker, away, want in (
            ("a Banshee", 31, False, None, PL_LOCK_S),
            ("a Banshee, the man-sized on flickering", 31, True, None, PL_LOCK_S),
            ("a man on foot", -1, False, None, CHARGE["plasma_launcher"][1]),
            ("a Banshee, the aim 20 deg off it 1.0-1.5 s", 31, False, (1.0, 1.5), 1.5 + PL_LOCK_S),
            ("a Banshee, the aim off it 1.0-1.2 s (a slip)", 31, False, (1.0, 1.2), PL_LOCK_S)):
        b = bot(m=get_map("reach_70_boneyard"))
        me = PlayerState(1, 0, "b", A, weapon="plasma_launcher", weapons=["plasma_launcher"])
        tgt = PlayerState(7, 1, "p", A + Vec(18.0, 0.0, 6.0), vehicle=veh)
        ya, pa = angles_to(eye(me), tgt.pos)
        let_go = None
        for k in range(200):
            t = 70.0 + k / 30
            a = Action()
            off = away is not None and away[0] <= t - 70.0 < away[1]
            a.yaw, a.pitch = ya + (0.35 if off else 0.0), pa
            b.charge_fire(t, me, tgt, 7, 19.0, not off and (not flicker or k % 2 == 0), True, a,
                          CHARGE["plasma_launcher"])
            if k and not a.fire:
                let_go = t - 70.0
                break
        if let_go is None or abs(let_go - want) > 0.05:
            fails.append(f"plasma launcher on {name}: let go after {let_go} s (want {want:.2f})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("boarding OK (boards a slow tank beside it or stalks one looking away, not one running at it; to the seat or a"
          " tank's front and Use; melee and a grenade aboard, Reach melee alone; anyone Normal+ after an enemy tank with"
          " a launcher; the plasma launcher locks on a vehicle)")


if __name__ == "__main__":
    main()
