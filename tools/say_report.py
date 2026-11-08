"""What the person's chat commands did in a match (the trace's {"say": ...} rows, tools/live_bots.py say_command): for each
stretch (before any command, after "follow me", after "roam"), his teammate bots' orders (share on escort, on defender),
their median distance to him, the share of them within 6 u of him, and how exposed the spots they stood on were (the
share of 16 directions with a clear line 12 u out, Terrain.los; 1.0 = open all round). Skips each stretch's first 8 s (the bots
on their way).

usage: python -I tools/say_report.py <trace.jsonl>
"""
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))


def openness(T, x, y, z, reach=12.0):
    """How exposed a spot is: the share of 16 directions with a clear line (Terrain.los: walls, windows and fences stop
    it) from it to a man standing 12 u off on its level; 1.0 open all round, low in a covered room."""
    from brain.core import Vec
    me, n = Vec(x, y, z), 0
    for a in range(16):
        q = Vec(x + math.cos(a * math.pi / 8) * reach, y + math.sin(a * math.pi / 8) * reach, z)
        n += bool(T.los(me, q))
    return n / 16


def main():
    path = sys.argv[1]
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.startswith("{")]
    meta = next(r["meta"] for r in rows if "meta" in r)
    says = [(r["t"], r["say"], r["team"]) for r in rows if "say" in r]
    if not says:
        sys.exit("no chat command in this trace")
    team = says[0][2]
    bots = {r["meta"]["bot"]["id"] for r in rows if "meta" in r and r["meta"]["bot"]["team"] == team}
    from brain.maps import get_map, terrain
    T = terrain(get_map(meta["map"]))
    edges = [(0.0, "before")] + [(t, w) for t, w, _ in says]
    end = max(r.get("t", 0) for r in rows)
    print(f"{os.path.basename(path)}: commands {[(round(t, 1), w) for t, w, _ in says]}, team {team}, bots {sorted(bots)}")
    for k, (t0, word) in enumerate(edges):
        t1 = edges[k + 1][0] if k + 1 < len(edges) else end
        lo = t0 + (8.0 if k else 20.0)
        orders, dists, opens = {}, [], []
        for r in rows:
            if not lo <= r.get("t", -1) < t1:
                continue
            if r.get("id") in bots and r.get("order"):
                orders[r["order"][0]] = orders.get(r["order"][0], 0) + 1
            if "world" in r:
                w = {p[0]: p for p in r["world"]}
                me = next((p for p in r["world"] if not p[8] and p[1] == team and p[2]), None)
                for b in bots:
                    p = w.get(b)
                    if p is None or not p[2]:
                        continue
                    if me is not None:
                        dists.append(math.hypot(p[3] - me[3], p[4] - me[4]))
                    if len(opens) < 400 and int(r["t"] * 4) % 8 == 0:
                        opens.append(openness(T, p[3], p[4], p[5]))
        total = sum(orders.values()) or 1
        share = {k2: f"{100 * v / total:.0f}%" for k2, v in sorted(orders.items(), key=lambda kv: -kv[1])}
        near = sum(1 for d in dists if d <= 6.0) / max(1, len(dists))
        print(f"  {word:7} {lo:6.1f}-{t1:6.1f} s: orders {share}; distance to you median "
              f"{statistics.median(dists) if dists else float('nan'):.1f} u, within 6 u {100 * near:.0f}%; "
              f"exposed (16 lines out 12 u) {statistics.mean(opens) if opens else float('nan'):.2f} ({len(opens)} samples)")


if __name__ == "__main__":
    main()
