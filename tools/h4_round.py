"""One Halo 4 look-probe round, end to end (test runs): start the next match, walk the host to the open valley spot on
Ragnarok and face it, add the spec's bots in a wide row, then a zoomed close-up of each and one sheet
(logs/looks/<label>_zoom.png). Read and write only the test bots; the host's own look is never changed.

usage: python -I h4_round.py <spec json> <label> [--game h4|h2a] [--first]   (--first: a match is already running)
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PY = [sys.executable, "-I"]


def run(*args, timeout=600):
    r = subprocess.run(PY + [os.path.join(HERE, args[0])] + list(args[1:]), capture_output=True, text=True, timeout=timeout,
                       env=dict(os.environ, MID="0.42", EYE="0.66"))
    return (r.stdout + r.stderr).strip().splitlines()


def main():
    spec, label = sys.argv[1], sys.argv[2]
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "h4"
    if "--first" not in sys.argv:
        print(run("next_match.py", game, "--load", "45")[-1:])
    spot = {"h4": "172.5,85.5"}.get(game) if "--ragnarok" in sys.argv else None
    walk = run("host_walk.py", "--game", game, *(["--near", spot] if spot else []))
    print([l for l in walk if "open ground" in l][-1:])
    if "--ragnarok" in sys.argv:
        run("mcc_nav.py", "turn", "3240")            # the valley lies behind the spot's facing
    print(run("look_probe.py", "0", "0", "--game", game, "--spec", spec, "--label", label, "--row", "6",
              "--spacing", sys.argv[sys.argv.index("--spacing") + 1] if "--spacing" in sys.argv else "1.6",
              "--dist", sys.argv[sys.argv.index("--dist") + 1] if "--dist" in sys.argv else "3.0")[-2:-1])
    for f in os.listdir(os.path.join(ROOT, "logs", "looks")):
        if f.startswith(f"{label}_") and f.endswith(".png") and not f.endswith("_zoom.png"):
            os.remove(os.path.join(ROOT, "logs", "looks", f))
    print(run("look_photo.py", label, "--game", game, "--aim", "--zoom")[-1:])
    from PIL import Image, ImageDraw
    names = [n.replace(" ", "_").replace("+", "p") for n, _ in json.load(open(spec))]
    tiles = []
    for n in names:
        p = os.path.join(ROOT, "logs", "looks", f"{label}_{n}.png")
        if not os.path.exists(p):
            print("missing", n)
            continue
        im = Image.open(p).crop((60, 0, 540, 700)).resize((330, 481))
        ImageDraw.Draw(im).rectangle((0, 0, 330, 16), fill=(0, 0, 0))
        ImageDraw.Draw(im).text((4, 2), n, fill=(255, 255, 0))
        tiles.append(im)
    out = Image.new("RGB", (330 * len(tiles), 481))
    for k, t in enumerate(tiles):
        out.paste(t, (330 * k, 0))
    out.save(os.path.join(ROOT, "logs", "looks", f"{label}_zoom.png"))
    print("sheet", len(tiles))


if __name__ == "__main__":
    main()
