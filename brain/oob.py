"""Out of bounds: where nobody may be. The games' soft kill zones (the "return to the battlefield" count) and kill zones
are not read from the maps; they are learned where they show:

  death  a player died with nobody who could have killed him: alive and on foot, health and shield full a second
         before, no fall (under FALL u down in the last 2 s), no enemy within NEAR u and none in sight within SIGHT u,
         and not one of several deaths at once (a round's reset). One such death is a candidate; it counts once a
         second one lands within R of it, or at once if no enemy was alive within ALONE u
  flag the player's bug report naming it ("out of bounds", "oob", "kill zone", "soft kill", "kill barrier"): at once,
         where he stood

Kept per map or Forge layout in maps/<map>/oob.json: {"spots": [[x, y, z, source, t, note]], "candidates": [...]}.
Terrain.set_oob (brain/terrain.py) makes the counted spots a soft wall: a step into a cell within R (and DZ of its
height) costs a barrier's, a goal there moves out, the vehicles' ground leaves it out, a pilot's probe sees it within
AIR_DZ of its height.
"""
import json
import math
import os
import re
import time

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps")
R, DZ, AIR_DZ = 4.0, 3.0, 8.0      # u: a spot's soft wall round it, its floors' height band, a pilot's
NEAR, SIGHT, ALONE, FALL = 6.0, 80.0, 80.0, 3.0   # (ALONE as SIGHT: a sniper 60 u off through a gap the level
# data has as solid is no out of bounds until a second death there)
FULL = 0.9                         # health and shield a second before: nothing had hurt him
AT_ONCE = 3                        # this many deaths inside a second: a reset, not a zone
WORDS = re.compile(r"out of bounds|\boob\b|kill ?zone|soft ?kill|kill ?barrier|kill ?boundar", re.I)


def path_of(map_name):
    return os.path.join(ROOT, map_name, "oob.json")


def load(map_name):
    try:
        d = json.load(open(path_of(map_name), encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    return {"spots": d.get("spots", []), "candidates": d.get("candidates", [])}


class Oob:
    """The map's out of bounds, watched live (the brain's loop and LiDAR's: watch every tick, flag per bug report)."""

    def __init__(s, map_name, clock=time.time):
        s.map, s.clock = map_name, clock
        d = load(map_name)
        s.spots, s.candidates = d["spots"], d["candidates"]
        s.hist, s.version = {}, 0              # (id -> [(t, pos, health, shield, riding)] last 2 s); bumped on change

    def _add(s, x, y, z, source, t, note=""):
        s.spots.append([round(x, 2), round(y, 2), round(z, 2), source, round(t, 1), note[:80]])
        s.version += 1

    def flag(s, text, pos, t):
        """the player's bug report: a spot where he stood when it names out of bounds. True if it did."""
        if not pos or not WORDS.search(text or ""):
            return False
        s._add(pos[0], pos[1], pos[2], "flag", t, text)
        return True

    def watch(s, now, people, sees=None):
        """people: [(id, team, (x, y, z) or None, alive, health, shield, riding)] this tick. sees(a, b): a clear line of
        sight between two places (the terrain's), or None (then nobody in sight counts only past SIGHT). Returns the
        deaths it took for out of bounds this tick, [(x, y, z, counted)]."""
        out, died = [], []
        for pid, team, pos, alive, hp, sh, riding in people:
            h = s.hist.setdefault(pid, [])
            if alive and pos is not None:
                h.append((now, pos, hp, sh, riding))
                while h and now - h[0][0] > 2.0:
                    h.pop(0)
            elif not alive and h:
                died.append((pid, team, h[-1], list(h)))
                s.hist[pid] = []
        if len(died) >= AT_ONCE:
            return out
        living = [(team, h[-1][1]) for pid, team, *_ in people for h in [s.hist.get(pid)] if h]
        for pid, team, last, h in died:
            t, pos, hp, sh, riding = last
            before = [e for e in h if now - e[0] >= 0.8] or h[:1]
            # riding: counted only with the vehicle's health read full before too (the player: a bot pilot flew him
            # out of bounds; a wreck kills its crew without a scratch on them, an unread vehicle stays skipped)
            hurt = [e[4] for e in before if e[4] is not False]
            if any(r is True or r < FULL for r in hurt) or min(e[2] for e in before) < FULL \
                    or min(e[3] for e in before) < FULL:
                continue
            if max(e[1][2] for e in h) - pos[2] >= FALL:
                continue                                     # a fall (LiDAR's deadly drops have it)
            foes = [q for tm, q in living if tm != team or tm < 0]
            near = [q for q in foes if math.dist(q, pos) < SIGHT]
            if any(math.dist(q, pos) < NEAR for q in near):
                continue
            if near and (sees is None or any(sees(q, pos) for q in near)):
                continue                                     # (no sight lines to test: anyone within SIGHT could)
            alone = not any(math.dist(q, pos) < ALONE for q in foes)
            twin = next((c for c in s.candidates if math.dist(c[:2], pos[:2]) < R and abs(c[2] - pos[2]) < DZ), None)
            counted = alone or twin is not None
            if counted:
                s._add(pos[0], pos[1], pos[2], "death", now, "alone" if alone else "twice")
                if twin is not None:
                    s.candidates.remove(twin)
            else:
                s.candidates.append([round(pos[0], 2), round(pos[1], 2), round(pos[2], 2), round(now, 1)])
            out.append((pos[0], pos[1], pos[2], counted))
        return out

    def save(s):
        p = path_of(s.map)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        json.dump({"spots": s.spots, "candidates": s.candidates}, open(tmp, "w", encoding="utf-8"), indent=1)
        os.replace(tmp, p)
        return p


def features(map_name, data=None):
    """The counted spots as the LiDAR view's zones (tools/lidar.py load_features)."""
    d = data if data is not None else load(map_name)
    return [dict(kind="zone", name=f"out of bounds ({sp[3]})", pos=sp[:3], station="out_of_bounds") for sp in d["spots"]]
