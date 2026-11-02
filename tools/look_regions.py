"""Each player's armor region permutations, read from its biped: one byte every 8 from a per-game offset, regions in
alphabetical order (Halo 3 Spartan +0x11B0: arms, body, chest, flaming head, helmet, left shoulder, legs, right
shoulder; Elite +0x1288; found with tools/look_diff.py against probe bots). Shows what a look byte actually put on a
bot, without photos. Read only.

usage: python -I look_regions.py [--game G] [--at HEX] [--n N] [--step N]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from look_dump import live_for  # noqa: E402

AT = {"h3": 0x11B0}               # where a game's bipeds keep the region bytes (others: --at, from look_diff)
NAMES = {"h3": ["arms", "body", "chest", "flames", "helmet", "Lshoulder", "legs", "Rshoulder"]}


def arg(name, default, base=10):
    return int(sys.argv[sys.argv.index(name) + 1], base) if name in sys.argv else default


def main():
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "h3"
    at, n, step = arg("--at", AT.get(game, 0), 16), arg("--n", 8), arg("--step", 8)
    names = (NAMES.get(game, []) + [f"r{k}" for k in range(n)])[:n]
    live = live_for(game)
    print("player".ljust(16) + " ".join(x[:9].rjust(9) for x in names))
    for p in live.players():
        o = live.object(p["unit"]) if p.get("unit") is not None else None
        if not o:
            print(p["name"].ljust(16), "no body")
            continue
        b = live.g.read(o + at, step * n)
        print(p["name"].ljust(16) + " ".join(str(b[step * k]).rjust(9) for k in range(n)))


if __name__ == "__main__":
    main()
