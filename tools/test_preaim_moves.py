"""More strafing, more jumps, pre-aim (brain/bot.py). Decision-level checks
no game:
1. jumps: a Legendary bot running out of a fight hops 18+ times a minute of running as a rusher, 9+ as a sniper (0.24
   x (0.4 + jumpiness) a second before: 14.4 and 7.2)
2. strafing: in a fight at 6 u it is side-stepping on 75%+ of the ticks (the 40% pauses of 0.25-0.5 s at a turn left
   about 60%); it plants its feet only past 10 u
3. gunfire: an unseen enemy whose magazine goes down within 30 u becomes a belief ("heard") for Normal and up, not for
   Easy, and never over a hit a moment ago (that turns the bot on its shooter)
4. pre-aim behind cover (seen, heard or called out): on real maps, of men walking round to a bot from behind cover,
   share with the bot's aim on them the moment they come into view (the measure's rule, tools/player_stats.py:
   within max(0.12 rad, atan(0.6 / d))), against aiming straight at his bearing through the wall
5. pre-aim on the move (nobody known): of men standing round the corner of a bot's route, share it has its aim on
   when they come into view, against the old look 8 u down the next waypoint
Fails on the code before (fewer hops, the pauses, no heard gunfire, no edge or route pre-aim).

usage: python -I test_preaim_moves.py      -> "pre-aim and moves OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np  # noqa: E402
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, angles_to, eye, wrap  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAPS = ("reach_30_settlement", "h3_construct")


def bot(m, tier="top", pers="rusher", seed=3):
    b = Bot(1, 0, make_profile(tier, pers, random.Random(seed)), m, random.Random(seed))
    b.can_pickup = False
    return b


def on_aim(src, look, target):
    """The measure's rule: is the view from src's eye toward look (aimed 0.35 over it) on target's chest?"""
    e = eye(src)
    y1, p1 = angles_to(e, look + Vec(0, 0, 0.35))
    y2, p2 = angles_to(e, target + Vec(0, 0, 0.35))
    d = math.dist((e.x, e.y, e.z), (target.x, target.y, target.z + 0.35))
    return math.hypot(wrap(y1 - y2), p1 - p2) < max(0.12, math.atan2(0.6, max(d, 0.1)))


def hops(m, pers, seconds=120.0):
    b, t, n = bot(m, pers=pers), 0.0, 0
    A = m["spawns"]["slayer"][0][0]
    goal = A + Vec(30.0, 0.0, 0.0)
    T = terrain(m)
    nav = lambda p, q, **k: T.nav(p, q, **k)
    while t < seconds:
        me = PlayerState(1, 0, "bot", A, vel=Vec(2.6, 0.0, 0.0), alive=True)
        b.order.point = goal
        a = b.think(t, 1 / 30, Snapshot(t, [me]), lambda p, q: True, nav, [])
        n += bool(a.jump)
        t += 1 / 30
    return n / (seconds / 60.0)


def fight(m, d, seconds=20.0, seed=4):
    b = bot(m, seed=seed)
    A = m["spawns"]["slayer"][0][0]
    t, yaw, side, ticks = 0.0, 0.0, 0, 0
    while t < seconds:
        me = PlayerState(1, 0, "bot", A, yaw=yaw, alive=True, weapon="assault_rifle", weapons=["assault_rifle"])
        foe = PlayerState(2, 1, "human", A + Vec(d, 0.0, 0.0), alive=True, yaw=math.pi)
        a = b.think(t, 1 / 30, Snapshot(t, [me, foe]), lambda p, q: True, lambda p, q, **k: q, [])
        yaw = a.yaw
        if t > 2.0 and not any("unstuck" in n for n in b.notes):   # (held in place here: the wiggle steers anyhow)
            ticks += 1
            side += abs(a.strafe) >= 0.5
        t += 1 / 30
    return side / max(ticks, 1)


def walkable_nodes(T, rng, n):
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    pick = rng.sample(range(len(ls)), min(n, len(ls)))
    return [T._center(int(ls[k]), int(js[k]), int(is_[k])) for k in pick]


def behind_cover(m, rng, tries=400):
    """(new share, old share, cases): men coming round cover toward a bot that holds a belief of them."""
    T = terrain(m)
    new = old = cases = 0
    nodes = walkable_nodes(T, rng, 1200)
    for _ in range(tries):
        A, B = rng.choice(nodes), rng.choice(nodes)
        dab = (B - A).flat()
        if not 6.0 < dab < 25.0 or abs(B.z - A.z) > 1.5 or T.los(A, B):
            continue
        path = T.path_ahead(B, A, n=200)
        q = next((p for p in path if T.los(A, p)), None)     # where he comes into view
        if q is None or (q - A).flat() < 3.0:
            continue
        b = bot(m, seed=cases)
        b.now = 10.0
        b.per.beliefs[2] = Belief(B, Vec(), 10.0, False, "heard")
        me = PlayerState(1, 0, "bot", A, alive=True)
        look = b.look_point(me, A, lambda p, qq, **k: T.nav(p, qq, **k), None)
        cases += 1
        new += on_aim(me, look, q)
        old += on_aim(me, B, q)                              # straight at his bearing, through the wall
    return new / max(cases, 1), old / max(cases, 1), cases


def round_corner(m, rng, tries=400):
    """(new share, old share, cases): men standing by a bot's route, out of sight, when they come into view as it walks."""
    T = terrain(m)
    new = old = cases = 0
    nodes = walkable_nodes(T, rng, 1200)
    for _ in range(tries):
        A, G = rng.choice(nodes), rng.choice(nodes)
        if (G - A).flat() < 20.0:
            continue
        route = T.path_ahead(A, G, n=160)
        if len(route) < 60:
            continue
        E = route[rng.randrange(40, len(route))]
        E = Vec(E.x + rng.uniform(-1.0, 1.0), E.y + rng.uniform(-1.0, 1.0), E.z)
        if T.los(A, E):
            continue
        b = bot(m, pers="flanker", seed=cases)
        prev = A
        for k, p in enumerate(route[::2]):
            if T.los(p, E):
                if (E - p).flat() < 2.0:
                    break
                vel = Vec(p.x - prev.x, p.y - prev.y, 0.0)
                me = PlayerState(1, 0, "bot", prev, vel=vel.norm() * 2.0 if vel.flat() > 1e-6 else Vec(), alive=True)
                b.now = 5.0 + k
                look = b.route_lead(me, G)
                w = T.nav(prev, G, jump=True, human=True)
                cases += 1
                new += look is not None and on_aim(me, look, E)
                old += on_aim(me, b.ahead(me, w) - Vec(0, 0, 0.35) + Vec(0, 0, 0.35), E)
                break
            prev = p
    return new / max(cases, 1), old / max(cases, 1), cases


def main():
    fails = []
    m0 = get_map(MAPS[0])
    # 1. jumps
    for pers, want in (("rusher", 18.0), ("sniper", 9.0)):
        got = hops(m0, pers)
        if got < want:
            fails.append(f"{pers} running hops {got:.1f} a minute of running (want {want}+)")
    # 2. strafing
    share = fight(m0, 6.0)
    if share < 0.75:
        fails.append(f"fight at 6 u: side-stepping on {share:.0%} of ticks (want 75%+)")
    # 3. gunfire heard
    for tier, want in (("top", True), ("novice", False)):
        b = bot(m0, tier=tier)
        me = PlayerState(1, 0, "bot", Vec(0, 0, 0), yaw=0.0, alive=True)
        got = False
        for k, mag in enumerate((32, 31, 30)):
            foe = PlayerState(2, 1, "human", Vec(-12.0, 0.0, 0.0), alive=True, weapon="assault_rifle",
                              weapons=["assault_rifle"], mag=[mag])
            b.per.update(1.0 + k * 0.1, me, Snapshot(1.0, [me, foe]), lambda p, q: False, [])
            got = got or (2 in b.per.beliefs and b.per.beliefs[2].source == "heard")
        if got != want:
            fails.append(f"{tier}: gunfire 12 u behind a wall {'heard' if got else 'not heard'} (want {want})")
    b = bot(m0)
    me = PlayerState(1, 0, "bot", Vec(0, 0, 0), alive=True)
    b.per.beliefs[2] = Belief(Vec(-12.0, 0, 0), Vec(), 1.0, False, "hit")
    for k, mag in enumerate((32, 31)):
        foe = PlayerState(2, 1, "human", Vec(-12.0, 0.0, 0.0), alive=True, weapon="assault_rifle", weapons=["assault_rifle"],
                          mag=[mag])
        b.per.hurt_by = lambda *a: None
        b.per.update(1.0 + k * 0.1, me, Snapshot(1.0, [me, foe]), lambda p, q: False, [])
    if b.per.beliefs[2].source != "hit":
        fails.append("gunfire replaced a hit a moment ago (the bot would not turn on its shooter)")
    # 4, 5. pre-aim on real maps
    lines, corner = [], [0.0, 0.0, 0]
    for name in MAPS:
        m = get_map(name)
        n4, o4, c4 = behind_cover(m, random.Random(7))
        n5, o5, c5 = round_corner(m, random.Random(8))
        lines.append(f"{name}: behind cover {n4:.0%} (straight at him {o4:.0%}, {c4} men); round the route's corner "
                     f"{n5:.0%} (old look {o5:.0%}, {c5} men)")
        if c4 < 20 or n4 < max(0.5, o4 + 0.2):
            fails.append(f"{name}: behind cover pre-aimed {n4:.0%} of {c4} men, straight at his bearing {o4:.0%}")
        corner = [corner[0] + n5 * c5, corner[1] + o5 * c5, corner[2] + c5]
    n5, o5 = corner[0] / max(corner[2], 1), corner[1] / max(corner[2], 1)
    lines.append(f"round the route's corner, both maps: {n5:.0%} (old look {o5:.0%}, {corner[2]} men)")
    if corner[2] < 40 or n5 < o5 + 0.1:            # (Construct alone gives too few men to tell: 22)
        fails.append(f"round the route's corner pre-aimed {n5:.0%} of {corner[2]} men, old look {o5:.0%}")
    print("\n".join(lines))
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print("pre-aim and moves OK")


if __name__ == "__main__":
    main()
