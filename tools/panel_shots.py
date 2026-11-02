"""Renders the BOTS panel (native/bin/panel_preview.exe, build with native/build_preview.bat) in every state
and size to logs/panel/<state>_<size>.png, for checking the design (the Master of UI/UX render matrix).

usage: python -I panel_shots.py [state,state..] [WxH,WxH..]
"""
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
EXE = os.path.join(ROOT, "native", "bin", "panel_preview.exe")
OUT = os.path.join(ROOT, "logs", "panel")
STATES = ["normal", "empty", "off", "lidar", "ce", "eight", "full", "long", "quick", "clear",
          "collector", "collectoroff"]
SIZES = ["1920x1080"]


def main():
    states = sys.argv[1].split(",") if len(sys.argv) > 1 else STATES
    sizes = sys.argv[2].split(",") if len(sys.argv) > 2 else SIZES
    os.makedirs(OUT, exist_ok=True)
    for st in states:
        for sz in sizes:
            ppm = os.path.join(OUT, f"{st}_{sz}.ppm")
            r = subprocess.run([EXE, "--state", st, "--size", sz, "--out", ppm], capture_output=True, text=True)
            if r.returncode:
                sys.exit(f"{st} {sz}: {r.stdout}{r.stderr}")
            Image.open(ppm).save(ppm[:-4] + ".png")
            os.remove(ppm)
            print(ppm[:-4] + ".png")


if __name__ == "__main__":
    main()
