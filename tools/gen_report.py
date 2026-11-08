"""Generator Defense in a match (the trace's world rows "gens", the bots' orders and notes; tools/live_bots.py gen_state,
brain/bot.py generator_work): every lock (when, which generator, which guard pressed and why, the gap to the team's last
lock: the guide's one per 10 s), how long it held (the game's lock is 30 s), each guard's distance to its own generator
at that moment (a guard: a Spartan bot on a Generator Defense defender order, its generator the one at its order's
point; "dead" while down), the share of the match each guard was within 8 u of its generator (alive), every guard
press, each breaker's shots by the generator's state (none should fall on a locked one), and when each generator died.

usage: python -I tools/gen_report.py <trace.jsonl>
"""
import json
import math
import sys

NEAR = 8.0       # u: a guard this near its generator can lock it (brain/bot.py GEN_ACT)


def main():
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.startswith("{")]
    state, since, locks, deaths = {}, {}, [], []
    presses, shots, cur, gpos = {}, {}, {}, {}
    order, pos, alive = {}, {}, {}
    guard_near, guard_n = {}, {}
    spartans = {r["meta"]["bot"]["id"] for r in rows if "meta" in r and r["meta"]["bot"]["team"] == 0}

    def guard_gen(i):
        o = order.get(i)
        if not o or o[0] != "defender" or not o[1] or not gpos:
            return None
        k = min(gpos, key=lambda g: math.hypot(gpos[g][0] - o[1][0], gpos[g][1] - o[1][1]))
        return k if math.hypot(gpos[k][0] - o[1][0], gpos[k][1] - o[1][1]) < 4.0 else None

    def gaps():
        out = {}
        for i in sorted(spartans):
            k = guard_gen(i)
            if k is None:
                continue
            if not alive.get(i, True) or i not in pos:
                out[i] = (k, None)
            else:
                out[i] = (k, math.hypot(pos[i][0] - gpos[k][0], pos[i][1] - gpos[k][1]))
        return out
    for r in rows:
        t = r.get("t", 0.0)
        if r.get("id") is not None:
            if r.get("order"):
                order[r["id"]] = r["order"]
            if "pos" in r:
                pos[r["id"]] = r["pos"]
        if "world" in r:
            for p in r["world"]:
                alive[p[0]] = p[2]
                if p[2]:
                    pos[p[0]] = [p[3], p[4], p[5]]
        if r.get("gens"):
            for g in r["gens"]:
                i, st = g[0], g[1]
                if len(g) >= 5:
                    gpos[i] = (g[3], g[4])
                cur[i] = st
                if state.get(i) != st:
                    if state.get(i) == "ready" and st == "locked":
                        locks.append([t, i, None, None, gaps()])
                    if st == "locked":
                        since[i] = t
                    if state.get(i) == "locked" and st != "locked" and i in since:
                        for lk in locks:
                            if lk[1] == i and lk[3] is None:
                                lk[3] = (t - since[i], st)
                    if st == "dead":
                        deaths.append((t, i))
                    state[i] = st
            for i, (k, d) in gaps().items():
                if d is not None and cur.get(k) != "dead":
                    guard_n[i] = guard_n.get(i, 0) + 1
                    guard_near[i] = guard_near.get(i, 0) + (d <= NEAR)
        for n in r.get("notes", []):
            if n.startswith("lockdown: generator"):
                gi = int(n.split()[2])
                presses.setdefault((r["id"], gi, n.split("(")[-1].rstrip(")")), []).append(t)
            elif n.startswith("breaking generator"):
                gi = int(n.split()[2])
                k = (r["id"], gi, cur.get(gi, "?"))
                shots[k] = shots.get(k, 0) + 1
    for lk in locks:                           # who pressed: a guard on that generator in the 3 s before
        cand = [k for k, ts in presses.items() if k[1] == lk[1] and any(lk[0] - 3.0 <= x <= lk[0] for x in ts)]
        lk[2] = cand[0] if cand else None
    print(f"locks: {len(locks)}")
    last = None
    for t, i, who, held, g in locks:
        gap = f", {t - last:.1f} s after the last" if last is not None else ""
        how = f"held {held[0]:.1f} s (then {held[1]})" if held else "held to the end of the trace"
        print(f"  {t:6.1f} s generator {i} locked by bot {who[0] if who else '?'} ({who[2] if who else '?'}){gap}; {how}")
        print("         guards then: " + "; ".join(
            f"bot {b} -> generator {k}: " + ("dead" if d is None else f"{d:.1f} u") for b, (k, d) in g.items()))
        last = t
    print("guards within %.0f u of their generator (alive, generator standing): " % NEAR + ", ".join(
        f"bot {i} {100 * guard_near[i] / guard_n[i]:.0f}%" for i in sorted(guard_n)))
    print("guard presses (bot, generator, why): " + ", ".join(f"{k}: {len(v)} ticks" for k, v in sorted(presses.items())))
    on_locked = sum(v for k, v in shots.items() if k[2] == "locked")
    print(f"breaker shot ticks: {sum(shots.values())}, on a locked generator {on_locked}; by state "
          + str({st: sum(v for k, v in shots.items() if k[2] == st) for st in {k[2] for k in shots}}))
    print("generators lost: " + (", ".join(f"{i} at {t:.1f} s" for t, i in deaths) or "none"))


if __name__ == "__main__":
    main()
