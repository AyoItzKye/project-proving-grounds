"""Invasion trace report (tools/live_bots.py --trace on a Reach Invasion map): every 10 s, how many bots of each team
stand in or near each territory of the map's setup (brain/invasion.py), and which goals they chase. For checking the
roles live: attackers in a territory, defenders around it, the core run in phase 3.

usage: python -I invasion_report.py <trace.jsonl> [map]      (map: reach_70_boneyard by default)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.maps import get_map  # noqa: E402


def main(path, name="reach_70_boneyard"):
    inv = invasion.layout(get_map(name)["objects"])
    zones = [(f"p{ph}{'abc'[k]}", z) for ph in (1, 2, 3) for k, z in enumerate(inv["phases"][ph])]
    zones.append(("core", inv["core"]))
    team, last, rows = {}, {}, []
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if "foes" in r and "id" in r:              # a bot's tick: its team is the one its foes are not
            last[r["id"]] = (r["t"], r["pos"], r.get("goal"), r.get("order"))
        if r.get("id") is not None and "order" in r:
            pass
    # second pass: sample every 10 s
    t_next, by_t = 0.0, {}
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if "pos" not in r or "foes" not in r:
            continue
        foes = {f[0] for f in r["foes"]}
        team[r["id"]] = 0 if 0 not in foes else 1      # (red bots never list player 0, the host, as a foe)
        by_t.setdefault(int(r["t"] // 10), {})[r["id"]] = (r["pos"], r.get("goal"))
    for slot in sorted(by_t):
        bots = by_t[slot]
        cells = []
        for zn, z in zones:
            near = {0: 0, 1: 0}
            for i, (p, g) in bots.items():
                if math.hypot(p[0] - z.x, p[1] - z.y) < 4.0 and abs(p[2] - z.z) < 3:
                    near[team.get(i, 0)] += 1
            if near[0] or near[1]:
                cells.append(f"{zn}:{near[0]}r/{near[1]}b")
        goals = {}
        for i, (p, g) in bots.items():
            goals[g] = goals.get(g, 0) + 1
        print(f"{slot * 10:5d}s  {' '.join(cells) or '-':40s} goals {goals}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
