"""Tier against tier in live matches (supervisor: "run a live Heroic vs Normal match and tune Heroic if it is still even"):
from brain traces (tools/live_bots.py --trace), each team's tier (the bots' meta lines) and how many times the other
team's bots died. The host (not a bot) is left out both ways: an idle host is a free kill for one side, and the sides
are swapped between matches anyway. A bot death is counted as a kill for the other team (suicides and falls count too:
ponytail, the trace does not say who killed whom).

usage: python -I tier_live.py <trace.jsonl> [more traces]     -> per tier: kills, deaths, share of the bot kills
"""
import collections
import json
import sys


def match(path):
    tiers, last, deaths = {}, {}, collections.Counter()
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        m = r.get("meta")
        if m and m.get("bot"):
            b = m["bot"]
            tiers[b["id"]] = (b["team"], b["tier"])
            continue
        for w in r.get("world") or []:
            pid, alive = w[0], w[2]
            if last.get(pid) and not alive and pid in tiers:
                deaths[pid] += 1
            last[pid] = alive
    return tiers, deaths


def main(paths):
    kills, died = collections.Counter(), collections.Counter()
    for p in paths:
        tiers, deaths = match(p)
        teams = collections.defaultdict(set)
        for pid, (team, tier) in tiers.items():
            teams[team].add(tier)
        for pid, n in deaths.items():
            team, tier = tiers[pid]
            died[tier] += n
            for other, ts in teams.items():
                if other != team:
                    for t in ts:
                        kills[t] += n / len(ts)
        print(f"{p}: " + ", ".join(f"team {t} {sorted(ts)} died {sum(n for i, n in deaths.items() if tiers[i][0] == t)}"
                                   for t, ts in sorted(teams.items())))
    total = sum(kills.values()) or 1
    for t in sorted(kills, key=lambda t: -kills[t]):
        print(f"{t:8s} kills {kills[t]:5.0f}  deaths {died[t]:4d}  share of bot kills {kills[t] / total:.2f}")


if __name__ == "__main__":
    main(sys.argv[1:])
