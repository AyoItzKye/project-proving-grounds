"""The player's Sandtrap CTF, Nov 12 (live 20261112-154827): "I tried to get the flag carrier in my vehicle and he just
ignored me and he wasnt even heading into the home plate direction". The carrier, given the director's "board" order for
the player's Warthog, weighed nothing (his run home banned from before the pickup, his "home" the Warthog's old spot)
and Bot.decide returned a roam before it read the order: 35 s roaming beside the Warthog with the flag.

1. a carrier under a "board" order, the Warthog 9.6 u off: goes to the Warthog
2. the same with a ban on every objective spot it knows from before the pickup: still the Warthog (a carrier's run is
   never banned)
3. the order's Warthog gone: the run home goes to our flag stand, not the Warthog's old spot
4. a bot with nothing to weigh but a "ride" order (a gun called for): the ride, not a roam

usage: python -I test_carrier_board.py      -> "carrier board OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


M = get_map("h3_shrine")
STAND = Vec(16.9, 33.2, -20.3)
HOG = 3800039441


def decide(carrying=True, role="board", hog=True, bans=False):
    b = Bot(3, 0, make_profile("top", "flanker", random.Random(3)), M, random.Random(3))
    me = PlayerState(3, 0, "carrier", Vec(-5.2, -58.4, -22.1), alive=True, has_flag=carrying, weapon="assault_rifle")
    person = PlayerState(0, 0, "person", Vec(-5.45, -48.8, -22.1), alive=True, vehicle=HOG if hog else -1)
    vs = [dict(handle=HOG, kind="warthog", pos=(-5.45, -48.8, -22.1), riders=2, occupied=True, team=0,
               fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0))] if hog else []
    flags = {0: FlagState(0, STAND, STAND, "home"),
             1: FlagState(1, Vec(-1.7, -58.0, -20.6), me.pos if carrying else Vec(-1.7, -58.0, -20.6),
                          "carried" if carrying else "home", 3 if carrying else None)}
    b.order = Order(role, Vec(3.3, -53.9, -21.9), target=HOG)
    b.via_left = [Vec(-35.8, -13.4, -23.2)]
    if bans:
        b.goal_ban = {("objective", x, y): 1e9 for x, y in ((3, -54), (-36, -13), (17, 33), (-2, -58))}
    snap = Snapshot(47.9, [me, person], flags, mode="ctf", vehicles=vs)
    b.now, b.notes, b.vehicles_now = 47.9, [], vs
    return b.decide(47.9, me, snap), b


g, _ = decide()
check("1. a carrier told to board the Warthog: to the Warthog", g == ("vehicle", HOG), g)
g, b = decide(bans=True)
check("2. bans on its old spots: still the Warthog", g == ("vehicle", HOG), (g, b.last_scores))
g, b = decide(hog=False)
check("3. the Warthog gone: home to our stand", g[0] == "objective" and dist(g[1], STAND) < 0.5, g)
g, b = decide(hog=False, bans=True)
check("3. ... with its old spots banned too", g[0] == "objective" and dist(g[1], STAND) < 0.5, (g, b.last_scores))
g, b = decide(carrying=False, role="ride", bans=True)
check("4. nothing to weigh but a ride order: the ride", g == ("vehicle", HOG), (g, b.last_scores))
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("carrier board OK")
