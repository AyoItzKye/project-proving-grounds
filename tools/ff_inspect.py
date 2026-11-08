"""What is in a running Halo: Reach match (Firefight above all): every object by its handle, kind, tag name, side and,
for the AI, its rank (the character tag: objects\\characters\\<species>\\ai\\<rank>). For learning what an NPC is.

    python -I tools/ff_inspect.py              one look: every biped and vehicle, then counts by tag
    python -I tools/ff_inspect.py --all        every object (weapons, equipment, scenery... too)
    python -I tools/ff_inspect.py --watch 300  spawns and deaths as they happen, for 300 s
    python -I tools/ff_inspect.py --json out   one look saved as JSON

Sides (unit +0x1CA): 1 Spartan players, 7 Elite players, 2 human AI (Marines), 3 the Covenant AI (live Beachhead)."""
import json
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.live import LiveReach, NONE  # noqa: E402
from brain.forge import _tag_names  # noqa: E402

KIND = {0: "biped", 1: "vehicle", 2: "weapon", 3: "equipment", 4: "terminal", 5: "projectile", 6: "scenery",
        7: "machine", 8: "control", 9: "sound_scenery", 10: "crate", 11: "creature", 12: "giant", 13: "effect_scenery"}
SIDE = {1: "spartan_players", 2: "human_ai", 3: "covenant_ai", 7: "elite_players"}
UNIT_SCAN = 0x214          # bytes read of a unit (side, damage, actor)


def look(live, every=False):
    names = _tag_names(live) or []
    ents, mx, _ = live._array(0x10)
    b = live.g.read(ents, mx * 0x18)
    owner = {}
    base, pmx, psize = live._array(0x18)
    for i in range(pmx):
        p = live.g.read(base + i * psize, 0xD0)
        if struct.unpack_from("<H", p, 0)[0]:
            owner[struct.unpack_from("<I", p, 0x28)[0]] = (i, p[0xB0:0xD0].decode("utf-16-le", "replace").partition("\0")[0],
                                                           p[0xAC])
    out = []
    for i in range(mx):
        salt = struct.unpack_from("<H", b, i * 0x18)[0]
        kind = b[i * 0x18 + 4]
        if not salt or (not every and kind not in (0, 1)):
            continue
        o = struct.unpack_from("<Q", b, i * 0x18 + 0x10)[0]
        u = live.g.read(o, UNIT_SCAN if kind in (0, 1) else 0x80)
        tag = struct.unpack_from("<I", u, 0)[0]
        h = (salt << 16) | i
        d = dict(handle=f"{h:08X}", kind=KIND.get(kind, kind), tag=names[tag & 0xFFFF] if (tag & 0xFFFF) < len(names) else
                 f"{tag:08X}", parent=f"{struct.unpack_from('<I', u, 0x14)[0]:08X}",
                 pos=[round(v, 2) for v in struct.unpack_from("<3f", u, 0x44)])
        if kind in (0, 1):
            d["side"] = SIDE.get(u[0x1CA], u[0x1CA])
            d["shield_dmg"], d["body_dmg"] = [round(v, 2) for v in struct.unpack_from("<2f", u, 0x124)]
            if h in owner:
                d["player"] = dict(zip(("index", "name", "team"), owner[h]))
            elif kind == 0:
                d["rank"] = live.ai_rank(u)
        out.append(d)
    return out


def show(rows):
    for d in rows:
        who = d.get("player")
        extra = f"player {who['index']} {who['name']} team {who['team']}" if who else f"rank {d.get('rank')}"
        print(f"{d['handle']} {d['kind']:<9} {d.get('side', ''):<16} {d['tag'].rsplit(chr(92), 1)[-1]:<22} "
              f"{extra if d['kind'] == 'biped' else ''} at {d['pos']}" + (" riding" if d["parent"] != f"{NONE:08X}" else ""))
    count = {}
    for d in rows:
        k = (d["kind"], d.get("side"), d["tag"], d.get("rank"))
        count[k] = count.get(k, 0) + 1
    print("\ncounts:")
    for (kind, side, tag, rank), n in sorted(count.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3} {kind} {side or ''} {tag}" + (f" ({rank})" if rank else ""))


def watch(live, seconds):
    t0, seen = time.time(), {}
    while time.time() - t0 < seconds:
        try:
            rows = {d["handle"]: d for d in look(live)}
        except Exception as e:
            print(f"{time.time() - t0:6.1f} s read failed ({e})")
            break
        for h, d in rows.items():
            if h not in seen:
                print(f"{time.time() - t0:6.1f} s + {h} {d['kind']} {d.get('side')} {d['tag'].rsplit(chr(92), 1)[-1]} "
                      f"{d.get('rank') or (d.get('player') or {}).get('name', '')} at {d['pos']}")
        for h, d in seen.items():
            if h not in rows:
                print(f"{time.time() - t0:6.1f} s - {h} {d['kind']} {d['tag'].rsplit(chr(92), 1)[-1]} gone")
        seen = rows
        sys.stdout.flush()
        time.sleep(0.5)


def main():
    live = LiveReach()
    if "--watch" in sys.argv:
        return watch(live, float(sys.argv[sys.argv.index("--watch") + 1]))
    rows = look(live, every="--all" in sys.argv)
    if "--json" in sys.argv:
        json.dump(rows, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    show(rows)


if __name__ == "__main__":
    main()
