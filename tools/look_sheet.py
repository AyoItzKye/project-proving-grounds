"""One contact sheet from tools/look_photo.py's close-ups: the same box cut from each photo (where the probe bot
stands, right of the crosshair), scaled up, labelled, BASE first. For comparing armor pieces by eye.

usage: python -I look_sheet.py <label> [x0 y0 x1 y1]     -> logs/looks/<label>_sheet.png
"""
import glob
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "logs", "looks")


def main():
    label = sys.argv[1]
    box = tuple(int(v) for v in sys.argv[2:6]) if len(sys.argv) >= 6 else (470, 500, 700, 970)
    files = sorted(glob.glob(os.path.join(OUT, f"{label}_*.png")), key=lambda f: (not f.endswith("_BASE.png"), f))
    files = [f for f in files if not f.endswith("_sheet.png")]
    w, h = box[2] - box[0], box[3] - box[1]
    k, cols = float(os.environ.get("SHEET_SCALE", "1.5")), 5
    cw, ch = int(w * k), int(h * k) + 24
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for n, f in enumerate(files):
        tile = Image.open(f).crop(box).resize((cw, ch - 24))
        x, y = (n % cols) * cw, (n // cols) * ch
        sheet.paste(tile, (x, y + 24))
        d.text((x + 6, y + 5), os.path.basename(f)[len(label) + 1:-4], fill=(255, 255, 0))
    dst = os.path.join(OUT, f"{label}_sheet.png")
    sheet.save(dst)
    print(dst, len(files), "photos")


if __name__ == "__main__":
    main()
