"""Save the first bytes of Halo: Reach's game globals (TLS +0x48 block, where the game options live) to a file, to tell
two game states apart by diffing two dumps (a theater film against a live match, to find the playback flag that keeps
bots out of films). Also prints a diff against a second file if given.

usage: python -I globals_dump.py <out.bin> [--size 0x4000] [--diff other.bin]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))


def main():
    out = sys.argv[1]
    size = int(sys.argv[sys.argv.index("--size") + 1], 0) if "--size" in sys.argv else 0x4000
    from brain.live import LiveReach
    live = LiveReach()
    live.players()
    gg = live.g.u64(live._blk + 0x48)
    data = live.g.read(gg, size)
    open(out, "wb").write(data)
    print(f"{len(data)} bytes of game globals ({gg:#x}) -> {out}; variant {live.variant_name()!r}")
    if "--diff" in sys.argv:
        other = open(sys.argv[sys.argv.index("--diff") + 1], "rb").read()
        n = 0
        for k in range(min(len(data), len(other))):
            if data[k] != other[k] and n < 200:
                print(f"  +{k:#06x}: {other[k]:#04x} -> {data[k]:#04x}")
                n += 1


if __name__ == "__main__":
    main()
