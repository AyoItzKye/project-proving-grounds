"""Map brain (docs/research/21-map-brain.md) rules in the director, offline on Blood Gulch:
1. MAP-06 / MAP-05: the Slayer anchor's post is picked by its power position score (tools/power_positions.py), and twice
   as likely where it sees the hot zone (where the team saw the enemy in the last 20 s); the score's sightlines count
   the floor people walked (LiDAR) for more
2. MAP-10: a bot at its post with nobody known faces the hot zone (the director hands it to every bot but Easy)
3. MAP-08 / CALL-04: with no fight to go to, the Slayer hunters go where the enemy will spawn: near his living
   teammates the team knows of, away from our men and out of their sight
4. MAP-12: Halo 3's weapon timers start 2 s after the weapon is disturbed

usage: python -I test_director_map.py      -> "director map OK"
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist, wrap  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, power_items, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

M = get_map("bloodgulch")
T = terrain(M)
PORT = Vec(82.8, -114.6, T.nav_z(82.8, -114.6, 50.0))      # Red port: three of the eight power positions see it
                                                            # (and still do 0.5 u off; Sunny's top was a grazing line)


def posts(d, n=1000, seen=None):
    """The anchor's post over n rotations (seen: a man reported there before each)."""
    out = []
    for k in range(n):
        now = 100.0 + 50.0 * k
        if seen is not None:
            d.report(now, 1, "seen", seen)
        d.post_until = 0.0
        d.slayer_slots(now, Snapshot(now, []), 4)
        out.append(d.post)
    return out


def main():
    testdata.need_lidar("h3_construct", "h3_guardian")
    fails = []
    pts = list(M["positions"])
    # 1. by score: the first spot scored 1.0, the other seven 0.1 (a flat pick: 12.5% each)
    m = dict(M, position_info=[dict(i, score=1.0 if k == 0 else 0.1) for k, i in enumerate(M["position_info"])])
    share = sum(p == pts[0] for p in posts(Director(0, m, {}, random.Random(1)))) / 1000
    if share < 0.4:
        fails.append(f"post by score: the best spot held {share:.0%} of rotations (want 40%+, 59% expected)")
    # ... and twice as likely where it sees the hot zone
    sees = [q for q in pts if T.los(q, PORT)]
    if not 0 < len(sees) < 4:
        sys.exit(f"FAIL: test premise: {len(sees)} of the power positions see Red port")
    flat = len(sees) / len(pts)
    hot = sum(p in sees for p in posts(Director(0, M, {}, random.Random(2)), seen=PORT)) / 1000
    if hot < flat + 0.1:
        fails.append(f"post by the hot zone: spots that see it held {hot:.0%} of rotations (flat {flat:.0%}; want "
                     f"10 points more, 56% expected)")
    # ... where a spot's sightlines count the floor people walked for more (tools/power_positions.py traffic, MAP-06)
    import power_positions
    c = get_map("h3_construct")
    walk = [w for w in json.load(open(os.path.join(HERE, "..", "maps", "h3_construct", "lidar.json")))["walk"]
            if len(w) == 5 and w[3] == 1]
    x, y, z, _, n = max(walk, key=lambda w: w[4])
    busy, empty = power_positions.traffic(c, [(x * 0.25, y * 0.25, z * 0.1), (999.0, 999.0, 0.0)])
    if busy < 1.0 + n ** 0.5 or empty != 1.0 or power_positions.traffic(M, [(0.0, 0.0, 0.0)]) is not None:
        fails.append(f"traffic: {busy:.0f} on Construct's most walked floor ({n} samples), {empty} off it, Blood Gulch "
                     f"(no people's walk) {power_positions.traffic(M, [(0.0, 0.0, 0.0)])} (want 1 + sqrt, 1, None)")
    # 2. MAP-10: the director hands its bots the hot zone (Easy plays for itself: none); one at its post with nobody
    #    known watches it (20 re-picks), not a random open line; 20 s on the hot zone is gone
    bots = {i: Bot(i, 0, make_profile(t, "camper", random.Random(i)), M, random.Random(i))
            for i, t in ((1, "average"), (2, "novice"))}
    d = Director(0, M, bots, random.Random(3))
    post = sees[0]
    men = [PlayerState(i, 0, f"b{i}", post + Vec(2.0 * i - 2.0, 0.0, 0.0)) for i in bots]
    d.report(50.0, 1, "seen", PORT)
    d.update(50.0, Snapshot(50.0, men))
    handed = tuple(getattr(bots[i], "hot_spot", None) for i in bots)
    want, views = math.atan2(PORT.y - post.y, PORT.x - post.x), 0
    for k in range(20):
        bots[1].now = 50.0 + 7.0 * k                       # past each re-pick (2.5-6 s)
        q = bots[1].look_point(men[0], post, post=post)
        views += abs(wrap(math.atan2(q.y - post.y, q.x - post.x) - want)) < math.radians(30)
    d.update(75.0, Snapshot(75.0, men))
    if handed != (PORT, None) or views < 19 or getattr(bots[1], "hot_spot", None) is not None:
        fails.append(f"post view: handed {handed} (want Red port, None for Easy), faced it {views} of 20 re-picks (want "
                     f"19+), 25 s on {getattr(bots[1], 'hot_spot', None)} (want None)")
    # 3. MAP-08 / CALL-04: with no fight to go to, the hunters go where they will spawn: the blue spawn nearest the man
    #    our bot saw 1 s ago (not where he really is: team knowledge only), then, with one of us on it, one he cannot see
    pool = M["spawns"]["slayer"][1]
    seen_at = Vec(50.0, -95.0, T.nav_z(50.0, -95.0))

    def target(tier, us):
        hunt = Director(0, M, {1: Bot(1, 0, make_profile(tier, "rusher", random.Random(5)), M, random.Random(5))},
                        random.Random(5))
        hunt.bots[1].per.beliefs[9] = Belief(pos=seen_at, vel=Vec(), t=199.0, seen=True, source="eyes")
        snap = Snapshot(200.0, [PlayerState(1 + k, 0, f"b{k}", p) for k, p in enumerate(us)] +
                        [PlayerState(9, 1, "e9", Vec(100.0, -100.0, T.nav_z(100.0, -100.0)))])
        hunt.slayer_slots(200.0, snap, 4)
        hunt.look_their_side = True                        # (drawn per rotation: 70% look their way)
        return hunt.slayer_slots(200.0, snap, 4)[1][1]    # the standard posture's hunter
    first = target("average", [M["flags"][0]])
    on = first + Vec(1.0, 0.0, 0.0)
    unseen = [q for q in pool if (q - on).flat() > 5.0 and (dist(q, on) > 40.0 or not T.los(on, q))]
    if not unseen:
        sys.exit("FAIL: test premise: a man beside the first guess sees every blue spawn")
    second = target("average", [M["flags"][0], on])
    easy = target("novice", [M["flags"][0]])               # Easy's eyes are its own: just away from us
    if first not in pool or dist(first, seen_at) > 15.0 or second not in unseen or dist(easy, seen_at) <= 15.0:
        fails.append(f"spawn guess: {first} (want a blue spawn within 15 u of {seen_at}), with one of us on it {second} "
                     f"(want one of the {len(unseen)} he cannot see); Easy's sighting {easy} (want not by it)")
    # 4. MAP-12: a Halo 3 weapon's timer starts 2 s after it is disturbed (Guardian: its weapons' respawn the
    #    scenario's + 2 s, its power-ups' as set); Blood Gulch's as set
    objs = lambda name: json.load(open(os.path.join(HERE, "..", "maps", name, "objects.json")))
    gd = [(i["kind"], i["respawn"] - p["respawn"]) for i, p in zip(get_map("h3_guardian")["items"],
                                                                    power_items(objs("h3_guardian")))]
    bg = [i["respawn"] for i in M["items"]] == [p["respawn"] for p in power_items(objs("bloodgulch"))]
    if not any(k == "weapon" for k, _ in gd) or any(d != (2 if k == "weapon" else 0) for k, d in gd) or not bg:
        fails.append(f"timers: Guardian's items (kind, respawn over the scenario's) {gd} (want +2 s on weapons), "
                     f"Blood Gulch's as set: {bg}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"director map OK (post by score {share:.0%}, by the hot zone {hot:.0%} against {flat:.0%} flat; "
          f"the post's view on the hot zone {views} of 20; spawn guess {dist(first, seen_at):.1f} u from the sighting, "
          f"then out of sight of the man on it)")


if __name__ == "__main__":
    main()
