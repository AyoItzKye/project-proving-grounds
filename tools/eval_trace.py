"""Score a live brain trace (logs/trace_<map>.jsonl, written when logs/trace_on exists): how often
players die, how often a bot's shot is followed by damage on the target it fights, how long bots
stand still while they mean to travel (blocked: pushing into something with nobody near;
crowded: pushing into another player; the rest of the still time is waiting at the destination). Compare runs before and after a brain change.

usage: python -I eval_trace.py <trace.jsonl> [...]
"""
import collections
import json
import math
import sys


def score(path):
    rows = [r for r in (json.loads(l) for l in open(path)) if "id" in r]   # (world lines: match_report.py)
    if not rows:
        return None
    span = rows[-1]["t"] - rows[0]["t"]
    hp = {}                      # (t rounded to tick, player) -> shield + health, from any bot's foe list
    deaths, alive = collections.Counter(), {}
    for r in rows:
        for pid, sh, h in r["foes"]:
            hp[(round(r["t"], 2), pid)] = sh + h
            a = h > 0
            if alive.get(pid, True) and not a:
                deaths[pid] += 1
            alive[pid] = a
    by = collections.defaultdict(list)
    at = collections.defaultdict(list)        # tick -> bot positions (who stands next to whom)
    for r in rows:
        by[r["id"]].append(r)
        at[round(r["t"], 1)].append((r["id"], r["pos"]))
    shots = hits = 0
    stuck = travel = blocked = crowded = 0
    for rs in by.values():
        for k, r in enumerate(rs):
            if r["goal"] == "fight" and r["cmd"][3] & 1 and r["arg"].isdigit():
                tid = int(r["arg"])
                now = next((f[1] + f[2] for f in r["foes"] if f[0] == tid), None)
                later = [f[1] + f[2] for q in rs[k + 1:k + 13] for f in q["foes"] if f[0] == tid]
                if now is not None and later and now > 0:
                    shots += 1
                    hits += min(later) < now - 0.01
            if k and r["goal"] not in ("hold", "fight") and r["t"] - rs[k - 1]["t"] < 0.1:
                travel += 1
                if math.dist(r["pos"][:2], rs[k - 1]["pos"][:2]) < 0.02:
                    stuck += 1
                    if math.hypot(r["cmd"][0], r["cmd"][1]) > 0.1:     # pushing and going nowhere
                        near = any(i != r["id"] and math.dist(q[:2], r["pos"][:2]) < 1.0 and abs(q[2] - r["pos"][2]) < 1
                                   for i, q in at[round(r["t"], 1)])
                        crowded += near
                        blocked += not near
    players = len({f[0] for r in rows for f in r["foes"]} | set(by))
    return dict(minutes=round(span / 60, 1), players=players, bots=len(by),
                deaths_per_player_min=round(sum(deaths.values()) / max(players, 1) / max(span / 60, 1e-9), 2),
                shot_hit_rate=round(hits / max(shots, 1), 2), shots=shots,
                still_while_travelling=round(stuck / max(travel, 1), 2),
                blocked=round(blocked / max(travel, 1), 3), crowded=round(crowded / max(travel, 1), 3))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, score(p))
