"""The Firefight lobby's title probe (native/overlay.cpp probe_lobby, the box in native/ui_layout.h mcc_ff_title_probe)
on two real frames of MCC's window (tools/fixtures: the top band, x 0-960 y 0-135 of the fitted 1920x1080 page, captured
live Nov 6 2026, installed 0.2.2-s180): the Reach Custom Firefight lobby counts as a lobby (the BOTS tile shows), its
post-game report does not (the tile stayed over the report's 6th stat tile till s179). The box and the threshold are
read from the C++ source, so this checks what ships.

usage: python -I tools/test_ff_title_probe.py      -> "ff title probe OK"
"""
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
NATIVE = os.path.join(HERE, "..", "native")


def main():
    layout = open(os.path.join(NATIVE, "ui_layout.h"), encoding="utf-8").read()
    overlay = open(os.path.join(NATIVE, "overlay.cpp"), encoding="utf-8").read()
    box = re.search(r"mcc_ff_title_probe\(float W, float H\) \{ return ui_at\(mcc_content\(W, H\), "
                    r"(\d+), (\d+), (\d+), (\d+)\); \}", layout)
    rule = re.search(r"ok = title \* 100 > tw \* th \* (\d+);", overlay)
    white = re.search(r"return r > (\d+) && g > \1 && b > \1;", overlay)
    if not (box and rule and white):
        sys.exit("ff title probe FAIL: the box, the threshold or the white test is no longer in the source as read here")
    x0, y0, x1, y1 = (int(v) for v in box.groups())
    pct, level = int(rule.group(1)), int(white.group(1))
    fails = []
    for name, want in (("ff_lobby_reach_title.png", True), ("ff_postgame_title.png", False)):
        img = Image.open(os.path.join(HERE, "fixtures", name)).convert("RGB")      # (page units = pixels here)
        lit = int((np.asarray(img.crop((x0, y0, x1, y1))) > level).all(axis=2).sum())
        lobby = lit * 100 > (x1 - x0) * (y1 - y0) * pct
        if lobby != want:
            fails.append(f"{name}: {lit} white of {(x1 - x0) * (y1 - y0)} -> {'lobby' if lobby else 'not a lobby'}"
                         f" (want {'lobby' if want else 'not a lobby'})")
    if fails:
        print("ff title probe FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("ff title probe OK")


if __name__ == "__main__":
    main()
