"""Lifts, man cannons and crouch-jumps for the LiDAR bots (tools/lidar_rides.py, tools/lidar.py, tools/lidar_sim.py):

1. the kits' tags: Aftship's three lifts read with their phantoms (aftship_lift_xl: up 8 / 9 u/s straight up, out
   10 / 7 u/s turned by the crate's 90 degree yaw); Halo 4 Adrift's two lifts (Halo 3 style XML)
2. the ride solver lands Adrift's lifts within 1 u (flat) and 1 u (height) of the rides bots made in real matches, and
   Aftship's big lift, steered sideways, on the side decks (9 u up: floor no walk reached)
3. the map's rides join the nav: Aftship's reachable floor grows (the director then sends bots up there)
4. the simulator's body standing in the big lift is carried up 6+ u within 2 s, and lands
5. a ride on the nav's way is ridden (trial kind "ride", steered in the air the solver's way); map rides and crouch-
   jumps bots found are not saved into lidar.json
6. a crouch-jump (feet tucked at the apex, lidar.CROUCH_TUCK from the bipeds' heights) lands on a ledge a plain jump
   falls short of

usage: python -I test_lidar_rides.py      -> "lidar rides OK"
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import testdata  # noqa: E402


def main():
    testdata.need("maps/reach_45_aftship/phantoms.json", "maps/h4_ca_warhouse/phantoms.json",
                  why="python -I tools/lidar_rides.py reach_45_aftship h4_ca_warhouse (needs the kits)")
    import random
    import numpy as np
    import jumpphys as J
    import lidar
    import lidar_rides as L
    import lidar_sim
    from brain.core import Vec
    from brain.maps import get_map, spawn_points, terrain
    fails = []
    # 1
    d = L.load("reach_45_aftship")
    xl = next((o for o in d.get("objects", []) if o["name"] == "aftship_lift_xl"), None)
    if len(d.get("objects", [])) != 3 or xl is None:
        fails.append(f"1. Aftship: {[o['name'] for o in d.get('objects', [])]}")
    else:
        up = next(s for s in xl["shapes"] if s["type"] == "up")
        out = next(s for s in xl["shapes"] if s["type"] == "out")
        if (up["acc"], up["vmax"]) != (8.0, 9.0) or up["dir"][2] < 0.999 or (out["acc"], out["vmax"]) != (10.0, 7.0) \
                or abs(out["dir"][1] - 0.965) > 0.01 or abs(out["dir"][0]) > 0.01:
            fails.append(f"1. aftship_lift_xl: up {up['acc'], up['vmax'], up['dir']}, out {out['acc'], out['vmax'], out['dir']}")
    if len(L.load("h4_ca_warhouse").get("objects", [])) != 2:
        fails.append("1. Adrift: its two lifts not read")
    # 2
    T4 = J.prepare(terrain(get_map("h4_ca_warhouse")))
    rows = L.check("h4_ca_warhouse", T4, J.Phys("h4"))
    if len(rows) < 4 or any(r[2] is None or r[3] > 1.0 or abs(r[4]) > 1.0 for r in rows):
        fails.append(f"2. Adrift rides against the recorded: {rows}")
    m = "reach_45_aftship"
    T = J.prepare(terrain(get_map(m)))
    ph = J.Phys("reach")
    rides = L.ride_links(m, T, ph)
    decks = [r for r in rides if r["name"] == "aftship_lift_xl" and r["land"][2] > 9.0 and abs(r["land"][0]) > 2.0]
    if not decks:
        fails.append(f"2. the big lift steered sideways: {[(r['steer'], r['land']) for r in rides if r['name'] == 'aftship_lift_xl']}")
    # 3
    T.set_spawns(spawn_points(get_map(m)))
    before = int((T.reach & T.lwalk).sum())
    rec = lidar.Recorder(m, count_run=False, path=os.path.join(tempfile.mkdtemp(), "lidar.json"))
    rec.links = list(rec.links) + rides
    lidar.nav_learn(T, m, rec.links)
    after = int((T.reach & T.lwalk).sum())
    if after - before < 2000:                         # (cells of 1/16 u2: 125 u2)
        fails.append(f"3. reachable cells {before} -> {after}")
    # 3b. the side decks are past a soft kill walkway (live Zealot: bots died on it): behind a kill zone, not to cover
    import lidar_director as Dr
    from brain import oob as O
    T.set_oob([], 0, O.volumes(m))
    dd = Dr.LidarDirector(T, rec, spawn_points(get_map(m)))
    dd.plan(0.0, {})
    rr = dd.report()
    decks_out = [p for p in rr["behind_kill_zone"] if abs(p["pos"][0]) > 14 and abs(p["pos"][2] - 9.3) < 0.5]
    if rr["behind_kill_zone_u2"] < 500 or len(decks_out) < 2 or dd.want[(abs(dd.x) > 14) & (abs(dd.z - 9.3) < 0.3)].any():
        fails.append(f"3b. behind kill zones {rr['behind_kill_zone_u2']} u2, decks {decks_out}")
    T.set_oob([], 1, [])
    # 3c. a crouch-jump bots keep missing leaves the nav and is never called again
    cj = dict(kind="jump", take_off=[1.0, 2.0, 3.0], land=[2.0, 3.0, 4.0], called=True, crouch=1, found_by="bot",
              human=0, bot_ok=1, bot_fail=0, path=[])
    rec.links.append(cj)
    rb = lidar.Roomba(2, random.Random(5))
    for _ in range(3):
        rb.score(cj, False, rec)
    if any(x is cj for x in rec.links) or rec.failed_calls.get((2, 4, 4, 6), 0) < 2:
        fails.append("3c. a crouch-jump missed 3 times (landed once) is still in the nav")
    # 4
    T.phantoms = L.all_shapes(d)
    a = L.step_in(T, xl)
    b = lidar_sim.Body(a)
    top, landed = a[2], False
    for k in range(int(8 * 30)):
        b.step(T, ph, (0.0, 0.0, 0.0, 0.0, 0), 1.0 / 30, random.Random(1))
        top = max(top, b.p[2])
        if k > 30 and b.ground:
            landed = True
            break
        if k == 60 and top < a[2] + 6.0:
            break
    if top < a[2] + 6.0 or not landed:
        fails.append(f"4. a body in the big lift rose to {top:.1f} from {a[2]:.1f}, landed {landed}")
    # 5
    bot = lidar.Roomba(0, random.Random(3))
    bot.target = tuple(decks[0]["land"]) if decks else None
    lk = decks[0] if decks else rides[0]
    w = type("W", (), {})()
    w.x, w.y, w.z, w.sx, w.sy = lk["land"][0], lk["land"][1], lk["land"][2], lk["take_off"][0], lk["take_off"][1]
    T.nav = lambda p, q, human=False: w                # (the nav's next step is that ride)
    bot.way_in(0.0, tuple(lk["take_off"]), rec, T)
    tr = bot.trial
    if tr is None or tr.get("kind") != "ride" or tr.get("steer") != lk.get("steer"):
        fails.append(f"5. the ride on the way: trial {tr and (tr.get('kind'), tr.get('steer'))}")
    elif lk.get("steer"):
        bot.phase, bot.fly_t, bot.track.air = "fly", 0.0, True
        st = bot.interact_steer(1.0, (0.0, -12.0, 12.0), rec, T, tr)
        if st is None or st[0] != 1.0 or abs(st[2] - math.atan2(lk["steer"][1], lk["steer"][0])) > 1e-6:
            fails.append(f"5. in the air on a map ride the bot steers {st}")
    # the edge guard: stepping onto the pad keeps the ride (its column has no floor); a deadly edge farther off drops it
    if tr is not None:
        to = tr["take_off"]
        for off, keep in ((0.8, True), (4.0, False)):
            b2 = lidar.Roomba(1, random.Random(4))
            b2.trial, b2.phase, b2.trial_t, b2.trial_s, b2.target = dict(tr), "go", 0.0, 60.0, tuple(to)
            b2.deadly = lambda *a, **k: True
            T.nav = lambda p, q, human=False, _t=to: type("W", (), dict(x=_t[0], y=_t[1], z=_t[2]))()
            T._field = lambda v: type("F", (), {"__getitem__": lambda s, k: 1.0})()
            b2.think(1.0, (to[0] - off, to[1], to[2]), rec, T, None)
            if (b2.trial is not None) != keep:
                fails.append(f"5. {off} u from the pad with an edge ahead: ride kept {b2.trial is not None}, want {keep}")
    rec.links.append(dict(kind="jump", take_off=[0, 0, 0], land=[1, 1, 1], called=True, crouch=1, found_by="bot",
                          human=0, bot_ok=1, bot_fail=0, path=[]))
    rec.save()
    saved = json.load(open(rec.path)).get("links", [])
    if any(l.get("found_by") == "map" or l.get("crouch") for l in saved):
        fails.append("5. map rides or bots' crouch-jumps were saved into lidar.json")
    # 6. a ledge between a plain jump's reach and a crouch-jump's on Construct's level data
    m3 = "h3_construct"
    T3 = J.prepare(terrain(get_map(m3)))
    ph3 = J.Phys("h3")
    tuck = lidar.CROUCH_TUCK["h3"]
    found = None
    rng = np.random.default_rng(5)
    ls, js, is_ = np.nonzero(T3.lwalk)
    for n in rng.choice(len(ls), 4000, replace=False):
        a3 = T3._center(int(ls[n]), int(js[n]), int(is_[n]))
        for ang in np.linspace(0, 2 * math.pi, 16, endpoint=False):
            ux, uy = math.cos(ang), math.sin(ang)
            o1 = lidar.fly_tuck(T3, ph3, (a3.x, a3.y, a3.z), ux * ph3.run, uy * ph3.run, 0.0)
            o2 = lidar.fly_tuck(T3, ph3, (a3.x, a3.y, a3.z), ux * ph3.run, uy * ph3.run, tuck)
            if o1[0] == "land" and o2[0] == "land" and o2[1][2] > max(o1[1][2], a3.z) + ph3.apex * 0.85:
                found = ((a3.x, a3.y, a3.z), o1[1], o2[1])
                break
        if found:
            break
    if found is None:
        fails.append("6. no ledge on Construct a crouch-jump lands on and a plain jump does not")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"lidar rides OK (Aftship {len(rides)} rides, side decks from the big lift; reachable cells {before} -> "
          f"{after}; Adrift within {max(r[3] for r in rows):.2f} u of the recorded rides; a crouch-jump from "
          f"{[round(v, 1) for v in found[0]]} lands {found[2][2] - found[1][2]:.2f} u higher)")


if __name__ == "__main__":
    main()
