"""Bot-to-human Fluidity.

Measures every player of a recorded match on the same habits and scores each bot against a skilled player's habits
(maps/_human/reference.json: the median of the matches given to --learn, refreshed whenever he records more). Input: a
Data collector file (logs/collect_<map>_<stamp>.jsonl, 30 samples a second: aim habits need it) or a trace (4 a second:
the aim habits are skipped). The trace of the same match gives the bots' difficulty, guns and buttons. Built on
tools/player_stats.py (line of sight, in-view and on-target rules).

The habits (each 0-100 human-like; Fluidity = their weighted mean):
  aim_body     share of trigger time on the body (aimbot: far above the person)
  reaction     time to get the aim on a man who comes into view (too fast = aimbot, too slow = asleep)
  shot_react   time to turn onto somebody after being shot; ignored     share of first hits never answered in 3 s
  snap         turn speed when getting onto a man (degrees a second at the 95th percentile of acquisitions)
  jitter       the small corrections a hand makes while tracking (a bot's perfectly smooth aim reads 0)
  look_ahead   share of walking time, out of fights, the view is over 60 degrees off the way it goes
  priority     seconds a minute aimed at one man while ANOTHER visible man shoots at it (and is not the aim)
  standing     share of time standing still
  herding      how much a team's moving bots head the same way (1 = all the same; humans spread out)
  explore      how many zones a player's lives cover (zone entropy) and how often the route out of spawn differs
  range        share of trigger time at a man farther than the gun's hold-fire line (brain/bot.py reach() x OUT_OF_REACH)
  melee        melee presses a minute of close fighting (under 1.5 units; bots only: no keys of a person are read)
  jumps        jumps a minute
  flick180     reversals over 150 degrees in a fifth of a second, out of fights, a minute

usage: python -I fluidity.py <collect or trace> [...]         prints the report, writes logs/fluidity_<stamp>.md / .json
       python -I fluidity.py --learn <collect> [...]          the person's numbers -> maps/_human/reference.json
       python -I fluidity.py --gold <collect> [...] the bots' numbers per difficulty in a match the player
                                                              called the gold standard -> maps/_human/gold.json
"""
import collections
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import player_stats as ps  # noqa: E402
from player_stats import X, Y, Z, YAW, PITCH, SH, HP, RIDE, wrap  # noqa: E402

REF_PATH = os.path.join(ROOT, "maps", "_human", "reference.json")
MELEE_BIT, FIRE_BIT = 16, 1
CLOSE_D = 1.5
# kind: "match" = should sit near the person's value (both ways off is unnatural); "max" = worse only when above it.
# weight: how much the habit shows to a player (the aim and the walking show at once; jumps hardly)
HABITS = {
    "aim_body": ("match", 2.0), "reaction": ("match", 1.5), "shot_react": ("match", 1.0), "ignored": ("max", 1.5),
    "snap": ("match", 1.5), "jitter": ("match", 1.0), "look_ahead": ("max", 2.0), "priority": ("max", 1.5),
    "standing": ("match", 1.0), "herding": ("max", 1.5), "explore": ("match", 1.0), "route_var": ("match", 1.0),
    "range": ("max", 1.5), "melee": ("match", 1.0), "jumps": ("match", 0.5), "flick180": ("max", 0.5),
    "pitch_var": ("match", 1.0), "speed_var": ("match", 1.0), "pre_aim": ("match", 1.0), "strafe": ("match", 1.0),
    "nades": ("match", 0.5),
}
# how far off the person's value a "match" habit may be before it scores 0 (a factor): calibrated so the
# player's Cyberdyne matches ("about 40% fluid") land near what they felt (see docs/HANDOFF.md)
SPREAD = 2.0
# what a "max" habit may reach before it costs anything (absolute floor beside the person's value): a person who never
# did it in one match must not make a single bot moment a zero
FLOOR = {"ignored": 0.15, "look_ahead": 0.08, "priority": 1.0, "herding": 0.45, "range": 0.05, "flick180": 0.5}
# fallback human values until --learn writes the reference file
DEFAULT_REF = {"aim_body": 0.68, "reaction": 0.45, "shot_react": 0.40, "ignored": 0.15, "snap": 400.0, "jitter": 0.35,
               "look_ahead": 0.08, "priority": 1.0, "standing": 0.06, "herding": 0.45, "explore": 0.75,
               "route_var": 0.8, "range": 0.05, "melee": 6.0, "jumps": 5.2, "flick180": 0.5,
               "pitch_var": 6.0, "speed_var": 0.35, "pre_aim": 0.3, "strafe": 0.74, "nades": 2.0}


def score(habit, v, ref):
    """0..1 human-like. match: 1 at the person's value, 0 at SPREAD times (or 1/SPREAD of) it. max: 1 up to the
    larger of the person's value and the floor, 0 at SPREAD times that."""
    if v is None or ref is None:
        return None
    kind = HABITS[habit][0]
    if kind == "match":
        if ref <= 0:
            return 1.0 if v <= 0.05 else 0.5
        if v <= 0:
            return 0.0
        return max(0.0, 1.0 - abs(math.log(v / ref)) / math.log(SPREAD))
    cap = max(ref, FLOOR.get(habit, 0.0))
    if v <= cap:
        return 1.0
    return max(0.0, 1.0 - (v - cap) / ((SPREAD - 1.0) * cap))


def trace_series(path):
    """{bot id: [(t, wpn, buttons)]} from the brain trace's bot lines (guns and buttons the bot used)."""
    out = collections.defaultdict(list)
    if not path:
        return out
    for x in open(path, encoding="utf-8"):
        if '"cmd"' not in x:
            continue
        try:
            d = json.loads(x)
            out[d["id"]].append((d["t"], d.get("wpn", "unknown"), int(d["cmd"][3])))
        except (ValueError, KeyError, IndexError, TypeError):
            pass
    return out


class Fluid:
    def __init__(s, path):
        s.m = ps.Match(path)
        s.trim()
        s.aim_ok = s.m.kind == "collect" and s.m.dt < 0.06        # aim habits need the collector's 30 a second
        s.series = trace_series(s.m.trace if s.m.kind == "collect" else path)
        s.moments = collections.defaultdict(list)                 # habit -> [(badness, t, player id, note)]

    def trim(s):
        """Drop the stretches where nobody walked for 5 s or more: an end-game dialog froze every player for 155 s
        and the recording went on (live: read as bots standing still). Respawns jump across the map: not walking."""
        m = s.m
        if m.n < 10:
            return
        moved = np.zeros(m.n, bool)
        for i in m.ids:
            xy = np.nan_to_num(m.P[i][:, [X, Y]])
            step = np.hypot(*(xy[1:] - xy[:-1]).T)
            moved[1:] |= (step > 0.01) & (step < 1.0)
        keep = np.ones(m.n, bool)
        cut = []
        k = 0
        while k < m.n:
            if moved[k]:
                k += 1
                continue
            j = k
            while j < m.n and not moved[j]:
                j += 1
            if m.t[min(j, m.n - 1)] - m.t[k] >= 5.0:
                keep[k:j] = False
                cut.append((m.t[k], m.t[min(j, m.n - 1)]))
            k = j
        if keep.all():
            return
        m.t = m.t[keep]
        m.P = {i: a[keep] for i, a in m.P.items()}
        m.alive = {i: a[keep] for i, a in m.alive.items()}
        m.fire = {i: a[keep] for i, a in m.fire.items()}
        m.n = int(keep.sum())

    # --- helpers
    def name(s, i):
        return s.m.meta.get(i, {}).get("name", "you" if not s.m.bot[i] else f"#{i}")

    def weapon_at(s, i, tt):
        """The gun in hand at each time in tt: the trace's bot lines, the collector's gear lines for a person."""
        if s.m.bot[i] and s.series.get(i):
            ev = s.series[i]
            et = np.array([e[0] for e in ev])
            k = np.clip(np.searchsorted(et, tt, side="right") - 1, 0, len(ev) - 1)
            return [ev[j][1] for j in k]
        g = [x for x in s.m.gear if x["id"] == i]
        if not g:
            return ["unknown"] * len(tt)
        gt = np.array([x["t"] for x in g])
        k = np.clip(np.searchsorted(gt, tt, side="right") - 1, 0, len(g) - 1)
        return [g[j]["wpn"] for j in k]

    def presses(s, i, bit):
        """Times a bot's button went down (its trace); None for a person (no keys are recorded)."""
        if not s.m.bot[i]:
            return None
        ev, out, was = s.series.get(i, []), [], False
        for t, _, b in ev:
            on = bool(b & bit)
            if on and not was:
                out.append(t)
            was = on
        return np.array(out)

    def combat(s, i, step):
        """Per sampled tick: aim on a visible enemy, firing, or hit in the last 2 s."""
        m = s.m
        idx = np.arange(0, m.n, step)
        c = np.zeros(len(idx), bool)
        for foe in m.enemies(i):
            c |= m.pair(i, foe, step)[3]
        if i in m.fire:
            c |= m.fire[i][idx]
        hv = np.nan_to_num(m.P[i][idx, SH] + m.P[i][idx, HP])
        hit = np.r_[False, hv[1:] < hv[:-1] - 0.02]
        recent = hit.copy()
        for k in range(1, int(2.0 / max(m.dt * step, 1e-3)) + 1):
            recent[k:] |= hit[:-k]
        return idx, c | recent

    # --- the habits
    def aim_habits(s, i):
        """snap (deg/s), jitter (deg) while tracking, flick180 a minute out of fights."""
        if not s.aim_ok:
            return {}
        m = s.m
        a = m.P[i]
        al = m.alive[i] & (np.nan_to_num(a[:, RIDE]) == 0)
        yaw = np.unwrap(np.nan_to_num(a[:, YAW]))
        dt = np.maximum(np.diff(m.t), 1e-3)
        rate = np.degrees(np.abs(np.diff(yaw)) / dt)
        ok = al[1:] & al[:-1] & (np.diff(m.t) < 0.1)
        step = 1
        snaps, track = [], np.zeros(m.n, bool)
        for foe in m.enemies(i):
            idx, d, vis, aim, body = m.pair(i, foe, step)
            track[idx[aim]] = True
            for k in np.nonzero(aim[1:] & ~aim[:-1])[0] + 1:        # the aim just got on him
                lo = max(0, k - int(0.3 / m.dt))
                w = rate[lo:k][ok[lo:k]]
                if len(w):
                    snaps.append(float(w.max()))
                    if w.max() > 900:
                        s.moments["snap"].append((float(w.max()), float(m.t[k]), i, f"{w.max():.0f} deg/s onto {s.name(foe)}"))
        # jitter: the small wobble of the aim while it stays on a man (second difference of yaw, degrees)
        j = np.degrees(np.abs(np.diff(yaw, 2)))
        tr = track[1:-1] & track[2:] & track[:-2] & ok[1:] & ok[:-1]
        jitter = float(np.median(j[tr])) if tr.sum() > 20 else None
        idx, fight = s.combat(i, 1)
        n180, minutes = 0, ok.sum() * m.dt / 60.0
        win = max(1, int(0.2 / m.dt))
        for k in range(0, m.n - win, win):
            if not ok[k:k + win].all() or fight[min(k, len(fight) - 1)]:
                continue
            turn = abs(yaw[k + win] - yaw[k])
            if turn > math.radians(150):
                n180 += 1
                s.moments["flick180"].append((math.degrees(turn), float(m.t[k]), i, f"{math.degrees(turn):.0f} deg in 0.2 s"))
        return dict(snap=float(np.percentile(snaps, 95)) if len(snaps) >= 5 else None, jitter=jitter,
                    flick180=n180 / minutes if minutes > 0.5 else None)

    def look_ahead(s, i):
        """Share of walking time out of fights with the view over 60 degrees off the way it goes."""
        m = s.m
        step = m.step_for(i) if not s.aim_ok else max(1, int(0.1 / m.dt))
        idx, fight = s.combat(i, step)
        a = m.P[i]
        off, n = 0, 0
        streak_start = None
        for kk in range(1, len(idx)):
            k0, k = idx[kk - 1], idx[kk]
            if not (m.alive[i][k] and m.alive[i][k0]) or np.nan_to_num(a[k, RIDE]) or fight[kk]:
                streak_start = None
                continue
            dt = m.t[k] - m.t[k0]
            vx, vy = (a[k, X] - a[k0, X]) / max(dt, 1e-3), (a[k, Y] - a[k0, Y]) / max(dt, 1e-3)
            if math.hypot(vx, vy) < 1.5 or dt > 0.6:
                streak_start = None
                continue
            n += 1
            ang = abs(wrap(math.atan2(vy, vx) - a[k, YAW]))
            if ang > math.radians(60):
                off += 1
                if streak_start is None:
                    streak_start = m.t[k]
                elif m.t[k] - streak_start > 2.0 and (not s.moments["look_ahead"] or s.moments["look_ahead"][-1][2] != i
                                                    or m.t[k] - s.moments["look_ahead"][-1][1] > 5):
                    s.moments["look_ahead"].append((float(m.t[k] - streak_start), float(streak_start), i,
                                                    f"walked {m.t[k] - streak_start:.1f} s looking {math.degrees(ang):.0f} deg away"))
            else:
                streak_start = None
        return off / n if n > 30 else None

    def priority(s, i):
        """Seconds a minute aimed at one man while another visible enemy has his aim on this player."""
        m = s.m
        step = m.step_for(i)
        foes = m.enemies(i)
        if len(foes) < 2:
            return None
        idx = np.arange(0, m.n, step)
        mine = {f: m.pair(i, f, step) for f in foes}
        theirs = {f: m.pair(f, i, m.step_for(f)) for f in foes}
        his_aim = {f: np.interp(m.t[idx], m.t[theirs[f][0]], theirs[f][3].astype(float)) > 0.5 for f in foes}
        wrong = np.zeros(len(idx), bool)
        multi = np.zeros(len(idx), bool)
        for f in foes:
            others = [g for g in foes if g != f]
            on_f = mine[f][3]
            threat = np.zeros(len(idx), bool)
            for g in others:
                threat |= his_aim[g] & mine[g][2] & ~mine[g][3]        # g aims at me, I see him, I am not on him
            wrong |= on_f & threat & ~his_aim[f]                        # ... and the man I am on is not shooting me
            multi |= mine[f][2]
        dtk = m.dt * step
        minutes = m.alive[i][idx].sum() * dtk / 60.0
        k, run = 0, 0
        for k in range(len(idx)):
            run = run + 1 if wrong[k] else 0
            if run * dtk == 1.0 or (run and abs(run * dtk - 1.0) < dtk / 2):
                s.moments["priority"].append((1.0, float(m.t[idx[k]] - 1.0), i, "aimed at one man while another shot at it"))
        return float(wrong.sum() * dtk / minutes) if minutes > 0.5 else None

    def ignored(s, i):
        """Share of first hits (after 2 s untouched) the player never answered: no aim on anybody within 3 s."""
        m = s.m
        step = m.step_for(i)
        idx = np.arange(0, m.n, step)
        tt = m.t[idx]
        hv = np.nan_to_num(m.P[i][idx, SH] + m.P[i][idx, HP])
        alive = m.alive[i][idx]
        on = np.zeros(len(idx), bool)
        for foe in m.enemies(i):
            on |= m.pair(i, foe, step)[3]
        quiet, firsts, missed = tt[0] if len(tt) else 0.0, 0, 0
        for k in range(1, len(idx)):
            hit = alive[k] and alive[k - 1] and hv[k] < hv[k - 1] - 0.02
            if hit and tt[k] - quiet >= 2.0 and not on[k - 1]:
                firsts += 1
                end = np.searchsorted(tt, tt[k] + ps.REACT_MAX)
                if not on[k:end].any() and alive[k:end].all():
                    missed += 1
                    s.moments["ignored"].append((1.0, float(tt[k]), i, "shot and never turned to answer"))
            if hit or not alive[k]:
                quiet = tt[k]
        return missed / firsts if firsts >= 4 else None

    def range_use(s, i):
        """Share of trigger time aimed at a man farther than the gun in hand reaches."""
        from brain.bot import reach, OUT_OF_REACH
        m = s.m
        if i not in m.fire:
            return None
        step = m.step_for(i)
        idx = np.arange(0, m.n, step)
        fire = m.fire[i][idx] & m.alive[i][idx]
        dist = np.full(len(idx), np.inf)
        for foe in m.enemies(i):
            _, d, vis, aim, body = m.pair(i, foe, step)
            dist = np.where(aim & (d < dist), d, dist)
        aimed = fire & np.isfinite(dist)
        if aimed.sum() < 10:
            return None
        w = s.weapon_at(i, m.t[idx])
        far = np.array([aimed[k] and w[k] not in ("unknown", "none") and dist[k] > reach(w[k]) * OUT_OF_REACH
                        for k in range(len(idx))])
        last = -9.0
        for k in np.nonzero(far)[0]:
            if m.t[idx[k]] - last > 4.0:
                s.moments["range"].append((float(dist[k] / max(reach(w[k]), 0.5)), float(m.t[idx[k]]), i,
                                           f"{w[k]} fired at {dist[k]:.0f} u (reach {reach(w[k]):.0f})"))
            last = m.t[idx[k]]
        return float(far.sum() / aimed.sum())

    def melee(s, i):
        """Share of close encounters (an enemy in view within 1.5 units for 0.3 s or more) with a melee press in them
        or in the 0.5 s after."""
        m = s.m
        step = m.step_for(i)
        idx = np.arange(0, m.n, step)
        close = np.zeros(len(idx), bool)
        for foe in m.enemies(i):
            _, d, vis, aim, body = m.pair(i, foe, step)
            close |= vis & (d < CLOSE_D)
        close &= m.alive[i][idx]
        tt = m.t[idx]
        eps, start = [], None
        for k in range(len(idx)):
            if close[k] and start is None:
                start = tt[k]
            elif not close[k] and start is not None:
                if tt[k] - start >= 0.3:
                    eps.append((start, tt[k]))
                start = None
        if len(eps) < 3:
            return None
        pr = s.presses(i, MELEE_BIT)
        if pr is None:
            return None
        n = 0
        for a, b in eps:
            hit = bool(len(pr)) and bool(((pr >= a) & (pr <= b + 0.5)).any())
            n += hit
            if not hit and b - a > 1.0:
                s.moments["melee"].append((b - a, float(a), i, f"{b - a:.1f} s within arm's reach, no melee"))
        return n / len(eps)

    def body_habits(s, i):
        """pitch_var: how much the view moves up and down out of fights (degrees, std); speed_var: how much the walking
        speed varies (coefficient of variation while moving); nades: grenade presses a minute alive (bots only)."""
        m = s.m
        a = m.P[i]
        step = max(1, int(0.1 / m.dt))
        idx, fight = s.combat(i, step)
        al = m.alive[i][idx] & (np.nan_to_num(a[idx, RIDE]) == 0)
        pitch = np.degrees(np.nan_to_num(a[idx, PITCH]))
        calm = al & ~fight
        pv = float(np.std(pitch[calm])) if calm.sum() > 50 else None
        tt = m.t[idx]
        v = np.hypot(np.diff(a[idx, X]), np.diff(a[idx, Y])) / np.maximum(np.diff(tt), 1e-3)
        mv = al[1:] & al[:-1] & (v > 0.5) & (v < 15.0) & (np.diff(tt) < 0.5)
        sv = float(np.std(v[mv]) / np.mean(v[mv])) if mv.sum() > 50 else None
        minutes = m.alive[i].sum() * m.dt / 60.0
        pr = s.presses(i, 8)
        nades = len(pr) / minutes if minutes > 0.5 and pr is not None else None
        return dict(pitch_var=pv, speed_var=sv, nades=nades)

    def herding(s, team):
        """Mean over time of the length of the mean heading vector of a team's moving bots (3 or more moving)."""
        m = s.m
        bots = [i for i in m.ids if m.bot[i] and m.team[i] == team]
        if len(bots) < 3:
            return None
        step = max(1, int(1.0 / m.dt))
        R, worst = [], (0.0, 0.0)
        for k in range(step, m.n, step):
            hs = []
            for i in bots:
                a = m.P[i]
                if m.alive[i][k] and m.alive[i][k - step] and not np.nan_to_num(a[k, RIDE]):
                    vx, vy = a[k, X] - a[k - step, X], a[k, Y] - a[k - step, Y]
                    if math.hypot(vx, vy) > 1.0:
                        hs.append(math.atan2(vy, vx))
            if len(hs) >= 3:
                r = math.hypot(np.mean(np.cos(hs)), np.mean(np.sin(hs)))
                R.append(r)
                if r > 0.95 and len(hs) >= 4:
                    s.moments["herding"].append((r, float(m.t[k]), bots[0], f"{len(hs)} bots of team {team} all heading the same way"))
        return float(np.mean(R)) if len(R) > 20 else None

    def explore(s, i):
        """(zone entropy 0..1 over the match, share of lives whose way out of spawn differs from every earlier one)."""
        m = s.m
        step = max(1, int(1.0 / m.dt))
        zones, lives, cur = collections.Counter(), [], None
        for k in range(0, m.n, step):
            if not m.alive[i][k]:
                cur = None
                continue
            z = m.zone_of((m.P[i][k, X], m.P[i][k, Y], m.P[i][k, Z]))
            zones[z] += 1
            if cur is None:
                cur = []
                lives.append(cur)
            if len(cur) < 4 and (not cur or cur[-1] != z):
                cur.append(z)
        tot = sum(zones.values())
        if tot < 30 or len(zones) < 2:
            return None, None
        p = np.array(list(zones.values())) / tot
        ent = float(-(p * np.log(p)).sum() / math.log(max(2, len(m_zone_names(m)))))
        seen, new = set(), 0
        for r in lives:
            key = tuple(r[:3])
            new += key not in seen
            seen.add(key)
        return ent, (new / len(lives) if len(lives) >= 3 else None)

    # --- everything
    def player(s, i):
        m = s.m
        p = m.player(i)
        out = dict(id=i, name=p["name"], tier=p["tier"] or ("you" if not m.bot[i] else "?"), bot=m.bot[i], team=m.team[i])
        dmg = p["damage"] or {}
        v = dict(aim_body=dmg.get("on_body"), reaction=ps.med(p["reaction"]["aim"]),
                 shot_react=ps.med(p["shot_reaction"]["times"]), standing=p["move"]["standing"],
                 jumps=p["move"]["jumps_min"])
        v.update(s.aim_habits(i))
        v["look_ahead"] = s.look_ahead(i)
        v["priority"] = s.priority(i)
        v["ignored"] = s.ignored(i)
        v["range"] = s.range_use(i)
        v["melee"] = s.melee(i)
        v["explore"], v["route_var"] = s.explore(i)
        v.update(s.body_habits(i))
        r = p["reaction"]
        v["pre_aim"] = r["pre"] / (r["pre"] + len(r["aim"])) if r["pre"] + len(r["aim"]) >= 8 else None
        v["strafe"] = p["move"]["strafe"]
        out["v"] = v
        out["kills"], out["deaths"] = dmg.get("kills"), p["deaths"]
        return out

    def run(s):
        rows = [s.player(i) for i in s.m.ids]
        herd = {t: s.herding(t) for t in sorted(set(s.m.team.values()))}
        for r in rows:
            r["v"]["herding"] = herd.get(r["team"]) if r["bot"] else None
        # the yardstick: a skilled player's habits over several matches (maps/_human/reference.json, --learn); one
        # match alone was too noisy (40 s on a turret made his on-body share 17% in one, 68% in another)
        ref = dict(load_ref())
        for r in rows:
            sc = {k: score(k, r["v"].get(k), ref.get(k)) for k in HABITS}
            r["scores"] = sc
            w = [(HABITS[k][1], x) for k, x in sc.items() if x is not None]
            r["fluidity"] = 100.0 * sum(a * b for a, b in w) / sum(a for a, _ in w) if w else None
        return dict(path=s.m.path, map=s.m.map, game=s.m.game, aim_measured=s.aim_ok, ref=ref, rows=rows,
                    herding=herd, moments={k: sorted(v, reverse=True)[:8] for k, v in s.moments.items()})


def m_zone_names(m):
    """The map's zone names (for the entropy's normalisation)."""
    try:
        from brain.maps import get_map
        z = get_map(m.map)["zones"]
        names = getattr(z, "names", None) or getattr(z, "zones", None)
        return list(names) if names else [None] * 8
    except Exception:
        return [None] * 8


def load_ref():
    try:
        return json.load(open(REF_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return DEFAULT_REF


# the bots' own habits in the matches (--gold), one per map (Construct 224609 Epitaph 000613): every report shows
# its map's, so a change that drifts from it shows before he plays; a map with none shows every map's
GOLD_PATH = os.path.join(ROOT, "maps", "_human", "gold.json")


def load_gold(map_name=None):
    """{map: {matches, tiers, ...}} for the report: this map's gold, else all of them."""
    try:
        golds = json.load(open(GOLD_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if "tiers" in golds:                    # (the first file: one Construct match)
        golds = {"h3_construct": golds}
    return {map_name: golds[map_name]} if map_name in golds else golds


TIER_ORDER = ["you", "Easy", "Normal", "Heroic", "Legendary"]
LABEL = {"aim_body": "on body", "reaction": "react s", "shot_react": "shot s", "ignored": "ignored", "snap": "snap d/s",
         "jitter": "jitter", "look_ahead": "look away", "priority": "wrong tgt", "standing": "standing",
         "herding": "herding", "explore": "explore", "route_var": "routes", "range": "out range", "melee": "melee/m",
         "jumps": "jumps/m", "flick180": "flick180",
         "pitch_var": "pitch sd", "speed_var": "speed cv", "pre_aim": "pre-aim", "strafe": "strafe",
         "nades": "nades/m"}


def fmt(k, x):
    if x is None:
        return "-"
    if k in ("aim_body", "ignored", "look_ahead", "standing", "range", "melee", "pre_aim"):
        return f"{x:.0%}"
    if k in ("snap",):
        return f"{x:.0f}"
    return f"{x:.2f}"


def report(res):
    lines = [f"# Fluidity: {os.path.basename(res['path'])} ({res['map']}, {res['game']})", ""]
    if not res["aim_measured"]:
        lines.append("(trace only: the aim habits snap / jitter / flick180 need a Data collector file)")
    groups = collections.defaultdict(list)
    for r in res["rows"]:
        groups[r["tier"]].append(r)
    lines.append("## Fluidity by difficulty (100 = moves like the person in this match)")
    for t in sorted(groups, key=lambda t: TIER_ORDER.index(t) if t in TIER_ORDER else 9):
        f = [r["fluidity"] for r in groups[t] if r["fluidity"] is not None]
        lines.append(f"- {t}: {np.mean(f):.0f}%  ({len(groups[t])} players)" if f else f"- {t}: -")
    lines += ["", "## Habits (value / score)", "| who | fluid | " + " | ".join(LABEL[k] for k in HABITS) + " |",
              "|" + "---|" * (len(HABITS) + 2)]
    lines.append("| reference | | " + " | ".join(fmt(k, res["ref"].get(k)) for k in HABITS) + " |")
    for gmap, gold in load_gold(res["map"]).items():
        for t in TIER_ORDER:
            g = gold.get("tiers", {}).get(t)
            if g and t in groups:
                where = "" if gmap == res["map"] else f" ({gmap})"
                lines.append(f"| gold {t}{where} | {g.get('fluidity', 0):.0f}% | " + " | ".join(fmt(k, g.get(k)) for k in HABITS)
                             + " |")
    for r in sorted(res["rows"], key=lambda r: (TIER_ORDER.index(r["tier"]) if r["tier"] in TIER_ORDER else 9, r["name"])):
        cells = []
        for k in HABITS:
            v, sc = r["v"].get(k), r["scores"].get(k)
            cells.append("-" if v is None else f"{fmt(k, v)} / {sc * 100:.0f}" if sc is not None else fmt(k, v))
        fl = f"{r['fluidity']:.0f}%" if r["fluidity"] is not None else "-"
        lines.append(f"| {r['name']} ({r['tier']}) | {fl} | " + " | ".join(cells) + " |")
    lines += ["", "## Least human habits, by difficulty (mean score)"]
    for t in sorted(groups, key=lambda t: TIER_ORDER.index(t) if t in TIER_ORDER else 9):
        if t == "you":
            continue
        means = {}
        for k in HABITS:
            xs = [r["scores"][k] for r in groups[t] if r["scores"].get(k) is not None]
            if xs:
                means[k] = float(np.mean(xs))
        worst = sorted(means.items(), key=lambda kv: kv[1])[:5]
        lines.append(f"- {t}: " + ", ".join(f"{LABEL[k]} {v * 100:.0f}" for k, v in worst))
    lines += ["", "## Worst moments (open in the Observer at the time)"]
    names = {r["id"]: r["name"] for r in res["rows"]}
    for k, ms in res["moments"].items():
        for bad, t, i, note in ms[:4]:
            lines.append(f"- {LABEL.get(k, k)} {t:6.1f} s {names.get(i, i)}: {note}")
    return "\n".join(lines)


def digest(res, top=6):
    """A few lines for the Ollama critic (brain/critic.py): each difficulty's fluidity and least human habits."""
    groups = collections.defaultdict(list)
    for r in res["rows"]:
        if r["bot"]:
            groups[r["tier"]].append(r)
    out = []
    for t, rs in groups.items():
        f = [r["fluidity"] for r in rs if r["fluidity"] is not None]
        means = {k: np.mean([r["scores"][k] for r in rs if r["scores"].get(k) is not None]) for k in HABITS
                 if any(r["scores"].get(k) is not None for r in rs)}
        worst = sorted(means.items(), key=lambda kv: kv[1])[:top]
        vals = {k: np.mean([r["v"][k] for r in rs if r["v"].get(k) is not None]) for k, _ in worst}
        out.append(f"{t}: fluidity {np.mean(f):.0f}%; least human: " + ", ".join(
            f"{LABEL[k]} {fmt(k, vals[k])} (person {fmt(k, res['ref'].get(k))})" for k, _ in worst))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    if "--learn" in sys.argv:
        vals = collections.defaultdict(list)
        for p in args:
            res = Fluid(p).run()
            for r in res["rows"]:
                if not r["bot"]:
                    for k, x in r["v"].items():
                        if x is not None:
                            vals[k].append(x)
        ref = dict(DEFAULT_REF)
        ref.update({k: float(np.median(v)) for k, v in vals.items()})
        os.makedirs(os.path.dirname(REF_PATH), exist_ok=True)
        json.dump(ref, open(REF_PATH, "w", encoding="utf-8"), indent=1)
        print("human reference ->", REF_PATH, json.dumps(ref))
        return
    if "--gold" in sys.argv:              # (the matches given are one map's: its entry is replaced, the rest kept)
        tiers = collections.defaultdict(lambda: collections.defaultdict(list))
        maps = set()
        for p in args:
            res = Fluid(p).run()
            maps.add(res["map"])
            for r in res["rows"]:
                if r["bot"]:
                    for k, x in list(r["v"].items()) + [("fluidity", r["fluidity"])]:
                        if x is not None:
                            tiers[r["tier"]][k].append(x)
        if len(maps) != 1:
            sys.exit(f"--gold takes one map's matches (got {sorted(maps)})")
        golds = load_gold()
        golds[next(iter(maps))] = dict(
            matches=[os.path.basename(p) for p in args],
            tiers={t: {k: float(np.median(v)) for k, v in hs.items()} for t, hs in tiers.items()})
        os.makedirs(os.path.dirname(GOLD_PATH), exist_ok=True)
        json.dump(golds, open(GOLD_PATH, "w", encoding="utf-8"), indent=1)
        print("gold standard ->", GOLD_PATH, sorted(golds))
        return
    for p in args:
        res = Fluid(p).run()
        text = report(res)
        print(text)
        stem = os.path.basename(p).replace("collect_", "").replace("trace_", "").replace(".jsonl", "")
        open(os.path.join(ROOT, "logs", f"fluidity_{stem}.md"), "w", encoding="utf-8").write(text)
        json.dump(res, open(os.path.join(ROOT, "logs", f"fluidity_{stem}.json"), "w", encoding="utf-8"), default=float)


if __name__ == "__main__":
    main()
