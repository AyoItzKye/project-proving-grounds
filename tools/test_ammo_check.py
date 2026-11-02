"""Offline check of tools/ammo_check.py on a made-up trace: a fall near a fire press and a refill the reserve pays
(also one tick late) pass; a fall with no press and a rise the reserve does not pay are listed; a gap (a respawn) or
a line with the rounds unknown or a switch to another gun breaks the comparison.

usage: python -I test_ammo_check.py      -> "ammo_check OK"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ammo_check import FIRE, RELOAD, check  # noqa: E402

ROWS = [(0.0, 60, 12, FIRE), (0.1, 59, 11, 0),         # a shot: falls near the press
        (1.0, 59, 11, 0), (1.1, 58, 10, 0),            # a fall 1.1 s after the last press: listed
        (2.0, 58, 10, RELOAD), (2.1, 58, 12, 0),       # a reload the reserve pays (48 -> 46)
        (2.2, 70, 24, 0),                              # 12 more with the reserve unchanged: listed
        (5.0, 100, 50, 0),                             # a respawn gap: not compared
        (6.0, 100, 10, 0), (6.1, 110, 20, 0), (6.2, 100, 20, 0),   # the reserve pays one tick late (90 -> 80)
        (6.3, None, None, 0), (6.4, 120, 30, 0),       # rounds unknown in between: not compared
        (6.5, 300, 60, 0, "assault_rifle")]            # a switch to another gun: not compared


def main():
    lines = [dict(t=t, id=1, wpn=(gun or ["pistol"])[0], cmd=[0, 0, 0, b, 0],
                  **({} if total is None else dict(ammo=[total], mag=[mag]))) for t, total, mag, b, *gun in ROWS]
    c, odd = check(lines)
    want = {"falls": 2, "falls near a fire press": 1, "rises": 3, "rises paid from the reserve": 2,
            "rises after a brain reload press (3 s)": 2}
    got = {k: c["pistol", k] for k in want}
    if got != want or len(odd) != 2 or "no fire press" not in odd[0] or "not paid" not in odd[1]:
        raise AssertionError(f"counts {got} (want {want}); exceptions {odd}")
    print("ammo_check OK")


if __name__ == "__main__":
    main()
