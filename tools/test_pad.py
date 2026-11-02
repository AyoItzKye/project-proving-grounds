"""The BOTS panel with a controller (Master of UI/UX: every menu by D-pad or stick and confirm / back, shoulders switch
tabs, back backs out one level, directions follow the layout). On the offline panel (native/bin/panel_preview.exe --keys
pad_...: the pad's buttons as ImGui gets them from XInput), the bot editor at 1920x1080:

1. D-pad Down x2, Right x2, Down x3 reach the Backpack box (its focus frame)
2. then A, Down x3, A: Law's End picked, the bot turned round in it (the same pixels as the bot set to it)
3. B in the open list closes the list, not the editor; B again closes the editor
4. Down from Halo 2 goes to Halo 3, the chosen game below it (not the picker in line with it)
5. RB in the editor: the next game (its pickers as when it is chosen); LB on the panel's Settings: the Bots tab (as a
   click on it)
6. the pad's A and B make the press and back sounds

usage: python -I test_pad.py      -> "pad OK"
"""
import collections
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "native", "bin")
EXE = os.path.join(BIN, "panel_preview.exe")
OUT = os.path.join(HERE, "..", "logs", "tmp", "pad_test.ppm")
VIEW = (672, 336, 1034, 768)
EDITOR = (380, 180, 1540, 900)
ROUTE = "pad_down*2,pad_right*2,pad_down*3"
FOCUS = (226, 236, 245)


def shot(state, keys=None, *more):
    args = [EXE, "--state", state, "--size", "1920x1080", "--out", OUT] + (["--keys", keys] if keys else []) + list(more)
    r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if r.returncode:
        sys.exit(f"FAIL\npanel_preview {keys}: {r.stdout[-300:]}{r.stderr[-300:]}")
    sounds = collections.Counter(ln.split()[1] for ln in r.stdout.splitlines() if ln.startswith("sound "))
    return np.asarray(Image.open(OUT).convert("RGB"), float), sounds


crop = lambda a, box: a[box[1]:box[3], box[0]:box[2]]
mean = lambda a, b: float(np.abs(a - b).mean())


def main():
    if not os.path.exists(EXE):
        print("pad: skipped (needs native/build_preview.bat)")
        return
    fails = []
    a, _ = shot("edit2mo", ROUTE)
    frame = int((np.abs(a[725:755, 1274:1281] - FOCUS).sum(2) < 30).sum())
    if frame < 20:
        fails.append(f"{ROUTE}: {frame} px of a focus frame on the Backpack box (want it there)")
    picked, snd = shot("edit2mo", ROUTE + ",pad_a,pad_down*3,pad_a")
    ref, _ = shot("edit2mor", None, "--set", "h3.backpack=13")
    if mean(crop(picked, VIEW), crop(ref, VIEW)) > 1.0:
        fails.append(f"A, Down x3, A: the view {mean(crop(picked, VIEW), crop(ref, VIEW)):.1f} off the bot turned round in "
                     f"Law's End (want under 1)")
    if snd["select"] < 2:
        fails.append(f"A, A: sounds {dict(snd)} (want two presses)")
    shut, snd = shot("edit2mo", ROUTE + ",pad_a,pad_b")
    if mean(crop(shut, EDITOR), crop(a, EDITOR)) > 1.0 or snd["back"] != 1:
        fails.append(f"B in the list: the editor {mean(crop(shut, EDITOR), crop(a, EDITOR)):.1f} off how it was, sounds "
                     f"{dict(snd)} (want the list shut, the editor as before, one back)")
    gone, _ = shot("edit2mo", ROUTE + ",pad_a,pad_b,pad_b")
    if mean(crop(gone, EDITOR), crop(a, EDITOR)) < 10.0:
        fails.append("B twice: the editor still open (want it closed)")
    h3, _ = shot("edit2mo", "tab*5,pad_down")                 # (Tab x5: Halo 2)
    ring = int((np.abs(h3[490:500, 395:660] - FOCUS).sum(2) < 30).sum())   # the ring's top edge, round Halo 3
    if ring < 100:
        fails.append(f"Down from Halo 2: {ring} px of a ring round Halo 3 (want the focus on it, the game below)")
    rb, _ = shot("edit2mo", "pad_rb")
    reach, _ = shot("edit3m")                                 # (its preferred species, as a game switch shows it)
    pick = (1040, 330, 1520, 830)                              # the pickers' column
    if mean(crop(rb, pick), crop(reach, pick)) > 2.0:
        fails.append(f"RB in the editor: the pickers {mean(crop(rb, pick), crop(reach, pick)):.1f} off Reach's (want the next game)")
    lb, _ = shot("mod", "pad_lb")
    click, _ = shot("mod", None, "--click", "323,217")
    if mean(lb, click) > 2.0:
        fails.append(f"LB on Settings: {mean(lb, click):.1f} off a click on the Bots tab (want the Bots tab)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("pad OK (the Backpack box by the D-pad, picked with A, B backs out one level, Down follows the game list, "
          "the shoulders switch the game and the tabs)")


if __name__ == "__main__":
    main()
