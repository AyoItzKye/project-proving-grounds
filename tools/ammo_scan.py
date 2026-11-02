"""Find where a game keeps a gun's rounds, live: with the brain off (logs/test_override.json "brain": "none"), every bot
fires in pulses (0.4 s of trigger every second) while each one's gun in hand is read (int16 at every even offset).
A magazine field falls while the trigger is down and only rises on a reload; a reserve field falls by what the
magazine gained, at the same tick (classify). Writes logs/verify/ammo_scan_<game>_<date>.txt.

usage: python -I ammo_scan.py <ce|h2|h3> [seconds] [span, default 0x400]      (a match running, botcore driving the bots, no brain)
"""
import collections
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
from brain.live import NONE, Live, LiveH2, LiveH3  # noqa: E402

# reader, the unit's in-hand index (offset, struct format), its 4 weapon handles
GUN = {"ce": (Live, 0x2D3, "<b", 0x2D8), "h2": (LiveH2, 0x226, "<b", 0x22C), "h3": (LiveH3, 0x262, "<b", 0x268)}


def release(m):
    """Every bot back to no buttons and no movement, its yaw kept, its pitch level."""
    for slot in botctl.status(m)["bots"]:
        yaw = struct.unpack_from("<f", m, botctl.OFF_ACTIONS + slot * 24 + 8)[0]
        botctl.act(m, slot, 0.0, 0.0, yaw, 0.0, 0)


def held(live, game, unit):
    _, at, fmt, slots = GUN[game]
    o = live.object(unit)
    if not o:
        return None, None
    cur = struct.unpack(fmt, live.g.read(o + at, struct.calcsize(fmt)))[0]
    h = struct.unpack("<4I", live.g.read(o + slots, 16))[cur] if 0 <= cur < 4 else NONE
    w = live.object(h) if h != NONE else None
    return h, w


def paid(ups, steps):
    """A reserve for these rises: each rise (sample, gain) met by a fall of the same size within a sample, and every
    fall of this field next to one of the rises (a reserve is spent on reloads only)."""
    falls = [(i, -g) for i, g in steps if g < 0]
    return bool(falls) and all(any(abs(i - j) <= 1 and g == gain for j, g in falls) for i, gain in ups) and all(
        any(abs(i - j) <= 1 for i, _ in ups) for j, _ in falls)


def classify(series):
    """(magazine candidates {offset: guns}, reserve candidates {(magazine, reserve): guns}, first values {offset: [...]})
    from {(bot slot, gun): [(t, firing, int16 values)]}. A magazine falls while the trigger is down (the fall right
    after it lets go is allowed: shots in flight) and rises only when a reload moves rounds into it, each rise paid by
    a reserve that falls at no other time. That rejects a shot counter (Halo 2 +0x1B6: the magazine falls on shots the
    counter does not count, so it is no reserve) and a field that jumps at every press (CE +0x22A on a plasma pistol:
    nothing pays it), and keeps a shotgun loaded shell by shell (third review B2: a limit on the number of rises let
    the jumper through and stopped the shotgun)."""
    mags, res = collections.Counter(), collections.Counter()
    examples = {}
    for key, rows in series.items():
        if len(rows) < 30:
            continue
        fire = [r[1] for r in rows]
        cols = list(zip(*[r[2] for r in rows]))            # one series per int16 offset
        ok = [min(v) >= 0 and max(v) <= 999 for v in cols]
        steps = [[(i, v[i + 1] - v[i]) for i in range(len(v) - 1) if v[i + 1] != v[i]] if ok[k] else []
                 for k, v in enumerate(cols)]
        for k, v in enumerate(cols):
            if not ok[k] or len(set(v)) < 3:
                continue
            falls = [i for i, g in steps[k] if g < 0]
            down_on = sum(1 for i in falls if fire[i + 1] or fire[i])
            if down_on < 3 or len(falls) - down_on > max(1, down_on // 4):
                continue
            ups = [(i, g) for i, g in steps[k] if g > 0]
            payers = [k2 for k2 in range(len(cols)) if k2 != k and paid(ups, steps[k2])] if ups else []
            if ups and not payers:
                continue                                   # it rose with nothing paying: no magazine
            mags[2 * k] += 1
            examples.setdefault(2 * k, list(v[:40]))
            for k2 in payers:
                res[(2 * k, 2 * k2)] += 1
    return mags, res, examples


def main():
    game = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    # bytes of each gun read (a third argument widens it); parsed here, not at import: zoom_probe imports release
    # with its own arguments ("--drive" third crashed it)
    span = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x400
    live, m = GUN[game][0](), botctl.shm()
    series = collections.defaultdict(list)          # (bot slot, gun handle) -> [(t, firing, int16 values)]
    t0 = time.time()
    try:
        while time.time() - t0 < seconds:
            t = time.time() - t0
            firing = (t % 1.0) < 0.4
            units = {p["index"]: p["unit"] for p in live.players() if p.get("pos") is not None}
            for slot, index in botctl.status(m)["bots"].items():
                yaw = struct.unpack_from("<f", m, botctl.OFF_ACTIONS + slot * 24 + 8)[0]
                botctl.act(m, slot, 0.0, 0.0, yaw, 0.0, 1 if firing else 0)
                if index in units:
                    h, w = held(live, game, units[index])
                    if w:
                        series[(slot, h)].append((t, firing, struct.unpack(f"<{span // 2}h", live.g.read(w, span))))
            time.sleep(1 / 30)
    finally:
        release(m)                                     # never leave the bots firing (botcore has no watchdog)
    mags, res, examples = classify(series)
    out = [f"{game}: {len(series)} guns sampled for {seconds:.0f} s (fire 0.4 s a second)"]
    out += [f"magazine candidate +{k:#x}: in {n} guns; first values {examples[k]}" for k, n in mags.most_common(6)]
    out += [f"reserve candidate +{r:#x} (with magazine +{k:#x}): in {n} guns" for (k, r), n in res.most_common(6)]
    path = os.path.join(HERE, "..", "logs", "verify",             # dated, as reload_probe's (third review N4)
                        f"ammo_scan_{game}_{time.strftime('%Y%m%d-%H%M%S')}.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
    print("written:", os.path.normpath(path))


if __name__ == "__main__":
    main()
