"""A gun freed between its handle and the read (brain/live.py weapon_name): every game's reader answers "none", not a
TypeError. Live ODST Firefight Nov 9: an AI's gun read empty every tick for 3 s and the brain stopped as "game gone".

usage: python -I test_freed_reads.py      -> "freed reads OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import live as L  # noqa: E402


class Gone:
    def read(s, addr, n):
        return None

    def u64(s, addr):
        return 0


def main():
    fails = []
    for cls in (L.Live, L.LiveH2, L.LiveH3, L.LiveReach, L.LiveODST, L.LiveH4F):
        r = object.__new__(cls)
        r.g = Gone()
        r.object = lambda handle: 0x1000          # (the handle still names an object)
        try:
            got = r.weapon_name(7)
        except Exception as e:
            got = f"{type(e).__name__}: {e}"
        if got != "none":
            fails.append(f"{cls.__name__}.weapon_name on a freed gun: {got!r}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("freed reads OK (every reader's weapon_name answers none)")


if __name__ == "__main__":
    main()
