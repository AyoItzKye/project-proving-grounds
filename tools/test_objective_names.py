"""brain/live.py: objective tags seeded from the map's tag names (Halo 4 / H2A), then flags_by_stand on them.
usage: python -I test_objective_names.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import live as L  # noqa: E402
from brain.core import Vec  # noqa: E402


class Fake:
    OBJECTIVE_NAMES = L.LiveH4F.OBJECTIVE_NAMES
    _name_objectives = L.LiveReach._name_objectives

    def __init__(s, names):
        s.names = names

    def _own_name(s, tag, folder):
        return s.names.get(tag)


f = Fake({1: "new_flag", 2: "storm_skull", 3: "storm_assault_rifle", 4: "h2a_assault_bomb", 5: "flag", 6: "h2a_oddball"})
f._name_objectives([(10 + t, t, L.NONE, (0.0, 0.0, 0.0)) for t in (1, 2, 3, 4, 5, 6)])
assert f._flag_tags == {1, 5}, f._flag_tags
assert f._ball_tags == {2, 6}, f._ball_tags
assert f._obj_tags == {"assault": {4}}, f._obj_tags
# seeded: every object of a flag tag is a flag (its team the nearest stand); a gun lying on a stand never is one
weapons = [(11, 1, L.NONE, (0.1, 0.0, 0.0)), (13, 3, L.NONE, (10.0, 0.1, 0.0))]
out = L.flags_by_stand(weapons, {}, {0: Vec(0, 0, 0), 1: Vec(10, 0, 0)}, f._flag_tags, {})
assert [(x["handle"], x["team"]) for x in out] == [(11, 0)], out
print("test_objective_names: ok")
