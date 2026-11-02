"""What a Halo: Reach saved film (.mov, MCC's Temporary/UserContent/HaloReach/Movie) says about itself: its chunks (the
'_blf' container's 4-letter chunk names and sizes) and the UTF-16 strings in it (players' names, the map, the game
type), to see whether a bot match's film names its bots (films of bot matches crash or drop out in Theater).

usage: python -I film_info.py <film.mov> [more.mov ...]
"""
import re
import struct
import sys


def chunks(data):
    out, at = [], 0
    while at + 12 <= len(data):
        name = data[at:at + 4]
        size = struct.unpack_from(">I", data, at + 4)[0]
        if not re.fullmatch(rb"[ -~]{4}", name) or size < 12 or at + size > len(data):
            break
        out.append((name.decode(), at, size))
        at += size
    return out, at


def main():
    for path in sys.argv[1:]:
        data = open(path, "rb").read()
        cs, end = chunks(data)
        print(f"== {path} ({len(data)} bytes)")
        print("   chunks:", ", ".join(f"{n}@{a:#x}+{s:#x}" for n, a, s in cs), f"(then {len(data) - end} bytes)")
        names = sorted({m.group().decode("utf-16-le") for m in re.finditer(rb"(?:[A-Za-z0-9_ \[\]\-:'.]\x00){4,32}", data)})
        print("   strings:", names[:60])


if __name__ == "__main__":
    main()
