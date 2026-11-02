"""Map brain INTER-TELE-03 (Bot.came_through): a bot that comes out of a teleporter with a man it saw a moment ago
behind it, at the pad it went in by, steps off the exit and stands watching it for 3 s, because the chaser may follow;
then it goes on. INTER-TELE-01 (Bot.pad_held): it does not step onto a teleporter into a man known at its exit: it
walks the way round, or with none (no more than 2.5 times as long) stands short of the pad, 6 s at most. On Blood
Gulch's first teleporter (its commands moved at 2.25 u/s):

1. a Normal bot chased through (out facing away, the way it goes): stops 2-5 u off the exit within 1.5 s and faces
   it (within 20 degrees) from 1 to 3 s
2. ... and walks on after the 3 s
3. nobody behind: it walks straight on
4. Easy, chased: walks on (Easy never plans)
5. the man known is ahead, near the exit (a hunt): walks on
6. the chaser comes out of the exit 1.5 s later: the watch ends and it is shooting at him within 1 s
7. on its way through the pad (its goal past the exit) with a man at the exit on its radar: it takes the way round
   (the walk over the gulch: never on the pad, never a stop, 15+ u off the pad at 16 s); as well with a man 10-18 u
   off the exit who sees it; with no short way round (on the pad's platform, its goal just past the exit) it stands
   5 s or more 2+ u short of the pad, then goes through
8. ... nobody at the exit: through without a stop; Easy with the man there: through as well

usage: python -I test_tele_watch.py      -> "tele watch OK"
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

M = get_map("bloodgulch")
T = terrain(M)
DT = 1 / 30


def run(tier, chaser=None, known=None, follows=None, secs=5.0):
    """The bot goes through the pad at t=10 and retreats to the gulch floor 15 u off the exit; per tick (t after the exit,
    distance to the exit, speed, yaw off the exit, watching, firing). chaser: a man standing there (seen from the pad),
    known: a man last seen there 0.5 s before, follows: the chaser comes out of the exit then. Sight goes 20 u (the pads
    are 43 u apart: out of each other's sight)."""
    a, b = M["teleporters"][0]
    goal = Vec(b.x - 15.0, b.y, T.nav_z(b.x - 15.0, b.y))       # open gulch floor
    bot = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), M, random.Random(1))
    bot._terrain = T
    bot.goal, bot.next_decide = ("retreat", goal), 1e9
    if known is not None:
        bot.per.beliefs[7] = Belief(pos=known, vel=Vec(), t=9.5, seen=True, source="eyes")
    pos, yaw, vel, t, rows = a, 0.0, Vec(), 9.0, []
    nav = lambda p, q, **k: T.nav(p, q, **k)
    pre = round(1.0 / DT)                             # 1 s on the pad first (time to notice the chaser)
    for k in range(pre + int(secs / DT) + 1):
        if k == pre:
            pos = b                                   # the teleporter puts it at the exit, facing the way it goes
            yaw = math.atan2(goal.y - b.y, goal.x - b.x)
        me = PlayerState(1, 0, "bot", pos, vel=vel, yaw=yaw)
        out = follows is not None and t >= 10.0 + follows
        men = [me] + ([PlayerState(7, 1, "chaser", b if out else chaser)] if chaser is not None else [])
        act = bot.think(t, DT, Snapshot(t, men), lambda p, q: (p - q).flat() < 20.0, nav, [])
        if k >= pre:
            to = math.atan2(b.y - pos.y, b.x - pos.x)
            rows.append((t - 10.0, (pos - b).flat(), vel.flat(), abs(math.atan2(math.sin(act.yaw - to), math.cos(act.yaw - to))),
                         bot.tele_watching(t) is not None, act.fire))
        yaw = act.yaw
        if k >= pre:                                  # walk where it says, on the ground
            w, sp = act.yaw + math.atan2(act.strafe, act.forward), min(1.0, math.hypot(act.forward, act.strafe)) * 2.25
            n = pos + Vec(math.cos(w), math.sin(w), 0.0) * (sp * DT)
            n = Vec(n.x, n.y, T.nav_z(n.x, n.y))
            vel, pos = (n - pos) * (1 / DT), n
        t += DT
    return rows, b


def walk(tier, camper, secs=16.0, start=None, goal=None):
    """From start (5 u off the pad) to goal (10 u past the exit; its route: round the base, up the pad's ramp), on the
    floor at its own height; camper: a man at the exit on its radar all along (a Vec: a man there). (when it went
    through, its longest stop in s, the nearest it stood to the pad, how far off the pad it ended)"""
    a, b = M["teleporters"][0]
    at = camper if isinstance(camper, Vec) else b + Vec(1.0, 0.0, 0.0)
    bot = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), M, random.Random(1))
    bot._terrain = T
    goal = goal or Vec(b.x - 10.0, b.y, T.nav_z(b.x - 10.0, b.y))
    bot.goal, bot.next_decide = ("hunt", goal), 1e9
    bot.detour_key, bot.detour_pt = ("hunt", round(goal.x), round(goal.y)), None   # by the shortest way (Bot.detour)
    pos, yaw, vel, t = start or Vec(a.x, a.y + 5.0, T.nav_z(a.x, a.y + 5.0)), 0.0, Vec(), 0.0
    through, stop, longest, near = None, 0.0, 0.0, 99.0
    nav = lambda p, q, **k: T.nav(p, q, **k)
    while t < secs and through is None:
        men = [PlayerState(1, 0, "bot", pos, vel=vel, yaw=yaw)]
        if camper:
            men.append(PlayerState(9, 1, "camper", at))
            bot.per.beliefs[9] = Belief(pos=at, vel=Vec(), t=t, seen=False, source="radar")
        act = bot.think(t, DT, Snapshot(t, men), lambda p, q: (p - q).flat() < 20.0, nav, [])
        yaw = act.yaw
        w, sp = act.yaw + math.atan2(act.strafe, act.forward), min(1.0, math.hypot(act.forward, act.strafe)) * 2.25
        n = pos + Vec(math.cos(w), math.sin(w), 0.0) * (sp * DT)
        l, j, i = T._node(Vec(n.x, n.y, pos.z + 0.3))     # the floor at its own height (on the pad, not under it)
        n = Vec(n.x, n.y, float(T.lz[l, j, i]))
        vel, pos = (n - pos) * (1 / DT), n
        stop = stop + DT if sp == 0.0 and t > 0.5 else 0.0
        if stop:
            longest, near = max(longest, stop), min(near, (pos - a).flat())
        if (pos - a).flat() < 0.75 and abs(pos.z - a.z) < 1.0:
            through = t                                   # on the pad's top: the teleporter takes it
        t += DT
    return through, longest, near, (pos - a).flat()


def main():
    fails = []
    a, b = M["teleporters"][0]
    chaser = a + Vec(2.0, 0.0, 0.0)
    rows, _ = run("average", chaser)
    stop = next((r for r in rows if r[0] > 0.3 and r[2] < 0.05), None)
    if stop is None or stop[0] > 1.5 or not 2.0 <= stop[1] <= 5.0:
        fails.append(f"chased through, Normal: stopped {stop and (round(stop[0], 2), round(stop[1], 2))} "
                     f"(want within 1.5 s, 2-5 u off the exit)")
    mid = [r for r in rows if 1.0 <= r[0] <= 3.0]
    facing = sum(r[3] < math.radians(20) for r in mid) / max(1, len(mid))
    if facing < 0.9:
        fails.append(f"chased through, Normal: faced the exit {facing:.0%} of 1-3 s (want 90%+)")
    if not any(r[0] > 3.2 and r[2] > 1.0 for r in rows):
        fails.append("chased through, Normal: never walked on after the 3 s")
    for label, rws in (("nobody behind", run("average")[0]), ("Easy, chased", run("novice", chaser)[0]),
                       ("the man ahead at the exit", run("average", known=b + Vec(3.0, 0.0, 0.0))[0])):
        if any(r[4] for r in rws) or max(r[1] for r in rws if r[0] <= 2.5) < 4.5:
            fails.append(f"{label}: watched or held near the exit (farthest {max(r[1] for r in rws if r[0] <= 2.5):.1f} u "
                         f"in 2.5 s; want walking on)")
    rows, _ = run("average", chaser, follows=1.5)
    shot = next((r[0] for r in rows if r[0] >= 1.5 and r[5]), None)
    if any(r[4] for r in rows if r[0] >= 2.5) or shot is None or shot > 2.5:
        fails.append(f"the chaser out of the exit at 1.5 s: first shot at {shot} s (want by 2.5), still watching after 2.5 s: "
                     f"{any(r[4] for r in rows if r[0] >= 2.5)}")
    through, longest, near, left = walk("average", True)
    if through is not None or longest > 1.0 or left < 15.0:
        fails.append(f"a man at the exit: through at {through}, longest stop {longest:.1f} s, {left:.1f} u off the pad at "
                     f"16 s (want the way round: never on the pad, no stop, 15+ u off it)")
    # ... and a man 10-18 u off the exit with a line of sight onto it (INTER-LIFT-01's "holds a sightline onto it")
    watcher = None
    for r in (10.0, 14.0, 18.0):
        for k in range(16):
            x, y = b.x + r * math.cos(k * math.pi / 8), b.y + r * math.sin(k * math.pi / 8)
            q = Vec(x, y, T.nav_z(x, y))
            if watcher is None and T.los(q, b):
                watcher = q
    th, lg, _, lf = walk("average", watcher) if watcher is not None else (0.0, 0.0, 0.0, 0.0)
    if th is not None or lg > 1.0 or lf < 15.0:
        fails.append(f"a man {watcher and round((watcher - b).flat(), 1)} u off watching the exit: through at {th}, "
                     f"longest stop {lg:.1f} s, {lf:.1f} u off the pad at 16 s (want the way round)")
    for label, tier, camper in (("nobody at the exit", "average", False), ("Easy, a man at the exit", "novice", True)):
        th, lg, _, _ = walk(tier, camper)
        if th is None or lg > 1.0:
            fails.append(f"{label}: through at {th}, longest stop {lg:.1f} s (want through, no stop)")
    # ... no short way round (on the pad's platform, its goal 3 u past the exit: 8 u through the pad, 61 u walking):
    # it stands short of the pad, 6 s at most, then goes through
    deck = Vec(a.x - 3.5, a.y - 2.0, T.nav_z(a.x - 3.5, a.y - 2.0, a.z))
    past = Vec(b.x, b.y + 3.0, T.nav_z(b.x, b.y + 3.0, b.z + 0.5))
    waited, wlg, wnear, _ = walk("average", True, 16.0, deck, past)
    if wlg < 5.0 or wnear < 2.0 or waited is None:                 # (its first 0.5 s of standing is not counted)
        fails.append(f"a man at the exit, no short way round: stood {wlg:.1f} s, {wnear:.1f} u off the pad, through at "
                     f"{waited} (want 5+ s, 2+ u off, then through)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"tele watch OK (Blood Gulch: stopped {stop[1]:.1f} u off the exit at {stop[0]:.2f} s, faced it {facing:.0%} of 1-3 s, "
          f"shot the chaser {shot - 1.5:.2f} s after he came out; a man at the exit: the way round, {left:.1f} u off the "
          f"pad at 16 s; with none, stood {wlg:.1f} s {wnear:.1f} u short of the pad, through at {waited:.1f} s)")


if __name__ == "__main__":
    main()
