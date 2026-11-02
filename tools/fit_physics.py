"""Each game's real gravity and jump speed, measured from players in the air in recorded matches
(logs/trace_*.jsonl: every bot's position each tick). A body in the air follows a parabola in
height over time: its curvature is gravity (times the character's gravity scale), its slope where
it left the ground is the jump speed. The editing kits give jump speeds but not every engine's
base gravity (tools/jumpphys.py); this measures it.

usage: python -I fit_physics.py [game ...]      (ce h2 h2a h3 odst reach h4; default all)
"""
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "..", "logs")
sys.path.insert(0, HERE)
from jumpphys import game_of  # noqa: E402

WIN = 9                   # samples per fitted window (~0.3 s)


def tracks(path):
    """{id: [(t, z, x, y)]} sorted by time, from a trace."""
    out = {}
    for line in open(path):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        p = r.get("pos")
        if p and len(p) >= 3:
            out.setdefault(r["id"], []).append((r["t"], p[2], p[0], p[1]))
    for v in out.values():
        v.sort()
    return out


def arcs(rows):
    """Stretches of a path that are parabolas in height (in the air): [(t array, z array, fit)]."""
    t = np.array([r[0] for r in rows])
    z = np.array([r[1] for r in rows])
    xy = np.array([r[2:] for r in rows])
    out, k = [], 0
    while k + WIN <= len(t):
        tt, zz = t[k:k + WIN], z[k:k + WIN]
        dt = np.diff(tt)
        if dt.min() <= 0 or dt.max() > 0.08 or np.hypot(*(xy[k + WIN - 1] - xy[k])) > 3.0:
            k += 1
            continue
        c = np.polyfit(tt - tt[0], zz, 2)
        res = zz - np.polyval(c, tt - tt[0])
        acc = 2 * c[0]
        if -25 < acc < -0.8 and np.sqrt(np.mean(res ** 2)) < 0.004 and np.ptp(zz) > 0.05:
            end = k + WIN                      # grow while it stays on the same parabola
            while end < len(t) and t[end] - t[end - 1] < 0.08:
                c2 = np.polyfit(t[k:end + 1] - tt[0], z[k:end + 1], 2)
                if np.sqrt(np.mean((z[k:end + 1] - np.polyval(c2, t[k:end + 1] - tt[0])) ** 2)) > 0.004:
                    break
                c, end = c2, end + 1
            out.append((t[k:end], z[k:end], c, k, end))
            k = end
        else:
            k += 1
    return out


def peak(values, step=0.05, lo=0.5, hi=8.0):
    """The most common value (histogram peak), refined as the median of the values near it."""
    v = np.asarray(values, float)
    hist, edges = np.histogram(v, bins=np.arange(lo, hi, step))
    m = edges[np.argmax(hist)] + step / 2
    near = v[np.abs(v - m) < 3 * step]
    return float(np.median(near)), int(len(near))


def run_speeds(rows):
    """Horizontal speeds over 0.3 s on flat ground (height steady), moving."""
    out = []
    for k in range(0, len(rows) - 10, 5):
        a, b = rows[k], rows[k + 9]
        dt = b[0] - a[0]
        zs = [r[1] for r in rows[k:k + 10]]
        if 0.2 < dt < 0.5 and max(zs) - min(zs) < 0.01:
            v = math.hypot(b[2] - a[2], b[3] - a[3]) / dt
            if v > 0.8:
                out.append(v)
    return out


def fit_game(game, paths):
    accs, launches, runs = [], [], []
    for path in paths:
        for rows in tracks(path).values():
            runs += run_speeds(rows)
            for tt, zz, c, k, end in arcs(rows):
                g = -2 * c[0]
                if tt[-1] - tt[0] >= 0.5:            # half a second in the air: not a hump in the ground
                    accs.append((g, len(tt)))
                # a jump: the sample before the arc on the ground (flat), the arc starts going up
                if k >= 3:
                    before = np.array([r[1] for r in rows[k - 3:k]])
                    if np.ptp(before) < 0.02 and c[1] > 0.3:
                        t_up = tt[0] - rows[k - 1][0]          # time from the last ground sample
                        z0 = before[-1]
                        # when the parabola left z0: solve c0 t^2 + c1 t + c2 = z0 for the earlier root
                        a2, b2, c2 = c[0], c[1], c[2] - z0
                        disc = b2 * b2 - 4 * a2 * c2
                        if disc >= 0:
                            r1 = (-b2 + math.sqrt(disc)) / (2 * a2)
                            r2 = (-b2 - math.sqrt(disc)) / (2 * a2)
                            t0 = max(r for r in (r1, r2) if r <= 0.01) if any(r <= 0.01 for r in (r1, r2)) else None
                            if t0 is not None and -0.1 <= t0 <= 0.01:
                                launches.append(c[1] + 2 * c[0] * t0)  # slope where it left the ground
    if not accs:
        return None
    g, gn = peak([a for a, n in accs])
    out = dict(game=game, arcs=len(accs), gravity=round(g, 3), gravity_n=gn)
    if launches:
        v, vn = peak(launches)
        out.update(jumps=len(launches), jump_speed=round(v, 3), jump_speed_n=vn, apex=round(v * v / (2 * g), 3))
    if runs:
        r, rn = peak(runs, step=0.02)
        out.update(run_speed=round(r, 3), run_n=rn)
    return out


def main():
    want = sys.argv[1:] or ["ce", "h2", "h2a", "h3", "odst", "reach", "h4"]
    by = {}
    for p in sorted(glob.glob(os.path.join(LOGS, "trace_*.jsonl"))):
        name = os.path.basename(p)[6:-6]
        if os.path.getsize(p) == 0:
            continue
        g = game_of(name) if name.startswith(("h2_", "h2a_", "h3_", "h4_", "odst_", "reach_")) else "ce"
        by.setdefault(g, []).append(p)
    for game in want:
        r = fit_game(game, by.get(game, []))
        print(game, len(by.get(game, [])), "traces:", r, flush=True)


if __name__ == "__main__":
    main()
