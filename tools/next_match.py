"""End the running custom game from its pause menu and start the next one with the same lobby settings (test runs on
MCC's window, any monitor; the click spots are tools/mcc_click.py's 1600x900 view of a 16:9 window). Waits for the new
match to load (the player list fills). Every menu step is screenshot-checked by the caller's logs/nav_now.jpg if it
fails. Halo 3, ODST, Reach, Halo 4, H2A share these menus.

usage: python -I next_match.py <game> [--load S]
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import mcc_nav  # noqa: E402
from mcc_click import click  # noqa: E402
from look_dump import live_for  # noqa: E402


def wait(s):
    time.sleep(s)


def main():
    game = sys.argv[1]
    load = float(sys.argv[sys.argv.index("--load") + 1]) if "--load" in sys.argv else 45.0
    mcc_nav.main_keys = None
    import subprocess
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "key", "esc"], capture_output=True)
    wait(1.5)
    # END GAME is the pause menu's second tile in multiplayer (after LEAVE), the first in Firefight (ODST)
    click(170, 216) if game == "odst" else click(366, 216)
    wait(1.5)
    click(683, 514)                  # YES
    wait(16)                         # the post-game report
    click(125, 835)                  # Back: to the lobby
    wait(4)
    start = (1045, 190) if game == "odst" else (907, 205)   # START tile (ODST has a fifth: difficulty)
    click(*start)                    # (twice: focus, open)
    wait(1.5)
    click(*start)
    wait(2)
    click(120, 717)                  # START (the label under the countdown)
    wait(1.5)
    click(120, 717)
    wait(load)
    t0 = time.time()
    while time.time() - t0 < 60:
        try:
            if live_for(game).players():
                print("match running")
                return
        except Exception:
            pass
        time.sleep(3)
    mcc_nav.shot()
    sys.exit("no match after the restart (see logs/nav_now.jpg)")


if __name__ == "__main__":
    main()
