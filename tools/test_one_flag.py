"""One Flag (live Avalanche was One Flag: one flag on (27, -32) all match, its the player key switching 0 -> 1 -> 0 at
426.6 and 853.8 s; round 1's attackers spent 57% of their runner time 40-50 u off it by their own base):

1. the sim plays it (Sim.set_one_flag): only the defenders' flag, on team 0's stand; an attacker takes it there, scores
   on the other stand, and the sides swap (the flag back on its stand, the other team's); a round's clock swaps too
2. the director reads it (is_one_flag) and its attackers run for the flag with nobody left home
3. the attackers press (Bot.pressing, as Invasion attackers do); the defenders do not; nor anyone in two-flag CTF

usage: python -I test_one_flag.py      -> "one flag OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.sim import Sim  # noqa: E402


def main():
    fails = []
    s = Sim("ctf", 2, 1, tiers=["top"], map_name="bloodgulch")
    s.set_one_flag(0, 60.0)
    stand, goal = s.m["flags"][0], s.m["flags"][1]
    if set(s.flags) != {0}:
        fails.append(f"One Flag: flags {set(s.flags)} (want only the defenders', team 0)")
    att = next(p for p in s.players if p.team == 1)
    att.pos = stand + Vec(0.3, 0.0, 0.0)
    s.ctf()
    if not att.has_flag or s.flags[0].state != "carried":
        fails.append("an attacker on the stand did not take the flag")
    att.pos = goal + Vec(0.2, 0.0, 0.0)
    s.ctf()
    if s.score[1] != 1 or set(s.flags) != {1} or dist(s.flags[1].home, stand) > 0.1 or att.has_flag:
        fails.append(f"a capture on the other stand: score {s.score}, flags {set(s.flags)} (want 1 for team 1, the flag "
                     f"team 1's on the same stand)")
    s.now = s.one_flag["until"] + 0.1
    s.ctf()
    if set(s.flags) != {0}:
        fails.append(f"the round's clock ran out: flags {set(s.flags)} (want the sides swapped back)")
    # 2. the director's plan
    snap = s.snapshot()
    d1 = s.directors[1]
    d1.assign_roles(s.now, snap)
    roles1 = set(d1.roles.values())
    if not d1.is_one_flag(snap) or "defender" in roles1 or "runner" not in roles1:
        fails.append(f"One Flag attackers' roles {roles1} (want runners, nobody defending)")
    # 3. pressing
    b = s.bots[att.id]
    me = snap.player(att.id)
    df = next(p for p in s.players if p.team == 0)
    two = Snapshot(0.0, s.players, {0: FlagState(0, stand, stand), 1: FlagState(1, goal, goal)}, mode="ctf")
    if not Bot.pressing(me, snap) or Bot.pressing(snap.player(df.id), snap) or Bot.pressing(me, two):
        fails.append(f"pressing: attacker {Bot.pressing(me, snap)}, defender {Bot.pressing(snap.player(df.id), snap)}, "
                     f"two-flag {Bot.pressing(me, two)} (want True, False, False)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("one flag OK (the sim's rounds: take, capture, swap, the clock; the attackers run and press)")


if __name__ == "__main__":
    main()
