"""The LiDAR bots' guards, from the Nov 4 live runs (tools/lidar.py, tools/lidar_director.py):

1. a learned fall spot blocks a walker's step only the way that bot fell (or, with no direction, a step coming nearer):
   with "any step near it" Construct's bots stood still beside the pit's 35 falls (half the bot time idle)
2. a called jump never starts where bots fell (its take-off or run-up): those calls were dropped at once
3. a call given up before its jump counts "dropped", not "missed" (live Construct read 0 landed / 155 missed)
4. the frontier searches without stepping onto kill-zone floor: Zealot's unpainted side decks, past a soft kill
   walkway, are no goal (48 bots died walking there)

usage: python -I test_lidar_guards.py      -> "lidar guards OK"
"""
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import testdata  # noqa: E402


def main():
    testdata.need("maps/h3_construct/heightmap.npz", "maps/reach_45_aftship/killzones.json", why="the map pack")
    import numpy as np
    import jumpphys as J
    import lidar
    import lidar_director as D
    from brain import oob as O
    from brain.core import Vec
    from brain.maps import get_map, spawn_points, terrain
    fails = []
    tmp = tempfile.mkdtemp()
    # 1
    rec = lidar.Recorder("h3_construct", count_run=False, path=os.path.join(tmp, "a.json"))
    rec.fall_grid = {}
    rec.add_fall((0.0, 0.0, 0.0), (3.0, 0.0, -20.0))          # fell toward +x
    rec.add_fall((10.0, 0.0, 0.0))                           # (no direction known)
    rb = lidar.Roomba(0, random.Random(1))
    cases = [((0.2, 0.0), (0.5, 0.0), True), ((0.2, 0.0), (-0.1, 0.0), False), ((0.2, 0.0), (0.2, 0.3), False),
             ((10.5, 0.0), (10.2, 0.0), True), ((10.2, 0.0), (10.5, 0.0), False)]
    for frm, to, want in cases:
        got = rb.deadly(to[0], to[1], 0.0, rec, None, frm=(frm[0], frm[1], 0.0))
        if got != want:
            fails.append(f"1. step {frm} -> {to}: deadly {got}, want {want}")
    if not rb.deadly(0.3, 0.0, 0.0, rec, None):
        fails.append("1. with no walker position a fall spot is still deadly ground (frontier / pocket filters)")
    # 2
    T = J.prepare(terrain(get_map("h3_construct")))
    rec2 = lidar.Recorder("h3_construct", count_run=False, T=T, path=os.path.join(tmp, "b.json"))
    rec2.phys, rec2.fall_grid, rec2.links = J.Phys("h3"), {}, []
    lidar.nav_learn(T, "h3_construct", [])
    first = None
    for k, p in enumerate(spawn_points(get_map("h3_construct"))):
        c = rb.pocket((p.x, p.y, p.z), rec2, T)
        if c is not None:
            first = ((p.x, p.y, p.z), c)
            break
    if first is None:
        fails.append("2. no called jump found from any Construct spawn")
    else:
        pos, c = first
        rec2.add_fall(c["take_off"], c["land"])
        c2 = rb.pocket(pos, rec2, T)
        if c2 is not None and math.dist(c2["take_off"][:2], c["take_off"][:2]) < 1.2:
            fails.append(f"2. a call from {c2['take_off']}, 1.2 u from a fall at {c['take_off']}")
        # 3
        l = dict(c, _key=(1, 2, 3, 4))
        rb.score(l, False, rec2, jumped=False)
        if rec2.calls.get("dropped") != 1 or rec2.calls.get("missed"):
            fails.append(f"3. calls {rec2.calls} (want 1 dropped, none missed)")
    # 4. Zealot's decks: painted everything else, a bot on the safe side
    m = "reach_45_aftship"
    T4 = terrain(get_map(m))
    T4.set_oob([], 0, O.volumes(m))
    rec4 = lidar.Recorder(m, count_run=False, T=T4, path=os.path.join(tmp, "c.json"))
    import lidar_rides
    rec4.links = list(rec4.links) + lidar_rides.ride_links(m, J.prepare(T4), J.Phys("reach"))
    lidar.nav_learn(T4, m, rec4.links)
    d = rec4.director = D.LidarDirector(T4, rec4, spawn_points(get_map(m)))
    deck = (np.abs(d.x) > 13) & (np.abs(d.z - 9.3) < 0.4)
    keep = ~deck
    from lidar import COVER
    rec4.cover = {(int(a // COVER), int(b // COVER), int(c // 1.0)) for a, b, c in zip(d.x[keep], d.y[keep], d.z[keep])}
    d.plan(0.0, {})
    me = (3.17, -12.42, 9.29)                                    # (the big lift's sideways landing)
    c = T4._center(*T4._reachable_node(*T4._node(Vec(*me)), me[2]))
    goals = [lidar.Roomba(1, random.Random(k)).frontier((c.x, c.y, c.z), rec4, T4) for k in range(12)]
    goal = next((g for g in goals if g is not None and abs(g[0]) > 13 and abs(g[2] - 9.3) < 0.5), None)
    if goal is not None:                                         # (the code before: (14.0, -10.1, 9.3), 12 of 12)
        fails.append(f"4. the frontier sent a bot to the deck behind the soft kill walkway: {goal}")
    # 5. a bot on the soft kill walkway (where Zealot's rides landed bots) walks out of the zone first
    on = (6.3, -3.6, 9.3)
    rb5 = lidar.Roomba(3, random.Random(4))
    rb5.pick(0.0, on, rec4, T4, d.bounds)
    if not T4.out_of_bounds(Vec(*on)) or rb5.target is None or T4.out_of_bounds(Vec(*rb5.target)) or \
            math.dist(rb5.target[:2], on[:2]) > 15:
        fails.append(f"5. from the walkway {on} (in a kill zone {T4.out_of_bounds(Vec(*on))}) the goal is {rb5.target}")
    # 7. a fall that was no walk off an edge (floor ahead by the level data: thrown by Construct's lift into the pit)
    #    blocks no walker; the 1,026 live refusals behind this one spot
    rec2.fall_grid = {}
    rec2.add_fall((2.4, 8.3, 8.7), (5.81, 14.68, -7.25))
    if rb.deadly(2.6, 8.6, 8.7, rec2, T, frm=(2.45, 8.35, 8.7)):
        fails.append("7. a lift-throw fall spot still refuses a walker's step onto floor")
    if not rec2.near_fall(2.6, 8.6, 8.7):
        fails.append("7. the same spot no longer counts for the frontier / pocket filters")
    # 6. a playtest's Construct jump that turns from its run-up (live: bots stood at the run-up, run / run-up / run ...)
    lk = dict(kind="jump", take_off=[0.51, -3.84, 11.82], land=[2.73, -6.22, 6.41], runup=[0.33, -4.84, 11.82],
              found_by="human", human=1, bot_ok=0, bot_fail=0, path=[])
    rb6 = lidar.Roomba(4, random.Random(6))
    rb6.trial, rb6.phase, rb6.trial_t, rb6.trial_s = lk, "run", 0.0, 30.0
    st = rb6.trial_steer(0.1, (0.34, -4.8, 11.82), rec2, T)
    if st is None or st[0] != 1.0 or rb6.phase != "run":
        fails.append(f"6. at the run-up of a jump turning from it: steer {st}, phase {rb6.phase} (want running on)")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"lidar guards OK (fall spots by direction; calls not from fall spots; dropped calls apart; no goal behind "
          f"Zealot's soft kill walkway, no deck goal in 12 searches)")


if __name__ == "__main__":
    main()
