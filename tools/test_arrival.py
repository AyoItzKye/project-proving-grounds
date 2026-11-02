"""Map brain INTER-CANNON-05, the landing ambush (Bot.arrival, Bot.launches): an enemy known a moment ago on a launch (a
teleporter pad, a man cannon, a gravity lift) whose landing is near the bot and in its sight: the bot pre-aims the
landing; Heroic and up throw a grenade onto it while he is on his way (INTER-LIFT-02's lift exit). On Blood Gulch,
the bot standing 10 u from its first teleporter's exit, the man on its pad on the bot's radar (43 u off, out of sight):

1. Normal: faces the exit (within 20 degrees) within 1.5 s, looking at it as "landing"
2. Easy: never (Easy never plans); 40 u from the exit: never; a contact 1 s old: never
3. a ride with 2 s in the air (the man on the radar at its foot, its landing 10 u off): Heroic throws a grenade onto it
   while he is on his way; Normal does not
4. the rides people made are launches with their airtime (Warhouse's man cannons, maps/h4_ca_warhouse/lidar.json)
5. INTER-LIFT-02, the rider: up a lift with nobody known, Normal looks at the cover a man waiting at its exit would
   hold; Easy does not

usage: python -I test_arrival.py      -> "arrival OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

M = get_map("bloodgulch")
T = terrain(M)
DT = 1 / 30
PAD, EXIT = M["teleporters"][0]


def run(tier, off, fresh=True, launch=None, secs=2.5):
    """The bot standing off the exit by off (a retreat there: it stays), facing away from it, the man on the pad (or on
    launch's foot) on its radar from t=10, refreshed each tick when fresh. Per tick (t from 10, yaw off the landing,
    what it looks at, grenade)."""
    land = launch[1] if launch else EXIT
    src = launch[0] if launch else PAD
    me_at = Vec(land.x + off.x, land.y + off.y, T.nav_z(land.x + off.x, land.y + off.y))
    bot = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), M, random.Random(1))
    bot._terrain = T
    if launch:
        bot._launches = [launch]
    bot.goal, bot.next_decide = ("retreat", me_at), 1e9
    yaw = math.atan2(me_at.y - land.y, me_at.x - land.x)        # facing away from the landing
    rows, t = [], 10.0
    los = lambda p, q: (p - q).flat() < 20.0
    while t < 10.0 + secs:
        if fresh or t < 10.0 + DT:                    # (not fresh: last on the radar 1 s before)
            bot.per.beliefs[9] = Belief(pos=src, vel=Vec(), t=t if fresh else 9.0, seen=False, source="radar")
        men = [PlayerState(1, 0, "bot", me_at, yaw=yaw), PlayerState(9, 1, "man", src)]
        act = bot.think(t, DT, Snapshot(t, men), los, lambda p, q, **k: T.nav(p, q, **k), [])
        to = math.atan2(land.y - me_at.y, land.x - me_at.x)
        rows.append((t - 10.0, abs(math.atan2(math.sin(act.yaw - to), math.cos(act.yaw - to))),
                     bot.att[1] if bot.att else None, act.grenade))
        yaw = act.yaw
        t += DT
    return rows


def main():
    testdata.need_lidar("h3_construct", "h4_ca_warhouse")
    fails = []
    near = Vec(-7.0, 7.0, 0.0)                    # about 10 u off the exit, the open gulch floor
    rows = run("average", near)
    on = next((r[0] for r in rows if r[1] < math.radians(20) and r[2] == "landing"), None)
    if on is None or on > 1.5:
        fails.append(f"Normal, a man on the pad: faced the exit at {on} s (want within 1.5 s, looking at it as landing)")
    for label, rws in (("Easy", run("novice", near)), ("40 u off", run("average", Vec(-28.0, 28.0, 0.0))),
                       ("a contact 1 s old", run("average", near, fresh=False))):
        if any(r[2] == "landing" for r in rws):
            fails.append(f"{label}: pre-aimed the landing (want not)")
    a = Vec(EXIT.x - 30.0, EXIT.y, T.nav_z(EXIT.x - 30.0, EXIT.y))   # its foot 24 u from the bot: on the radar, out of
    ride = (a, EXIT, 2.0)                                               # sight; its landing where case 1's exit is
    heroic = run("strong", near, launch=ride)
    thrown = [r[0] for r in heroic if r[3]]
    if not thrown or not 0.0 <= thrown[0] <= 1.25:
        fails.append(f"Heroic, a man 2 s from the landing: grenades at {thrown[:3]} s (want one in the first 1.2 s)")
    if any(r[3] for r in run("average", near, launch=ride)):
        fails.append("Normal threw a grenade onto the landing (want Heroic and up only)")
    wh = Bot(1, 0, make_profile("average", "rusher", random.Random(1)), get_map("h4_ca_warhouse"), random.Random(1))
    rides = [x for x in wh.launches() if x[2] > 0.0]
    if not rides or not all(0.3 < x[2] < 6.0 for x in rides):
        fails.append(f"Warhouse: rides as launches {[(round(x[2], 2)) for x in rides]} (want its man cannons, 0.3-6 s each)")
    # 5. INTER-LIFT-02, the rider's side: up Construct's lift with nobody known, Normal looks at the cover a man waiting
    #    at its exit would hold (one of LiDAR's cover spots 3-10 u off the landing, on its floor, that sees it); Easy not
    cm = get_map("h3_construct")
    rider = lambda tier: Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), cm, random.Random(1))
    ct = rider("average").T()
    take, land = next((Vec(*k["take_off"]), Vec(*k["land"])) for _, _, k, _ in ct.hjumps
                      if k["land"][2] - k["take_off"][2] > 3.0 and rider("average").lift_near(*k["take_off"][:2]))
    cover = {(round(float(c[0]), 2), round(float(c[1]), 2), round(float(c[2]), 2)) for c in ct.cover_spots}
    looked = {}
    for tier in ("average", "novice"):
        rb = rider(tier)
        rb.now, rb.lift_ride = 10.0, (rb.lift_near(take.x, take.y), land, 9.5)
        q = rb.look_point(PlayerState(1, 0, "r", take + Vec(0.0, 0.0, 3.0), vel=Vec(0.0, 0.0, 4.0)), land)
        c = Vec(q.x, q.y, q.z - 0.62)
        looked[tier] = ((round(c.x, 2), round(c.y, 2), round(c.z, 2)) in cover and 3.0 <= (c - land).flat() <= 10.0
                        and abs(c.z - land.z) < 1.5 and ct.los(c, land))
    if looked != {"average": True, "novice": False}:
        fails.append(f"up Construct's lift, on a cover spot by its exit: {looked} (want Normal yes, Easy no)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"arrival OK (Blood Gulch: faced the teleporter's exit at {on:.2f} s; Heroic's grenade {thrown[0]:.2f} s after "
          f"the man stepped on; Warhouse: {len(rides)} rides, {min(x[2] for x in rides):.1f}-{max(x[2] for x in rides):.1f} s)")


if __name__ == "__main__":
    main()
