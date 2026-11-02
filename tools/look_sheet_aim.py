"""After tools/look_probe.py: turn the player's view onto each probe bot in turn (relative mouse moves, as mcc_nav.py
turn) and save one labelled close crop per bot as a contact sheet, so a crowded lineup reads bot by bot (Halo 4
Forge Island: 13 bots in two rows overlapped on one screenshot).

usage: python -I look_sheet_aim.py <game> <label> [--names A,B,...]   -> logs/looks/<game>_<label>_sheet.png
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import mcc_nav  # noqa: E402
from input_replay import INPUT, INPUT_MOUSE, MI, U, send  # noqa: E402
from look_dump import live_for  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def yaw_of(live):
    a = live.players()[0]["aim"]
    return math.atan2(a[1], a[0])


def nudge(dx):
    for _ in range(10):
        send(INPUT(INPUT_MOUSE, U(mi=MI(int(dx / 10), 0, 0, 0x0001, 0, 0))))   # MOUSEEVENTF_MOVE
        time.sleep(0.02)
    time.sleep(0.4)


def turn_to(live, want, per_rad):
    for _ in range(4):                               # a few corrections: the game's turn rate is not exactly linear
        err = math.atan2(math.sin(yaw_of(live) - want), math.cos(yaw_of(live) - want))
        if abs(err) < math.radians(0.6):
            return
        nudge(err * per_rad)                         # +x turns right (yaw goes down)


def main():
    game, label = sys.argv[1], sys.argv[2]
    live = live_for(game)
    if not mcc_nav.focus(mcc_nav.mcc_window()):
        sys.exit("MCC window not focused")
    y0 = yaw_of(live)
    nudge(200)
    per_rad = 200 / max(1e-3, abs(math.atan2(math.sin(y0 - yaw_of(live)), math.cos(y0 - yaw_of(live)))))
    ps = live.players()
    me = ps[0]
    names = sys.argv[sys.argv.index("--names") + 1].split(",") if "--names" in sys.argv else None
    bots = [p for p in ps[1:] if p.get("pos") and (names is None or p["name"] in names)]
    tiles = []
    for p in bots:
        dx, dy = p["pos"][0] - me["pos"][0], p["pos"][1] - me["pos"][1]
        turn_to(live, math.atan2(dy, dx), per_rad)
        time.sleep(0.5)
        img = mcc_nav.grab()
        w, h = img.size
        d = math.hypot(dx, dy)
        half = max(60, int(h * 0.42 / max(d, 1.0)))    # about a body's height on screen at that distance
        tile = img.crop((w // 2 - half // 2, h // 2 - int(half * 0.55), w // 2 + half // 2, h // 2 + int(half * 0.75)))
        tile = tile.resize((240, int(240 * tile.size[1] / tile.size[0])))
        ImageDraw.Draw(tile).text((6, 4), p["name"], fill=(255, 255, 255))
        tiles.append(tile)
    turn_to(live, y0, per_rad)
    th = max(t.size[1] for t in tiles)
    cols = 7
    sheet = Image.new("RGB", (240 * cols, th * ((len(tiles) + cols - 1) // cols)), (20, 20, 20))
    for k, t in enumerate(tiles):
        sheet.paste(t, (240 * (k % cols), th * (k // cols)))
    out = os.path.join(ROOT, "logs", "looks", f"{game}_{label}_sheet.png")
    sheet.save(out)
    print(out, len(tiles), "bots")


if __name__ == "__main__":
    main()
