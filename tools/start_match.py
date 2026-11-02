"""From a custom game lobby (or its carnage report) start the next match with the lobby's settings, for
test runs. Clicks only (MCC menus follow the mouse). Coordinates are logs/nav_now.jpg ones. START
sometimes needs a second press (Halo 3's lobby); a second press on a running countdown cancels it, so
the countdown digits are compared on two screenshots before pressing again.

usage: python -I start_match.py [--from-report] [--map N]
  --from-report  press Back on the carnage report first
  --map N        pick the N-th built-in map in the lobby carousel first (1 = the first; UNRELIABLE past 4)
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from mcc_click import click  # noqa: E402

CAROUSEL_X = (380, 580, 780, 980)   # the four visible map tiles, y 315; the right arrow at 1083
CAROUSEL_Y = 315
DIGITS = (330, 330, 420, 400)       # the countdown digits in nav_now.jpg


def digits():
    from PIL import Image
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "mcc_nav.py"), "shot"], capture_output=True)
    return Image.open(os.path.join(ROOT, "logs", "nav_now.jpg")).convert("L").crop(DIGITS).tobytes()


def counting():
    a = digits()
    time.sleep(1.3)
    b = digits()
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) > 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-report", action="store_true")
    ap.add_argument("--map", type=int)
    o = ap.parse_args()
    if o.from_report:
        click(296, 622); time.sleep(4)
    if o.map:
        click(360, 147); time.sleep(2)                       # the map tile: opens the carousel at map 1
        for _ in range(max(0, o.map - 4)):
            click(1083, CAROUSEL_Y); time.sleep(0.7)
        click(CAROUSEL_X[min(o.map, 4) - 1], CAROUSEL_Y); time.sleep(2)
    click(880, 150); time.sleep(2)                           # START tile
    for attempt in range(3):
        click(295, 533); time.sleep(1.5)                     # START
        if counting():
            print("countdown running")
            return
    print("countdown did not start: look at logs/nav_now.jpg")


if __name__ == "__main__":
    main()
