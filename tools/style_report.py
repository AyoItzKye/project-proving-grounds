"""Do the play styles show?

Measures what every bot did in recorded matches (logs/trace_*.jsonl bot and think lines) and groups it by
difficulty and play style, so a style's effect is compared within one difficulty:
  hold     share of time holding a power spot (the camper / sniper habit)
  fight / hunt / obj   share of time fighting, hunting a man, on the objective
  still    share of time standing still (under 0.3 units a second)
  fights   fights started a minute
  dist     median distance to the man it fights
  jumps, nades   jump and grenade presses a minute
  crouch   share of time crouched
  runner / defender   share of time in those team roles (objective games)
  side     share of time off the straight line between the bases (a flanker should be high)

usage: python -I style_report.py [trace ...]      (default: the 8 newest traces)
"""
import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
TIER = {"novice": "Easy", "average": "Normal", "strong": "Heroic", "top": "Legendary"}
STYLE = {"rusher": "Rusher", "camper": "Camper", "flanker": "Flanker", "objector": "Objective", "spammer": "Grenadier",
         "grudger": "Grudge", "sniper": "Sniper"}


def side_of(m):
    """A function (x, y) -> distance from the straight line between the two teams' bases, or None."""
    try:
        a, b = m["flags"][0], m["flags"][1]
    except (KeyError, TypeError):
        return None
    dx, dy = b.x - a.x, b.y - a.y
    n = math.hypot(dx, dy) or 1.0
    return lambda x, y: abs((x - a.x) * dy - (y - a.y) * dx) / n


def bots_in(path):
    """{bot id: stats} for one trace."""
    meta, st, mp = {}, {}, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if '"meta"' in line:
                d = json.loads(line)["meta"]
                mp = mp or d.get("map")
                if d.get("bot"):
                    meta[d["bot"]["id"]] = d["bot"]
            elif '"cmd"' in line or '"think"' in line:
                d = json.loads(line)
                i = d["id"]
                s = st.setdefault(i, dict(n=0, goals=Counter(), still=0, crouch=0, jumps=0, nades=0, fights=0,
                                          dist=[], roles=Counter(), side=0, side_n=0, last=None))
                if "think" in d:
                    if d.get("order"):
                        s["roles"][d["order"][0]] += 1
                    continue
                s["n"] += 1
                s["goals"][d["goal"]] += 1
                b = d["cmd"][3]
                lp = s["last"]
                if lp:
                    dt = d["t"] - lp[0]
                    if 0 < dt < 0.5 and math.dist(d["pos"][:2], lp[1][:2]) / dt < 0.3:
                        s["still"] += 1
                    if b & 2 and not lp[2] & 2:
                        s["jumps"] += 1
                    if b & 8 and not lp[2] & 8:
                        s["nades"] += 1
                    if d["goal"] == "fight" and lp[3] != "fight":
                        s["fights"] += 1
                if b & 4:
                    s["crouch"] += 1
                if d["goal"] == "fight" and d.get("fx", {}).get("d") is not None:
                    s["dist"].append(d["fx"]["d"])
                s["last"] = (d["t"], d["pos"], b, d["goal"])
                s.setdefault("pos", []).append(d["pos"][:2]) if s["n"] % 30 == 0 else None
    side = None
    if mp:
        try:
            from brain.maps import get_map
            side = side_of(get_map(mp))
        except Exception:                       # a map without data: no side measure
            side = None
    out = {}
    for i, s in st.items():
        if i not in meta or not s["n"]:
            continue
        if side:
            ds = [side(x, y) for x, y in s.get("pos", [])]
            s["side"] = sum(1 for v in ds if v > 6.0)
            s["side_n"] = len(ds)
        out[i] = (meta[i], s)
    return out


def report(paths):
    groups = defaultdict(list)
    for p in paths:
        for b, s in bots_in(p).values():
            groups[(TIER.get(b["tier"], b["tier"]), STYLE.get(b["pers"], b["pers"]))].append(s)
    rows = []
    for (tier, style), ss in sorted(groups.items()):
        n = sum(s["n"] for s in ss) or 1
        mins = n / 30.0 / 60.0 or 1e-9
        g = Counter()
        for s in ss:
            g.update(s["goals"])
        roles = Counter()
        for s in ss:
            roles.update(s["roles"])
        rn = sum(roles.values()) or 1
        dists = sorted(d for s in ss for d in s["dist"])
        sn = sum(s["side_n"] for s in ss)
        rows.append(dict(tier=tier, style=style, bots=len(ss), minutes=round(mins, 1),
                         hold=g["hold"] / n, fight=g["fight"] / n, hunt=g["hunt"] / n, obj=g["objective"] / n,
                         still=sum(s["still"] for s in ss) / n, fights=sum(s["fights"] for s in ss) / mins,
                         dist=dists[len(dists) // 2] if dists else None,
                         jumps=sum(s["jumps"] for s in ss) / mins, nades=sum(s["nades"] for s in ss) / mins,
                         crouch=sum(s["crouch"] for s in ss) / n, runner=roles["runner"] / rn,
                         defender=roles["defender"] / rn, side=(sum(s["side"] for s in ss) / sn) if sn else None))
    return rows


def show(rows):
    print(f"{'difficulty':<10} {'style':<10} {'bots':>4} {'min':>5} {'hold':>5} {'fight':>5} {'hunt':>5} {'obj':>5} "
          f"{'still':>5} {'fights':>6} {'dist':>5} {'jumps':>5} {'nades':>5} {'crouch':>6} {'runner':>6} {'defend':>6} {'side':>5}")
    pct = lambda v: "  -  " if v is None else f"{v * 100:4.0f}%"       # noqa: E731
    for r in rows:
        dist = "  -  " if r["dist"] is None else f"{r['dist']:5.1f}"
        print(f"{r['tier']:<10} {r['style']:<10} {r['bots']:>4} {r['minutes']:>5} {pct(r['hold'])} {pct(r['fight'])} "
              f"{pct(r['hunt'])} {pct(r['obj'])} {pct(r['still'])} {r['fights']:6.1f} {dist} "
              f"{r['jumps']:5.1f} {r['nades']:5.1f} {pct(r['crouch'])}  {pct(r['runner'])}  {pct(r['defender'])} {pct(r['side'])}")


def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "logs", "trace_*_*.jsonl")), key=os.path.getmtime)[-8:]
    print("traces:", ", ".join(os.path.basename(p) for p in paths))
    show(report(paths))


if __name__ == "__main__":
    main()
