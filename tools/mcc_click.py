"""Click a point given in logs/nav_now.jpg coordinates (mcc_nav.py shot: MCC's window scaled to fit
1600x900, on whichever monitor it is), then park the cursor in that window's corner (a hovered tile steals
menu focus).

usage: python -I mcc_click.py <x> <y>
"""
import ctypes as C
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from input_replay import mouse  # noqa: E402
from mcc_nav import mcc_rect  # noqa: E402

user32 = C.windll.user32


def click(x, y, hover=0.0):
    """hover: seconds the cursor rests on the spot first. Halo 3's END GAME dialog and the BOTS panel's controls
    ignore a press that arrives with no frame of the mouse over them (YES missed four times running)"""
    left, top, right, bottom = mcc_rect()
    k = max((right - left) / 1600, (bottom - top) / 900)
    X, Y = left + int(x * k), top + int(y * k)
    if hover:
        user32.SetCursorPos(X, Y)
        time.sleep(hover)
    mouse({"action": "left_down", "x": X, "y": Y})
    time.sleep(0.05)
    mouse({"action": "left_up", "x": X, "y": Y})
    time.sleep(0.3)
    user32.SetCursorPos(left + 20, top + 20)
    return X, Y


if __name__ == "__main__":
    print(click(float(sys.argv[1]), float(sys.argv[2])))
