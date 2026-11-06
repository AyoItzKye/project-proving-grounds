"""A zone holder in its zone does not step out for a gun lying just outside it (Bot.keep_role / out_of_held). Live
Boneyard B22 R1 (trace logs/tmp/invasion_regress/traces/trace_reach_70_boneyard_20261105-131829.jsonl, 208.4 s): the
Elites' 12.0 s uncontested hold of the south territory ended with the lone holder (Elite 7) going 1.4 u out for a gun at
(257.17, 80.43), 1.8 u off; B14 R1 the same. A gun inside the zone is still picked up; off its post as before.

usage: python -I test_hold_item.py      -> "hold item OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = "reach_70_boneyard/variants/v86d95e85"


def pick(me_at, gun):
    m = get_map(M)
    L = invasion.layout(m["objects"])
    zones = L["phases"][1]
    zone = min(zones, key=lambda z: (z - Vec(255.81, 81.95, -4.0)).flat())
    b = Bot(7, 1, make_profile("top", "objector", random.Random(7)), m, random.Random(7))
    b.order = Order("defender", zone)
    me = PlayerState(7, 1, "e", me_at)
    sn = Snapshot(208.0, [me], mode="invasion", inv_phase=1, inv_attackers=1, inv_zones=list(zones),
                  inv_zone_r=[invasion.zone_radius(L, z) for z in zones], inv_phase_t=100.0)
    sc = {("item", gun): 1.9, ("objective", zone): 1.4}
    b.keep_role(sc, me, sn, [])
    return max(sc, key=sc.get)[0]


def main():
    fails = []
    if pick(Vec(255.6, 81.9, -4.0), Vec(257.17, 80.43, -4.0)) != "objective":
        fails.append("in the territory, a gun 1.8 u off it: it goes for the gun")
    if pick(Vec(255.6, 81.9, -4.0), Vec(255.9, 82.1, -4.0)) != "item":
        fails.append("a gun inside the territory: not taken")
    if fails:
        print("hold item FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("hold item OK")


if __name__ == "__main__":
    main()
