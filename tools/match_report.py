"""Match report from a brain trace (live: logs\\trace_<map>.jsonl when logs\\trace_on exists; offline:
brain.sim --trace). the player: tools to track movement and gameplay, so stuck bots, blobs,
self-deaths, games that do not end on score and fights that do not happen show up in numbers and on
the map, not only by watching.

Reads two kinds of lines: a bot line per bot per tick {t, id, pos, goal, cmd, foes, ...} and (newer
traces) a world line {t, world: [[id, team, alive, x, y, z, shield, health, bot, flag], ...], score,
limit, time_left, mode, posture}. Older traces have bot lines only; the report says what it lacks.

Writes logs\\report_<name>.md and logs\\report_<name>.png (the map's topdown with where bots were,
where they got stuck, where teammates bunched up and where everyone died).

usage: python -I match_report.py <trace.jsonl> [--map <map>] [--skip 5]
"""
import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)

FIRE = 1                 # botctl.BTN["fire"]
STUCK_S = 2.0            # trying to move for this long without getting 0.5 units anywhere
CROWD_R, CROWD_N = 4.0, 3       # three or more teammates within 4 units of one another: a blob
TOUCH_R = 1.5            # a teammate this close: bumping into each other
NO_ENEMY_R = 60.0        # died with no enemy alive this close: a self-death (fall, own explosive)
FALL_DZ = 2.5            # dropped this far in the last 1.5 s before dying: a fall


def load(path):
    bots, world = collections.defaultdict(list), []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if "world" in r:
            world.append(r)
        elif "id" in r and "cmd" in r:       # bot ticks (decision lines carry "think", no "cmd")
            bots[r["id"]].append(r)
    return bots, world


def stuck_episodes(rows):
    """[(t0, t1, x, y)] where the bot pushed its stick (forward/strafe >= 0.5) for STUCK_S seconds
    and stayed within 0.5 units, not fighting (fight strafes in place on purpose)."""
    out, start = [], None
    for r in rows:
        f, s = r["cmd"][0], r["cmd"][1]
        pushing = math.hypot(f, s) >= 0.5 and r["goal"] not in ("fight", "retreat") and r.get("veh", -1) == -1
        if pushing:
            if start is None or math.dist(start["pos"][:2], r["pos"][:2]) > 0.5:
                if start is not None and r["t"] - start["t"] >= STUCK_S:
                    out.append((start["t"], r["t"], start["pos"][0], start["pos"][1]))
                start = r
        else:
            if start is not None and r["t"] - start["t"] >= STUCK_S:
                out.append((start["t"], r["t"], start["pos"][0], start["pos"][1]))
            start = None
    return out


def deaths_from_world(world):
    """[(t, id, team, pos, kind)] kind = fall | alone | combat, from alive -> dead in world lines."""
    out, prev, path = [], {}, collections.defaultdict(collections.deque)
    for w in world:
        t = w["t"]
        rows = {p[0]: p for p in w["world"]}
        gone = sum(1 for pid, p in rows.items() if not p[2] and prev.get(pid) is not None and prev[pid][2])
        if gone >= max(3, len(rows) // 2):      # half the players or more at once: the match ended (or a new
            prev = rows                         # round), not deaths (Lockdown game 3: all 6 "alone" deaths
            continue                            # were the end of the match; live_bots does the same)
        for pid, p in rows.items():
            alive, pos = p[2], p[3:6]
            if alive:
                q = path[pid]
                q.append((t, pos))
                while q and t - q[0][0] > 1.5:
                    q.popleft()
            was = prev.get(pid)
            if was is not None and was[2] and not alive:
                last = was[3:6]
                hist = path[pid]
                top = max((z for _, (x, y, z) in hist), default=last[2])
                foes = [o for o in rows.values() if o[1] != was[1] and o[2] and math.dist(o[3:5], last[:2]) < NO_ENEMY_R]
                kind = "fall" if top - last[2] > FALL_DZ else ("alone" if not foes else "combat")
                out.append((t, pid, was[1], last, kind))
                path[pid].clear()
        prev = rows
    return out


def crowding(world, skip_spawn=5.0):
    """Per team: share of samples with a blob (CROWD_N+ alive teammates within CROWD_R of one of them),
    share of bot-samples touching a teammate, and where blobs happened."""
    blob_t, touch, samples, spots = collections.Counter(), collections.Counter(), collections.Counter(), []
    spawned = {}
    for w in world:
        t = w["t"]
        live = [p for p in w["world"] if p[2]]
        for p in w["world"]:
            if not p[2]:
                spawned[p[0]] = None
            elif spawned.get(p[0], "x") is None:
                spawned[p[0]] = t
        teams = collections.defaultdict(list)
        for p in live:
            if p[8] and t - (spawned.get(p[0]) or -99) > skip_spawn:   # bots only, not just respawned
                teams[p[1]].append(p)
        for team, ps in teams.items():
            samples[team] += 1
            for p in ps:
                if any(q is not p and math.dist(p[3:5], q[3:5]) < TOUCH_R and abs(p[5] - q[5]) < 1.0 for q in ps):
                    touch[team] += 1
            for p in ps:
                near = [q for q in ps if math.dist(p[3:5], q[3:5]) < CROWD_R and abs(p[5] - q[5]) < 1.5]
                if len(near) >= CROWD_N:
                    blob_t[team] += 1
                    spots.append((t, team, p[3], p[4], len(near)))
                    break
    return blob_t, touch, samples, spots


def report(path, map_name=None, skip=0.0):
    bots, world = load(path)
    name = os.path.splitext(os.path.basename(path))[0].replace("trace_", "")
    lines = [f"# Match report: {name}", "", f"Trace {path}"]
    if not bots:
        return "\n".join(lines + ["", "No bot lines."]), None
    t0 = min(rs[0]["t"] for rs in bots.values())
    t1 = max(rs[-1]["t"] for rs in bots.values())
    span = max(t1 - t0, 1e-6)
    lines += [f"Length {span / 60:.1f} min, {len(bots)} bots" + ("" if world else " (no world lines: old trace, "
              "score, deaths by kind and blobs need a newer one)"), ""]
    # --- score
    if world:
        # the last line the game's match state was read on: after the end the memory is reused
        # (live_bots drops it and the line falls back to a 0-0 score with no limit)
        last = next((w for w in reversed(world) if w.get("limit")), world[-1])
        sc, lim, tl = last.get("score") or {}, last.get("limit") or 0, last.get("time_left")
        mode = last.get("mode", "?")
        lines.append(f"## Score ({mode})")
        lines.append(f"Final {sc}, limit {lim or 'unknown'}, time left {tl if tl is not None else 'unknown'}")
        if sc:
            best = max(sc.values())
            ended = ("score limit reached" if lim and best >= lim else
                     "time ran out" if tl is not None and tl <= 1 else "still running when the trace ended")
            rate = best / (span / 60)
            proj = (lim - best) / rate if lim and rate > 0 and best < lim else 0.0
            lines.append(f"Ended: {ended}. Leader's pace {rate:.2f} points/min" +
                         (f", {proj:.1f} more minutes to the limit at this pace" if proj else ""))
        post = collections.Counter(w.get("posture", {}).get(str(k), "?") if isinstance(w.get("posture"), dict) else "?"
                                   for w in world for k in (0, 1))
        if any(k != "?" for k in post):
            lines.append("Posture samples (both teams): " + ", ".join(f"{k} {v}" for k, v in post.most_common()))
        lines.append("")
    # --- deaths
    deaths = deaths_from_world(world) if world else []
    if world:
        kinds = collections.Counter(d[4] for d in deaths)
        bot_ids = {p[0] for w in world for p in w["world"] if p[8]}
        lines.append("## Deaths")
        lines.append(f"{len(deaths)} deaths, {len(deaths) / (span / 60):.1f} per minute: combat {kinds['combat']}, "
                     f"falls {kinds['fall']}, alone (no enemy within {NO_ENEMY_R:.0f}: own grenade, rocket, fall the "
                     f"trace missed) {kinds['alone']}")
        per = collections.Counter(d[1] for d in deaths if d[1] in bot_ids)
        lines.append("Per bot: " + ", ".join(f"{k}: {v}" for k, v in sorted(per.items())))
        lines.append("")
    # --- movement
    lines.append("## Movement")
    stuck_all, idle = [], {}
    for bid, rs in sorted(bots.items()):
        rs = [r for r in rs if r["t"] - t0 >= skip]
        ep = stuck_episodes(rs)
        stuck_all += [(bid,) + e for e in ep]
        still = sum(1 for a, b in zip(rs, rs[1:]) if math.dist(a["pos"][:2], b["pos"][:2]) < 0.01
                    and b["goal"] not in ("fight", "hold") and math.hypot(*b["cmd"][:2]) < 0.1)
        idle[bid] = still / max(1, len(rs))
    stuck_s = sum(e[2] - e[1] for e in stuck_all)
    lines.append(f"Stuck episodes (pushing {STUCK_S:.0f}+ s without moving): {len(stuck_all)}, {stuck_s:.0f} s in all "
                 f"({stuck_s / (span * len(bots)) * 100:.1f}% of bot time)")
    spots = collections.Counter((round(e[3] / 2) * 2, round(e[4] / 2) * 2) for e in stuck_all)
    if spots:
        lines.append("Worst spots (2-unit cells): " + ", ".join(f"({x}, {y}) x{n}" for (x, y), n in spots.most_common(8)))
    lines.append("Idle share (not moving, not fighting or holding) per bot: " +
                 ", ".join(f"{k}: {v:.0%}" for k, v in sorted(idle.items())))
    goals = collections.Counter(r["goal"] for rs in bots.values() for r in rs)
    tot = sum(goals.values())
    lines.append("Goal mix: " + ", ".join(f"{g} {n / tot:.0%}" for g, n in goals.most_common()))
    shots = sum(1 for rs in bots.values() for r in rs if r["cmd"][3] & FIRE)
    lines.append(f"Trigger pulls: {shots / (span / 60) / len(bots):.0f} per bot per minute")
    lines.append("")
    # --- crowding
    blob_spots = []
    if world:
        blob_t, touch, samples, blob_spots = crowding(world)
        lines.append("## Teammates bunching up")
        for team in sorted(samples):
            n = sum(len([p for p in w["world"] if p[1] == team and p[2] and p[8]]) for w in world) or 1
            lines.append(f"Team {team}: a blob of {CROWD_N}+ within {CROWD_R:.0f} units {blob_t[team] / max(1, samples[team]):.0%} "
                         f"of the time; bots touching a teammate {touch[team] / n:.0%} of bot time")
        lines.append("")
    png = draw(path, name, bots, deaths, stuck_all, blob_spots, map_name)
    if png:
        lines.append(f"Map: {png}")
    return "\n".join(lines), png


def draw(path, name, bots, deaths, stuck, blobs, map_name):
    if not map_name:
        return None
    try:
        import numpy as np
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    d = os.path.join(ROOT, "maps", map_name)
    if not os.path.exists(os.path.join(d, "topdown.png")):
        return None
    hm = np.load(os.path.join(d, "heightmap.npz"))
    x0, y0, cell, (h, w) = float(hm["x0"]), float(hm["y0"]), float(hm["cell"]), hm["top"].shape
    img = Image.open(os.path.join(d, "topdown.png")).convert("RGB")
    sc = img.width / w
    P = lambda x, y: ((x - x0) / cell * sc, (h - (y - y0) / cell) * sc)
    dr = ImageDraw.Draw(img, "RGBA")
    col = {0: (255, 70, 70, 50), 1: (80, 140, 255, 50)}
    for bid, rs in bots.items():
        for r in rs[::6]:
            x, y = P(*r["pos"][:2])
            dr.point((x, y), fill=col.get(r.get("team", bid % 2), (255, 255, 255, 50)))
    for t, team, x, y, n in blobs[::5]:
        cx, cy = P(x, y)
        dr.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=(0, 255, 255, 160), width=2)
    for bid, a, b, x, y in stuck:
        cx, cy = P(x, y)
        r = 4 + min(10, (b - a))
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 230, 0, 230), width=2)
    for t, pid, team, pos, kind in deaths:
        cx, cy = P(pos[0], pos[1])
        c = {"combat": (255, 40, 40, 220), "fall": (255, 0, 255, 255), "alone": (255, 140, 0, 255)}[kind]
        dr.line((cx - 5, cy - 5, cx + 5, cy + 5), fill=c, width=2)
        dr.line((cx - 5, cy + 5, cx + 5, cy - 5), fill=c, width=2)
    out = os.path.join(ROOT, "logs", f"report_{name}.png")
    img.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--map", help="map folder (for the picture); default: from the trace name")
    ap.add_argument("--skip", type=float, default=0.0, help="ignore the first seconds (spawn rush)")
    o = ap.parse_args()
    m = o.map
    if not m:
        guess = os.path.splitext(os.path.basename(o.trace))[0].replace("trace_", "")
        m = next((d for d in sorted(os.listdir(os.path.join(ROOT, "maps")), key=len, reverse=True)
                  if guess.startswith(d) and os.path.exists(os.path.join(ROOT, "maps", d, "heightmap.npz"))), None)
    text, png = report(o.trace, m, o.skip)
    name = os.path.splitext(os.path.basename(o.trace))[0].replace("trace_", "")
    out = os.path.join(ROOT, "logs", f"report_{name}.md")
    open(out, "w", encoding="utf-8").write(text + "\n")
    print(text)
    print("written", out)


if __name__ == "__main__":
    main()
