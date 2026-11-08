"""The profile view shows a Halo 3 backpack when one is picked. From the front a backpack hardly shows, so picking one
turns the bot round once its look comes in (native/bots_panel.cpp g_turn_after). Checked on the offline panel with real
clicks (native/bin/panel_preview.exe --click: the Backpack box, then Seafoam Trident in its list, at 1920x1080):

1. after the pick the 3D view is the one of the bot set to Seafoam Trident and turned round (the same pixels)
2. and not the front it showed before
3. picking its own roll again (nothing changes) leaves it facing the front
Keyboard (Master of UI/UX 11.11; the panel's keyboard navigation, overlay.cpp):
4. Tab x23 to the Backpack box, Space, Down x3, Enter: Law's End (13) picked, the view as the bot set to it, turned (one stop per game in the list: 7 with ODST)
5. Esc in the open list closes the list, not the editor (the editor as before the list opened)
6. the arrows on the 3D view (Tab x11) turn it, and nothing else moves (the focus stays on it)
A save that fails (--readonly: the profiles file read-only, Code Master DD-01 8):
7. the pick shows the save error (its red line under the pickers) and the bot stays facing the front (no look made,
   no turn to the old one); the file is writable again afterwards
The focus colour (Master of Game Design 5.6.6, one meaning a colour):
8. the frame on the focused Backpack box is near-white, not gold (gold already says changed / current)

usage: python -I test_backpack_view.py      -> "backpack view OK"
"""
import os
import stat
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "native", "bin")
EXE = os.path.join(BIN, "panel_preview.exe")
TMP = os.path.join(HERE, "..", "logs", "tmp")
VIEW = (672, 336, 1034, 768)                 # the 3D view at 1920x1080
EDITOR = (380, 180, 1540, 900)               # the editor
FULL = (0, 0, 1920, 1080)
CLICKS = "1386,740;1370,601"                 # the Backpack box; Seafoam Trident (10) in the open list
SAME = "1386,740;1405,370"                   # the box; Evalach's Lament (15), bot 0's roll


def shot(name, *args, view=VIEW):
    out = os.path.join(TMP, f"bpv_{name}.ppm")
    r = subprocess.run([EXE, "--size", "1920x1080", "--out", out] + list(args), capture_output=True, text=True, timeout=120)
    if r.returncode:
        sys.exit(f"FAIL\n{name}: {r.stdout}{r.stderr}")
    im = np.asarray(Image.open(out).convert("RGB").crop(view), float)
    os.remove(out)
    return im


def main():
    if not os.path.exists(EXE) or not os.path.exists(os.path.join(BIN, "models", "h3_spartan.mdl")):
        print("backpack view: skipped (needs native/build_preview.bat and tools/make_models.py)")
        return
    os.makedirs(TMP, exist_ok=True)
    front = shot("front", "--state", "edit2mo")
    picked = shot("picked", "--state", "edit2mo", "--click", CLICKS)
    back = shot("back", "--state", "edit2mor", "--set", "h3.backpack=10")
    same = shot("same", "--state", "edit2mo", "--click", SAME)
    keyed = shot("keyed", "--state", "edit2mo", "--keys", "tab*23,space,down*3,enter")
    back13 = shot("back13", "--state", "edit2mor", "--set", "h3.backpack=13")
    on_box = shot("onbox", "--state", "edit2mo", "--keys", "tab*23", view=EDITOR)
    esc = shot("esc", "--state", "edit2mo", "--keys", "tab*23,space,esc", view=EDITOR)
    on_view = shot("onview", "--state", "edit2mo", "--keys", "tab*11", view=FULL)
    turned = shot("turned", "--state", "edit2mo", "--keys", "tab*11,left*20", view=FULL)
    prof = os.path.join(os.environ.get("TEMP", ""), "hb_profiles_preview.ini")
    try:
        failed = shot("failed", "--state", "edit2mo", "--click", CLICKS, "--readonly", view=FULL)
    finally:
        if os.path.exists(prof):
            os.chmod(prof, stat.S_IWRITE | stat.S_IREAD)  # (the preview clears it too)
    writable = os.access(prof, os.W_OK)
    fails = []
    d_back, d_front = np.abs(picked - back).mean(), np.abs(picked - front).mean()
    if d_back > 1.0:
        fails.append(f"after the pick the view is {d_back:.1f} off the bot turned round in Seafoam Trident (want under 1)")
    if d_front < 10.0:
        fails.append(f"after the pick the view is {d_front:.1f} off the front it showed (want it turned round: over 10)")
    if np.abs(same - front).mean() > 1.0:
        fails.append(f"picking its own roll again moved the view {np.abs(same - front).mean():.1f} (want it left facing the front)")
    d_keys, d_esc = np.abs(keyed - back13).mean(), np.abs(esc - on_box).mean()
    if d_keys > 1.0:
        fails.append(f"by keys (Tab x23, Space, Down x3, Enter): the view is {d_keys:.1f} off the bot turned round in Law's End "
                     f"(want under 1: the Backpack box reached and its pack picked)")
    if d_esc > 1.0:
        fails.append(f"Esc in the open Backpack list: the editor is {d_esc:.1f} off how it was (want under 1: the list "
                     f"closed, the editor open)")
    inside = np.zeros(turned.shape[:2], bool)
    inside[VIEW[1]:VIEW[3], VIEW[0]:VIEW[2]] = True
    d_view, d_rest = np.abs(turned - on_view)[inside].mean(), np.abs(turned - on_view)[~inside].mean()
    if d_view < 10.0 or d_rest > 0.5:
        fails.append(f"the arrows on the 3D view: it changed {d_view:.1f}, the rest {d_rest:.2f} (want it turned, over 10, "
                     f"and nothing else, under 0.5)")
    edge = on_box[725 - EDITOR[1]:755 - EDITOR[1], 1274 - EDITOR[0]:1281 - EDITOR[0]]   # the frame left of the box
    white = int(((edge > 200).all(2)).sum())
    gold = int((np.abs(edge - (255, 201, 77)).sum(2) < 60).sum())
    if white < 20 or gold:
        fails.append(f"the Backpack box's focus frame: {white} near-white px, {gold} gold px (want the focus colour, no gold)")
    red = (np.abs(failed[850:900, 600:1540] - (255, 107, 94)).sum(2) < 40).sum()     # the error line's DANGER text
    d_failed = np.abs(failed[VIEW[1]:VIEW[3], VIEW[0]:VIEW[2]] - front).mean()
    if red < 200 or d_failed > 1.0 or not writable:
        fails.append(f"a save that fails: {red} px of the error's red, the view {d_failed:.1f} off the front, the file "
                     f"writable after: {writable} (want the error shown, under 1: no turn, writable)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"backpack view OK (picked vs turned round {d_back:.1f}, vs the front {d_front:.1f}; by keys {d_keys:.1f}, "
          f"Esc in the list {d_esc:.1f}, the arrows turn the view {d_view:.1f}; a save that fails: error shown ({red} px), "
          f"no turn {d_failed:.1f})")


if __name__ == "__main__":
    main()
