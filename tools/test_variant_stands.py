"""Halo 3 CTF on a map variant with its own flag stands (the player's Sandtrap One Flag, Nov 11, the variant "SAND TARP":
read as Slayer all match, no bot touched the flag). LiveH3.flags with the objects the live probe read (logs/tmp/
play_nov11/oneflag_probe2.py, Nov 11 17:29): the flag hung on a stand object (type 10) at (-0.28, -50.48), 23.7 u from
the map's nearest stand point:

1. it is found, on a stand of its own (live_stands), owned by the team that spawned by it (One Flag)
2. a gun on a turret (parent a vehicle) is no flag; a loose gun on no stand neither
3. with a flag already known, nothing new is made a stand

usage: python -I test_variant_stands.py      -> "variant stands OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.live import LiveH3  # noqa: E402

FLAG, STAND_PARENT = 0xE3DB016C, 0xE3830114
WEAPONS = [(FLAG, 0xFC721AFC, STAND_PARENT, (-0.28, -50.48, -21.69)),       # the flag on the variant's stand
           (0xE279000A, 0xE75305DD, 0xE2780009, (4.24, -47.05, -21.95)),   # a gun on a turret (a vehicle parent)
           (0xE2940025, 0xF19C1026, 0xFFFFFFFF, (-2.49, -49.27, -21.73))]  # a loose gun
STANDS = {0: Vec(0.0, 22.5, -23.7), 1: Vec(-21.0, -62.0, -20.8)}         # the map's stand points (built-in Sandtrap)


class Stub(LiveH3):
    """LiveH3 without the game: _weapons_held hands the probe's objects back, marking the flag as on a stand."""
    def __init__(s, on_stand=True):
        s.on = on_stand

    def _weapons_held(s, players):
        s._third, s._attached, s._riding, s._riding_frame = set(), {FLAG, 0xE279000A}, {}, {}
        s._on_stand = {FLAG} if s.on else set()
        return list(WEAPONS), {}

    def _placed(s, weapons):
        return ()


fails = []
players = [dict(index=0, team=0, unit=1, pos=(-0.2, -54.8, -22.2)), dict(index=2, team=1, unit=2, pos=(20.2, 6.4, -22.6))]
live = Stub()
got = live.flags(players, STANDS)
if len(got) != 1 or got[0]["handle"] != FLAG or abs(got[0]["pos"][1] + 50.48) > 0.01:
    fails.append(f"1. the variant's flag: {got} (want the one on its own stand)")
elif got[0]["team"] != 0:
    fails.append(f"1. One Flag's owner: team {got[0]['team']} (want 0, who spawned beside it)")
if not any(abs(v.y + 50.48) < 0.01 for v in getattr(live, "live_stands", {}).values()):
    fails.append(f"1. its stand not passed on: {getattr(live, 'live_stands', None)}")
old = Stub(on_stand=False)               # (the reader before: no stand objects known)
if old.flags(players, STANDS):
    fails.append("2. a gun on a turret or a loose gun was taken for a flag")
known = Stub()
known._flag_tags = {0x12345678}           # a flag tag already learned (another object): no new stands
known.flags(players, STANDS)
if any(abs(v.y + 50.48) < 0.01 for v in getattr(known, "live_stands", {}).values()):
    fails.append("3. with a flag known, the variant stand was still added")
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("variant stands OK")
