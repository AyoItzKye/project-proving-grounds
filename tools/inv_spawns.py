"""Where Reach Invasion really respawns each side, per phase, learned from live match traces: the simulator's respawn zones
from the scenario (brain/invasion.py layout "res": three zone centres a phase) put Spire's phase 2 defenders 44 u from
where the game respawned them. Every respawn in the traces (a player alive again) with the phase and whether its team
attacked; the points 1 u apart at most are merged. Written to maps/<map>/inv_spawns.json {"att": {phase: [[x, y, z]]},
"def": {...}}; brain/sim_modes.py spawns there when the file exists.

The file's "named" spawns (the spawn screen's names, read by the player: River, Conveyor Belt, BFG, High Trail #1 and #2
on Spire; brain/invasion.py honor_spawn) are kept: name, side, weight and each phase's centre ("at": [x, y, z, facing
degrees], the zone's flag); their "points" are filled here: the respawns seen (either side: spawn points are the map's)
within NAME_R of a phase's centre and NAME_DZ of its height, or the centre when none was seen.

usage: python -I inv_spawns.py <map> [trace ...]     (default: every logs/trace_<map>_*.jsonl)
"""
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
NAME_R, NAME_DZ = 3.0, 1.5       # the zones' rings are 3 u (objects.json boundary w)


def name_points(named, seen):
    for n in named:
        n["points"] = {ph: [p for p in seen if math.dist(p[:2], c[:2]) <= NAME_R and abs(p[2] - c[2]) <= NAME_DZ]
                       or [c[:3]] for ph, c in n["at"].items()}
    return named


def learn(paths):
    out = {"att": {}, "def": {}}
    seen = out["_seen"] = []
    for path in paths:
        alive = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                if '"world"' not in line or '"invasion"' not in line:
                    continue
                r = json.loads(line)
                inv = r.get("invasion")
                if not inv or inv[0] not in (1, 2, 3):
                    continue
                phase, att = inv[0], inv[1]
                for w in r["world"]:
                    if w[2] and alive.get(w[0]) is False:
                        side = "att" if w[1] == att else "def"
                        pts = out[side].setdefault(str(phase), [])
                        p = [round(w[3], 2), round(w[4], 2), round(w[5], 2)]
                        if not any(math.dist(p, q) < 1.0 for q in pts):
                            pts.append(p)
                        if not any(math.dist(p, q) < 1.0 for q in seen):
                            seen.append(p)
                    alive[w[0]] = bool(w[2])
    return out


def main():
    name = sys.argv[1]
    paths = sys.argv[2:] or sorted(glob.glob(os.path.join(ROOT, "logs", f"trace_{name}_*.jsonl")))
    data = learn(paths)
    seen = data.pop("_seen")
    path = os.path.join(ROOT, "maps", name, "inv_spawns.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    for s in ("att", "def"):                     # the points learned before stay (older traces are pruned: 10 kept)
        for ph, pts in old.get(s, {}).items():
            cur = data[s].setdefault(ph, [])
            for p in pts:
                for into in (cur, seen):
                    if not any(math.dist(p, q) < 1.0 for q in into):
                        into.append(p)
    for k in ("named", "ally", "note"):
        if k in old:
            data[k] = name_points(old[k], seen) if k == "named" else old[k]
    json.dump(data, open(path, "w"), indent=1)
    print(name, {s: {ph: len(v) for ph, v in d.items()} for s, d in data.items() if s in ("att", "def")}, "from", len(paths),
          "traces ->", path)
    for n in data.get("named", []):
        print(f"  {n['name']:14} {n['side']} " + ", ".join(f"phase {ph}: {len(p)} points" for ph, p in n["points"].items()))


if __name__ == "__main__":
    main()
