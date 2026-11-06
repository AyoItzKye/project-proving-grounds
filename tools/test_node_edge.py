"""Offline check: a bot standing on a floor whose edge its cell's centre misses, under a tread over it, is on that floor
in the nav, not the tread (live Boneyard 20261105-041255, issue #4's stairs at (258.2, 106.5): bots at -6.15 read as on
the -5.08 tread, their next point their own cell, 10-16 s spells there).

usage: python -I test_node_edge.py      -> "node edge OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


def main():
    T = terrain(get_map("reach_70_boneyard/variants/v86d95e85"))
    p = Vec(258.24, 106.48, -6.15)
    l, j, i = T._node(p)
    assert abs(float(T.lz[l, j, i]) - p.z) < 0.4, f"on the floor at its feet, not {float(T.lz[l, j, i]):.2f}"
    goal = Vec(256.12, 82.36, -4.0)
    q = p
    for _ in range(40):                                 # its way on: up the stairs east and to the goal
        w = T.nav(q, goal, jump=True, human=True)
        q = Vec(w.x, w.y, w.z)
    assert (q - goal).flat() < 2.0, f"the way from there reaches the goal: ended at {q}"
    q = Vec(258.3, 106.3, -5.05)                        # on the tread: still the tread
    l, j, i = T._node(q)
    assert abs(float(T.lz[l, j, i]) - q.z) < 0.2, "a bot on the tread is on it"
    print("node edge OK")


if __name__ == "__main__":
    main()
