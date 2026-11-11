"""Passive LiDAR (tools/lidar.py HumanWatch, every normal match): a person's jump that landed higher over its take-off than
the game's plain jump rises, by up to a crouch's tuck, was a crouch-jump even where the game does not say he crouched
(every game but H2A and Halo 4): the bots copy it crouched in the air (brain/maps.py crouch_jumps, GitHub #20).

usage: python -I test_passive_lidar.py      -> "passive lidar OK"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain.games import plain_jump  # noqa: E402
from brain.maps import crouch_jumps  # noqa: E402

fails = []


def check(what, ok):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        fails.append(what)


# 1. each game's plain jump from the measured physics (tools/jumpphys.py): Halo 3 1.11 u, Reach 0.67, CE 0.65
apex = {g: plain_jump(g) for g in ("ce", "h2", "h2a", "h3", "odst", "reach", "h4")}
check(f"plain jumps {apex}", abs(apex["h3"] - 1.107) < 0.01 and abs(apex["reach"] - 0.672) < 0.01
      and abs(apex["ce"] - 0.651) < 0.01 and all(0.5 < a < 1.3 for a in apex.values()))


def link(rise, **kw):
    return dict(dict(take_off=[0.0, 0.0, 0.62], land=[1.5, 0.0, round(0.62 + rise, 2)], apex=0.62 + rise + 0.02,
                     air_s=0.9, human=1, bot_ok=0, bot_fail=0), **kw)


# 2. Halo 3 (crouch not read): onto a ledge 1.20 u up, past the plain 1.11: a crouch-jump; 1.05 up: plain
out = crouch_jumps([link(1.20), link(1.05), link(1.50), link(0.0)], "h3")
check("h3: 1.20 up is a crouch-jump", out[0].get("crouch") == 1)
check("h3: 1.05 up stays a plain jump", not out[1].get("crouch"))
check("h3: 1.50 up (past any tuck: a ramp's carry, a lift) is not marked", not out[2].get("crouch"))
check("h3: a level jump is not marked", not out[3].get("crouch"))
# 3. Reach's lower jump: 0.80 up is past its 0.67 plain jump
check("reach: 0.80 up is a crouch-jump", crouch_jumps([link(0.80)], "reach")[0].get("crouch") == 1)
# 3b. one jump onto a ledge at about its top: 1.20 up taking 1.4 s aloft was stairs or a ramp read as air, or hops
check("h3: 1.20 up over 1.4 s (stairs, hops) is not marked", not crouch_jumps([link(1.20, air_s=1.4)], "h3")[0].get("crouch"))
# 4. only people's own jumps: not a bot's call, a ride, a painted jump or a route; an H2A crouch the game read stays
check("a bot's called jump is not marked", not crouch_jumps([link(1.2, called=1, human=0)], "h3")[0].get("crouch"))
check("a man cannon ride is not marked", not crouch_jumps([link(1.2, ride=True)], "h3")[0].get("crouch"))
check("a painted jump is not marked", not crouch_jumps([link(1.2, painted=1)], "h3")[0].get("crouch"))
check("a crouch route is left alone", crouch_jumps([link(1.2, kind="crouch")], "h3")[0].get("kind") == "crouch"
      and not crouch_jumps([link(1.2, kind="crouch")], "h3")[0].get("crouch"))
check("a crouch the game read stays", crouch_jumps([link(0.3, crouch=1)], "h2a")[0].get("crouch") == 1)
# 5. the saved data is not changed (a copy is marked: the LiDAR file keeps what was seen)
orig = [link(1.2)]
crouch_jumps(orig, "h3")
check("the input links are not changed", "crouch" not in orig[0])

if fails:
    sys.exit(f"FAIL {len(fails)}")
print("passive lidar OK")
