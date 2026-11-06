"""The LiDAR director's map model, coverage and assignment plan (tools/lidar_director.py, tools/lidar.py Roomba):

1. a patch beyond the frontier's 150 units of path (Blood Gulch, everything else painted): the bot's frontier finds
   nothing twice (a 10 s wander between), and the director sends it to that patch's floor (Roomba.pick -> fallback)
2. every open patch's floor is among the frontier's candidates (its random 2500-node sample misses small patches): a
   2-5 u2 patch near a bot is what its frontier picks (slivers under 1.5 u2 are paint noise: not added)
3. spread: three patches, three bots bunched together: one bot a patch, the nearest pair first
4. kill zones (Terrain.oob) are not floor to cover: left out of the coverage and the patches, counted in the report
5. a bot walking to its patch that neither paints any of it nor gets closer for PATCH_S fails a try and gets another;
   after PATCH_TRIES the patch is left and reported "no way found", offered again after PATCH_RETRY; under the target
   there is still work (the simulator does not stop)
6. one plan with the gametype objectives: at most OBJECTIVE_SHARE of the bots on objectives, every other bot on its
   own patch, no bot on both
7. done at the target; the report, the view's coverage and lidar.json "coverage" are written

usage: python -I test_lidar_coverage.py      -> "lidar coverage OK"
"""
import json
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def paint(rec, d, holes, extra=2.2):
    """Paint every director sample except those within r (+ the explored() neighbourhood) of each hole (x, y, r)."""
    import numpy as np
    from lidar import COVER
    keep = np.ones(len(d.x), bool)
    for x, y, r in holes:
        keep &= np.hypot(d.x - x, d.y - y) > r + extra
    rec.cover = {(int(a // COVER), int(b // COVER), int(c // 1.0)) for a, b, c in zip(d.x[keep], d.y[keep], d.z[keep])}


def main():
    testdata.need("maps/h3_construct/heightmap.npz", "maps/bloodgulch/heightmap.npz", why="the map pack")
    import numpy as np
    from scipy.sparse.csgraph import dijkstra
    import lidar
    import lidar_director as D
    from brain.core import Vec
    from brain.maps import get_map, spawn_points, terrain
    lidar.PROBE_P = lidar.RIDE_P = lidar.USE_P = 0.0
    fails = []
    tmp = tempfile.mkdtemp()

    def recorder(m):
        rec = lidar.Recorder(m, count_run=False, path=os.path.join(tmp, m + ".json"))
        rec.shot_recipes, rec.phys = [], None
        return rec

    # 1. Blood Gulch: a patch over 150 units of path from the bot
    m = "bloodgulch"
    T = terrain(get_map(m))
    rec = recorder(m)
    d = rec.director = D.LidarDirector(T, rec, spawn_points(get_map(m)))
    reach = d._reach() & ~d.kz
    on = np.nonzero(reach)[0]
    k0 = int(on[np.argmin(d.x[on] + d.y[on])])       # a corner of the canyon
    me = (float(d.x[k0]), float(d.y[k0]), float(d.z[k0]))
    l, j, i = T._node(Vec(*me))
    dist = dijkstra(getattr(T, "graph_h", T.graph), directed=True, indices=(l * T.nh + j) * T.nw + i)
    ds = dist[(d.l * T.nh + d.j * D.STEP) * T.nw + d.i * D.STEP]
    far = np.nonzero(reach & np.isfinite(ds) & (ds > 170) & (ds < 1000))[0]
    if not len(far):
        raise SystemExit(f"FAIL: no reachable floor 170-1000 units of path away on Blood Gulch (most {np.nanmax(np.where(np.isfinite(ds), ds, np.nan)):.0f})")
    kp = int(far[np.argmin(ds[far])])
    P = (float(d.x[kp]), float(d.y[kp]), float(d.z[kp]))
    paint(rec, d, [(P[0], P[1], 3.0)])
    d.plan(0.0, {0: me})
    bot = lidar.Roomba(0, random.Random(1))
    bot.pick(0.0, me, rec, T, d.bounds)            # (dry: a 10 s wander first, then the director's patch)
    bot.pick(11.0, me, rec, T, d.bounds)
    if bot.target is None or math.hypot(bot.target[0] - P[0], bot.target[1] - P[1]) > 6.0:
        fails.append(f"1. a patch {ds[kp]:.0f} units of path away: the bot's goal is {bot.target}, not near {P}")
    # 2-7: Construct (no island jump jobs here: those come first in a plan, late in a run)
    D.ISLANDS = False
    m = "h3_construct"
    T = terrain(get_map(m))
    rec = recorder(m)
    d = rec.director = D.LidarDirector(T, rec, spawn_points(get_map(m)))
    reach = d._reach() & ~d.kz
    on = np.nonzero(reach)[0]
    # 2. a small patch 10 u from the bot, the rest painted: the frontier picks it
    k0 = int(on[len(on) // 3])
    me = (float(d.x[k0]), float(d.y[k0]), float(d.z[k0]))
    near = on[(np.abs(np.hypot(d.x[on] - me[0], d.y[on] - me[1]) - 10.0) < 0.5) & (np.abs(d.z[on] - me[2]) < 0.5)]
    P = (float(d.x[near[0]]), float(d.y[near[0]]), float(d.z[near[0]]))
    paint(rec, d, [(P[0], P[1], 0.8)], extra=1.4)
    d.plan(0.0, {0: me})
    small = [r for r in d.patches if np.hypot(d.x[r[1]] - P[0], d.y[r[1]] - P[1]) < 3.0]
    nodes = set(d.open_nodes.tolist())
    goal = lidar.Roomba(0, random.Random(2)).frontier(me, rec, T)
    if not small or small[0][0] * 0.25 > 6.0 or not set(((d.l[small[0][2]] * T.nh + d.j[small[0][2]] * D.STEP) * T.nw
                                                         + d.i[small[0][2]] * D.STEP).tolist()) <= nodes:
        fails.append(f"2. the small patch at {P}: {[(r[0], d.x[r[1]], d.y[r[1]]) for r in small]}, not all in open_nodes")
    elif goal is None or math.hypot(goal[0] - P[0], goal[1] - P[1]) > 3.0:
        fails.append(f"2. the frontier picked {goal}, not the small patch at {P}")
    # 3. three patches far apart, three bots bunched near the first
    pick = [on[0]]
    for k in on[np.argsort(-np.hypot(d.x[on] - d.x[on[0]], d.y[on] - d.y[on[0]]))]:
        if all(math.hypot(d.x[k] - d.x[q], d.y[k] - d.y[q]) > 1.2 * D.TILE for q in pick):
            pick.append(k)
        if len(pick) == 3:
            break
    holes = [(float(d.x[k]), float(d.y[k]), 2.0) for k in pick]
    paint(rec, d, holes)
    A = (float(d.x[pick[0]]), float(d.y[pick[0]]), float(d.z[pick[0]]))
    bots = {i: (A[0] + 1.0 + i, A[1], A[2]) for i in range(3)}
    d.jobs, d.next_t = {}, 0.0
    d.plan(10.0, bots)
    goes = {i: j[5] for i, j in d.jobs.items() if j[0] == "go"}
    near_a = min(range(len(d.patches)), key=lambda k: math.hypot(d.x[d.patches[k][1]] - A[0], d.y[d.patches[k][1]] - A[1]))
    if len(d.patches) < 3 or len(goes) != 3 or len(set(goes.values())) != 3 or goes.get(0) != near_a:
        fails.append(f"3. {len(d.patches)} patches, bots' patches {goes} (want three different, bot 0 on {near_a})")
    # 4. a kill zone over the third patch: not floor to cover
    hx, hy, _ = holes[2]
    jj, ii = np.mgrid[0:T.nh, 0:T.nw]
    zone = (np.hypot(T.x0 + (ii + 0.5) * 0.25 - hx, T.y0 + (jj + 0.5) * 0.25 - hy) < 6.0)[None] & T.lwalk
    T.oob = zone
    d.next_t = 0.0
    d.plan(20.0, bots)
    r = d.report()
    if len(d.patches) != 2 or any(j[0] == "go" and d.kz[j[2]].any() for j in d.jobs.values()) or r["killzone_u2"] < 20:
        fails.append(f"4. with a kill zone: {len(d.patches)} patches (want 2), kill zone {r['killzone_u2']} u2")
    # 5. a bot walking to its patch that never gets there: failed tries, then the patch is left
    d.jobs, d.next_t = {}, 0.0
    stay = {0: bots[0]}
    t = 30.0
    d.plan(t, stay)
    first = d.jobs[0][5]
    target = d.fallback(0, stay[0])
    tries = []
    for _ in range(int(3 * D.PATCH_TRIES * D.PATCH_S / D.PERIOD) + 4):
        t += D.PERIOD
        d.next_t = 0.0
        d.plan(t, stay)
        if 0 in d.jobs and d.jobs[0][0] == "go" and not d.jobs[0][6]:
            d.fallback(0, stay[0])                 # (its frontier finds nothing: it walks there again)
        tries.append(max(int(d.tries[m_].max()) for _, _, m_ in d.patches))
        if tries[-1] >= D.PATCH_TRIES:
            break
    left = [p for p in d.report()["patches"] if p["reason"].startswith("no way found")]
    if target is None or max(tries) < D.PATCH_TRIES or not left or not d.open_work():
        fails.append(f"5. first patch {first}, goal {target}, tries {tries}, left {left}, open work {d.open_work()}")
    d.next_t = 0.0                                 # PATCH_RETRY on: the patches left are offered again
    d.plan(d.retry_t + D.PATCH_RETRY, stay)
    if any(int(d.tries[m_].max()) for _, _, m_ in d.patches):
        fails.append("5. patches left were not offered again after PATCH_RETRY")
    # 6. objectives and patches in one plan
    T.oob = None
    paint(rec, d, [(float(d.x[k]), float(d.y[k]), 2.0) for k in on[::max(1, len(on) // 12)][:12]])
    d2 = rec.director = D.LidarDirector(T, rec, spawn_points(get_map(m)))
    for k in on[::max(1, len(on) // 4)][:4]:
        d2.add_spot((float(d.x[k]), float(d.y[k]), float(d.z[k])), bots=1, label="flag")
    sp = np.array([q["pos"] for q in d2.spots])
    far = [k for k in on[::25] if np.min(np.hypot(sp[:, 0] - d.x[k], sp[:, 1] - d.y[k])) > 5.0]   # (no bot on a spot)
    six = {i: (float(d.x[far[i]]), float(d.y[far[i]]), float(d.z[far[i]])) for i in range(6)}
    d2.plan(0.0, six)
    kinds = [d2.jobs.get(i, ("none",))[0] for i in six]
    if kinds.count("spot") != math.ceil(D.OBJECTIVE_SHARE * 6) or kinds.count("go") != 6 - kinds.count("spot") or \
            len({j[5] for j in d2.jobs.values() if j[0] == "go"}) != kinds.count("go"):
        fails.append(f"6. jobs {kinds} (want {math.ceil(D.OBJECTIVE_SHARE * 6)} on objectives, the rest on their own patch)")
    # 7. done at the target; report, view, lidar.json "coverage"
    paint(rec, d2, [])
    d2.spots = []
    d2.next_t = 0.0
    d2.plan(100.0, six)
    data = rec.save()
    saved = json.load(open(rec.path)).get("coverage") or {}
    hub = lidar.Hub(rec, "sim")
    view = hub.live(0).get("coverage") or {}
    if not d2.done() or d2.open_work() or d2.reached_at != 100.0 or saved.get("coverage", 0) < D.TARGET or \
            data.get("coverage", {}).get("coverage") != saved.get("coverage") or view.get("coverage", 0) < D.TARGET or not any("Coverage" in x for x in d2.lines()):
        fails.append(f"7. done {d2.done()}, open {d2.open_work()}, reached {d2.reached_at}, saved {saved.get('coverage')}, "
                     f"view {view.get('coverage')}")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"lidar coverage OK (a patch {ds[kp]:.0f} u of path off reached, small patches seen, one bot a patch, kill "
          f"zones left out, {D.PATCH_TRIES} failed tries leave a patch, objectives share the plan, target "
          f"{100 * D.TARGET:.0f}%)")


if __name__ == "__main__":
    main()
