"""Generator Defense in a match (the trace's world rows "gens", the bots' notes; tools/live_bots.py gen_state,
brain/bot.py generator_work): every lock (when, which generator, which guard pressed and why, the gap to the team's last
lock: the guide's one per 10 s), how long each lock held, every guard press, each breaker's shots by the generator's
state (none should fall on a locked one), and when each generator died.

usage: python -I tools/gen_report.py <trace.jsonl>
"""
import json
import sys


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.startswith("{")]
    state, since, locks, deaths = {}, {}, [], []
    presses, shots = {}, {}
    cur = {}
    for r in rows:
        t = r.get("t", 0.0)
        if r.get("gens"):
            for i, st, hp in r["gens"]:
                cur[i] = st
                if state.get(i) != st:
                    if state.get(i) == "ready" and st == "locked":
                        locks.append([t, i, None, None])
                    if st == "locked" and state.get(i) != "locked":
                        since[i] = t
                    if state.get(i) == "locked" and st != "locked" and i in since:
                        for lk in locks:
                            if lk[1] == i and lk[3] is None:
                                lk[3] = t - since[i]
                    if st == "dead":
                        deaths.append((t, i))
                    state[i] = st
        for n in r.get("notes", []):
            if n.startswith("lockdown: generator"):
                gi = int(n.split()[2])
                presses.setdefault((r["id"], gi, n.split("(")[-1].rstrip(")")), []).append(t)
            elif n.startswith("breaking generator"):
                gi = int(n.split()[2])
                k = (r["id"], gi, cur.get(gi, "?"))
                shots[k] = shots.get(k, 0) + 1
    for lk in locks:                           # who pressed: the guard on that generator in the 3 s before
        cand = [(k, max(ts)) for k, ts in presses.items() if k[1] == lk[1] and any(lk[0] - 3.0 <= x <= lk[0] for x in ts)]
        lk[2] = cand[0][0] if cand else None
    print(f"locks: {len(locks)}")
    last = None
    for t, i, who, held in locks:
        gap = f", {t - last:.1f} s after the last" if last is not None else ""
        print(f"  {t:6.1f} s generator {i} locked by bot {who[0] if who else '?'} ({who[2] if who else '?'}){gap}; "
              f"held {held:.1f} s" if held else f"  {t:6.1f} s generator {i} locked by bot {who[0] if who else '?'} "
              f"({who[2] if who else '?'}){gap}; held to the end")
        last = t
    print("guard presses (bot, generator, why): " + ", ".join(f"{k}: {len(v)} ticks" for k, v in sorted(presses.items())))
    on_locked = sum(v for k, v in shots.items() if k[2] == "locked")
    print(f"breaker shot ticks: {sum(shots.values())}, on a locked generator {on_locked}; by state "
          + str({st: sum(v for k, v in shots.items() if k[2] == st) for st in {k[2] for k in shots}}))
    print("generators lost: " + (", ".join(f"{i} at {t:.1f} s" for t, i in deaths) or "none"))


if __name__ == "__main__":
    main()
