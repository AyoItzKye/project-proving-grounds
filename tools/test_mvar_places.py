"""A Reach map variant read from its .mvar file (brain/maps.py load_map) keeps the scenario's places of a mode the file
has none of (MVAR_KEEP): Boardwalk's built-in variant labels Stockpile's goals and respawn zones but no stp_flag, and
live Stockpile Nov 10 read no flag in 516 s (0-0, the trace's items empty while a probe read 7 stands). Every filed
Boardwalk variant: Stockpile's stands as the base map's, Assault / Territories / Headhunter places present.

usage: python -I test_mvar_places.py      -> "mvar places OK"
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import modes  # noqa: E402
from brain.maps import load_map  # noqa: E402


def count(m, mode, kind):
    return len(modes.layout(m["objects"], mode).get(kind, []))


def main():
    fails = []
    base = load_map("reach_50_panopticon")
    want = count(base, "stockpile", "stockpile_flag")
    root = os.path.join(HERE, "..", "maps", "reach_50_panopticon", "variants")
    vs = [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(root, "*", "mvar_objects.json"))]
    if not vs:
        fails.append("no Boardwalk variant with an mvar_objects.json filed")
    for v in vs:
        m = load_map(f"reach_50_panopticon/variants/{v}")
        got = count(m, "stockpile", "stockpile_flag")
        if got != want or want == 0:
            fails.append(f"{v}: {got} Stockpile stands (the base map {want})")
        for mode, kind in (("assault", "bomb"), ("territories", "territory"), ("headhunter", "drop_point")):
            if not count(m, mode, kind):
                fails.append(f"{v}: no {mode} places")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"mvar places OK ({len(vs)} Boardwalk variants, {want} Stockpile stands each)")


if __name__ == "__main__":
    main()
