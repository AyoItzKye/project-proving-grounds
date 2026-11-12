"""Power spots (brain/spots.py; the player's ask, Nov 12: Oddball bots left good covered places to run about; a sniper's
spot and a ball spot differ):

1. Zanzibar: the room the player held the ball in (18, -2) scores as a ball spot (walls round it, a roof, one way in)
   above the open middle of the map
2. Triplicate: the player's two longest holds score 3.5+ and the map's best ball spots lie by them (within 6 u)
3. the Oddball carrier's spot (Director.ball_spot): kept while the enemies move about but stay off it; given up when one
   comes within ODD_FREE_R of it; switch off (POWER_SPOTS): the old pick
4. a bot with a sniper rifle and no objective job holds the best overwatch near it (SNIPER_SPOTS); a rifleman does not

usage: python -I test_power_spots.py      -> "power spots OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.director as DD  # noqa: E402
from brain import spots  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


Z = get_map("h3_zanzibar")
TZ = terrain(Z)
dz = spots.deaths_of(Z)
room = Vec(18.0, -2.0, TZ.nav_z(18.0, -2.0, 2.0))
mid = Z["points"]["mid"]
mid = Vec(mid.x, mid.y, TZ.nav_z(mid.x, mid.y, mid.z))
a, b = spots.ball_score(TZ, room, dz), spots.ball_score(TZ, mid, dz)
check("1. Zanzibar: the player's ball room scores above the open middle", a > b + 1.0 and a > 2.5, (a, b))

T3 = get_map("h2_triplicate")
TT = terrain(T3)
holds = [Vec(40.0, -16.0, TT.nav_z(40.0, -16.0, 1.5)), Vec(14.0, 10.0, TT.nav_z(14.0, 10.0, 2.0))]
sc = [spots.ball_score(TT, h, spots.deaths_of(T3)) for h in holds]
check("2. Triplicate: the player's two longest holds score 3.5+", min(sc) >= 3.5, sc)
top = [p for _, p in spots.spots(TT, T3, "ball")[:8]]
check("2. the map's best ball spots lie by one of his holds", any(dist(p, h) < 6.0 for p in top for h in holds),
      [(round(p.x), round(p.y)) for p in top])

# 3. the carrier's spot on Construct (no people's holds there): kept while they move about off it
C = get_map("h3_construct")
d = Director(0, C, {}, random.Random(1))
d._odd_people = []
car = PlayerState(1, 0, "carrier", Vec(0.0, 0.0, 0.0), has_flag=True)


def pick(foes):
    sn = Snapshot(10.0, [car] + [PlayerState(20 + k, 1, "f", q) for k, q in enumerate(foes)], mode="oddball")
    sn.ball, sn.ball_carrier = car.pos, 1
    return d.carry_point(sn)


s1 = pick([Vec(30.0, 30.0, 0.0)])
s2 = pick([Vec(26.0, 34.0, 0.0)])
check("3. the carrier's spot kept while they move about off it", s1 == s2, (s1, s2))
s3 = pick([Vec(s1.x + 2.0, s1.y, s1.z)])
check("3. given up once one of them is on it", dist(s3, s1) > 3.0, (s1, s3))
DD.POWER_SPOTS = False
d2 = Director(0, C, {}, random.Random(1))
d2._odd_people = []
sn = Snapshot(10.0, [car, PlayerState(20, 1, "f", Vec(30.0, 30.0, 0.0))], mode="oddball")
sn.ball, sn.ball_carrier = car.pos, 1
old = d2.carry_point(sn)
DD.POWER_SPOTS = True
check("3. switch off: the old pick (a map hold or mid)", any(dist(old, h) < 0.5 for h in C["holds"][0] + C["holds"][1]
                                                               + [C["points"]["mid"]]), old)

# 4. a sniper rifle in hand
def decide(weapon):
    bot = Bot(1, 0, make_profile("top", "flanker", random.Random(2)), C, random.Random(2))
    bot.order = Order("free", None)
    me = PlayerState(1, 0, "bot", Vec(0.0, -10.0, TT.nav_z(0.0, -10.0, 0.0) * 0 + 0.0), weapon=weapon, weapons=[weapon])
    bot.decide(5.0, me, Snapshot(5.0, [me], mode="slayer"))
    return [k for k in (getattr(bot, "last_scores", {}) or {}) if k[0] == "hold"]


check("4. a sniper rifle in hand: a hold at an overwatch spot", bool(decide("sniper")), decide("sniper"))
check("4. a rifleman: no overwatch hold", not any(k for k in decide("assault_rifle")
                                                 if any(dist(k[1], p) < 0.5 for _, p in spots.spots(terrain(C), C, "sniper")[:20])))

if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("power spots OK")
