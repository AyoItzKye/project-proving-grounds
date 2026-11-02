"""Vehicle wedges (Spire match 221404: three bots in two rounds pinned their Warthogs at (-143.4, -352.7) and (-140.3,
-353.5) with the throttle down; people drove up to there and turned west, the vehicle ground ran on south through a gap
no person ever drove). tools/wedges.py learns wedge spots from traces; brain/terrain.py _build_vnav leaves the undriven
floor round them off the vehicles' ground and prices people's driving lines as roads (ROAD_COST):

1. on the player's Spire variant the drive south from (-139, -345) keeps out of the gap (x -145..-140, y -361..-355,
   where the old route went (-143.6, -354.6) -> (-142.6, -360.1)) and follows his road west (x under -148 by y -357);
   from the wedge spot itself it heads west
2. the learner: a bot stopped twice with the throttle down at one spot is a wedge; one stop is not; never by a
   vehicle's spawn pad, never an aircraft; floor a person drove stays drivable (no nodrive cell within 0.75 u of it)
3. the route guard: a spot whose cut stops a pad-to-pad drive that arrived is left out (Boneyard), one that stops none
   is kept
4. the drive north on the player's variant: each south pad's drive to the north Warthog pad gets there in real steps,
   and a bot at the wheel at (-139.9, -348.3), where the road runs along a wall, drives on (it got out there)
5. no way on the vehicle's ground (Breakpoint east to west): the drive ends as near as its piece goes, on it, never back
   and forth off its edge

usage: python -I test_wedges.py      -> "wedges OK"
"""
import json
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import wedges  # noqa: E402
from brain.bot import Action, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def route(T, a, b, n=6):
    pts, p = [], Vec(*a)
    for _ in range(n):
        w = T.vnav(p, Vec(*b))
        pts.append(w)
        if math.hypot(w.x - p.x, w.y - p.y) < 0.5:
            break
        p = w
    return pts


def main():
    testdata.need_lidar("reach_35_island", "reach_dlc_invasion")
    testdata.need("maps/reach_35_island/wedges.json")
    fails = []
    T = terrain(get_map("reach_35_island/variants/v3977bae2"))
    pts = route(T, (-139.1, -345.1, -59.4), (-165.14, -418.57, -60.87))
    gap = [p for p in pts if -145.0 <= p.x <= -140.0 and -361.0 <= p.y <= -355.0]
    west = any(p.x < -148.0 and p.y > -360.0 for p in pts)
    if gap or not west:
        fails.append(f"the drive south: {[(round(p.x, 1), round(p.y, 1)) for p in pts]} (want out of the gap, west by "
                     f"his road)")
    w = T.vnav(Vec(-143.4, -352.7, -57.6), Vec(-165.14, -418.57, -60.87))
    if w.x > -145.0:
        fails.append(f"from the wedge spot the next point is ({w.x:.1f}, {w.y:.1f}) (want west, off the gap)")
    # 2. the learner on a made-up trace
    with tempfile.TemporaryDirectory() as tmp:
        tr = os.path.join(tmp, "trace_x.jsonl")
        rows = [json.dumps({"t": 0.0, "world": [], "vehicles": [[5, "warthog", 0, 0, 0, 1, 0, None],
                                                                 [6, "banshee", 0, 0, 0, 1, 0, None]]})]

        def stuck(bot, t0, at, veh=5, n=8):
            for k in range(n):
                rows.append(json.dumps({"t": t0 + 0.5 * k, "id": bot, "pos": list(at), "seat": "driver", "veh": veh,
                                        "cmd": [1.0, 0.0, 0.0, 0, 0.0]}))
        stuck(1, 10.0, (-150.0, -300.0, -60.0))
        stuck(2, 40.0, (-150.2, -300.1, -60.0))          # a second stop at the same spot: a wedge
        stuck(3, 70.0, (-120.0, -280.0, -60.0))          # one stop: not
        stuck(4, 90.0, (-160.0, -290.0, -60.0), veh=6)   # an aircraft
        stuck(4, 130.0, (-160.1, -290.0, -60.0), veh=6)
        open(tr, "w").write("\n".join(rows) + "\n")
        found, cells = wedges.learn([tr], "reach_35_island")
        spots = [(round(x), round(y)) for x, y, z, n in found]
        if spots != [(-150, -300)]:
            fails.append(f"learned spots {found} (want the one stopped at twice, by a ground vehicle)")
        pad = json.load(open(os.path.join(HERE, "..", "maps", "reach_35_island", "objects.json")))["vehicles"][0]["pos"]
        rows = rows[:1]
        stuck(1, 10.0, pad)
        stuck(2, 40.0, pad)
        open(tr, "w").write("\n".join(rows) + "\n")
        if wedges.learn([tr], "reach_35_island")[0]:
            fails.append("a stop at a vehicle's spawn pad was learned as a wedge")
    people = [tuple(r[:3]) for f in (os.path.join(HERE, "..", "maps", "reach_35_island", "variants", v, "rides.json")
                                     for v in ("v3977bae2", "v704f87f3")) if os.path.exists(f)
              for r in json.load(open(f)).get("drive", []) if r[3] >= 1]
    saved = json.load(open(os.path.join(HERE, "..", "maps", "reach_35_island", "wedges.json")))
    driven = [c for c in saved["nodrive"] if any(math.dist(c[:2], q[:2]) < 0.75 and abs(c[2] - q[2]) < 1.5 for q in people)]
    if driven or not saved["nodrive"]:
        fails.append(f"{len(driven)} nodrive cells on floor a person drove (want none), {len(saved['nodrive'])} in all")
    # 3. the route guard (Boneyard): the cut round (282.3, 93.4) stopped the east Scorpion's drive to the north Ghost,
    # so it is left out; the cut round (238.1, 82.5) stops none and is kept
    bad, good = [282.27, 93.35, -10.74, 32], [238.06, 82.48, -8.81, 13]
    cells = [[round(w[0] + dx * 0.5, 2), round(w[1] + dy * 0.5, 2), w[2]] for w in (bad, good)
             for dx in range(-5, 6) for dy in range(-5, 6) if math.hypot(dx * 0.5, dy * 0.5) <= wedges.WEDGE_R]
    # (on the shortest-line routing of: since the vehicles' ground keeps off walls, Terrain.VEH_WALL_COST, and that
    # drive goes round the cut, so the guard's case needs the old routes)
    from brain.terrain import Terrain
    cost, Terrain.VEH_WALL_COST = Terrain.VEH_WALL_COST, 0.0
    try:
        kept, _, dropped = wedges.keep_routes("reach_70_boneyard", [bad, good], cells, [])
    finally:
        Terrain.VEH_WALL_COST = cost
    if kept != [good] or dropped != [bad]:
        fails.append(f"the route guard kept {kept}, left out {dropped} (want {good} kept, {bad} left out)")
    # 4. the drive north on the player's variant: at (-139.9, -348.3) the people's road runs along a wall, every
    # straight line past the next cell touched it, the look ahead was that one cell (0.25 u) and drive read it as the
    # end of the vehicle ground: a bot driving to the north base got out 39 u short. Each south pad's drive to the north
    # Warthog pad gets there in real steps (0.3 u and up: drive's end test), and a bot at the wheel there drives on
    M = get_map("reach_35_island/variants/v3977bae2")
    north = Vec(-122.3, -313.5, -60.2)
    for v in M["objects"]["vehicles"]:
        if v["item"] not in ("warthog", "mongoose", "ghost") or v["pos"][1] > -370.0:
            continue
        p = Vec(*v["pos"])
        for _ in range(60):
            q = T.vnav(p, north)
            if (q - p).flat() < 0.3:
                break
            p = q
        if (p - north).flat() >= 6.0:
            fails.append(f"the drive from the {v['item']} pad ({v['pos'][0]:.1f}, {v['pos'][1]:.1f}) to the north "
                         f"Warthog pad stops at ({p.x:.1f}, {p.y:.1f}), {(p - north).flat():.1f} u short")
    at = Vec(-139.89, -348.32, -58.53)

    def at_wheel(ground):
        """A Warthog driver at (-139.9, -348.3) on the way to the north pad, one tick: its commands."""
        b = Bot(1, 0, make_profile("top", "rusher", random.Random(4)), M, random.Random(4))
        b._terrain, b.drive_to = ground, north
        b.seat_for, b.seat_since, b.seat = 5, 0.0, "driver"
        me = PlayerState(1, 0, "d", at, yaw=math.pi / 2, vehicle=5)
        act = Action(yaw=math.pi / 2)
        b.drive(10.0, 1 / 30, me, Snapshot(10.0, [me], vehicles=[dict(handle=5, kind="warthog", pos=(at.x, at.y, at.z),
                                                                    riders=1, occupied=True, fwd=(0.0, 1.0, 0.0))]),
                act, lambda p, q, **k: q)
        return act
    act = at_wheel(T)
    if act.action or act.forward <= 0.0:
        fails.append(f"a driver at (-139.9, -348.3) on the way to the north pad: Use {act.action}, forward "
                     f"{act.forward} (want driving on, not getting out)")

    class Step:                     # the real ground, vnav answering a step north (0: where the bot is, the end)
        def __init__(s, d):
            s.d = d

        def __getattr__(s, k):
            return getattr(T, k)

        def vnav(s, a, b):
            return Vec(a.x, a.y + s.d, a.z) if s.d else a
    for d, out in ((0.25, False), (0.0, True)):
        if at_wheel(Step(d)).action != out:
            fails.append(f"vnav answering a {d} u step 39 u from the goal: Use {not out} (want "
                         f"{'out, the end of the vehicle ground' if out else 'driving on: a short step is not the end'})")
    # 5. no way on the vehicle's ground (Breakpoint): from the east pad to the west one the walking answer was off the
    # ground at (33.1, -11.9) and the next answer back onto it at (34.6, -12.4), every tick, never an end. Now it drives
    # as near the goal as its piece of ground goes and ends there (vnav answering where it is), on that ground
    B = terrain(get_map("reach_dlc_invasion"))
    p, goal, seen = Vec(38.5, -19.4, -7.1), Vec(-6.1, 38.2, -9.2), []
    for _ in range(200):
        q = B.vnav(p, goal)
        if q == p:
            break
        seen.append((round(q.x, 2), round(q.y, 2)))
        p = q
    if q != p or len(seen) != len(set(seen)) or not B.vroomy[B._node(p)]:
        fails.append(f"Breakpoint, no vehicle way east to west: {len(seen)} steps, {len(seen) - len(set(seen))} back to a "
                     f"point it had been, ends ({p.x:.1f}, {p.y:.1f}) (want an end on the vehicle ground, never back)")
    # the match's end prune (wedges.prune, live_bots at every match's end): nodrive cells a person drove over come out,
    # the rest stay, the file untouched when none does
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, "maps", "m", "variants", "v1"))
    json.dump(dict(wedges=[[0, 0, 0, 9]], nodrive=[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]], note="n"),
              open(os.path.join(tmp, "maps", "m", "wedges.json"), "w"))
    json.dump(dict(drive=[[0.2, 0.1, 0.0, 1]]), open(os.path.join(tmp, "maps", "m", "variants", "v1", "rides.json"), "w"))
    root, wedges.ROOT = wedges.ROOT, tmp
    try:
        n, again = wedges.prune("m"), wedges.prune("m")
        left = json.load(open(os.path.join(tmp, "maps", "m", "wedges.json")))
    finally:
        wedges.ROOT = root
    if (n, again) != (1, 0) or left["nodrive"] != [[10.0, 0.0, 0.0]] or left["wedges"] != [[0, 0, 0, 9]]:
        fails.append(f"the match's end prune: took {n} then {again}, left {left} (want the driven cell out, the rest kept)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"wedges OK (the drive south: {[(round(p.x, 1), round(p.y, 1)) for p in pts][:5]})")


if __name__ == "__main__":
    main()
