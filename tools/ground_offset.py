"""How high the bots' reported position sits above the map's floor (the terrain layers), from a trace:
the median and spread of (z - nearest floor at or below z) over every bot sample. A game whose
position is not the feet shows a steady offset, and then every ground test with a small drop (the edge
guard's "grounded") reads false on solid floor.: Lockout falls (H2A).

usage: python -I ground_offset.py <trace.jsonl> <map>
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


def main():
    T = terrain(get_map(sys.argv[2]))
    off = []
    for line in open(sys.argv[1]):
        d = json.loads(line)
        for row in d.get("world", []):
            if not row[2]:
                continue
            x, y, z = row[3:6]
            try:
                j, i = T._cell(Vec(x, y))
            except Exception:
                continue
            if not (0 <= j < T.lz.shape[1] and 0 <= i < T.lz.shape[2]):
                continue
            f = T.lz[:, j, i]
            f = f[np.isfinite(f) & (f <= z + 0.3)]
            if len(f):
                off.append(z - f.max())
    a = np.array(off)
    a = a[a < 3]                      # in the air or over a far lower floor: not standing
    print(f"{len(a)} samples standing: median {np.median(a):.2f}, 10% {np.percentile(a, 10):.2f}, "
          f"90% {np.percentile(a, 90):.2f}; share above 0.6: {np.mean(a > 0.6):.0%}")


if __name__ == "__main__":
    main()
