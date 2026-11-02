"""How bots used their guns in a live trace (the weapon rules, brain/bot.py): switches by reason, in-fight weapon changes
by range, the AR's trigger up close (on target, and every tick the man is in view), DMR press gaps by range, charge
holds, zoom asked by weapon and range. Writes logs/verify/fight_check_<trace stem>.txt.

usage: python -I fight_check.py logs\\trace_<map>_<stamp>.jsonl
"""
import collections
import json
import os
import statistics
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def main():
    recs = collections.defaultdict(list)
    for line in open(sys.argv[1], encoding="utf-8"):
        r = json.loads(line)
        if "cmd" in r and "id" in r:
            recs[r["id"]].append(r)
    why, changes, launcher = collections.Counter(), collections.Counter(), []
    ar_on, ar_seen = [0, 0], [0, 0]
    gaps = collections.defaultdict(list)
    zoom, charge = collections.Counter(), collections.Counter()
    for b, rs in recs.items():
        last_press = None
        for p, r in zip(rs, rs[1:]):
            for n in r.get("notes") or []:
                if n.startswith("switch:"):
                    why[n] += 1
            if r["t"] - p["t"] < 0.5 and r["wpn"] != p["wpn"] and p["goal"] == "fight":
                d0 = (p.get("fx") or {}).get("d", 99)
                changes[(p["wpn"], r["wpn"], "close<4" if d0 < 4 else "far")] += 1
                if p["wpn"] == "plasma_launcher":
                    launcher.append((p["t"], d0, [n for q in rs if p["t"] - 0.5 <= q["t"] <= r["t"] for n in q.get("notes") or []]))
            fx = r.get("fx") or {}
            btn = r["cmd"][3]
            if r["goal"] != "fight" or not fx:
                last_press = None
                continue
            d = fx.get("d", 99)
            if fx.get("charge") is not None:
                charge[r["wpn"]] += 1
            if r["wpn"] == "assault_rifle" and d < 4:
                if fx.get("on"):
                    ar_on[0] += 1
                    ar_on[1] += btn & 1
                if fx.get("unseen", 99) < 0.25:
                    ar_seen[0] += 1
                    ar_seen[1] += btn & 1
            if r["wpn"] == "dmr" and btn & 1 and not p["cmd"][3] & 1:
                if last_press is not None and r["t"] - last_press[0] < 1.5 and abs(d - last_press[1]) < 2:
                    band = "short <4" if d < 4 else "medium 4-10" if d <= 10 else "long >10"
                    gaps[band].append(r["t"] - last_press[0])
                last_press = (r["t"], d)
            zoom[(r["wpn"], "<4.5" if d < 4.5 else ">=4.5", (btn >> 12) & 3)] += 1   # every gun: a fight tick's ask
    out = [f"trace: {sys.argv[1]}",
           f"switch notes: {dict(why)}",
           f"in-fight weapon changes (from, to, range): {dict(changes)}",
           f"plasma launcher changes (t, d, notes around): {launcher}",
           f"AR within 4 units: on target {ar_on[0]} ticks, trigger down {ar_on[1] / max(1, ar_on[0]):.0%}; "
           f"man in view {ar_seen[0]} ticks, trigger down {ar_seen[1] / max(1, ar_seen[0]):.0%}"]
    out += [f"DMR {band}: {len(g)} gaps, median {statistics.median(g):.2f} s" for band, g in sorted(gaps.items())]
    out += [f"charge holds (ticks by weapon): {dict(charge)}", f"zoom asked (weapon, range, level): ticks {dict(zoom)}"]
    path = os.path.join(ROOT, "logs", "verify", "fight_check_" + os.path.basename(sys.argv[1]).replace(".jsonl", ".txt"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
