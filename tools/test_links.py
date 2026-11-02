"""Offline check: a jump a person landed (a LiDAR link) is used by bots. On real level data (H2A
Zenith) find two floors a short jump apart that are a long walk apart, add that jump as a
person's link, and check: the nav offers it (with the run-up) to bots that jump, not to bots that
never jump, and Bot.move_to goes to the run-up spot, runs through the take-off and jumps.

usage: python -I test_links.py      -> "links OK"
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import Terrain  # noqa: E402


def find_gap(T, rng):
    """(take-off node, landing node): floors 1-2.5 units apart, the landing lower or level, where
    walking costs more than 12 (or is impossible)."""
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    for _ in range(4000):
        k = rng.randrange(len(ls))
        src = (int(ls[k]), int(js[k]), int(is_[k]))
        dj, di = rng.randint(-10, 10), rng.randint(-10, 10)
        if not 16 <= dj * dj + di * di <= 100:
            continue
        j, i = src[1] + dj, src[2] + di
        if not (0 <= j < T.nh and 0 <= i < T.nw):
            continue
        for l in range(T.L):
            if T.lwalk[l, j, i] and T.reach[l, j, i] and -2.5 <= T.lz[l, j, i] - T.lz[src] <= 0.0:
                dst = (l, j, i)
                walk = T._field(T._center(*dst))[src]
                if walk > 12:
                    return src, dst
    return None


def main():
    m = get_map("h2a_ca_ascension")
    T = Terrain(m["heightmap"], m["bases"])             # a fresh copy: the shared one stays as is
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    gap = find_gap(T, random.Random(5))
    assert gap, "no test gap found on Zenith"
    src, dst = gap
    a, b = T._center(*src), T._center(*dst)
    d = Vec(b.x - a.x, b.y - a.y, 0)
    run = a - d * (0.8 / d.flat())
    link = dict(take_off=[a.x, a.y, a.z], land=[b.x, b.y, b.z], runup=[run.x, run.y, a.z], human=1, bot_ok=0, bot_fail=0)
    walk_cost = T._field(b)[src]
    assert T.add_human_links([link]) == 1, "link not added"
    fails = []
    near = a + Vec(0.3, 0.0, 0.0)
    w = T.nav(near, b, human=True)
    if not hasattr(w, "sx"):
        fails.append(f"nav(human=True) did not offer the jump (walk cost {walk_cost:.1f})")
    elif math.isnan(w.rx) or math.hypot(w.rx - run.x, w.ry - run.y) > 0.01:
        fails.append("the jump came without its run-up")
    if hasattr(T.nav(near, b), "sx"):
        fails.append("a bot that never jumps was offered the jump")
    # Bot.move_to: run-up first, then the take-off, then jump
    bot = Bot(1, 0, make_profile("average", "rusher", random.Random(1)), m, random.Random(1))
    nav = lambda p, q, **k: T.nav(p, q, **k)
    def step(pos):
        me = PlayerState(1, 0, "bot", pos, yaw=0.0)
        act = Action(yaw=0.0)
        bot.move_to(me, b, act, nav)
        return act
    far = a + d * (1.0 / d.flat())                       # past the take-off, toward the landing
    act = step(far)
    off = math.atan2(act.strafe, act.forward) - math.atan2(run.y - far.y, run.x - far.x)
    if act.jump or abs((off + math.pi) % (2 * math.pi) - math.pi) > 0.3:
        fails.append("move_to did not head for the run-up first")
    step(Vec(run.x, run.y, a.z))                          # at the run-up: done
    act = step(a + d * (-0.4 / d.flat()))                 # running in, 0.4 before the take-off
    if act.jump:
        fails.append("jumped before the take-off")
    act = step(a + d * (0.05 / d.flat()))                 # at the take-off
    if not act.jump:
        fails.append("did not jump at the take-off")
    fails += possession_check(T, near)
    fails += ways_check(m)
    fails += cover_check(m)
    fails += crouch_checks(m)
    fails += route_check(m)
    fails += frontier_check(m)
    fails += pocket_check()
    fails += feature_check()
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print(f"links OK (a {math.hypot(d.x, d.y):.1f}-unit jump that saves a {walk_cost:.0f}-unit walk)")


def cover_check(m):
    """LiDAR paint and walls: paint spreads around a player over connected floor and stops at an edge;
    upright walls are found; a bot backing off from a threat beyond a wall picks a spot that wall
    shields (the threat cannot see it)."""
    sys.path.insert(0, HERE)
    import lidar
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    rec = lidar.Recorder(m["name"], count_run=False, T=T)
    rec.walk, rec.events, rec.cover_spots = {}, [], {}
    fails = []
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    rng = random.Random(6)
    edge = None
    for _ in range(4000):                          # a floor cell next to the void
        k = rng.randrange(len(ls))
        l, j, i = int(ls[k]), int(js[k]), int(is_[k])
        if 0 < i < T.nw - 1 and not np.isfinite(T.lz[:, j, i + 1]).any():
            edge = (l, j, i)
            break
    if edge:
        c = T._center(*edge)
        rec.spread((c.x, c.y, c.z))
        void_x = T.x0 + (edge[2] + 1.5) * 0.25
        if any(abs(k[0] * 0.25 - void_x) < 0.13 and abs(k[1] * 0.25 - c.y) < 0.13 and k[3] == lidar.KIND_SPREAD for k in rec.walk):
            fails.append("paint spread past an edge into the void")
    for _ in range(600):
        k = rng.randrange(len(ls))
        c = T._center(int(ls[k]), int(js[k]), int(is_[k]))
        rec.spread((c.x, c.y, c.z))
    walls = sum(1 for k in rec.walk if k[3] == lidar.KIND_WALL)
    if walls == 0 or not rec.cover_spots:
        return fails + ["no upright walls found on Zenith"]
    T.cover_spots = np.array(sorted(rec.cover_spots.values()), dtype=float)
    bot = Bot(3, 0, make_profile("strong", "camper", random.Random(3)), m, random.Random(3))
    bot._terrain = T
    tested = 0
    for x, y, z, dx, dy in T.cover_spots[:400]:
        spot = Vec(x, y, z)
        threat = Vec(x + dx * 2.5, y + dy * 2.5, z)
        me_pos = Vec(x - dx * 2.0, y - dy * 2.0, z)
        if T.los(threat, spot) or not T.walkable(me_pos):
            continue
        tested += 1
        got = bot.cover_from(PlayerState(3, 0, "bot", me_pos), [threat])
        if got is None or T.los(threat, got):
            fails.append("a bot backing off did not pick a spot the wall shields")
        break
    if not tested:
        fails.append("no wall with a threat behind it to test")
    return fails


def ways_check(m):
    """Two-way / one-way: a level gap that is a long walk around is offered back the other way too; a
    big drop is not offered back up."""
    from brain.terrain import jump_ways
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    rng, found = random.Random(11), {}
    for _ in range(8000):
        k = rng.randrange(len(ls))
        src = (int(ls[k]), int(js[k]), int(is_[k]))
        dj, di = rng.randint(-10, 10), rng.randint(-10, 10)
        j, i = src[1] + dj, src[2] + di
        if not (25 <= dj * dj + di * di <= 100 and 0 <= j < T.nh and 0 <= i < T.nw):
            continue
        for l in range(T.L):
            if not (T.lwalk[l, j, i] and T.reach[l, j, i]):
                continue
            dz = T.lz[l, j, i] - T.lz[src]
            kind = "level" if abs(dz) < 0.2 else "drop" if dz < -2.0 else None
            if kind and kind not in found and T._field(T._center(l, j, i))[src] > 12 and T._field(T._center(*src))[(l, j, i)] > 12:
                a, b = T._center(*src), T._center(l, j, i)
                link = dict(take_off=[a.x, a.y, a.z], land=[b.x, b.y, b.z], human=1, bot_ok=0, bot_fail=0)
                if kind == "drop" or jump_ways(link, T, 1.03) == "two-way":
                    found[kind] = link
        if len(found) == 2:
            break
    fails = []
    for kind, link in found.items():
        T.jump_apex = 1.03                          # H2A, measured by LiDAR
        T.add_human_links([link])
        a, b = Vec(*link["take_off"]), Vec(*link["land"])
        back = T.nav(b + Vec(0.1, 0, 0), a, human=True)
        if kind == "level" and not (hasattr(back, "sx") and math.hypot(back.sx - b.x, back.sy - b.y) < 0.5):
            fails.append("a level gap jump was not offered back the other way")
        if kind == "drop" and hasattr(back, "sx") and math.hypot(back.sx - b.x, back.sy - b.y) < 0.5:
            fails.append("a big drop was offered back up as a jump")
    if len(found) < 2:
        fails.append(f"two-way test spots not found on Zenith ({sorted(found)})")
    return fails


def possession_check(T0, near0):
    """A jump is a way in, never a detour. A recorded "jump" across open floor (walking it is
    cheaper) with a goal straight beyond it: the old rule (jump if the landing is 1.5 closer to
    the goal) took it; the nav must not. The real gap jump must still be offered."""
    m = get_map("h2a_ca_ascension")
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    gap = T0.hjumps[0][2]
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    rng = random.Random(4)
    for _ in range(4000):
        n = rng.randrange(len(ls))
        src = (int(ls[n]), int(js[n]), int(is_[n]))
        dst = (src[0], src[1], src[2] + 12)                    # 3 units east, same storey
        far = (src[0], src[1], src[2] + 36)                    # the goal: 6 more units east
        if far[2] >= T.nw or not (T.lwalk[dst] and T.lwalk[far] and T.reach[far]):
            continue
        if abs(T.lz[dst] - T.lz[src]) > 0.2 or abs(T.lz[far] - T.lz[src]) > 0.3:
            continue
        a, b, g = T._center(*src), T._center(*dst), T._center(*far)
        if T._field(b)[src] > 4.0:                             # not open floor between
            continue
        T.add_human_links([gap, dict(take_off=[a.x, a.y, a.z], land=[b.x, b.y, b.z], human=1, bot_ok=0, bot_fail=0)])
        c = T._field(g, False, True)
        here = T._node(a)
        if not c[T._node(b)] + 1.5 < c[here]:
            continue                                           # the old rule would not have jumped either
        fails = []
        if hasattr(T.nav(a, g, human=True), "sx"):
            fails.append("a bot still took a recorded jump across open floor on its way past")
        if not hasattr(T.nav(near0, Vec(*gap["land"]), human=True), "sx"):
            fails.append("the real gap jump is no longer offered")
        return fails
    return ["no open-floor test spot found on Zenith"]


def far_pair(T, rng):
    """Two floors ~2-3 units apart, same level, a long walk apart: (node, node) or None."""
    ls, js, is_ = np.nonzero(T.lwalk & T.reach)
    for _ in range(6000):
        k = rng.randrange(len(ls))
        src = (int(ls[k]), int(js[k]), int(is_[k]))
        dj, di = rng.randint(-12, 12), rng.randint(-12, 12)
        j, i = src[1] + dj, src[2] + di
        if not (64 <= dj * dj + di * di <= 144 and 0 <= j < T.nh and 0 <= i < T.nw):
            continue
        for l in range(T.L):
            if T.lwalk[l, j, i] and T.reach[l, j, i] and abs(T.lz[l, j, i] - T.lz[src]) < 0.3:
                if T._field(T._center(l, j, i))[src] > 15:
                    return src, (l, j, i)
    return None


def route_check(m):
    """A route recorded with F6: the nav offers it one way only; a bot following it jumps at its
    take-off point and crouches where flagged. Giving the nav the links again (LiDAR does, live)
    keeps a learned spot's cost and does not count people's jumps twice."""
    from brain.terrain import RouteVec, ROUTE_JUMP, ROUTE_CROUCH
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    pair = far_pair(T, random.Random(9))
    if not pair:
        return ["no route test pair found on Zenith"]
    a, b = T._center(*pair[0]), T._center(*pair[1])
    path = [[a.x + (b.x - a.x) * t / 8, a.y + (b.y - a.y) * t / 8, a.z + (b.z - a.z) * t / 8, 0] for t in range(9)]
    path[3][3], path[6][3], path[7][3] = ROUTE_JUMP, ROUTE_CROUCH, ROUTE_CROUCH
    link = dict(kind="route", take_off=path[0][:3], land=path[-1][:3], path=path, human=1, bot_ok=0, bot_fail=0)
    T.add_human_links([link])
    fails = []
    there, back = T.nav(a + Vec(0.2, 0, 0), b, human=True), T.nav(b + Vec(0.2, 0, 0), a, human=True)
    if not isinstance(there, RouteVec):
        return [f"a recorded route was not offered ({type(there).__name__})"]
    if isinstance(back, RouteVec):
        fails.append("a recorded route was offered back the other way")
    bot = Bot(4, 0, make_profile("novice", "rusher", random.Random(4)), m, random.Random(4))
    bot._terrain, bot.now = T, 0.0
    nav = lambda p, q, **k: T.nav(p, q, **k)
    def step(q):
        act = Action(yaw=0.0)
        bot.move_to(PlayerState(4, 0, "bot", Vec(*q[:3]), yaw=0.0), b, act, nav)
        return act
    if step(path[0]).jump or step(path[1]).jump:
        fails.append("jumped before the route's take-off")
    if not step(path[3]).jump:
        fails.append("did not jump at the route's take-off point")
    if not step(path[5]).crouch:
        fails.append("did not crouch where the route was crouched")
    # live re-add: a learned spot keeps its cost
    spot = T._center(*pair[0])
    T.learn_stuck(spot, sure=True)
    n = (pair[0][0] * T.nh + pair[0][1]) * T.nw + pair[0][2]
    T.add_human_links([link])
    g = T.graph_h_to
    if g.indptr[n + 1] > g.indptr[n] and g.data[g.indptr[n]:g.indptr[n + 1]].min() < T.STUCK_COST:
        fails.append("giving the nav its links again lost a learned spot")
    # and on a CE map (jump graph): people's jump edges do not add up call after call
    bg = get_map("bloodgulch")
    TB = Terrain(bg["heightmap"], bg["bases"])
    TB.build_jumps()
    ls, js, is_ = np.nonzero(TB.lwalk)
    src = (int(ls[0]), int(js[0]), int(is_[0]))
    dst = next(((l, j, i) for l, j, i in zip(ls, js, is_) if abs(j - src[1]) + abs(i - src[2]) >= 8), None)
    ca, cb = TB._center(*src), TB._center(*map(int, dst))
    jl = dict(take_off=[ca.x, ca.y, ca.z], land=[cb.x, cb.y, cb.z], human=1, bot_ok=0, bot_fail=0)
    ids = ((src[0] * TB.nh + src[1]) * TB.nw + src[2], (int(dst[0]) * TB.nh + int(dst[1])) * TB.nw + int(dst[2]))
    TB.add_human_links([jl])
    w1 = TB.graph_jump[ids]
    TB.add_human_links([jl])
    if TB.graph_jump[ids] != w1:
        fails.append(f"a person's jump edge grew when the links were given again ({w1:.2f} -> {TB.graph_jump[ids]:.2f})")
    return fails


def frontier_check(m):
    """LiDAR Roombas explore by the nav: the goal is unexplored floor the bot can walk to, a second
    Roomba picks a goal away from the first one's, and the bot heads along the nav's path to it."""
    sys.path.insert(0, HERE)
    import lidar
    lidar.PROBE_P = 0.0                             # nav goals only here (probe_check below)
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    rec = lidar.Recorder(m["name"], count_run=False, T=T)
    rec.walk, rec.cover, rec.fall_grid, rec.targets, rec.links, rec.floor_keys = {}, set(), {}, {}, [], set()
    sp = m["spawns"]["slayer"][0][0]
    c = T._center(*T._node(sp))
    pos = (c.x, c.y, c.z)
    for dx in range(-10, 11):                       # 10 units around the start, every storey: painted already
        for dy in range(-10, 11):
            for dz in range(-10, 11):
                rec.cover.add((int((c.x + dx) // 1), int((c.y + dy) // 1), int(c.z // 1) + dz))
    fails = []
    r1, r2 = lidar.Roomba(1, random.Random(1)), lidar.Roomba(2, random.Random(2))
    t1 = r1.frontier(pos, rec, T)
    if t1 is None:
        return ["no frontier found on Zenith"]
    r1.pick(0.0, pos, rec, T, None)
    r2.pick(0.0, pos, rec, T, None)
    if math.dist(r1.target[:2], r2.target[:2]) < 8.0:
        fails.append("two Roombas picked goals next to each other")
    if rec.explored(*t1) or not np.isfinite(T._field(Vec(*t1), human=False)[T._node(c)]):
        fails.append(f"a Roomba's goal was explored or out of reach ({t1})")
    from scipy.sparse.csgraph import dijkstra       # and it is near the nearest unexplored floor by path
    l, j, i = T._node(c)
    d = dijkstra(T.graph, directed=True, indices=(l * T.nh + j) * T.nw + i).reshape(T.L, T.nh, T.nw)
    ls, js, is_ = np.nonzero(np.isfinite(d))
    near = min(d[a, b_, e] for a, b_, e in zip(ls, js, is_)
               if not rec.explored(T.x0 + (e + 0.5) * 0.25, T.y0 + (b_ + 0.5) * 0.25, T.lz[a, b_, e]))
    got = d[T._node(Vec(*t1))]
    if not got <= near + 10.0:
        fails.append(f"a Roomba's goal was {got:.0f} units of path away, the nearest unexplored floor {near:.0f}")
    yaw = r1.think(0.1, pos, rec, T, None)[2]
    w = T.nav(c, Vec(*r1.target), human=True)
    want = math.atan2(w.y - c.y, w.x - c.x)
    if abs((yaw - want + math.pi) % (2 * math.pi) - math.pi) > 0.2:
        fails.append("a Roomba did not head along the nav's path")
    return fails + probe_check(lidar)


def probe_check(lidar):
    """Battle Creek: the level data cuts the bases' upper floors off from the ground (steps over
    the nav's limit; people walk up). A probing Roomba picks such floor and walks straight at it."""
    bc = get_map("beavercreek")
    T = Terrain(bc["heightmap"], bc["bases"])
    T.set_spawns([p for mode in bc["spawns"].values() for team in mode.values() for p in team])
    rec = lidar.Recorder("beavercreek", count_run=False, T=T)
    rec.walk, rec.cover, rec.fall_grid, rec.targets, rec.links, rec.floor_keys = {}, set(), {}, {}, [], set()
    c = T._center(*T._node(Vec(2.5, 8.0, -0.2)))     # outside the red base's steps
    pos = (c.x, c.y, c.z)
    lidar.PROBE_P = 1.0
    rb = lidar.Roomba(3, random.Random(3))
    rb.pick(0.0, pos, rec, T, None)
    lidar.PROBE_P = 0.25
    t = rb.target
    if not rb.straight or t[2] < c.z + 0.3 or T.reach[T._node(Vec(*t))]:
        return [f"a probing Roomba did not pick floor the nav cannot reach ({t}, straight {rb.straight})"]
    yaw = rb.think(0.1, pos, rec, T, None)[2]
    if abs((yaw - math.atan2(t[1] - c.y, t[0] - c.x) + math.pi) % (2 * math.pi) - math.pi) > 0.05:
        return ["a probing Roomba did not walk straight at its goal"]
    return []


def pocket_check():
    """Called jumps on real level data: on Battle Creek a bot calls a jump to floor it cannot walk
    to; the simulator's body, jumping from the take-off at full speed, comes down within CALL_XY
    of the call; a made call becomes a link the nav then offers (the floor past it becomes
    reachable)."""
    sys.path.insert(0, HERE)
    import jumpphys
    import lidar
    import lidar_sim
    bc = get_map("beavercreek")
    T = jumpphys.prepare(Terrain(bc["heightmap"], bc["bases"]))
    T.set_spawns([p for mode in bc["spawns"].values() for team in mode.values() for p in team])
    rec = lidar.Recorder("beavercreek", count_run=False, T=T, path=os.devnull)
    rec.links, rec.cover, rec.fall_grid = [], set(), {}
    rec.phys = jumpphys.Phys("ce")
    calls = []
    for k in range(8):
        c = T._center(*T._node(Vec(2.5 + 3 * k, 8.0, -0.2)))
        call = lidar.Roomba(k, random.Random(k)).pocket((c.x, c.y, c.z), rec, T)
        if call:
            calls.append(call)
    if not calls:
        return ["no called jump found on Battle Creek"]
    fails, made = [], 0
    for call in calls:
        a, b = call["take_off"], call["land"]
        d = math.dist(a[:2], b[:2])
        body = lidar_sim.Body(a)
        body.ground = False
        body.v = [(b[0] - a[0]) / d * rec.phys.run, (b[1] - a[1]) / d * rec.phys.run, rec.phys.v0]
        for _ in range(200):
            if body.step(T, rec.phys, (0, 0, 0, 0, 0), 1 / 30, random.Random(0)) or body.ground:
                break
        made += body.ground and math.dist(body.p[:2], b[:2]) < lidar.CALL_XY and abs(body.p[2] - b[2]) < lidar.CALL_Z
    if made < len(calls) * 0.8:
        fails.append(f"only {made} of {len(calls)} called jumps came down on their call")
    call = calls[0]
    rb = lidar.Roomba(0, random.Random(0))
    rb.trial, rb.phase, rb.fly_t = call, "fly", 0.0
    rb.landed(dict(landing=tuple(call["land"]), t0=1.0), None, rec)
    lidar.nav_learn(T, "beavercreek", rec.links)     # what the simulator and the mapper do with a made call
    w = T.nav(Vec(*call["take_off"]) + Vec(0.1, 0, 0), Vec(*call["land"]), human=True)
    if not (call in rec.links and hasattr(w, "sx")):
        fails.append(f"a made call was not offered by the nav (link made {call in rec.links}, got {type(w).__name__})")
    return fails


def feature_check():
    """The map's painted features on H2A Zenith: its placed teleporter pair is in the nav (the
    exporter missed fw_teleporter_*); a LiDAR bot picks the man cannon nobody has ridden; a ride
    it lands becomes a link the nav offers; the simulator replays that ride."""
    sys.path.insert(0, HERE)
    import jumpphys
    import lidar
    import lidar_sim
    from brain.maps import usable_links
    zm = get_map("h2a_ca_ascension")
    fails = []
    kinds = {f["kind"] for f in zm["features"]}
    if not {"weapon", "objective", "teleporter", "launcher", "control", "shield"} <= kinds:
        fails.append(f"Zenith's features miss kinds: {sorted(kinds)}")
    if not zm["teleporters"]:
        return fails + ["Zenith's placed teleporters are not in the nav"]
    T = jumpphys.prepare(Terrain(zm["heightmap"], zm["bases"]))
    T.add_links(zm["teleporters"])
    T.set_spawns([p for mode in zm["spawns"].values() for team in mode.values() for p in team])
    rec = lidar.Recorder("h2a_ca_ascension", count_run=False, T=T, path=os.devnull)
    rec.links = []
    cannon = next(f for f in rec.features if f["kind"] == "launcher")
    c = T._center(*T._node(Vec(*cannon["pos"])))
    near = None
    for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (3, 3), (-3, -3)):
        q = T._center(*T._node(Vec(c.x + dx, c.y + dy, c.z)))
        if abs(q.z - c.z) < 0.5 and math.isfinite(T._field(c)[T._node(q)]):
            near = (q.x, q.y, q.z)
            break
    if near is None:
        return fails + ["no floor to walk to Zenith's man cannon from"]
    go = lidar.Roomba(1, random.Random(1)).interactable(near, rec, T, ("launcher", "lift"))
    if not go or go["kind"] != "ride" or math.dist(go["take_off"][:2], cannon["pos"][:2]) > 0.2:
        fails.append(f"a LiDAR bot did not pick the untested man cannon ({go and go['name']})")
        return fails
    # a made-up landing 6-15 units off that walking reaches only the long way (as a man cannon's does)
    from scipy.sparse.csgraph import dijkstra
    src = T._node(c)
    dwalk = dijkstra(T.graph, directed=True, indices=(src[0] * T.nh + src[1]) * T.nw + src[2]).reshape(T.L, T.nh, T.nw)
    land = None
    for l2, j2, i2 in zip(*np.nonzero(T.lwalk & T.reach)):
        q = T._center(int(l2), int(j2), int(i2))
        dd = math.hypot(q.x - c.x, q.y - c.y)
        if 6 < dd < 15 and dwalk[l2, j2, i2] > 3 * dd + 10:
            land = q
            break
    if land is None:
        return fails + ["no far-by-walking landing near Zenith's man cannon for the test"]
    rb = lidar.Roomba(1, random.Random(1))
    rb.trial, rb.phase, rb.fly_t = go, "fly", 0.0
    rb.landed(dict(landing=(land.x, land.y, land.z), t0=1.0, apex=c.z + 3, air_s=1.5,
                   trail=[(c.x + 6, c.y, c.z + 3)]), None, rec)
    rides = [l for l in rec.links if l.get("ride")]
    if not rides or rides[0] not in usable_links(rec.links):
        return fails + ["a landed ride did not become a usable link"]
    lidar.nav_learn(T, "h2a_ca_ascension", rec.links)
    w = T.nav(Vec(*rides[0]["take_off"]) + Vec(0.1, 0, 0), land, human=True)
    if not hasattr(w, "sx"):
        fails.append(f"the nav does not offer the ride ({type(w).__name__})")
    T.rides = [(l["take_off"], l["path"], l.get("air_s") or 1.5) for l in rides]
    body = lidar_sim.Body(rides[0]["take_off"])
    for _ in range(60):
        body.step(T, jumpphys.Phys("h2a"), (0, 0, 0, 0, 0), 1 / 20, random.Random(0))
        if body.ground and math.dist(body.p[:2], rides[0]["take_off"][:2]) > 2:
            break
    if math.dist(body.p[:2], (land.x, land.y)) > 0.3:
        fails.append(f"the simulator did not replay the ride ({[round(v, 2) for v in body.p]})")
    return fails


def crouch_checks(m):
    """A crouch route people walked: the nav offers it both ways, a bot follows it crouched to the
    end and lets go after; on crouch floor any bot crouches."""
    from brain.terrain import RouteVec, crouch_key
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    fails = []
    pair = far_pair(T, random.Random(8))
    if not pair:
        return ["no crouch test pair found on Zenith"]
    a, b = T._center(*pair[0]), T._center(*pair[1])
    path = [[a.x + (b.x - a.x) * t / 8, a.y + (b.y - a.y) * t / 8, a.z + (b.z - a.z) * t / 8] for t in range(9)]
    T.add_human_links([dict(kind="crouch", take_off=[a.x, a.y, a.z], land=[b.x, b.y, b.z], path=path, human=1, bot_ok=0, bot_fail=0)])
    there, back = T.nav(a + Vec(0.2, 0, 0), b, human=True), T.nav(b + Vec(0.2, 0, 0), a, human=True)
    if not isinstance(there, RouteVec) or not isinstance(back, RouteVec):
        fails.append(f"crouch route not offered both ways ({type(there).__name__}, {type(back).__name__})")
        return fails
    bot = Bot(2, 0, make_profile("novice", "rusher", random.Random(2)), m, random.Random(2))   # Easy: navigation only
    bot._terrain, bot.now = T, 0.0
    nav = lambda p, q, **k: T.nav(p, q, **k)
    def step(pos):
        act = Action(yaw=0.0)
        bot.move_to(PlayerState(2, 0, "bot", pos, yaw=0.0), b, act, nav)
        return act
    if not step(a).crouch:
        fails.append("an Easy bot did not crouch into the crouch route")
    mid = Vec(*path[4])
    act = step(mid)
    if not act.crouch or abs(math.atan2(act.strafe, act.forward) - math.atan2(b.y - mid.y, b.x - mid.x)) % (2 * math.pi) > 0.3 \
            and abs(abs(math.atan2(act.strafe, act.forward) - math.atan2(b.y - mid.y, b.x - mid.x)) - 2 * math.pi) > 0.3:
        fails.append("mid route: not crouched toward the far end")
    step(b)
    if getattr(bot, "route", None):
        fails.append("the route did not end at its far end")
    T.crouch_cells = {crouch_key(a.x, a.y, a.z)}
    act = Action(yaw=0.0)
    bot.crouch_spots(PlayerState(2, 0, "bot", a, yaw=0.0), act)
    if not act.crouch:
        fails.append("a bot on crouch floor did not crouch")
    return fails


if __name__ == "__main__":
    main()
