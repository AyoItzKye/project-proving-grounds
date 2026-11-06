"""A low ceiling over floor nobody walked is no floor (Terrain._low_ceiling). Spire, live S6-S9 (traces in
logs/tmp/invasion_regress/traces): attackers stalled 22-70 s at (-128.6..-131.2, -344..-346.3, -61) on the way to
phase 1's territory B; the nav ran them north under a rock lip leaning over the floor (wall bits at 0.62-0.7 over
it, none at the chest or at 0.85) where no person walked, people walked the open strip south of it.

1. From the stall spots the nav's way to territory B keeps out of the rock's cells (y north of -344.3 for x -133.5 to
   -129.7) and goes by the strip people walked.
2. The rock's cell (-129.89, -343.82) the old way went through is not walkable, the strip's (-130.0, -345.25) is; a cell people walked under a
   wall bit at those heights stays walkable (their walk is the truth there).
3. Without people's walks (walked=None) the rule is off: the wall bits alone are as before.

usage: python -I test_low_ceiling.py      -> "low_ceiling OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

B = Vec(-159.791, -348.584, -55.086)


def way(T, a, n=40):
    pts, p = [], a
    for _ in range(n):
        w = T.nav(p, B, jump=True, human=True)
        if w is None or (w - p).length() < 0.05:
            break
        pts.append(w)
        p = Vec(w.x, w.y, w.z)
    return pts


def main():
    fails = []
    T = terrain(get_map("reach_35_island"))
    under = lambda q: -133.5 <= q.x <= -129.7 and q.y > -344.3 and q.z < -59.5
    for a in (Vec(-128.6, -344.2, -61.5), Vec(-131.1, -345.4, -60.9), Vec(-129.1, -344.4, -61.3)):
        bad = [(round(q.x, 2), round(q.y, 2)) for q in way(T, a) if under(q)]
        if bad:
            fails.append(f"from ({a.x}, {a.y}): the way runs under the rock at {bad[:3]}")
    # the live layout (Invasion: Spire, variant v3977bae2: S10 bot 3 stalled 26.6 s at (-128.7, -344.3)): its LiDAR has
    # the bots' own records under the rock; only a person's walk keeps a low ceiling open
    TV = terrain(get_map("reach_35_island/variants/v3977bae2"))
    bad = [(round(q.x, 2), round(q.y, 2)) for q in way(TV, Vec(-128.7, -344.3, -61.5)) if under(q)]
    if bad:
        fails.append(f"Spire's Invasion layout, from (-128.7, -344.3): the way runs under the rock at {bad[:3]}")
    # 4. the same rock's low faces (knee to eye walled, open at 0.85): the owner's 233940 flag at 85 s, TheSkull wedged
    #    at (-131.38, -346.0); the way from the attackers' side ran 0.28 u past the face at (-125.9, -342.1)
    for a in (Vec(-118.0, -340.0, -60.8), Vec(-110.0, -346.0, -60.8)):
        pts = way(TV, a, 60)
        for sx, sy in ((-125.9, -342.1), (-131.6, -347.4), (-131.38, -346.0)):
            d = min((((q.x - sx) ** 2 + (q.y - sy) ** 2) ** 0.5 for q in pts), default=99)
            if d < 1.0:
                fails.append(f"from ({a.x}, {a.y}): the way passes {d:.2f} u from the rock face at ({sx}, {sy})")
    node = lambda x, y: T._node_at(x, y, -61.0)          # (the cell itself: _node moves onto a walkable neighbour)
    if T.lwalk[node(-129.89, -343.82)]:
        fails.append("the cell under the rock (-129.89, -343.82), on the old way, is walkable")
    if not T.lwalk[node(-130.0, -345.25)]:
        fails.append("the strip people walked (-130.0, -345.25) is not walkable")
    step = int(round(0.25 / T.cell))

    saved = T.walked_cells
    T.walked_cells = None
    if T._low_ceiling(T.walls[::step, ::step]).any():
        fails.append("no people's walks: the rule still closed cells")
    T.walked_cells = saved
    # a walked cell with the same wall bits stays open: mark the rock cell walked, it is not closed
    l, j, i = node(-129.89, -343.82)
    x, y = T.x0 + (i + 0.5) * 0.25, T.y0 + (j + 0.5) * 0.25
    T.walked_cells = set(saved) | {(round(x / 0.25), round(y / 0.25), round(float(T.lz[l, j, i]) / 0.1))}
    if T._low_ceiling(T.walls[::step, ::step])[l, j, i]:
        fails.append("a cell people walked was closed by the wall bits over it")
    T.walked_cells = saved
    if fails:
        print("low_ceiling FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("low_ceiling OK")


if __name__ == "__main__":
    main()
