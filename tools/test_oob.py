"""Out of bounds is learned and kept off:

1. the detector: a death nobody caused counts (full health a second before, on foot, no fall, no enemy within 6 u or
   in sight); one with an enemy close, in sight, after a fall, after damage, in a vehicle, or among three at once does
   not; with an enemy alive within 40 u it is a candidate until a second one lands there
2. the player's flag that names it ("out of bounds", "oob", "kill zone", "soft kill") is a spot where he stood; other
   notes are not; oob.json keeps the spots and candidates
3. the soft wall on Halo 3's Sidewinder: a walk across a spot goes round it (no route point within its radius); a goal
   inside it moves out; the roam spots never fall in it; the vehicles' ground leaves it out; a pilot's probe stops at
   it at its height and not 20 u over it
4. the maps' own kill zones (brain/oob.py KNOWN, tools/killzones.py): box (rotated too), sector prism, cylinder,
   sphere and soft kill surface containment, a pad, a safe zone's outside; base map and layout files, a conditioned
   volume left out; a death in one (and a fall onto one) counted at once as known, no learned spot; on Sidewinder a
   kill box is walked round, a goal in it moves out, vehicles and pilots keep off it, a soft safe sphere puts the
   floors outside it out of bounds; the real files: Lockout's kill_pit (H2), Island's kill_soft / safe_zone_soft
   (Reach), Sandbox's soft kill ceiling (H3 BSP), and no spawn point of five maps in a kill zone

usage: python -I test_oob.py      -> "out of bounds OK (...)"
"""
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import oob as O  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


def life(o, t0, deaths, others=(), hp=1.0, sh=1.0, fall=0.0, riding=False, sees=None):
    """Two seconds alive for each victim (id, team, pos), then dead; others alive throughout. The deaths taken."""
    taken = []
    for k in range(21):
        t = t0 + k * 0.1
        rows = [(pid, team, (p[0], p[1], p[2] + fall * (1 - k / 20)), True, hp, sh, riding) for pid, team, p in deaths]
        o.watch(t, rows + [(pid, team, p, True, 1.0, 1.0, False) for pid, team, p in others], sees)
    taken += o.watch(t0 + 2.2, [(pid, team, None, False, 0.0, 0.0, False) for pid, team, _ in deaths] +
                     [(pid, team, p, True, 1.0, 1.0, False) for pid, team, p in others], sees)
    return taken


def main():
    fails = []
    REAL, O.ROOT = O.ROOT, tempfile.mkdtemp()
    o = O.Oob("test_map", clock=lambda: 0.0)
    far = (300.0, 300.0, 0.0)
    # 1. the detector
    got = life(o, 0.0, [(1, 0, (0.0, 0.0, 0.0))], others=[(2, 1, far)])
    if got != [(0.0, 0.0, 0.0, True)] or len(o.spots) != 1:
        fails.append(f"1. a death alone at full health: {got}, {len(o.spots)} spots (want counted)")
    cases = [("an enemy 4 u off, out of sight", (4.0, 0.0, 0.0), dict(sees=lambda a, b: False)),
             ("an enemy in sight 30 u off", (30.0, 0.0, 0.0), dict(sees=lambda a, b: True)),
             ("after a 5 u fall", None, dict(fall=5.0)),
             ("after damage", None, dict(sh=0.3)),
             ("in a vehicle unread", None, dict(riding=True)),
             ("in a vehicle hurt (0.5 health)", None, dict(riding=0.5))]
    for k, (name, off, kw) in enumerate(cases):
        n, at = len(o.spots), (50.0 * (k + 1), 0.0, 0.0)
        foe = far if off is None else (at[0] + off[0], at[1] + off[1], at[2] + off[2])
        got = life(o, 10.0 * (k + 1), [(1, 0, at)], others=[(2, 1, foe)], **kw)
        if got or len(o.spots) != n:
            fails.append(f"1. {name}: taken {got} (want nothing)")
    # 1b. in a vehicle read whole before: counted
    n = len(o.spots)
    got = life(o, 70.0, [(1, 0, (0.0, -100.0, 0.0))], others=[(2, 1, far)], riding=1.0)
    if got != [(0.0, -100.0, 0.0, True)] or len(o.spots) != n + 1:
        fails.append(f"1b. a death in a whole vehicle, alone: {got} (want counted)")
    n = len(o.spots)
    got = life(o, 80.0, [(1, 0, (0.0, 100.0, 0.0)), (3, 0, (0.0, 120.0, 0.0)), (4, 0, (0.0, 140.0, 0.0))],
               others=[(2, 1, far)])
    if got or len(o.spots) != n:
        fails.append(f"1. three deaths at once: taken {got} (want nothing: a reset)")
    hidden = dict(others=[(2, 1, (30.0, 200.0, 0.0))], sees=lambda a, b: False)
    first = life(o, 90.0, [(1, 0, (0.0, 200.0, 0.0))], **hidden)
    second = life(o, 95.0, [(1, 0, (1.0, 201.0, 0.0))], **hidden)
    if first != [(0.0, 200.0, 0.0, False)] or not second or not second[0][3] or o.candidates:
        fails.append(f"1. an enemy alive 30 u off, out of sight: first {first}, second {second} (want a candidate, "
                     f"then counted)")
    # 2. flags, and the file
    if not o.flag("this is out of bounds", (5.0, 5.0, 1.0), 12.0) or o.flag("nice shot", (6.0, 6.0, 1.0), 13.0):
        fails.append("2. the flag words: want 'out of bounds' a spot, 'nice shot' none")
    if not all(O.WORDS.search(w) for w in ("OOB here", "kill zone", "soft kill", "killzone")):
        fails.append("2. the flag words miss one of oob / kill zone / soft kill / killzone")
    o.save()
    back = O.load("test_map")
    if back["spots"] != o.spots:
        fails.append(f"2. oob.json kept {len(back['spots'])} spots of {len(o.spots)}")
    # 3. the soft wall on Sidewinder: a flat open stretch mid-map
    T = terrain(get_map("h3_sidewinder"))
    floor = lambda x, y: Vec(x, y, T.top_near(x, y, 0.1))    # (the floor walked on: ground() is the level's lowest)
    a, b, mid = floor(-42.0, 8.0), floor(-28.0, 8.0), floor(-35.0, 8.0)   # (flat 20 x 12 u: logs/tmp/dbg_oob.py)

    def walk(p, goal, n=80):
        pts = []
        for _ in range(n):
            q = T.nav(p, goal)
            if q is None or (q - p).flat() < 0.2:
                break
            pts.append(q)
            p = q
        return pts
    before = walk(a, b)
    if not any((q - mid).flat() < O.R for q in before):
        fails.append("3. the test's walk did not cross its spot before (the test's ground)")
    T.set_oob([[mid.x, mid.y, mid.z, "flag", 0.0, ""]], version=1)
    after = walk(a, b)
    inside = [q for q in after if (q - mid).flat() < O.R - 0.3 and abs(q.z - mid.z) < O.DZ]
    if inside or not after or (after[-1] - b).flat() > 1.5:
        fails.append(f"3. the walk across the spot: {len(inside)} points inside it, ended "
                     f"{(after[-1] - b).flat() if after else -1:.1f} u from the goal (want none inside, arrived)")
    if not T.out_of_bounds(mid):
        fails.append("3. the spot's centre does not read out of bounds")
    goal_in = walk(a, mid)
    if goal_in and (goal_in[-1] - mid).flat() < O.R - 0.3:
        fails.append(f"3. a goal inside it: the walk ended {(goal_in[-1] - mid).flat():.1f} u from its centre (want out)")
    rng = random.Random(4)
    spots = [T.open_spot(mid, 6.0, rng) for _ in range(30)]
    if any(q is not None and T.out_of_bounds(q) for q in spots):
        fails.append("3. a roam spot fell out of bounds")
    T.__dict__.pop("graph_v", None)
    T.vnav(a, b)
    if T.vroomy[T._node(mid)]:
        fails.append("3. the vehicles' ground still has the spot")
    yaw = 0.0                                          # (a to b runs east)
    low = Vec(a.x, a.y, mid.z + 1.0)
    probe = lambda q, av: T.fly_clear(q, yaw, 30.0, floor=a.z, avoid=av)
    d_low, d_high = probe(low, T.oob_avoid()), probe(low + Vec(0, 0, 20.0), T.oob_avoid())
    free_low, free_high = probe(low, []), probe(low + Vec(0, 0, 20.0), [])
    edge = (mid - a).flat() - O.R
    if not (abs(d_low - edge) < 0.5 and free_low > d_low + 1.0) or d_high != free_high:
        fails.append(f"3. a pilot's probe: {d_low:.1f} u at its height ({free_low:.1f} without the spot; want its edge "
                     f"{edge:.1f}), {d_high:.1f} u 20 u over it ({free_high:.1f} without; want the same)")
    T.set_oob([], version=2)
    if T.out_of_bounds(mid) or walk(a, b)[-1:] == []:
        fails.append("3. cleared spots still out of bounds")
    # 4. the maps' own kill zones (killzones.json): containment, the files, the detector, the terrain, real data
    import numpy as np
    box = dict(kind="hard", shape="box", center=[0, 0, 0], size=[4, 2, 2], label="b")
    rot = dict(box, rotation=dict(forward=[0.70711, 0.70711, 0], up=[0, 0, 1]))
    prism = dict(kind="soft", shape="box", center=[0, 0, 0], size=[10, 10, 2], points=[[0, 0], [4, 0], [0, 4]], label="p")
    cyl = dict(kind="soft", shape="cylinder", center=[0, 0, 0], size=[3, 3, 2], label="c")
    ball = dict(kind="soft_safe", shape="sphere", center=[0, 0, 0], size=[5, 5, 5], label="s")
    tri = dict(kind="soft", shape="plane", center=[1, 1, 5], size=[4, 4, 0], triangles=[[[0, 0, 5], [4, 0, 5], [0, 4, 5]]],
               label="t")
    want = [(box, (1.9, 0.9, 0.9), True), (box, (2.1, 0, 0), False), (box, (0, 1.1, 0), False), (box, (0, 0, 1.1), False),
            (rot, (1.3, 1.3, 0), True), (rot, (1.9, 0, 0), False), (prism, (1, 1, 0), True), (prism, (3, 3, 0), False),
            (prism, (1, 1, 1.5), False), (cyl, (2.1, 2.1, 0), True), (cyl, (2.2, 2.2, 0), False),
            (cyl, (0, 0, 1.2), False), (ball, (0, 0, 4.9), True), (ball, (3, 3, 3), False),
            (tri, (1, 1, 5.4), True), (tri, (1, 1, 5.6), False), (tri, (3, 3, 5), False)]
    for v, p, inside in want:
        if bool(O.contains(v, p)[0]) != inside:
            fails.append(f"4. containment: {v['shape']}{' rotated' if 'rotation' in v else ''}"
                         f"{' prism' if 'points' in v else ''} at {p}: want {'in' if inside else 'out'}")
    if not O.contains(box, (2.9, 0, 0), pad=1.0)[0] or O.contains(box, (3.1, 0, 0), pad=1.0)[0]:
        fails.append("4. containment's pad: a box grown 1 u")
    if O.where([ball], (0, 0, 1)) is not None or O.where([ball], (0, 0, 6)) is None or \
            O.where([ball], (0, 0, 4.5), pad=1.0) is None:
        fails.append("4. a safe zone: inside safe, outside (or within the pad of its rim) out of bounds")
    for m, vs in (("base", [box, dict(cyl, condition="game type: x")]), ("base/variants/v1", [dict(ball, source="mvar")])):
        os.makedirs(os.path.join(O.ROOT, m), exist_ok=True)
        with open(os.path.join(O.ROOT, m, "killzones.json"), "w") as f:
            f.write('{"volumes": %s}' % str(vs).replace("'", '"'))
    got = [v["label"] for v in O.volumes("base/variants/v1")]
    if got != ["b", "s"] or [v["label"] for v in O.volumes("base")] != ["b"]:
        fails.append(f"4. volumes(): a layout's {got} (want the base map's box and its own sphere, the conditioned cylinder"
                     " left out)")
    k = O.Oob("base")
    got = life(k, 0.0, [(1, 0, (0.5, 0.0, 0.0))], others=[(2, 1, (3.0, 0.0, 0.0))], sees=lambda a, b: True)
    fallen = life(k, 10.0, [(1, 0, (0.0, 0.0, 6.0))], others=[(2, 1, far)], fall=5.0)
    if got != [(0.5, 0.0, 0.0, True)] or fallen != [(0.0, 0.0, 6.0, True)] or len(k.known) != 2 or k.spots:
        fails.append(f"4. deaths in a known kill zone: {got}, a fall onto it {fallen}, {len(k.known)} known, "
                     f"{len(k.spots)} spots (want both counted at once as known, no learned spot)")
    zone = dict(kind="hard", shape="box", center=[mid.x, mid.y, mid.z + 1.0], size=[4.0, 4.0, 3.0], label="kill")
    T.set_oob([], version=3, volumes=[zone])
    after = walk(a, b)
    inside = [q for q in after if O.contains(zone, (q.x, q.y, q.z + 0.3))[0]]
    if inside or not after or (after[-1] - b).flat() > 1.5 or not T.out_of_bounds(mid):
        fails.append(f"4. a kill box on Sidewinder: {len(inside)} walk points in it, ended "
                     f"{(after[-1] - b).flat() if after else -1:.1f} u from the goal, centre out: {T.out_of_bounds(mid)}")
    goal_in = walk(a, mid)
    if goal_in and O.contains(zone, (goal_in[-1].x, goal_in[-1].y, goal_in[-1].z + 0.3))[0]:
        fails.append(f"4. a goal in the kill box: the walk ended inside it at {goal_in[-1]} (box {zone['center']})")
    T.__dict__.pop("graph_v", None)
    T.vnav(a, b)
    if T.vroomy[T._node(mid)]:
        fails.append("4. the vehicles' ground still has the kill box")
    d_low, d_high = probe(low, T.oob_avoid()), probe(low + Vec(0, 0, 20.0), T.oob_avoid())
    if not d_low < free_low - 1.0 or d_high != free_high:
        fails.append(f"4. a pilot's probe at the kill box: {d_low:.1f} u at its height ({free_low:.1f} free), "
                     f"{d_high:.1f} 20 u over it ({free_high:.1f} free)")
    T.set_oob([], version=4, volumes=[dict(kind="soft_safe", shape="sphere", center=[a.x, a.y, a.z], size=[3, 3, 3],
                                           label="safe")])
    if T.out_of_bounds(a) or not T.out_of_bounds(b):
        fails.append("4. a soft safe sphere round a: a in, b out of bounds (want a in bounds, b out)")
    T.set_oob([], version=5, volumes=[])
    if T.out_of_bounds(mid) or T.out_of_bounds(b) or T.oob_avoid():
        fails.append("4. cleared volumes still out of bounds")
    if not any(f["kind"] == "kill_edge" for f in O.features("base")) or \
            not any(f["kind"] == "zone" and f["name"].startswith("kill zone") for f in O.features("base")):
        fails.append("4. the LiDAR view's features: no kill zone or rim dots")
    O.ROOT = REAL                                     # the real files: the kits' data
    lock = O.volumes("h2_lockout")
    if not any(v["label"] == "kill_pit" and v["kind"] == "hard" for v in lock):
        fails.append("4. h2_lockout's kill_pit (H2 scenario kill trigger) missing from killzones.json")
    isl = {v["label"]: v for v in O.volumes("reach_35_island")}
    if isl.get("kill_soft", {}).get("kind") != "soft" or isl.get("safe_zone_soft", {}).get("kind") != "soft_safe":
        fails.append(f"4. reach_35_island: kill_soft / safe_zone_soft kinds {sorted((k, v['kind']) for k, v in isl.items())}")
    if not any(v["source"] == "bsp" and v["shape"] == "plane" for v in O.volumes("h3_sandbox")):
        fails.append("4. h3_sandbox: no BSP soft kill ceiling")
    import json
    for m in ("h2_lockout", "reach_35_island", "h4_ca_redoubt", "h2a_ca_relic", "h3_guardian"):
        vs = O.volumes(m)
        sp = np.asarray([q["pos"] for q in json.load(open(os.path.join(REAL, m, "objects.json")))["spawns"]], float)
        bad = sum(int(O.contains(v, sp + [0, 0, 0.3]).sum()) for v in vs if v["kind"] in O.KILLS)
        if not vs or bad:
            fails.append(f"4. {m}: {len(vs)} volumes, {bad} of its spawn points in a kill zone (want some, none)")
    if fails:
        print("\n".join(fails))
        sys.exit(1)
    print(f"out of bounds OK ({len(o.spots)} spots; the walk round it {len(after)} steps, {len(before)} before)")


if __name__ == "__main__":
    main()
