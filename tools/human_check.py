"""What in a match is not human-like. From a live trace (tools/live_bots.py, 4 world rows a second
bot rows every tick): per bot and in all,
  stuck        share of living time not moving (under 0.3 u/s for 3 s+) while its goal is to go somewhere
  look_away    share of moving time out of fights the view is 75+ degrees off the way it walks
  engage       seconds from an enemy first in its view (line of sight by the map data, within its 70 degree half-view,
               under 30 u) to its aim
               on him; and the enemies in view never aimed at before they left (ignored)
  peripheral   enemies within 45-70 degrees off its view and 15 u, in sight, for 1.5 s+, never turned to
  melee        with a melee weapon (gravity hammer, energy sword), seconds within 2.5 u of an enemy before its first
               swing; for the hammer, swings by the melee button (B) against swings by the trigger (its main attack)
  objective    share of its goal ticks on the objective; Invasion: attackers' and defenders' time within 6 u of the
               phase's territories / the core
usage: python -I human_check.py <trace.jsonl>      -> prints the report; logs/human_<trace name>.md
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MELEE_W = ("gravity_hammer", "energy_sword", "sword")


def ang(a, b):
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def main():
    path = sys.argv[1]
    team, alive, pos, yaw = {}, {}, {}, {}
    bots = set()
    still_t = collections.Counter()
    goal_t = collections.Counter()
    moving_t, away_t = collections.Counter(), collections.Counter()
    obj_t, all_t = collections.Counter(), collections.Counter()
    first_seen, aimed = {}, {}
    engage = collections.defaultdict(list)
    ignored = collections.Counter()
    periph_since, periph_n = {}, collections.Counter()
    melee_close, melee_wait = {}, collections.defaultdict(list)
    hammer_b, hammer_trig = collections.Counter(), collections.Counter()
    last_pos, last_t = {}, {}
    goal, wpn, cmd = {}, {}, {}
    near_obj = collections.Counter()
    inv = None
    T, los = None, (lambda a, b: True)
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            t = r.get("t", 0.0)
            if "meta" in r:
                bots.add(r["meta"]["bot"]["id"])
                if T is None:
                    sys.path.insert(0, ROOT)
                    from brain.maps import get_map, terrain
                    from brain.core import Vec
                    T = terrain(get_map(r["meta"]["map"]))
                    los = lambda a, b: T.los(Vec(a[0], a[1], a[2] + 0.6), Vec(b[0], b[1], b[2] + 0.6))
                continue
            if r.get("id") is not None and "goal" in r:
                i = r["id"]
                goal[i], wpn[i], cmd[i] = r.get("goal"), r.get("wpn"), r.get("cmd") or []
                all_t[i] += 1
                if r.get("goal") == "objective":
                    obj_t[i] += 1
                yaw[i] = r.get("yaw", yaw.get(i, 0.0))
                att = r.get("att") or []
                if att and att[0] == "aim":
                    aimed[(i, att[1])] = t
                # gravity hammer: the main attack is the trigger; the melee button (B) is the bash
                if wpn.get(i) == "gravity_hammer" and len(cmd[i]) > 3:
                    b = cmd[i][3]
                    if b & 16:
                        hammer_b[i] += 1
                    if b & 1:
                        hammer_trig[i] += 1
                continue
            if "world" not in r:
                continue
            if r.get("invasion"):
                inv = r["invasion"]
            rows = r["world"]
            for w in rows:
                team[w[0]], alive[w[0]] = w[1], w[2]
                pos[w[0]] = (w[3], w[4], w[5])
            for w in rows:
                i = w[0]
                if i not in bots or not w[2]:
                    last_pos.pop(i, None)
                    continue
                p = pos[i]
                lp, lt = last_pos.get(i), last_t.get(i)
                last_pos[i], last_t[i] = p, t
                if lp is None or not 0.1 < t - lt < 0.6:
                    continue
                dt = t - lt
                v = math.hypot(p[0] - lp[0], p[1] - lp[1]) / dt
                g = goal.get(i)
                if g in ("objective", "hunt", "item"):
                    goal_t[i] += dt
                    if v < 0.3:
                        still_t[i] += dt
                if v > 1.0 and g not in ("fight", "retreat"):
                    moving_t[i] += dt
                    walk = math.atan2(p[1] - lp[1], p[0] - lp[0])
                    if ang(walk, yaw.get(i, walk)) > math.radians(75):
                        away_t[i] += dt
                if inv and inv[2] is not None:
                    core = inv[2:5]
                    if math.dist(core, p) < 6.0:
                        near_obj[(team[i] == inv[1], i)] += dt
                # enemies in view / periphery / melee range
                for w2 in rows:
                    e = w2[0]
                    if not w2[2] or team.get(e) == team.get(i):
                        continue
                    q = pos[e]
                    d = math.dist(p, q)
                    if d > 30:
                        first_seen.pop((i, e), None)
                        continue
                    off = ang(math.atan2(q[1] - p[1], q[0] - p[0]), yaw.get(i, 0.0))
                    key = (i, e)
                    if off < math.radians(70) and not los(p, q):     # behind a wall: not in view
                        first_seen.pop(key, None)
                        periph_since.pop(key, None)
                        continue
                    if off < math.radians(70):
                        if key not in first_seen:
                            first_seen[key] = t
                        if aimed.get(key, -1) >= first_seen[key]:
                            engage[i].append(aimed[key] - first_seen[key])
                            first_seen[key] = 1e9          # (counted once)
                    elif key in first_seen and first_seen[key] < 1e9 and t - first_seen[key] > 3.0:
                        ignored[i] += 1
                        first_seen.pop(key)
                    if math.radians(45) < off < math.radians(70) and d < 15:
                        periph_since.setdefault(key, t)
                        if t - periph_since[key] > 1.5 and aimed.get(key, -1) < periph_since[key]:
                            periph_n[i] += 1
                            periph_since[key] = 1e9
                    else:
                        periph_since.pop(key, None)
                    if wpn.get(i) in MELEE_W:
                        if d < 2.5:
                            melee_close.setdefault(key, t)
                        elif key in melee_close:
                            melee_close.pop(key)
    out = [f"# Not human-like: {os.path.basename(path)}", ""]
    tot = lambda c: sum(c.values())
    out.append(f"- stuck (still with somewhere to go): {tot(still_t) / max(1e-9, tot(goal_t)):.0%} of goal time")
    out.append(f"- looking 75+ degrees off the way it walks: {tot(away_t) / max(1e-9, tot(moving_t)):.0%} of walking time")
    e_all = [x for v in engage.values() for x in v]
    if e_all:
        e_all.sort()
        out.append(f"- time to aim at an enemy that comes into view: median {e_all[len(e_all) // 2]:.2f} s, 90th "
                   f"{e_all[int(len(e_all) * 0.9)]:.2f} s ({len(e_all)} times); in view 3 s+ and never aimed at: "
                   f"{tot(ignored)}")
    out.append(f"- enemies at the edge of view (45-70 degrees, under 15 u) 1.5 s+ never turned to: {tot(periph_n)}")
    out.append(f"- gravity hammer: melee button (B) {tot(hammer_b)} ticks, trigger (main attack) {tot(hammer_trig)} ticks")
    out.append(f"- objective goal share: {tot(obj_t) / max(1, tot(all_t)):.0%}")
    if near_obj:
        a = sum(v for (att, _), v in near_obj.items() if att)
        d = sum(v for (att, _), v in near_obj.items() if not att)
        out.append(f"- Invasion: bot-seconds within 6 u of the core / phase objective: attackers {a:.0f}, defenders {d:.0f}")
    out.append("")
    out.append("| bot | team | stuck | look away | engage med s | ignored | periphery | objective |")
    out.append("|---|---|---|---|---|---|---|---|")
    for i in sorted(bots):
        ev = sorted(engage.get(i, []))
        out.append(f"| {i} | {team.get(i)} | {still_t[i] / max(1e-9, goal_t[i]):.0%} | {away_t[i] / max(1e-9, moving_t[i]):.0%} | "
                   f"{ev[len(ev) // 2] if ev else float('nan'):.2f} | {ignored[i]} | {periph_n[i]} | {obj_t[i] / max(1, all_t[i]):.0%} |")
    text = "\n".join(out)
    print(text)
    name = os.path.splitext(os.path.basename(path))[0]
    open(os.path.join(ROOT, "logs", f"human_{name}.md"), "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
