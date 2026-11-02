"""Each bot's own emblem, an MCC emblem (brain/emblems.py; the player: "each bot profile has its own randomized
emblem and background (everything, all the logos, backgrounds and colors and randomized disabled parts of logos)";
"ensure these bot profiles clan tags, and emblems appear in each respective game and scoreboard"):
1. the roll: fixed per seed, varied across seeds, only ids in MCC's catalog (maps/_looks/mcc_emblems.json: MCC's
   renderer refuses an unknown one), the second part off (MCC's transparent colour 31) about a quarter of the time,
   the primary colour readable on the background's
2. with the art extracted (tools/emblems.py extract): the player's MCC emblem (Wolf on Racing Stripes, colours 1, 2,
   22: his carnage report rows) composes to 128 x 128, its second part gone when off
3. every profile bot gets a different emblem, the one botctl sends (looks.emblem_of)

usage: python -I test_emblems.py      -> "emblems OK"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import emblems, looks  # noqa: E402


def main():
    fails = []
    emblems.selftest()
    fgs, bgs, cols = emblems.catalog()
    if len(fgs) < 200 or len(bgs) < 100 or len(cols) != 30 or emblems.OFF in cols:
        fails.append(f"catalog: {len(fgs)} foregrounds, {len(bgs)} backgrounds, {len(cols)} colours")
    wolf = dict(fg=29, bg=555, primary=1, secondary=2, background=22)
    img = emblems.compose(wolf)
    if img is not None:
        import numpy as np
        a = np.asarray(img)
        sec = np.array(cols[2])
        on = int((np.abs(a[..., :3].astype(int) - sec).sum(2) < 12).sum())
        off = np.asarray(emblems.compose(dict(wolf, secondary=emblems.OFF)))
        on2 = int((np.abs(off[..., :3].astype(int) - sec).sum(2) < 12).sum())
        if img.size != (128, 128) or a[..., 3].max() < 200 or not on2 < on // 4:
            fails.append(f"composed: size {img.size}, alpha max {a[..., 3].max()}, secondary px {on} -> {on2} off")
    names = [n for n, _ in looks.profiles(looks.PROFILES)]
    rolls = {emblems.ids(emblems.roll(looks.seed_of(n, looks.PROFILES))) for n in names}
    if len(rolls) != len(names):
        fails.append(f"{len(names)} bots, {len(rolls)} different emblems")
    if any(looks.emblem_of(n) != emblems.ids(emblems.roll(looks.seed_of(n, looks.PROFILES))) for n in names):
        fails.append("looks.emblem_of is not the bot's roll")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("emblems OK")


if __name__ == "__main__":
    main()
