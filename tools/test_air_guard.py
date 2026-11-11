"""A pilot does not fly into a structure beside it (the Banshee's attack passes ran 3-6 u under the spire top's level, z
-26 to -31 within 10 u of its middle, its height taken from the ground 30 u under it):

1. Terrain.top_near by the spire's top reads the top's level, out in the open the ground's
2. a Banshee at speed where it flew live (485 s, z -26.7, heading in): pulls up and eases off
3. a Banshee out in the open, fast or slow: untouched; a gunner: untouched; slow under the overhang heading at the
   spire's side: the probe's turn or climb (tools/test_air_stuck.py)
4. a Banshee at speed setting down over the core's top, its destination (drive's landing: match 220515, held
   1.5-6 u over the core's top for 200 s, never out): untouched

usage: python -I test_air_guard.py      -> "air guard OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("reach_35_island")
T = terrain(M)
TOP_MID = Vec(-175.4, -401.6, -24.3)


def fly(pos, vel, yaw, seat="driver", landing=False, dest=None):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, rng=random.Random(1))
    b._terrain, b.seat, b.notes, b.landing, b.air_dest = T, seat, [], landing, dest
    me = PlayerState(1, 0, "pilot", pos, vel=vel, yaw=yaw, alive=True, vehicle=9)
    act = Action(yaw=yaw)
    act.forward, act.pitch = 1.0, -0.2
    b.air_guard(me, act, Snapshot(10.0, [me], vehicles=[dict(handle=9, kind="banshee", pos=(pos.x, pos.y, pos.z),
                                                               occupied=True, riders=1, team=0)]))
    return act, b.notes


def main():
    fails = []
    top = T.top_near(-177.8, -406.8, 6.0)
    # out in the open: the lowest-topped of a few spots round the map, its top the ground's level
    spots = [(x, y) for x in range(-220, -100, 12) for y in range(-460, -300, 12)]
    ox, oy = min(spots, key=lambda q: T.top_near(q[0], q[1], 6.0))
    ground = T.top_near(ox, oy, 6.0)
    if not -26.0 < top < -18.0 or ground > -50.0:
        fails.append(f"top_near: by the spire's top {top:.1f} (want its level, -26 to -18), out in the open {ground:.1f}")
    live = Vec(-181.3, -404.5, -26.7)
    into = math.atan2(TOP_MID.y - live.y, TOP_MID.x - live.x)
    act, notes = fly(live, Vec(5.0, -2.0, 0.0), into)
    if act.pitch < 0.35 or act.forward > 0.5 or not notes:
        fails.append(f"a Banshee at speed under the spire top's level, heading in: pitch {act.pitch:.2f}, forward "
                     f"{act.forward:.2f} (want a pull-up)")
    for pos, vel, seat, what in ((Vec(ox, oy, ground + 15.0), Vec(6.0, 0.0, 0.0), "driver", "out in the open"),
                                 (Vec(ox, oy, ground + 15.0), Vec(1.0, 0.0, 0.0), "driver", "slow, out in the open"),
                                 (live, Vec(5.0, -2.0, 0.0), "gunner", "a gunner")):
        act, notes = fly(pos, vel, 0.0, seat)
        if act.pitch != -0.2 or act.forward != 1.0:
            fails.append(f"{what}: pitch {act.pitch:.2f}, forward {act.forward:.2f} (want untouched)")
    # (slow under the overhang, heading at the spire's side: untouched until; the stuck Banshees that night were slow
    # ones, so the probe turns it now: tools/test_air_stuck.py)
    act, notes = fly(live, Vec(1.0, 0.0, 0.0), 0.0)
    if not any(n.startswith("air: wall ahead") for n in notes):
        fails.append(f"slow under the spire's overhang, heading at its side: {notes} (want the probe's turn or climb)")
    # setting down over the core's top, where the stand reads solid all round (the probe looks no further than the spot)
    act, notes = fly(TOP_MID + Vec(0, 0, 1.5), Vec(5.0, -2.0, 0.0), into, landing=True, dest=TOP_MID)
    if act.pitch != -0.2 or act.forward != 1.0 or notes:
        fails.append(f"setting down at its destination: pitch {act.pitch:.2f}, forward {act.forward:.2f}, {notes} "
                     f"(want untouched)")
    # 5. over the spire's top under the map's roof (1.5-2.5 u of room over the decks, live 20261110-201813: "pull up" and
    # the roof's "down" on 5,583 rows of one Banshee): from the upper half of the room under the roof no pull-up, whatever
    # its speed (in the room it keeps the middle)
    for pos in (Vec(-178.0, -397.0, -17.5), Vec(-170.0, -395.0, -17.5)):
        for vel in (Vec(5.0, -2.0, 0.0), Vec(1.0, 0.0, 0.0)):
            act, notes = fly(pos, vel, 0.0)
            if any("pull up" in n for n in notes):
                fails.append(f"over the spire's top at {pos} under the roof, speed {vel.flat():.0f}: {notes} (pulled up "
                             "into the roof)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"air guard OK (the spire's top reads {top:.1f}; a Banshee under it pulls up; the open and gunners as they were; "
          "no pull-up into the roof over the top)")


if __name__ == "__main__":
    main()
