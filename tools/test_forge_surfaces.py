"""Forge building pieces face by face (brain/forge.py block, Terrain.add_faces). On Forge World's own ground (the flat at
z 44.65 where the player's shields stood, under its roof at 56 - 58), kit pieces (maps/_shapes/reach_faces.json) and two
made-up wedges either side of the 50 degree limit (the kit's Spartan and Elite: maximum slope angle 50):
1. a block (ff_plat_2x2): its top is floor to stand on, no floor is left inside it, its side is a wall to the
   crosshair reading (Terrain.clearance) and to shots
2. a ramp (ff_ramp_2x2, 27 degrees) and a steep ramp (ff_ramp_2x2_steep, 45: steeper than a plain step allows): the nav
   walks from the ground up to the top of each, and keeps their slope
3. wedges: 49 degrees a ramp (walked up), 55 a wall (no floor on it, and it stops the crosshair)
4. a piece both walls and floors (ff_bunker_stair): floor at several heights inside it, and walls
5. a bridge (ff_bridge_2x2) over the ground: the ground under it stays floor
6. which pieces count (block): the tall tower with energy-glass windows goes in with its faces (its first material
   left it out before); lights and shields alone are no building pieces
7. LiDAR: its paint around a player marks the
   ramps (KIND_RAMP, orange in the 3D view) on their own cells only, the block's top plain floor, and the block's side
   and the 55 degree face as walls
Fails on the code before (every piece one solid box: nothing on a piece walkable, no ramps).

usage: python -I test_forge_surfaces.py      -> "forge surfaces OK"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.forge import _shapes, block  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

Z = 44.65                                    # the ground (open from x 52 to 75, y 211 to 235)
BAND = (Z - 1.0, Z + 3.5)                    # floor levels looked at: not the level under it (2.2) or its roof
AX = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
SPOTS = {"block": (54.0, 214.0), "ramp": (60.0, 214.0), "steep": (66.0, 214.0), "stair": (72.0, 222.0),
         "bridge": (54.0, 222.0), "wedge49": (60.0, 230.0), "wedge55": (66.0, 230.0)}


def wedge(deg, run=2.0):
    """A made-up wedge rising along +x at deg degrees over x -1..1, y -1..1: its faces, outward."""
    h = run * math.tan(math.radians(deg))
    A, B, C, D, E, F = (-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (1, -1, h), (1, 1, h)
    polys = [(A, D, C, B), (A, E, F, D), (B, C, F, E), (A, B, E), (D, F, C)]
    return [("hard_metal_thick_for", [float(v) for p in poly for v in p]) for poly in polys], h


def on_ground(name, key, sink=0.02):
    """Kit piece `name` standing on the ground at SPOTS[key] (its bottom 0.02 into it, as Forge pieces sit)."""
    x, y = SPOTS[key]
    return block(name, (x, y, Z - _shapes()[name]["min"][2] - sink), AX)


def levels(T, x, y, lo=BAND[0], hi=BAND[1]):
    """The walkable floor heights of the cell at (x, y) between lo and hi."""
    j, i = T._cell(Vec(x, y, Z))
    return [float(v) for v, w in zip(T.lz[:, j, i], T.lwalk[:, j, i]) if np.isfinite(v) and w and lo < v < hi]


def top_node(T, x, y, lo, hi):
    """The highest walkable node of the cell at (x, y) between lo and hi, or None."""
    j, i = T._cell(Vec(x, y, Z))
    ls = [l for l in range(T.L) if T.lwalk[l, j, i] and lo < T.lz[l, j, i] < hi]
    return (max(ls, key=lambda l: T.lz[l, j, i]), j, i) if ls else None


def main():
    fails = []
    T0 = terrain(get_map("reach_forge_halo"))
    pieces = {"block": on_ground("ff_plat_2x2", "block"), "ramp": on_ground("ff_ramp_2x2", "ramp"),
              "steep": on_ground("ff_ramp_2x2_steep", "steep"), "stair": on_ground("ff_bunker_stair", "stair"),
              "bridge": block("ff_bridge_2x2", SPOTS["bridge"] + (Z + 1.6,), AX)}
    for deg in (49.0, 55.0):
        polys, h = wedge(deg)
        key = f"wedge{deg:.0f}"
        pieces[key] = (SPOTS[key] + (Z - 0.02,), AX, [-1, -1, 0], [1, 1, h], key, polys)
    if any(len(p or ()) != 6 for p in pieces.values()):
        fails.append(f"pieces without their faces: {[k for k, p in pieces.items() if len(p or ()) != 6]}")
    for key, (x, y) in SPOTS.items():
        if levels(T0, x, y) != [Z] and not (len(levels(T0, x, y)) == 1 and abs(levels(T0, x, y)[0] - Z) < 0.01):
            fails.append(f"{key}: the ground at {x}, {y} is not open floor at {Z} before: {levels(T0, x, y)}")
    T = terrain(get_map("reach_forge_halo"), live_blocks=list(pieces.values()))
    kinds = getattr(T, "face_kinds", {})
    if not all(kinds.get(k) for k in ("floor", "ramp", "wall")):
        fails.append(f"face kinds {kinds}: want floors, ramps and walls")
    # 1. the block: floor on top, none inside, a wall at its side (x 53 - 55)
    x, y = SPOTS["block"]
    top, lv = Z - 0.02 + 1.0, levels(T, x, y)
    if len(lv) != 1 or abs(lv[0] - top) > 0.05:
        fails.append(f"block: floor levels at its middle {lv}, want its top {top:.2f} alone")
    near, far = Vec(x - 2.0, y, Z), Vec(x + 2.0, y, Z)
    d0, d = T0.clearance(near, 0.0), T.clearance(near, 0.0)
    if not (d0 >= 2.9 and 0.75 <= d <= 1.25):
        fails.append(f"block: the crosshair reading 1 u from its side {d:.2f} (before {d0:.2f}), want about 1.0")
    if not T0.los(near, far) or T.los(near, far):
        fails.append("block: a shot through it is open")
    # 2. ramps: walked up from the ground at their foot, their slope kept
    for key, deg in (("ramp", 26.57), ("steep", 45.0)):
        x, y = SPOTS[key]
        n = top_node(T, x + 0.85, y, Z + 0.5, Z + 2.5)
        if n is None:
            fails.append(f"{key}: no walkable floor near its top ({levels(T, x + 0.85, y)})")
            continue
        if not T.reaches(Vec(x - 1.6, y, Z), T._center(*n)):
            fails.append(f"{key}: the nav does not walk up it (foot -> {T._center(*n)})")
        got = math.degrees(math.atan(float(T.tz[n]))) if T.tz is not None else 0.0
        if abs(got - deg) > 1.0:
            fails.append(f"{key}: slope kept {got:.1f} degrees, want {deg}")
    # 3. wedges either side of 50 degrees
    for deg in (49.0, 55.0):
        x, y = SPOTS[f"wedge{deg:.0f}"]
        on = [n for a in np.arange(x - 0.9, x + 0.91, 0.25) for b in np.arange(y - 0.9, y + 0.91, 0.25)
              for n in [top_node(T, a, b, Z + 0.3, BAND[1])] if n]
        if deg < 50:
            best = max(on, key=lambda q: T.lz[q]) if on else None
            if not best or T.lz[best] < Z + 1.5 or not T.reaches(Vec(x - 1.6, y, Z), T._center(*best)):
                fails.append(f"wedge {deg}: a ramp, but not walked up (highest walkable "
                             f"{float(T.lz[best]) - Z if best else None} over the ground)")
        else:
            if on:
                fails.append(f"wedge {deg}: a wall, but {len(on)} walkable cells on it")
            d = T.clearance(Vec(x - 2.5, y, Z), 0.0)
            if not 1.25 <= d <= 1.75:
                fails.append(f"wedge {deg}: the crosshair reading 1.5 u from its foot {d:.2f}, want about 1.5")
    # 4. walls and floors at once (the bunker stair: x -2.9..1.8, y -2.4..2.6 of its middle)
    x, y = SPOTS["stair"]
    zs = sorted({round(v - Z, 1) for a in np.arange(x - 2.75, x + 1.76, 0.25) for b in np.arange(y - 2.25, y + 2.51, 0.25)
                 for v in levels(T, a, b, Z + 0.3)})
    j0, i0 = T._cell(Vec(x - 3.0, y - 2.5, Z))
    j1, i1 = T._cell(Vec(x + 2.0, y + 2.75, Z))
    walled = int(T._wall_bit(T.walls[j0:j1, i0:i1], np.full((j1 - j0, i1 - i0), Z + 0.8)).sum())
    if len(zs) < 3 or walled < 10:
        fails.append(f"bunker stair: floor heights over the ground {zs}, cells walled at body height {walled}; want "
                     "several of each")
    # 5. the bridge (its deck at its middle, 1.6 over the ground): the ground under it kept
    lv = levels(T, *SPOTS["bridge"])
    if not (any(abs(v - Z) < 0.05 for v in lv) and any(Z + 1.5 < v < Z + 2.1 for v in lv)):
        fails.append(f"bridge: floor levels under its middle {lv}, want the ground {Z} and its deck about {Z + 1.6:.2f}")
    # 6. which pieces count
    for name, want in (("ff_tower_tall", 6), ("ff_wall_2x2_window", 6), ("ff_light_red", 0), ("ff_one_way_door_small", 0)):
        got = len(block(name, (0.0, 0.0, 0.0), AX) or ())
        if got != want:
            fails.append(f"{name}: {'with its faces' if got == 6 else 'a solid box' if got == 5 else 'left out'}, want "
                         f"{'with its faces' if want == 6 else 'left out'}")
    fails += lidar_paint(T)
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print(f"forge surfaces OK ({kinds})")


def lidar_paint(T):
    """7: LiDAR's paint (Recorder.spread, as around a standing player) on the pieces."""
    import tempfile
    sys.path.insert(0, HERE)
    import lidar
    fails = []

    def paint(x, y, lo, hi):
        rec = lidar.Recorder("reach_forge_halo", count_run=False, T=T,
                             path=os.path.join(tempfile.gettempdir(), "no_such_lidar.json"))
        n = top_node(T, x, y, lo, hi)
        if n is None:
            return None
        c = T._center(*n)
        rec.spread((c.x, c.y, c.z))
        return {k: [(a * lidar.CELL, b * lidar.CELL) for a, b, _, kk in rec.walk if kk == k]
                for k in (lidar.KIND_SPREAD, lidar.KIND_RAMP, lidar.KIND_WALL)}

    inside = lambda pts, x, y, r: [p for p in pts if abs(p[0] - x) <= r[0] and abs(p[1] - y) <= r[1]]
    for key, r in (("steep", (1.1, 1.1)), ("wedge49", (1.1, 1.1))):
        x, y = SPOTS[key]
        got = paint(x, y, Z + 0.5, Z + 2.5)
        if got is None or not got[lidar.KIND_RAMP]:
            fails.append(f"LiDAR: no ramp marked on the {key} ramp")
        elif len(inside(got[lidar.KIND_RAMP], x, y, r)) != len(got[lidar.KIND_RAMP]):
            fails.append(f"LiDAR: ramp marked off the {key} ramp: {sorted(set(got[lidar.KIND_RAMP]) - set(inside(got[lidar.KIND_RAMP], x, y, r)))[:5]}")
    x, y = SPOTS["block"]
    got = paint(x, y, Z + 0.5, Z + 1.5)
    if got is None or not got[lidar.KIND_SPREAD] or got[lidar.KIND_RAMP]:
        fails.append(f"LiDAR: block top floor {None if got is None else len(got[lidar.KIND_SPREAD])} cells, ramp "
                     f"{None if got is None else len(got[lidar.KIND_RAMP])} (want floor, no ramp)")
    for key, (x, y), wx in (("block side", SPOTS["block"], 53.0), ("wedge 55", SPOTS["wedge55"], SPOTS["wedge55"][0] - 1.0)):
        got = paint(x - 2.5, y, Z - 0.3, Z + 0.3)
        walls = [p for p in (got or {}).get(lidar.KIND_WALL, []) if abs(p[0] - wx) < 0.6 and abs(p[1] - y) < 1.0]
        if not walls:
            fails.append(f"LiDAR: the {key} not painted a wall from the ground beside it")
        if got and inside(got[lidar.KIND_RAMP], x, y, (1.1, 1.1)):
            fails.append(f"LiDAR: ramp marked on the {key}")
    return fails


if __name__ == "__main__":
    main()
