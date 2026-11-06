"""the player's flags in Halo 3 Shrine (Sandtrap) King match 20261104-154714 (his install's bug report):

1. 99.8 s "Hill doesnt seem to be getting any urgency": the match read as Slayer 23.8-119.2 s, so nobody played the
   hill. Halo 3's hill comes from the host's HUD waypoint, which the game hides while he stands in the hill (383 of 389
   ticks with him in it read no hill). live_bots.snapshot keeps the last hill read in a King game: a missed read is
   still King, on the same hill
2. that frame replayed (99.8 s, blue down 7-83, the host and a red bot in the hill): with the hill, blue's director
   sends men onto it; read as Slayer (the old snapshot) it sent none
3. 95.5 s "Guy in banshee isnt using any weapons": bot 9's Banshee runs fired on 43 of 428 ticks under 28 u. Its guns
   needed the hand gun's man-sized window on the aim plan's point; now its nose within AIR_GUN_R of him fires them
   (a run tick of his: 2.9 deg off a man 20 u away, no aim plan yet)

usage: python -I test_flags_154714.py      -> "flags 154714 OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import live_bots  # noqa: E402
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, angles_to, eye  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_shrine")
HILL = Vec(15.43, -20.76, -20.08)
# the 99.8 s frame: [id, team, x, y, z] (bot 5 dead, left out); 0 is the host
FRAME = [(0, 0, 16.4, -20.4, -20.3), (1, 0, 24.7, 15.4, -21.6), (2, 1, -5.8, -54.8, -20.2), (3, 0, 5.1, 14.0, -20.3),
         (4, 1, 0.3, -37.9, -22.5), (6, 1, 28.3, -5.8, -22.2), (7, 0, 16.4, -20.4, -20.3), (8, 1, 8.3, -37.2, -19.8),
         (9, 0, -13.1, -26.2, -5.7), (10, 1, -2.2, -55.6, -21.6), (11, 0, 18.3, 18.5, -21.0), (12, 1, -3.1, -56.3, -22.2),
         (13, 0, 11.5, 9.9, -22.8), (14, 1, -0.2, -54.4, -22.1), (15, 1, 8.3, -37.2, -19.8)]


class KingLive:
    """A Halo 3 King game whose hill read misses after the first tick (the host walked into it)."""
    def __init__(s):
        s.reads = 0

    def engine(s):
        return 4

    def players(s):
        return [dict(index=0, name="Host", team=0, unit=1, pos=(16.4, -20.4, -20.3), fwd=(1, 0, 0), aim=(1, 0, 0),
                     health=1.0, shield=1.0, weapon="br", weapons=["br"]),
                dict(index=1, name="Bot", team=1, unit=2, pos=(0.3, -37.9, -22.5), fwd=(0, 1, 0), aim=(0, 1, 0),
                     health=1.0, shield=1.0, weapon="br", weapons=["br"])]

    def objects(s, types=None):
        return []

    def flags(s, players, stands=None):
        return []

    def king_hill(s):
        s.reads += 1
        return ((HILL.x, HILL.y, HILL.z), 3.0) if s.reads == 1 else None


def main():
    fails = []
    # 1. a missed hill read keeps the hill
    live_bots.MAP = M
    getattr(live_bots, "HILL", {}).clear()
    live = KingLive()
    first = live_bots.snapshot(live, 0.0, {}, {1})
    later = [live_bots.snapshot(live, 0.25 * k, {}, {1}) for k in range(1, 5)]
    if first.mode != "king" or any(s.mode != "king" or s.hill is None or (s.hill - HILL).length() > 0.01 for s in later):
        fails.append(f"hill read missed: modes {[s.mode for s in later]} (want king on the same hill)")
    # 2. the frame replayed: blue's plan with the hill, and as the old Slayer read
    sent = {}
    for mode in ("king", "slayer"):
        bots = {i: Bot(i, 1, make_profile("top", "objector", random.Random(i)), M, random.Random(i))
                for i, team, *_ in FRAME if team == 1}
        d = Director(1, M, bots, random.Random(0))
        ps = [PlayerState(i, team, f"p{i}", Vec(x, y, z)) for i, team, x, y, z in FRAME]
        for b in bots.values():                      # the host in the hill, seen
            b.per.beliefs[0] = Belief(Vec(16.4, -20.4, -20.3), Vec(), 99.8, True, "eyes")
        snap = Snapshot(99.8, ps, mode=mode, hill=HILL if mode == "king" else None, hill_r=3.0,
                        score={0: 83, 1: 7})
        slots = d.role_slots(99.8, snap, len(bots))
        sent[mode] = sum(1 for r, q, f in slots if q is not None and (q - HILL).flat() < 3.5)
    if sent["king"] < 1 or sent["slayer"]:
        fails.append(f"frame 99.8 s: blue posts on the hill {sent} (want some with the hill, none as Slayer)")
    # 3. the Banshee's run: nose 2.9 deg off a man 20 u ahead, no aim plan (on_target alone: no shot)
    b = Bot(9, 0, make_profile("top", "flanker", random.Random(9)), M, random.Random(9))
    b.order = Order("mid", HILL)
    me = PlayerState(9, 0, "pilot", Vec(-5.0, -30.0, -8.0), vehicle=77)
    foe = Vec(14.0, -24.0, -20.0)
    ya, pa = angles_to(eye(me), foe)
    me.yaw, me.pitch = ya + math.radians(2.9), pa
    b.air_run = ["in", 4, 9.0, me.yaw]
    a = Action()
    a.yaw, a.pitch = me.yaw, me.pitch
    b.air_pass(10.0, me, 4, Belief(foe, Vec(), 10.0, True, "eyes"), foe, a)
    if not a.fire:
        fails.append("Banshee run 2.9 deg off a man 20 u ahead: the cannons held (want firing)")
    a = Action()
    me.yaw = ya + math.radians(15.0)
    a.yaw, a.pitch = me.yaw, me.pitch
    b.air_pass(10.1, me, 4, Belief(foe, Vec(), 10.1, True, "eyes"), foe, a)
    if a.fire:
        fails.append("Banshee run 15 deg off him: fired (want held)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"flags 154714 OK (a missed hill read stays King; the 99.8 s frame: {sent['king']} blue posts on the hill, "
          f"{sent['slayer']} as Slayer; the Banshee fires 2.9 deg off, holds at 15)")


if __name__ == "__main__":
    main()
