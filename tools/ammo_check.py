"""Ammo reads in a match trace (logs/trace_*.jsonl, any game): per bot and gun in hand, the magazine should fall only
within 0.5 s of a fire press, and rise only when the reserve pays exactly what it gained (a reload: the brain's press,
or the game's own on an empty magazine). Counts both per gun kind and lists every exception. Writes
logs/verify/ammo_check_<trace name>.txt.

usage: python -I ammo_check.py <trace.jsonl>
"""
import collections
import json
import os
import sys

FIRE, RELOAD = 1, 64          # buttons word bits (tools/live_bots.py buttons())


def series(lines):
    """{bot id: [(t, gun, reserve, magazine, last fire press t, last reload press t) or None (a break)]}."""
    out, fired, pressed = collections.defaultdict(list), {}, {}
    for r in lines:
        if "cmd" not in r:
            continue                                   # (the brain's think lines)
        bot, b = r["id"], r["cmd"][3]
        if b & FIRE:
            fired[bot] = r["t"]
        if b & RELOAD:
            pressed[bot] = r["t"]
        inv = r.get("inv") or [r["wpn"]]
        i = inv.index(r["wpn"]) if inv.count(r["wpn"]) == 1 else None    # two of a kind: which one is in hand?
        if i is None or len(r.get("mag", ())) != len(inv) or min(r["ammo"][i], r["mag"][i]) < 0:
            out[bot].append(None)
            continue
        out[bot].append((r["t"], r["wpn"], r["ammo"][i] - r["mag"][i], r["mag"][i], fired.get(bot, -9.0),
                         pressed.get(bot, -9.0)))
    return out


def check(lines):
    """(Counter {(gun, what): n}, [exceptions])."""
    c, odd = collections.Counter(), []
    for bot, rows in series(lines).items():
        same = lambda j, k: (0 <= j < len(rows) and 0 <= k < len(rows) and rows[j] and rows[k]
                             and rows[j][1] == rows[k][1] and abs(rows[k][0] - rows[j][0]) <= 0.5)
        for k in range(1, len(rows)):
            if not same(k - 1, k):
                continue                               # a break, another gun, or a respawn gap
            (t, gun, res, mag, fire_t, reload_t), p = rows[k], rows[k - 1]
            dm = mag - p[3]
            if dm < 0:
                ok = t - fire_t <= 0.5
                c[gun, "falls"] += 1
                c[gun, "falls near a fire press"] += ok
                if not ok:
                    odd.append(f"bot {bot} t={t:.2f} {gun}: magazine {p[3]} -> {mag} with no fire press in 0.5 s")
            elif dm > 0:
                # the reserve pays in the same tick or one either side (the two fields are read a moment apart)
                paid = any(same(j, l) and rows[l][2] - rows[j][2] == -dm for j in (k - 2, k - 1) for l in (k, k + 1))
                c[gun, "rises"] += 1
                c[gun, "rises paid from the reserve"] += paid
                c[gun, "rises after a brain reload press (3 s)"] += t - reload_t <= 3.0
                if not paid:
                    odd.append(f"bot {bot} t={t:.2f} {gun}: magazine {p[3]} -> {mag}, reserve {p[2]} -> {res}: not paid")
    return c, odd


def main():
    path = sys.argv[1]
    lines, rows = open(path, encoding="utf-8").read().splitlines(), []
    for k, x in enumerate(lines):
        try:
            rows.append(json.loads(x))
        except ValueError:
            if k != len(lines) - 1:
                raise                      # only the last line may be cut off (a trace still being written)
    c, odd = check(rows)
    out = [f"{os.path.basename(path)}: magazine changes of the gun in hand (rounds known)"]
    for gun in sorted({g for g, _ in c}):
        out.append(f"  {gun}: falls {c[gun, 'falls']} (near a fire press {c[gun, 'falls near a fire press']}); "
                   f"rises {c[gun, 'rises']} (paid from the reserve {c[gun, 'rises paid from the reserve']}, "
                   f"after a brain reload press {c[gun, 'rises after a brain reload press (3 s)']})")
    out.append(f"exceptions: {len(odd)}")
    out += ["  " + x for x in odd[:40]]
    name = os.path.basename(path).replace("trace_", "").replace(".jsonl", "")
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "verify", f"ammo_check_{name}.txt")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
    print("written:", os.path.normpath(dest))


if __name__ == "__main__":
    main()
