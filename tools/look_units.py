"""Each player's body: its object's tag path (which biped: ODST's characters are different bipeds) and the region
permutation bytes (ODST: 16 bytes from biped +0x1358, found against probe bots). Read only.

usage: python -I look_units.py [--game odst] [--at HEX] [--n N]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from look_dump import live_for  # noqa: E402

AT = {"odst": 0x1358}


def main():
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "odst"
    at = int(sys.argv[sys.argv.index("--at") + 1], 16) if "--at" in sys.argv else AT.get(game, 0)
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 16
    live = live_for(game)
    paths = {h: path for h, typ, path, pos in live.objects((0,))}       # bipeds (object type 0)
    for p in live.players():
        h = p.get("unit")
        o = live.object(h) if h is not None else None
        if not o:
            print(p["name"].ljust(12), "no body")
            continue
        regions = live.g.read(o + at, n)
        tag = paths.get(h, "?").rsplit("\\", 1)[-1]
        print(f"{p['name']:<12} {tag:<28} " + " ".join("%3d" % (b if b != 255 else -1) for b in regions))


if __name__ == "__main__":
    main()
