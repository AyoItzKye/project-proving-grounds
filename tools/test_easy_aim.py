"""Easy's aim: an Easy bot goes for the head 20% of the time and zooms only with a sniper-type weapon; a Legendary bot
zooms rifles at range as before.

usage: python -I test_easy_aim.py      -> "easy aim OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Vec, PlayerState  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def main():
    fails = []
    m = get_map("bloodgulch")
    rng = random.Random(7)
    easy = Bot(1, 0, make_profile("novice", "rusher", rng), m, rng=rng)
    top = Bot(2, 0, make_profile("top", "rusher", rng), m, rng=rng)
    want = [(easy, "battle_rifle", 15.0, 0), (easy, "dmr", 30.0, 0), (easy, "sniper", 10.0, 1), (easy, "sniper", 30.0, 2),
            (easy, "beam_rifle", 12.0, 1), (top, "battle_rifle", 15.0, 1), (top, "sniper", 30.0, 2)]
    for b, w, d, z in want:
        got = b.zoom_level(100.0, w, d, True)
        if got != z:
            fails.append(f"{b.p.tier} {w} at {d:.0f} u: zoom {got}, want {z}")
    # head shots: one decision per target, weapon and shield state; a bare target (SWAT) for many targets
    me = PlayerState(1, 0, "e", Vec(0, 0, 0), Vec(), 0.0, 0.0, True, 1, 1, "battle_rifle")
    heads = 0
    for tid in range(4000):
        target = PlayerState(100 + tid, 1, "t", Vec(10, 0, 0), Vec(), 0.0, 0.0, True, 0.0, 1, "battle_rifle")
        heads += easy.aim_head(1.0, me, target, 100 + tid)
    share = heads / 4000
    if not 0.17 <= share <= 0.23:
        fails.append(f"Easy head-shot share {share:.2f}, want about 0.20")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"easy aim OK (Easy goes for the head {share:.0%})")


if __name__ == "__main__":
    main()
