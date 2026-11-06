"""Aircraft heights from the map's own shape (Terrain.air_levels): nothing painted by hand ("Air space navmesh should
automatically determine low flight height and high fly height by distance from ground instead of making me do it").

Checks: on real maps the attack-run height is 2.5-6 u and the travel height 2+ u over it and at most 25 u; Blood Gulch's
canyon walls do not count as things to fly over (travel under 12 u, people's Banshee median is 14.8); Boneyard's
buildings lift travel over Blood Gulch's; a map's learned heights (people's flying) win over the measured ones.

usage: python -I tools/test_air_levels.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402


def main():
    got = {}
    for name in ("bloodgulch", "reach_70_boneyard", "reach_35_island"):
        T = terrain(get_map(name))
        low, high = T.air_levels()
        assert 2.5 <= low <= 6.0, (name, low)
        assert low + 2.0 <= high <= 25.0, (name, low, high)
        got[name] = (low, high)
    assert got["bloodgulch"][1] < 12.0, got              # the canyon walls are not flown over
    assert got["reach_70_boneyard"][1] > got["bloodgulch"][1], got   # buildings are
    T = terrain(get_map("bloodgulch"))
    had = getattr(T, "air_heights", None)
    try:
        T.air_heights = (3.3, 11.1)
        assert Bot.air_heights(None, T) == (3.3, 11.1)     # learned from people first
        T.air_heights = None
        assert Bot.air_heights(None, T) == T.air_levels()
    finally:
        T.air_heights = had
    print("air levels OK", got)


if __name__ == "__main__":
    main()
