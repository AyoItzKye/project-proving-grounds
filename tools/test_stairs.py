"""Stairs on Halo 4 / H2A levels (brain/terrain.py stair_rule): Adrift's red flag deck is reached up its stairs (risers of
0.20-0.26 a cell, over MAX_RISE) from the blue side's CTF spawns. Without the rule 2 of 53 reached it and runners stood
under the flag for minutes.

usage: python -I test_stairs.py      -> "stairs OK"
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

m = get_map("h4_ca_warhouse")
T = terrain(m)
objs = json.load(open(os.path.join(HERE, "..", "maps", "h4_ca_warhouse", "objects.json")))
blue = [Vec(*s["pos"]) for s in objs["spawns"] if int(s["team"]) == 1 and "ctf" in s.get("games", [])]
ok = sum(1 for p in blue if T.path_ahead(p, m["flags"][0], n=2000, human=True))
if ok < 0.9 * len(blue):
    sys.exit(f"FAIL: Adrift's red flag reached from {ok} of {len(blue)} blue CTF spawns (stairs walled off)")
print(f"stairs OK (Adrift's red flag from {ok} of {len(blue)} blue CTF spawns)")
