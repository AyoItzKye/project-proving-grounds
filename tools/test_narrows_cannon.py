"""Narrows' man cannons (Halo 3 h3_chill, flagged Nov 8: "Bots arent using map man cannon"): they throw people across
the gap level, 28 u in 4.2 s, not up, so LiDAR's link from one (a person's ride, twice) read as a plain 28 u jump,
costed like the walk round, and bots walked. brain/maps.py anchor_launches marks a long link off a man cannon a ride
(on its trigger), brain/terrain.py costs a ride across by its airtime.
  1. the person's cannon link is a ride, taking off at the cannon
  2. the nav's way from beside the cannon to the far base takes it (its first jump is that ride) and is far cheaper
     than the walk round
  3. a ride, a lift or a man cannon, is never held back by a watched exit (Bot.exit_held): no bot is kept off one;
     a big drop still is

usage: python -I test_narrows_cannon.py      -> "narrows cannon OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import testdata  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.core import Vec  # noqa: E402

CANNON = (6.699, 14.008, 60.092)
HERE_AT, FAR = Vec(6.0, 17.0, 60.2), Vec(6.8, -15.0, 59.2)


def main():
    testdata.need_lidar("h3_chill")
    fails = []
    M = get_map("h3_chill")
    T = terrain(M)
    rides = [k for _, _, k, _ in T.hjumps if k.get("ride") and math.hypot(k["take_off"][0] - CANNON[0], k["take_off"][1] - CANNON[1]) < 1.5]
    if not rides:
        fails.append("1: no ride off the man cannon at y 14 in the nav")
    # 4. the blue base's cannon (y -14), never ridden by a person, takes its twin's ride turned half round: blue bots
    #    went by foot all match while red bots used theirs (live Nov 8)
    blue = [k for _, _, k, _ in T.hjumps if k.get("ride") and math.hypot(k["take_off"][0] - 6.612, k["take_off"][1] + 14.002) < 1.5]
    if not blue or not any(k["land"][1] > 10.0 for k in blue):
        fails.append(f"4: the blue base's cannon has no ride across in the nav ({[k['land'][:2] for k in blue]})")
    nb = T._node(Vec(5.0, -18.0, 60.1))                 # (by the blue base)
    if not float(T._field(Vec(6.6, 11.0, 59.2), True, True, False)[nb]) < 0.6 * float(T._field(Vec(6.6, 11.0, 59.2), False, False, False)[nb]):
        fails.append("4: from beside the blue cannon to the red base the cannon is not far cheaper than the walk")
    across = [(w, k) for _, _, k, w in T.hjumps if k.get("ride") and math.hypot(k["land"][0] - k["take_off"][0], k["land"][1] - k["take_off"][1]) > 20]
    if not across or min(w for w, _ in across) > 15.0:
        fails.append(f"2: the cannon ride costs {[round(w, 1) for w, _ in across]} (want about its 4.2 s aloft, under 15)")
    n = T._node(HERE_AT)
    with_cannon = float(T._field(FAR, True, True, False)[n])
    walk = float(T._field(FAR, False, False, False)[n])
    if not (with_cannon < 0.6 * walk):
        fails.append(f"2: from beside the cannon to the far base {with_cannon:.0f} with it, {walk:.0f} walking (want it far cheaper)")
    from brain.bot import Bot
    from brain.profiles import make_profile
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b._terrain, b.notes, b.now = T, [], 100.0

    class J:                                     # the nav's jump: from (sx, sy), landing at (x, y, z)
        pass
    j = J()
    j.sx, j.sy = CANNON[0], CANNON[1] + 0.9
    j.x, j.y, j.z = 6.8, -12.7, 59.2
    me = type("Me", (), {"pos": Vec(j.sx, j.sy, 60.2), "has_flag": False})()
    b.exit_watched = lambda now, ex, r: True     # (an enemy watches every exit)
    if b.exit_held(me, j, FAR) != "":
        fails.append("3: the man cannon ride was held back by a watched landing (want ridden)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("narrows cannon OK")


if __name__ == "__main__":
    main()
