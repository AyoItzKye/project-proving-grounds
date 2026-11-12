"""Power spots: how good a place is to hold, read from the level data and from where people died (the player's ask, Nov 12:
bots in Oddball left good covered places to run about; a sniper's spot and a ball spot are not the same).

kind "ball": an objective held from inside. Walls round it (enclosure: the share of 16 directions with a wall within
  RING_R), a roof (a floor 2-8 u over it), few ways in (entrances: separate open arcs of those 16 directions; one or two
  best, none is a sealed pocket and no spot at all), little death there (heat: deaths within HEAT_R, LiDAR's records).
kind "sniper": high ground with long sight lines (the share of sample floor points 15-70 u off seen from its eye), a
  wall at its back or side, little death there.

Scores are 0..about 5. spots(T, m, kind) lists (score, Vec) best first, made once per map and kind (a few hundred
candidates; clearance and sight rays only on the ones that pass the cheap filters)."""
import json
import math
import os
import random

import numpy as np

from .core import Vec, dist

ARC = 16
RING_R = 6.0           # u: a wall this near in a direction counts toward enclosure; an arc open this far is a way in
HEAT_R = 5.0           # u: deaths this near a spot count toward its heat
MAX_CANDS = 450        # candidates scored a kind (sampled, seeded: the same every run)
_CACHE = {}


def deaths_of(m):
    """Where people and bots died on map m (maps/<map>/lidar.json and lidar_sim.json: LiDAR's deaths)."""
    from .maps import ROOT
    out = []
    for fn in ("lidar.json", "lidar_sim.json"):
        p = os.path.join(ROOT, m["name"], fn)
        try:
            out += [Vec(*d["pos"][:3]) for d in (json.load(open(p, encoding="utf-8")).get("deaths") or []) if "pos" in d]
        except (OSError, ValueError, TypeError, KeyError):
            pass
    return out


def ring(T, p, far=RING_R):
    """Clearance in 16 directions from p (the 'crosshair distance' all round)."""
    return [T.clearance(p, k * 2 * math.pi / ARC, far) for k in range(ARC)]


def entrances(cl, far=RING_R):
    """Ways in: the separate runs of directions open to far (all open: ARC, the open ground)."""
    open_ = [c >= far * 0.95 for c in cl]
    if all(open_):
        return ARC
    return sum(1 for k in range(ARC) if open_[k] and not open_[k - 1])


def roofed(T, p):
    j, i = T._cell(p)
    col = T.lz[:, j, i]
    return bool(np.any(np.isfinite(col) & (col > p.z + 2.0) & (col < p.z + 8.0)))


def heat(p, deaths):
    return min(1.0, sum(1 for d in deaths if dist(d, p) < HEAT_R) / 5.0)


ENT_SCORE = {0: 0.0, 1: 1.0, 2: 1.0, 3: 0.6, 4: 0.3}
FLOOD_R, FLOOD_STEP = 10.0, 2      # u, fine cells a step (0.5 u: a doorway between wall cells): the walk-flood round a spot
STEP_UP = 1.1                      # u up or down a 1 u step: a stair (0.5 u risers half a unit apart)
CRAMPED = 48                       # 0.5 u cells (12 square u): a room this small is a grenade trap


def flood(T, p, r=FLOOD_R):
    """Walk out from p over the floor of its level (steps of 1 u, no step through a wall cell or up / down more than 0.6
    u) up to r: (cells reached, share of the r-disk reached, ways out: separate runs of 16 directions in which the flood
    reached the edge)."""
    l0, j0, i0 = T._node(p)
    k = FLOOD_STEP
    R = int(r / 0.25 / k)
    seen = {(j0, i0): float(T.lz[l0, j0, i0])}
    todo = [(j0, i0)]
    edge = set()
    while todo:
        j, i = todo.pop()
        z = seen[(j, i)]
        for dj, di in ((k, 0), (-k, 0), (0, k), (0, -k)):
            jj, ii = j + dj, i + di
            if (jj, ii) in seen or not (0 <= jj < T.nh and 0 <= ii < T.nw):
                continue
            if ((jj - j0) ** 2 + (ii - i0) ** 2) > (R * k) ** 2:
                edge.add(int(round(math.atan2(jj - j0, ii - i0) / (2 * math.pi / ARC))) % ARC)
                continue
            col = T.lz[:, jj, ii]
            ok = [l for l in range(T.L) if T.lwalk[l, jj, ii] and abs(col[l] - z) < STEP_UP]
            if not ok:
                continue
            zz = float(col[ok[0]])
            # (the fine cells between: a wall a cell thick stops it)
            if any(not np.any(T.lwalk[:, j + dj * t // k, i + di * t // k] & (np.abs(T.lz[:, j + dj * t // k,
                                                                                    i + di * t // k] - z) < 0.6))
                   for t in range(1, k)):
                continue
            seen[(jj, ii)] = zz
            todo.append((jj, ii))
    ways = sum(1 for d in range(ARC) if d in edge and (d - 1) % ARC not in edge)
    if edge and len(edge) == ARC:
        ways = ARC
    return len(seen), len(seen) / max(1.0, math.pi * R * R), ways


def ball_score(T, p, deaths, cl=None):
    """kind "ball" score of p: walls round it (1 - the share of the 10 u disk walkable from it), one or two ways out of
    it best, a roof, no cramped closet (CRAMPED), little death (0 for a pocket with no way out)."""
    n, share, ways = flood(T, p)
    if ways == 0:
        return 0.0
    return (2.0 * (1.0 - min(1.0, share)) + 1.5 * ENT_SCORE.get(ways, 0.0) + (1.0 if roofed(T, p) else 0.0)
            - (1.0 if n < CRAMPED else 0.0) - 1.0 * heat(p, deaths))


def _floor_cells(T, stride):
    """Walkable floor points on a stride grid (every level), as Vec."""
    out = []
    L, H, W = T.lz.shape
    for l in range(L):
        js, is_ = np.nonzero(T.lwalk[l, ::stride, ::stride])
        for j, i in zip(js * stride, is_ * stride):
            out.append(T._center(l, int(j), int(i)))
    return out


def spots(T, m, kind="ball"):
    """(score, Vec) best first for this map and kind, made once."""
    key = (m["name"], kind)
    if key in _CACHE:
        return _CACHE[key]
    from .terrain import NAV_CELL
    rng = random.Random(7)
    cells = _floor_cells(T, max(1, int(round(2.0 / NAV_CELL))))
    deaths = deaths_of(m)
    out = []
    if kind == "ball":
        cands = [p for p in cells if roofed(T, p)]
        if len(cands) < 40:                       # (an open map: the walled ones instead of the roofed)
            cands = cells
        cands = rng.sample(cands, min(MAX_CANDS, len(cands)))
        out = [(ball_score(T, p, deaths), p) for p in cands]
    elif kind == "sniper":
        zs = sorted(p.z for p in cells)
        if not zs:
            return []
        hi = zs[int(0.7 * (len(zs) - 1))]
        lo, top = zs[0], zs[-1]
        cands = rng.sample([p for p in cells if p.z >= hi], min(MAX_CANDS // 3, sum(1 for p in cells if p.z >= hi)))
        probes = rng.sample(cells, min(60, len(cells)))
        for p in cands:
            far = [q for q in probes if 15.0 < dist(p, q) < 70.0]
            if not far:
                continue
            sight = sum(1 for q in far if T.sees(p, q)) / len(far)
            cl = ring(T, p, 3.0)
            back = 1.0 if sum(1 for c in cl if c < 2.85) >= 3 else 0.0
            out.append((3.0 * sight + (p.z - lo) / max(top - lo, 1.0) + 0.5 * back - heat(p, deaths), p))
    out.sort(key=lambda sp: -sp[0])
    _CACHE[key] = out
    return out


def best_near(T, m, kind, near, r, n=1, exclude=()):
    """The best n spots of a kind within r of near (and none within 3 u of exclude)."""
    got = [(sc, p) for sc, p in spots(T, m, kind) if dist(p, near) < r and all(dist(p, x) > 3.0 for x in exclude)]
    return got[:n]
