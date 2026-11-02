"""What each bot was doing in the seconds before it fell to its death (match_report.py counts falls: a
2.5+ unit drop in the last 1.5 s). Prints, per fall: where it started and ended, the bot's goal and
the stick / buttons it was given., fall deaths on Halo 3 Construct.

usage: python -I fall_check.py <trace.jsonl> [--before 3]
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from match_report import load, deaths_from_world  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--before", type=float, default=3.0)
    o = ap.parse_args()
    bots, world = load(o.trace)
    for t, pid, team, pos, kind in deaths_from_world(world):
        if kind != "fall" or pid not in bots:
            continue
        rows = [r for r in bots[pid] if t - o.before <= r["t"] <= t]
        print(f"\nbot {pid} fell, died at t={t:.1f} ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
        goals = collections.Counter(r["goal"] for r in rows)
        print("  goals:", dict(goals))
        for r in rows[:: max(1, len(rows) // 8)]:
            print(f"  t={r['t']:.2f} pos=({r['pos'][0]:.1f},{r['pos'][1]:.1f},{r['pos'][2]:.1f}) goal={r['goal']} "
                  f"cmd=fwd {r['cmd'][0]} strafe {r['cmd'][1]} buttons {r['cmd'][3]} wp={r.get('wp')}")


if __name__ == "__main__":
    main()
