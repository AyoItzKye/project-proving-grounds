"""Offline check: a person's run-up a bot cannot reach in Bot.RUNUP_GIVE_UP s, with the take-off within 2.5 u, is let
go: the bot takes off from where it is (live Boneyard 20261105-033712 / 035632, the drop to the core in phase 3: 3-6
attackers bunched on the way to the run-up 2.8 u behind the take-off, none dropped in 250 s).

usage: python -I test_runup_give_up.py      -> "run-up give up OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def main():
    m = get_map("reach_70_boneyard/variants/v86d95e85")
    T = terrain(m)
    L = invasion.layout(m["objects"])
    invasion.apply_barriers(T, L, {b["key"]: False for b in L["barriers"] if b["kind"] == "gate"})
    goal, here = Vec(300.717, 108.269, -7.0), Vec(264.5, 90.0, -5.0)   # phase 3's way to the core; the bunch's spot
    take_off = Vec(265.67, 89.63, -5.0)
    w = T.nav(here, goal, jump=True, human=True)
    assert hasattr(w, "sx") and abs(w.sx - take_off.x) < 0.05, f"the drop is the nav's way: {w}"
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    nav = lambda a, q, **k: T.nav(a, q, **k)

    def heading(now, at=None):
        b.now = now
        me = PlayerState(1, 0, "bot", at or here, yaw=0.0)
        act = Action(yaw=0.0)
        b.move_to(me, goal, act, nav)
        return math.atan2(act.strafe, act.forward)        # (yaw 0: the walk's world heading)

    # the bunch's spot is on the run's line past the run-up: on to the take-off at once (c3a4eeb, test_runup_line)
    now_h = heading(50.0)
    want0 = math.atan2(take_off.y - here.y, take_off.x - here.x)
    assert math.cos(now_h - want0) > 0.9, f"on the run line: at the take-off at once, east (heading {now_h:.2f})"
    b.runup_key = None
    here = Vec(264.9, 90.7, -5.0)                         # off the line (0.9 u to its side), the take-off 1.3 u away
    w = T.nav(here, goal, jump=True, human=True)
    assert hasattr(w, "sx") and abs(w.sx - take_off.x) < 0.05, f"the drop is the nav's way from beside it too: {w}"
    to_run = heading(100.0)
    assert math.cos(to_run - math.pi) > 0.7, f"first to the person's run-up, west: heading {to_run:.2f}"
    later = heading(100.0 + Bot.RUNUP_GIVE_UP + 0.5)
    want = math.atan2(take_off.y - here.y, take_off.x - here.x)
    assert math.cos(later - want) > 0.9, f"after {Bot.RUNUP_GIVE_UP} s: at the take-off, east (heading {later:.2f})"
    print("run-up give up OK")


if __name__ == "__main__":
    main()
