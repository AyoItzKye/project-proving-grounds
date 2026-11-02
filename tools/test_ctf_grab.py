"""CTF runners go in (live, both Halo 3 CTF games 0-0: The Pit with both flags home 2,202 of 2,508 world rows; the sim on
The Pit, 8v8 Legendary, 3 x 300 s: 2 pulls, 1 capture, runners holding for a clear base 39% of their time 12-18 u out
and no life of 41 within 6 u of the stand). On h3_cyberdyne, a Legendary runner by their flag on its stand:

1. with a teammate beside it and a defender in sight at the flag (never "clear" in 8v8) it does not hold (stage)
2. alone it holds for company, STAGE_WAIT at most, guarded or not
3. 5 u from the flag with a defender 7 u off in sight (a new fight) and a teammate beside it: the grab; alone,
   the fight first (grab_ok: a carrier cannot shoot back)
4. cracked at 5 u from the flag with cover beside it: the grab, not backing off to cover
5. outside GRAB_R the fight still wins (a defender 7 u off with the flag 14 u away), and a man at arm's length is fought

usage: python -I test_ctf_grab.py      -> "ctf grab OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import bot as B  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("h3_cyberdyne")
T = terrain(MAP)
RED, BLUE = MAP["flags"][0], MAP["flags"][1]


def toward(a, b, d):
    v = b - a
    n = v.flat()
    p = Vec(b.x - v.x / n * d, b.y - v.y / n * d, 0.0)
    return Vec(p.x, p.y, T.nav_z(p.x, p.y, b.z))


def runner(seed=1):
    b = Bot(1, 0, make_profile("top", "objector", random.Random(seed)), MAP, random.Random(seed))
    b._terrain = T
    b.order = Order("runner", BLUE)
    b.posture = 0.5
    return b


def see(b, pid, pos, t):
    b.per.beliefs[pid] = Belief(pos, Vec(), t, True, "eyes")
    b.per.recognized.add(pid)
    b.per.last_seen[pid] = t


def snap_of(t, me, others):
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, BLUE, "home")}
    return Snapshot(t, [me] + others, flags, mode="ctf")


def choose(b, t, me, snap, n=20):
    got = []
    for k in range(n):
        b.goal, b.next_decide = ("roam", None), 0.0
        got.append(b.decide(t + k * 0.01, me, snap)[0])
    return max(set(got), key=got.count)


def main():
    fails = []
    at = toward(RED, BLUE, 15.0)
    me = PlayerState(1, 0, "r", at, shield=1.0, health=1.0)
    mate = PlayerState(2, 0, "m", at + Vec(2.0, 0.0, 0.0))
    foe = PlayerState(5, 1, "d", BLUE + Vec(1.5, 0.0, 0.0))
    # 1. company, a defender in sight at the flag
    b = runner()
    see(b, 5, foe.pos, 10.0)
    snap = snap_of(10.0, me, [mate, foe])
    held = b.stage(me, snap, {}, BLUE, need_clear=B.STAGE_NEED_CLEAR)
    if held:
        fails.append("with company and a defender at their flag: it held (want it to go in)")
    # 2. alone: holds for company, then goes
    b = runner(2)
    see(b, 5, foe.pos, 10.0)
    waits = [b.stage(me, snap_of(10.0 + k * 0.5, me, [foe]), {}, BLUE, need_clear=B.STAGE_NEED_CLEAR)
             for k in range(20)]
    first_go = next((k * 0.5 for k, w in enumerate(waits) if not w), None)
    if not waits[0] or first_go is None or not B.STAGE_WAIT - 0.1 <= first_go <= B.STAGE_WAIT + 0.6:
        fails.append(f"alone, guarded: held {waits[0]}, went after {first_go} s (want a hold of about {B.STAGE_WAIT} s)")
    # 3. 5 u from the flag, a defender 7 u off in sight: the grab
    at = toward(RED, BLUE, 5.0)
    me = PlayerState(1, 0, "r", at, shield=1.0, health=1.0)
    foe = PlayerState(5, 1, "d", at + Vec(0.0, 7.0, 0.0), shield=1.0, health=1.0, weapon="assault_rifle")
    b = runner(3)
    see(b, 5, foe.pos, 20.0)
    near = PlayerState(2, 0, "m", at + Vec(-3.0, 0.0, 0.0))
    got = choose(b, 20.0, me, snap_of(20.0, me, [near, foe]))
    if got != "objective":
        fails.append(f"5 u from their flag, a defender 7 u off, a teammate beside it: chose {got} (want the grab)")
    # 3b. the same alone (its mate 10+ u back): the room is cleared first (grab_ok; lone pulls died in 1-2 s in the sim)
    b = runner(3)
    see(b, 5, foe.pos, 20.0)
    got = choose(b, 20.0, me, snap_of(20.0, me, [mate, foe]))
    if got != "fight":
        fails.append(f"5 u from their flag, a defender 7 u off, alone: chose {got} (want the fight first)")
    # 4. cracked by the flag: no backing off to cover a step from it
    me = PlayerState(1, 0, "r", at, shield=0.0, health=0.6)
    b = runner(4)
    see(b, 5, foe.pos, 30.0)
    foes = [foe, PlayerState(6, 1, "d2", at + Vec(-6.0, 3.0, 0.0), shield=1.0, health=1.0)]
    see(b, 6, foes[1].pos, 30.0)
    got = choose(b, 30.0, me, snap_of(30.0, me, foes))
    if got == "retreat":
        fails.append("cracked 5 u from their flag: backed off to cover (want the grab)")
    # 5. outside GRAB_R the fight wins; a man at arm's length is fought by the flag too
    far = toward(RED, BLUE, 14.0)
    me = PlayerState(1, 0, "r", far, shield=1.0, health=1.0)
    foe = PlayerState(5, 1, "d", far + Vec(0.0, 7.0, 0.0), shield=1.0, health=1.0, weapon="assault_rifle")
    b = runner(5)
    see(b, 5, foe.pos, 40.0)
    got = choose(b, 40.0, me, snap_of(40.0, me, [mate, foe]))
    if got != "fight":
        fails.append(f"14 u from their flag, a man 7 u off: chose {got} (want the fight)")
    me = PlayerState(1, 0, "r", at, shield=1.0, health=1.0)
    foe = PlayerState(5, 1, "d", at + Vec(0.0, 2.0, 0.0), shield=1.0, health=1.0, weapon="assault_rifle")
    b = runner(6)
    see(b, 5, foe.pos, 50.0)
    got = choose(b, 50.0, me, snap_of(50.0, me, [mate, foe]))
    if got != "fight":
        fails.append(f"5 u from their flag, a man 2 u off: chose {got} (want the fight)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"ctf grab OK (goes in with company, holds alone {first_go:.1f} s, the grab inside {B.GRAB_R:.0f} u)")


if __name__ == "__main__":
    main()
