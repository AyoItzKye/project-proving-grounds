"""How fights end, from traces: each run of a bot's "fight" goal on one target ends with the target dead
within 1 s (finished), the bot dead, or the bot dropping it while the target is alive (abandoned: what
it switched to and how far the target was)..

usage: python -I fight_ends.py <trace.jsonl> [...] [--map NAME]   (--map: split "abandoned" by line of sight then)
"""
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def stats(paths, T=None):
    from brain.core import Vec
    ends, switched_to, dists, lengths = collections.Counter(), collections.Counter(), [], []
    for path in paths:
        alive, pos, cur = {}, {}, {}
        rows = [json.loads(line) for line in open(path)]
        world = [(d["t"], {r[0]: (r[2], r[3:6]) for r in d["world"]}) for d in rows if "world" in d]
        wi = 0

        def state_at(t):
            nonlocal wi
            while wi + 1 < len(world) and world[wi + 1][0] <= t:
                wi += 1
            return world[wi][1] if world else {}

        for d in rows:
            if "world" in d:
                continue
            b, t, goal, arg = d["id"], d["t"], d["goal"], d.get("arg")
            c = cur.get(b)
            if goal == "fight":
                try:
                    tgt = int(arg)
                except (TypeError, ValueError):
                    continue
                if c is None or c[0] != tgt:
                    cur[b] = (tgt, t)
                continue
            if c is None:
                continue
            del cur[b]
            tgt, t0 = c
            lengths.append(t - t0)
            w = state_at(t + 1.0)
            me = w.get(b)
            tg = w.get(tgt)
            if me is not None and not me[0]:
                ends["bot died"] += 1
            elif tg is not None and not tg[0]:
                ends["target died (finished)"] += 1
            else:
                w0 = state_at(t)
                m0, g0 = w0.get(b), w0.get(tgt)
                in_sight = None
                if T is not None and m0 is not None and g0 is not None and m0[0] and g0[0]:
                    in_sight = T.los(Vec(*m0[1]), Vec(*g0[1]))
                kind = ("abandoned in sight" if in_sight else "lost him (no line of sight)" if in_sight is False
                        else "abandoned, target alive")
                ends[kind] += 1
                if in_sight is not False:
                    switched_to[goal] += 1
                if tg is not None and me is not None:
                    dists.append(math.dist(me[1][:2], tg[1][:2]))
    n = sum(ends.values())
    print(f"{n} fights: " + ", ".join(f"{k} {v} ({v / max(1, n):.0%})" for k, v in ends.most_common()))
    print("  abandoned for: " + ", ".join(f"{k} {v}" for k, v in switched_to.most_common()))
    if dists:
        ds = sorted(dists)
        print(f"  target distance when abandoned: median {ds[len(ds) // 2]:.1f}, "
              f"{sum(1 for x in ds if x < 10) / len(ds):.0%} within 10 units")
    ls = sorted(lengths)
    if ls:
        print(f"  fight length median {ls[len(ls) // 2]:.1f} s")


if __name__ == "__main__":
    args = sys.argv[1:]
    T = None
    if "--map" in args:
        i = args.index("--map")
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from brain.maps import get_map, terrain
        T = terrain(get_map(args[i + 1]))
        del args[i:i + 2]
    stats(args, T)
