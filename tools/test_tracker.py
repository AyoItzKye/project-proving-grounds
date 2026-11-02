"""Motion tracker: a Legendary bot picks up a moving enemy behind a wall on its tracker, and never does when the
match settings hide enemies from it (PlayerState.tracker False: Motion Tracker Off or Allies Only, read live from
each game by brain/live.py tracker).

usage: python -I test_tracker.py      -> "tracker OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Perception  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def radar_hits(tracker):
    rng = random.Random(3)
    per = Perception(make_profile("top", "rusher", rng), rng)
    me = PlayerState(1, 0, "me", Vec(0, 0, 0), Vec(), 0.0, 0.0, True, 1, 1, "battle_rifle", tracker=tracker)
    foe = PlayerState(2, 1, "foe", Vec(-10, 0, 0), Vec(0, 2.0, 0), 0.0, 0.0, True, 1, 1, "battle_rifle")
    hits = 0
    for i in range(300):
        now = i / 30
        per.update(now, me, Snapshot(now, [me, foe]), lambda *a, **k: False, [])
        b = per.beliefs.get(2)
        hits += b is not None and b.source == "radar"
    return hits


def main():
    on, off = radar_hits(True), radar_hits(False)
    if on == 0 or off != 0:
        sys.exit(f"FAIL: radar beliefs with a tracker {on} (want some), without one {off} (want 0)")
    print(f"tracker OK (with a tracker {on} radar ticks, without one {off})")


if __name__ == "__main__":
    main()
