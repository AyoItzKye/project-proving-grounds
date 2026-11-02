"""Input stalls in a match recording: moments when 3+ bots' views stand still while their commands turn (the game
dropping or replaying their actions; pauses skipped), how long and how many a minute.: Halo 3 bots stalled
6-7 s a minute in the player's Construct matches, every time he fired on someone (botcore s94 fixed the cause: his aim
assist copied into their actions failed the game's action check). With botcore's tick count in the trace (world rows
"gt", from) each stall also says whether the game kept ticking.
usage: python -I input_stalls.py <trace> [...]"""
import collections
import json
import sys


def stalls(path):
    rows, world = collections.defaultdict(list), []
    for l in open(path, encoding="utf-8"):
        if '"world"' in l:
            r = json.loads(l)
            world.append((r["t"], tuple((round(x[3], 2), round(x[4], 2)) for x in sorted(r["world"]) if x[2]), r.get("gt")))
        elif '"cmd"' in l:
            r = json.loads(l)
            rows[r["id"]].append((r["t"], r["yaw"], r["cmd"][2], r.get("veh", -1)))
    paused, prev, since = [], None, None          # every player frozen: the pause menu (recordings before)
    for t, pic, _ in world:
        if pic == prev:
            since = since if since is not None else t - 0.25
        else:
            if since is not None and t - since > 1.0:
                paused.append((since, t))
            since = None
        prev = pic
    frozen = collections.Counter()
    for rs in rows.values():
        for (t0, y0, c0, v0), (t1, y1, _c1, _v1) in zip(rs, rs[1:]):
            if y1 == y0 and abs(c0 - y0) > 0.03 and v0 == -1 and t1 - t0 < 0.2:
                frozen[round(t1, 1)] += 1
    bins = sorted(b for b, n in frozen.items() if n >= 3 and not any(p0 - 0.5 <= b <= p1 + 0.5 for p0, p1 in paused))
    out, cur = [], None
    for b in bins:
        if cur is not None and b - cur[1] <= 0.25:
            cur[1] = b
        else:
            if cur and cur[1] - cur[0] >= 0.5:
                out.append(tuple(cur))
            cur = [b, b]
    if cur and cur[1] - cur[0] >= 0.5:
        out.append(tuple(cur))
    span = (world[-1][0] - world[0][0]) / 60 if world else 0.0
    played = span - sum(b - a for a, b in paused) / 60
    ticking = []
    for s0, s1 in out:
        g = [gt for t, _, gt in world if s0 <= t <= s1 and gt is not None]
        ticking.append(None if len(g) < 2 else g[-1] > g[0])
    return out, played, ticking


def main():
    for f in sys.argv[1:]:
        out, played, ticking = stalls(f)
        total = sum(b - a for a, b in out)
        print("%s: %.1f min played, %d stalls, %.1f s (%.1f s a minute)" % (f, played, len(out), total,
                                                                        total / max(played, 0.1)))
        for (a, b), tk in list(zip(out, ticking))[:12]:
            print("   %.1f-%.1f s%s" % (a, b, "" if tk is None else "  game ticking" if tk else "  game tick stopped"))


if __name__ == "__main__":
    main()
