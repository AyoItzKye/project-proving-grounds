"""Pick a game type in Halo: Reach's custom game lobby by clicks (measured on logs/nav_now.jpg): the game type tile,
a category in its carousel, a variant in that category, then Accept options. Screenshot at the end. Reach's
carousel (1 of 11): Slayer, Capture the Flag, Oddball, King of the Hill...; CTF's variants: Capture the Flag, One
Flag CTF, Multi Flag CTF... Positions past the fourth go through the carousel's right arrow (as start_match.py's
maps: check the screenshot).

usage: python -I set_gametype.py <category 1..> <variant 1..>     e.g. 2 1 = Capture the Flag
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mcc_click import click  # noqa: E402

CATEGORY_X, CATEGORY_Y, CATEGORY_NEXT = (380, 578, 777, 975), 315, 1083
VARIANT_X, VARIANT_Y, VARIANT_NEXT = (565, 732, 900), 325, 990    # (the big tile left of them is the category)
ACCEPT = (562, 489)


def pick(xs, y, nxt, n):
    for _ in range(max(0, n - len(xs))):
        click(nxt, y)
        time.sleep(0.7)
    click(xs[min(n, len(xs)) - 1], y)
    time.sleep(2.5)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    cat, var = int(sys.argv[1]), int(sys.argv[2])
    click(560, 147)                 # the game type tile
    time.sleep(2.5)
    pick(CATEGORY_X, CATEGORY_Y, CATEGORY_NEXT, cat)
    pick(VARIANT_X, VARIANT_Y, VARIANT_NEXT, var)
    click(*ACCEPT)                  # the variant opens its options: accept them
    time.sleep(2.0)
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "shot"], capture_output=True)
    print("look at logs/nav_now.jpg")


if __name__ == "__main__":
    main()
