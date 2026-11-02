"""Spire's gravity lifts under the spire ride as lifts: the map files them as inv_mancannon launchers, so the bots ran the
people's link (33 u up, 15 u aside) as a jump at its landing and left the column; 1 of 5 phase-3 visits to its base got
up.

1. Bot.lift_base: the people's link up from the launcher under the spire is a lift (its base: the launcher); a man
   cannon's long low arc from the same spot is not; nor is a 2 u hop
2. on the ride (Bot.ride_lift) a bot 1 u off the column's middle steers into it, not at the landing 15 u aside

usage: python -I test_spire_lift.py      -> "spire lift OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Bot  # noqa: E402
from brain.core import PlayerState, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import JumpVec  # noqa: E402


def main():
    fails = []
    M = get_map("reach_35_island")
    b = Bot(1, 1, make_profile("top", "objector", random.Random(1)), M, random.Random(1))
    take, land = Vec(-160.6, -380.3, -57.7), Vec(-169.2, -392.5, -24.3)
    me = PlayerState(1, 1, "b", take)
    up = JumpVec(land.x, land.y, land.z, take.x, take.y)
    arc = JumpVec(take.x - 30.0, take.y, take.z + 5.0, take.x, take.y)
    hop = JumpVec(take.x - 2.0, take.y, take.z + 1.0, take.x, take.y)
    base = b.lift_base(up, me)
    if base is None or (base - take).flat() > 1.0 or b.lift_base(arc, me) is not None or b.lift_base(hop, me) is not None:
        fails.append(f"lift_base: the climb {base}, a long arc {b.lift_base(arc, me)}, a hop {b.lift_base(hop, me)} "
                     "(want the launcher under the spire, None, None)")
    if base is not None:
        off = PlayerState(1, 1, "b", Vec(base.x + 1.0, base.y, base.z), yaw=0.0)
        b.now, b.lift_ride = 10.0, (base, land, 9.8)
        a = Action(yaw=0.0)
        b.ride_lift(off, a)
        want = math.atan2(base.y - off.pos.y, base.x - off.pos.x)
        moving = math.atan2(a.forward * math.sin(a.yaw) + a.strafe * math.cos(a.yaw),
                            a.forward * math.cos(a.yaw) - a.strafe * math.sin(a.yaw))
        if abs(math.atan2(math.sin(moving - want), math.cos(moving - want))) > 0.6 or not (a.forward or a.strafe):
            fails.append(f"on the ride 1 u off the middle: moving {math.degrees(moving):.0f} deg (want into the column, "
                         f"{math.degrees(want):.0f} deg)")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("spire lift OK (the climb under the spire rides as a lift, into its column)")


if __name__ == "__main__":
    main()
