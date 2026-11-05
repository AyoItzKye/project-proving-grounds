"""LiDAR and gametype objectives (tools/lidar.py Objectives, tools/lidar_director.py objective spots), and the LiDAR
Viewer and Simulator apart (tools/launcher.py, tools/lidar_sim.py):

1. every map's objective places, all modes at once (objective_points): Blood Gulch and Construct have flag stands,
   hills and oddball spawns, places closer than OBJ_MERGE are one
2. each place is a spot for one bot: at most OBJECTIVE_SHARE of the bots at a time, each to its nearest; a bot (or a
   person) at a place marks it reached; clear_spots keeps the objectives
3. saved in lidar.json "objectives" with the nav's verdict; a later run keeps "reached" and does not send a bot there
   again
4. Halo 3's flag and bomb stands read live are objectives, not spawns (brain/stations.py classify)
6. an objective object the running game spawned that no place covers becomes a place and a spot at once (add_live)
5. the Simulator serves its own port, not the Viewer's / a LiDAR match's (a simulator left open kept the live view of
   a LiDAR match from starting: "3D view not started: port 8797 is in use")

usage: python -I test_lidar_objectives.py      -> "lidar objectives OK"
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def main():
    fails = []
    # 5 (no map data needed)
    import launcher
    import lidar
    import lidar_sim
    if lidar_sim.PORT == lidar.PORT or launcher.TASKS["lidar_sim"][2] != lidar_sim.PORT or \
            launcher.TASKS["lidar_view"][2] != lidar.PORT:
        fails.append(f"5. ports: sim {lidar_sim.PORT} / task {launcher.TASKS['lidar_sim'][2]}, view {lidar.PORT} / "
                     f"task {launcher.TASKS['lidar_view'][2]}")
    # 4
    from brain.stations import classify
    for name in ("objects\\multi\\ctf\\ctf_flag_spawn_point", "objects\\multi\\assault\\assault_bomb_spawn_point",
                 "objects\\multi\\koth\\mp_hill_beacon", "objects\\multi\\models\\mp_flag_base\\mp_flag_base"):
        if classify(name, 0)[0] != "objective":
            fails.append(f"4. {name} is {classify(name, 0)}")
    if classify("objects\\multi\\spawning\\respawn_point", 0)[0] != "spawn":
        fails.append("4. a respawn point is no longer a spawn")
    testdata.need("maps/bloodgulch/heightmap.npz", why="the map pack")
    import lidar_director as D
    from brain.maps import get_map, terrain
    # 1
    for m, want in (("bloodgulch", {"flag", "hill", "ball"}), ("h3_construct", {"flag", "hill", "ball", "flag_return"})):
        pts = lidar.objective_points(m)
        roles = {r for p in pts for r in p["roles"]}
        close = [(a["pos"], b["pos"]) for k, a in enumerate(pts) for b in pts[k + 1:] if math.dist(a["pos"], b["pos"]) < lidar.OBJ_MERGE]
        if not want <= roles or close:
            fails.append(f"1. {m}: roles {sorted(roles)}, {len(close)} places closer than {lidar.OBJ_MERGE}")
    # 2
    m = "h3_construct"
    T = terrain(get_map(m))
    rec = lidar.Recorder(m, count_run=False, path=os.path.join(tempfile.mkdtemp(), "lidar.json"))
    d = D.LidarDirector(T, rec, [])
    ob = lidar.Objectives(m, T)
    n = ob.seed(d)
    on_nav = [p for p in ob.points if p["reach"]]
    if n != len(ob.points) or n < 4 or len(on_nav) < n - 2:
        fails.append(f"2. {n} spots for {len(ob.points)} places, {len(on_nav)} on the nav")
    p0 = on_nav[0]["floor"]
    bots = {i: (p0[0] + 6.0 * (i + 1), p0[1], p0[2]) for i in range(6)}
    d.plan(0.0, bots)
    sent = {i: j for i, j in d.jobs.items() if j[0] == "spot"}
    if len(sent) != math.ceil(D.OBJECTIVE_SHARE * len(bots)) or len({j[2] for j in sent.values()}) != len(sent):
        fails.append(f"2. {len(sent)} bots sent ({sorted(j[2] for j in sent.values())}), want "
                     f"{math.ceil(D.OBJECTIVE_SHARE * len(bots))} to as many places")
    first = min(sent, key=lambda i: math.dist(bots[i], d.spots[sent[i][2]]["pos"]))
    if first != 0:
        fails.append(f"2. the bot nearest a place (0) was not sent first: {sent}")
    ob.update([tuple(p0)], 1.0)                      # someone stands on the first place
    k0 = ob.points.index(on_nav[0])
    if not ob.points[k0]["reached"] or not ob.spots[k0]["done"]:
        fails.append("2. a place someone stood on is not reached")
    d.add_spot((p0[0] + 1, p0[1], p0[2]))           # a marked spot, then cleared: the objectives stay
    d.clear_spots()
    if len(d.spots) != n or any(j[0] == "spot" and not d.spots[j[2]].get("label") for j in d.jobs.values()):
        fails.append(f"2. clear_spots: {len(d.spots)} spots left of {n} objectives")
    # 3
    rec.objectives = ob
    data = rec.save()
    saved = json.load(open(rec.path)).get("objectives", [])
    if len(saved) != n or not all({"roles", "pos", "reached", "on", "reach", "floor"} <= set(p) for p in saved) or \
            not 1 <= sum(p["reached"] for p in saved) <= 2 or data.get("objectives") != saved:   # (2: one beside it)
        fails.append(f"3. saved {len(saved)} of {n}, reached {sum(p.get('reached', 0) for p in saved)}")
    again = lidar.Objectives(m, T, saved)
    d2 = D.LidarDirector(T, rec, [])
    if again.seed(d2) != n - sum(p["reached"] for p in saved) or not again.points[k0]["reached"]:
        fails.append("3. a place reached in an earlier run was sent again or forgotten")
    # 6. an objective the game spawned that no place covers (a Forge layout's first run): a new place, a spot now
    import types
    far = on_nav[-1]["floor"]
    seen = types.SimpleNamespace(objects=[dict(kind="objective", what="flag_stand", pos=[far[0] + 0.5, far[1], far[2]]),
                                          dict(kind="objective", what="ctf_flag_spawn_point",
                                               pos=[p0[0] + 40.0, p0[1] + 40.0, p0[2]])])
    n2 = len(d2.spots)
    added = again.add_live(seen, d2)
    if len(added) != 1 or len(d2.spots) != n2 + 1 or \
            added[0]["src"] != "live" or added[0]["roles"] != ["flag"] or again.add_live(seen, d2):
        fails.append(f"6. live objectives added {[(p['names'], p['roles']) for p in added]}, spots {n2} -> {len(d2.spots)}")
    rec.map = "test_lidar_objectives"                # (the report under its own name, not the map's real one)
    path = lidar.report(rec, data, T)
    text = open(path, encoding="utf-8").read()
    os.remove(path)
    if "Gametype objective places" not in text:
        fails.append("3. the report has no objectives line")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"lidar objectives OK (Construct: {n} places, {len(on_nav)} on the nav; one bot each, "
          f"{D.OBJECTIVE_SHARE:.0%} of the bots at a time; saved and kept over runs; Simulator on {lidar_sim.PORT}, "
          f"Viewer on {lidar.PORT})")


if __name__ == "__main__":
    main()
