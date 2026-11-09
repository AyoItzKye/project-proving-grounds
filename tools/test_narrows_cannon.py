"""Narrows' man cannons (Halo 3 h3_chill, flagged Nov 8: "Bots arent using map man cannon"): they throw people across
the gap level, 28 u in 4.2 s, not up, so LiDAR's link from one (a person's ride, twice) read as a plain 28 u jump,
costed like the walk round, and bots walked. brain/maps.py anchor_launches marks a long link off a man cannon a ride
(on its trigger), brain/terrain.py costs a ride across by its airtime.
  1. the person's cannon link is a ride, taking off at the cannon
  2. the nav's way from beside the cannon to the far base takes it (its first jump is that ride) and is far cheaper
     than the walk round
  3. a ride, a lift or a man cannon, is never held back by a watched exit (Bot.exit_held): no bot is kept off one;
     a big drop still is
  5. a cannon is gone into from behind (a 1 u lane between two fins, the far end a drop; flagged Nov 8: bots on the
     walkways beside the fins pushed through a fin at the trigger): the ride's run-up is its entrance, 1.5 u back on the
     throw's line, and a bot walking the nav from the walkway beside the fin gets the ride only at the entrance, never
     stepping into a fin on the way
  6. a flag carrier's way across takes the cannon too, and the ride carries its airtime (judged once down: judged 2 s
     into the 4.2 s throw every ride read short and barred the cannon)
  7. four others in the cannon's lane send a bot the way round; three do not
  8. a bot runs through (flagged Nov 8: bots stopped at the entrance, hopped at the foot, walked back out): in the lane
     the nav still offers the ride, and the bot steers on down the lane's line, never at a stop, no jump

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
    j.rx, j.ry, j.air = math.nan, math.nan, 4.18
    b.exit_watched = lambda now, ex, r: True     # (an enemy watches every exit)
    if b.exit_held(me, j, FAR) != "":
        fails.append("3: the man cannon ride was held back by a watched landing (want ridden)")
    # 5. the entrance
    red = rides[0] if rides else {}
    run = red.get("runup")
    if not run or abs(run[0] - red["take_off"][0]) > 0.2 or not 1.3 < run[1] - red["take_off"][1] < 1.7:
        fails.append(f"5: the red cannon's ride has no entrance 1.5 u behind its trigger (run-up {run})")
    fins = lambda q: 13.8 <= abs(q.y) <= 15.8 and (5.8 <= q.x <= 6.25 or 7.3 <= q.x <= 7.5)
    for start in (Vec(5.0, 15.0, 60.2), Vec(8.1, 15.0, 60.2), Vec(5.0, -15.0, 60.2), Vec(8.1, -15.0, 60.2)):
        goal = FAR if start.y > 0 else Vec(6.6, 11.0, 59.2)
        p, got = start, None
        for _ in range(60):
            nxt = T.nav(p, goal, jump=True, human=True)
            if hasattr(nxt, "sx"):
                got = nxt
                break
            if fins(nxt) or nxt is None:
                fails.append(f"5: from {start} the nav walks into a fin at {nxt}")
                break
            d = nxt - p
            p = p + d * min(1.0, 0.5 / max(d.length(), 1e-6))
        if got is None or math.isnan(got.rx):
            fails.append(f"5: from the walkway at {start} no cannon ride with its entrance ({got})")
        elif abs(p.y) < 15.8 or math.hypot(p.x - got.rx, p.y - got.ry) > 0.9:
            fails.append(f"5: from {start} the ride was handed at {p}, not at its entrance ({got.rx:.1f}, {got.ry:.1f})")
        elif not 3.5 < got.air < 5.0:
            fails.append(f"6: the ride's airtime is {got.air} (want its 4.2 s)")
    # 6. a carrier
    if not float(T._field(FAR, True, True, True)[n]) < 0.6 * float(T._field(FAR, False, False, True)[n]):
        fails.append("6: a flag carrier's way from beside the cannon to the far base does not take it")
    # 7. jammed
    b.p.tier, b.per.beliefs = "top", {}
    j.rx, j.ry = red["runup"][0] if run else j.sx, red["runup"][1] if run else j.sy + 1.5
    me.pos = Vec(j.rx, j.ry + 0.5, 60.2)
    b.exit_watched = lambda now, ex, r: False
    for k, want in ((3, ""), (4, "round")):
        b.round_goal = None
        b.mates_now = [Vec(j.sx, j.sy + 0.4 * q, 60.2) for q in range(k)]
        got = b.exit_held(me, j, FAR)
        if got != want:
            fails.append(f"7: {k} others in the cannon's lane: exit_held {got!r} (want {want!r})")
    # 8. run through
    for p in (Vec(6.65, 15.9, 60.2), Vec(6.65, 15.2, 60.2), Vec(6.75, 14.6, 60.2)):
        got = T.nav(p, FAR, jump=True, human=True)
        if not getattr(got, "air", 0.0):
            fails.append(f"8: in the cannon's lane at {p} the nav offers {got}, not the ride (want: on through)")
    from brain.core import Action
    from brain.terrain import JumpVec
    ride = JumpVec(6.8, -12.7, 59.2, red["take_off"][0], red["take_off"][1], *(red.get("runup") or (math.nan,) * 2)[:2], 4.18)
    seen = []
    b.steer = lambda me_, tgt, act_, *a, **kw: seen.append(tgt)
    for p, committed in ((Vec(6.0, 17.2, 60.2), False), (Vec(6.65, 16.5, 60.2), True), (Vec(6.7, 15.3, 60.2), True)):
        act = Action()
        me.pos, b.planned_jump, b.ride_until = p, False, 0.0
        b.cannon_run(me, ride, act)
        t = seen[-1]
        if act.jump or not (t.y < p.y - 0.7 and abs(t.x - ride.rx) < 0.3):
            fails.append(f"8: running in from {p}: steers at {t}, jump {act.jump} (want down the lane's line ahead, no jump)")
        # 9. the flight: once in the lane, the edge guard's jump window covers the whole throw (it ended 2 s in: riders
        #    were pulled back mid-gap and fell, live Nov 8); not before (off the line its window steered through a fin)
        if b.planned_jump != committed or (committed and not 4.5 < b.ride_until - b.now < 5.0):
            fails.append(f"9: at {p}: committed {b.planned_jump}, window {b.ride_until - b.now:.1f} s (want {committed}, the throw)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("narrows cannon OK")


if __name__ == "__main__":
    main()
