"""Boarder flees and boarding that never take (live Avalanche CTF, trace_h3_sidewinder_20261031-064500, master 5008de4:
ground-vehicle stalls 552 s in 9 min, 216 s of them "vehicle: away from a boarder"; logs/tmp/stalls.py of wt/flight).
The frame at 150.3 s: xXSentinelXx (#1, team 0) in a Warthog at (-24.36, -29.12, -4.49) by red's base, yaw 2.23;
xXJackalXx's teammate #7 (team 1) on foot 1.34 u off at (-24.56, -30.44, -4.46), its goal "board" on that Warthog
5,768 rows (about 200 s), never aboard:

1. the driver, pinned (it never moves, as against the garage wall): it flees at most once in a row, then fights for
   FLEE_REST s; its flee heads by the vehicle's nav, not straight away from him. Prints the flee seconds of 20 s, the
   old play (straight away, every 1.2 s) and now
2. the boarder: Use beside the seat that does not take, given up after BOARD_GIVE_UP s, and that Warthog not offered
   again for BOARD_BAN s (board_check)
3. a driver in a seat runs no anti-vehicle errand (vehicle_mission)

usage: python -I test_flee_stall.py      -> "flee stall OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import bot as B  # noqa: E402
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_sidewinder")
T = terrain(M)
CAR, YAW, BOARDER, H = Vec(-24.36, -29.12, -4.49), 2.23, Vec(-24.56, -30.44, -4.46), 3799908367
HOG = dict(handle=H, kind="warthog_snow", pos=(CAR.x, CAR.y, CAR.z), riders=1, occupied=True, team=0,
           fwd=(math.cos(YAW), math.sin(YAW), 0.0), up=(0.0, 0.0, 0.99), gunner=False, turrets=[], manned=[])


def driver():
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b._terrain = T
    b.seat, b.seat_for, b.seat_since, b.crew_ride = "driver", H, 0.0, H
    b.order, b.drive_to = Order("mid", M["points"]["mid"]), M["points"]["mid"]
    # (as live at 150.3 s: already fleeing him, cmd forward 1, att evade; not running him down)
    b.threat_first, b.threat_roll = {(7, "away from a boarder"): 0.0}, {(7, "away from a boarder"): True}
    return b


def flee_seconds(b, secs=20.0):
    fled, heads = 0, []
    for k in range(int(secs * 30)):
        t = 100.0 + k / 30
        b.per.beliefs[7] = Belief(BOARDER, Vec(), t, True, "eyes")
        b.per.recognized.add(7)
        b.notes = []
        me = PlayerState(1, 0, "Sentinel", CAR, yaw=YAW, vehicle=H)
        a = Action(yaw=YAW)
        b.drive(t, 1 / 30, me, Snapshot(t, [me, PlayerState(7, 1, "boarder", BOARDER, weapon="battle_rifle",
                                                             weapons=["assault_rifle", "battle_rifle"])], vehicles=[HOG], mode="ctf"),
                a, lambda p, q, **kw: q)
        if b.att and b.att[0] == "evade":
            fled += 1
            heads.append(a.yaw)
    return fled / 30, heads


def main():
    fails = []
    real_open, real_prog = Bot.open_way, B.FLEE_PROGRESS
    Bot.open_way, B.FLEE_PROGRESS = (lambda s, me, away: away), -1.0      # the old play
    old, _ = flee_seconds(driver())
    Bot.open_way, B.FLEE_PROGRESS = real_open, real_prog
    new, heads = flee_seconds(driver())
    if new > 0.4 * old or new > 6.0:
        fails.append(f"pinned by a boarder: fled {new:.1f} of 20 s (old {old:.1f}); want it to stop fleeing a wall")
    away = math.atan2(CAR.y - BOARDER.y, CAR.x - BOARDER.x)
    w = T.vnav(CAR, Vec(CAR.x + 8 * math.cos(away), CAR.y + 8 * math.sin(away), CAR.z))
    want = math.atan2(w.y - CAR.y, w.x - CAR.x)
    if heads and abs(math.atan2(math.sin(heads[0] - want), math.cos(heads[0] - want))) > 0.05:
        fails.append(f"flee heading {heads[0]:.2f}, the vehicle nav's {want:.2f}")
    # 2. the boarder
    b = Bot(7, 1, make_profile("top", "flanker", random.Random(7)), M, random.Random(7))
    b._terrain = T
    b.goal, b.next_decide = ("board", H), 1e9
    gave = None
    drv = PlayerState(1, 0, "Sentinel", CAR, vehicle=H)
    for k in range(int(8 * 30)):
        t = 100.0 + k / 30
        me = PlayerState(7, 1, "boarder", BOARDER)
        b.think(t, 1 / 30, Snapshot(t, [me, drv], vehicles=[HOG], mode="ctf"), T.los, T.nav, [])
        if getattr(b, "board_ban", {}).get(H, 0.0) > t:
            gave = t - 100.0
            break
    if gave is None or gave > B.BOARD_GIVE_UP + 0.5:
        fails.append(f"the boarder at the seat: gave up after {gave} s (want about {B.BOARD_GIVE_UP})")
    scores = {}
    b.notes = []
    b.board_check(PlayerState(7, 1, "boarder", BOARDER), Snapshot(110.0, [PlayerState(7, 1, "boarder", BOARDER), drv],
                                                                  vehicles=[HOG], mode="ctf"), scores)
    if any(k[0] == "board" for k in scores):
        fails.append("the given-up Warthog was offered for boarding again within BOARD_BAN")
    # 3. a driver runs no launcher errand
    d = driver()
    d.notes = []
    me = PlayerState(1, 0, "Sentinel", CAR, vehicle=H, weapons=["assault_rifle"])
    d.per.beliefs[7] = Belief(BOARDER, Vec(), 100.0, True, "eyes")
    d.vehicle_mission(100.0, me, Snapshot(100.0, [me, PlayerState(7, 1, "t", BOARDER, vehicle=55)],
                                         vehicles=[HOG, dict(HOG, handle=55, kind="scorpion", team=1)], mode="ctf"), {})
    if d.mission_keys:
        fails.append(f"a driver in his seat went for a launcher: {d.mission_keys}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"flee stall OK (frame 150.3 s: fled {old:.1f} of 20 s before, {new:.1f} now; the boarder gave up after "
          f"{gave:.1f} s)")


if __name__ == "__main__":
    main()
