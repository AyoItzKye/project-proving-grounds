"""Route-field caches hold at most FIELD_BYTES each (a Forge World run once kept up to 200 vehicle fields of 84 MB
each, the brain out of memory at 834 s and the bots stopped), and that budget follows the PC's memory:

1. keep_field: past the budget the least recently used field goes first; cached_field makes a field the most recent
2. on a real map (Blood Gulch) walking and driving to many goals keep each cache within the budget, with the same
   answers as an unbounded cache
3. field_budget: a fifth of the PC's memory for the four caches, at most 1.5 GB each; this PC's memory is read

usage: python -I test_route_memory.py      -> "route memory OK"
"""
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import terrain as TR  # noqa: E402
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


def main():
    fails = []
    # 1. the cache
    TR.FIELD_BYTES = 3 * 800
    c = {}
    for k in range(4):
        TR.keep_field(c, k, np.zeros(100))
    TR.cached_field(c, 1)
    TR.keep_field(c, 4, np.zeros(100))
    if list(c) != [3, 1, 4]:
        fails.append(f"1. kept {list(c)} (want [3, 1, 4]: 0 and 2 the least recently used, 1 used again)")
    # 2. Blood Gulch: walking and driving to 12 goals with room for 3 fields per cache
    M = get_map("bloodgulch")
    T = terrain(M)
    rng = random.Random(3)
    a = M["flags"][0]
    goals = [Vec(a.x + rng.uniform(-60, 60), a.y + rng.uniform(-60, 60), a.z) for _ in range(12)]
    TR.FIELD_BYTES = 1e18
    want = [(T.nav(a, g), T.vnav(a, g)) for g in goals]
    T._fields.clear()
    T._vfields.clear()
    size = T.L * T.nh * T.nw * 8
    TR.FIELD_BYTES = 3 * size
    got = [(T.nav(a, g), T.vnav(a, g)) for g in goals]
    if len(T._fields) > 3 or len(T._vfields) > 3:
        fails.append(f"2. caches hold {len(T._fields)} walking / {len(T._vfields)} driving fields (want 3 at most)")
    if got != want:
        fails.append("2. a bounded cache changed the answers")
    # 3. the budget follows the PC's memory: the four caches at most a fifth of it, each at most 1.5 GB
    gb = 1024 ** 3
    for ram, want_each in ((8 * gb, 0.4 * gb), (16 * gb, 0.8 * gb), (32 * gb, 1.5e9), (64 * gb, 1.5e9), (None, 1.5e9)):
        if abs(TR.field_budget(ram) - want_each) > 1:
            fails.append(f"3. {ram and ram / gb} GB: {TR.field_budget(ram) / gb:.2f} GB a cache, want {want_each / gb:.2f}")
    if not TR.total_ram() or TR.total_ram() < gb:
        fails.append(f"3. this PC's memory not read ({TR.total_ram()})")
    if fails:
        print("\n".join(fails))
        sys.exit(1)
    print(f"route memory OK (LRU, Blood Gulch 12 goals within 3 fields of {size / 1e6:.1f} MB per cache)")


if __name__ == "__main__":
    main()
