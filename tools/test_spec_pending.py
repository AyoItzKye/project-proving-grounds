"""SPEC CHANGES AWAITING REVIEW (Code Master TS-18: a changed test is a spec change, in its own commit with its
reason, reviewed). Two expectations changed in ffbfb4d together with the behaviour, not in their own commit; they live
here, apart from the suites they came from, until a review answers keep or revert.

1. An SMG at 8 units (Medium band), from test_brain_tactics 8.
   Before ffbfb4d: taps, the trigger held at most 2 ticks ("at Medium it still taps").
   Since: 3-5 round bursts, held at most 13 ticks with gaps, trigger down 1-75%.
   Reason: guide 03 (docs/bot-brain/03-weapon-deep-dives.md): "Burst fire at the top of Short band (30 to 40 ft) in
   H3 and Reach: three to five rounds at a time keeps the spread tight."
2. A shotgun at 3 units (30 ft), from test_close_combat 5.
   Before ffbfb4d: it fires.
   Since: it holds fire (it closes in); at 2 units it fires.
   Reason: guide 03: "hold fire until the enemy is within one-shot range; a two-shot at 20 ft gives the enemy time to
   melee or run" (one-shot about 10 ft, two-shot about 20 ft).

Revert means: the old expectation back here, and the old behaviour in brain/bot.py (bursts past Short band: the
`elif w in AUTO:` branch in Bot.fight; the shotgun's reach: WEAPON_RANGE["shotgun"] and the `+ 0.7` gate).

usage: python -I test_spec_pending.py -> "spec pending OK (2 expectations await the player)"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import test_brain_tactics as tactics  # noqa: E402
import test_close_combat as close  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def trigger(weapon, gap):
    """test_brain_tactics 8's harness: the longest run of trigger-down ticks and the share down, once on target."""
    bot = Bot(10, 0, make_profile("strong", "rusher", random.Random(10)), tactics.MAP, random.Random(10))
    foe = PlayerState(2, 1, "human", tactics.A + Vec(-gap, 0.0, 0.0), alive=True)
    t, yaw, pitch, fires = 0.0, 3.14159, 0.0, []
    while t < 4.0:
        me = PlayerState(10, 0, "bot", tactics.A, yaw=yaw, pitch=pitch, alive=True, weapon=weapon)
        a = bot.think(t, 1 / 30, Snapshot(t, [me, foe]), tactics.T.los, lambda p, q, **k: q, [])
        yaw, pitch = a.yaw, a.pitch
        fires.append((t, bool(a.fire)))
        t += 1 / 30
    fires = fires[60:]                                 # spotted, turned and on target by 2 s
    runs, n = [], 0
    for _, f in fires:
        n = n + 1 if f else 0
        runs.append(n)
    return max(runs), sum(f for _, f in fires) / len(fires)


def main():
    fails = []
    # 1. (pending) an SMG at 8 units: 3-5 round bursts, not taps
    longest, down = trigger("smg", 8.0)
    if longest > 13 or down > 0.75 or down == 0.0:
        fails.append(f"an SMG at 8 units: longest hold {longest} ticks, trigger down {down:.0%} (Medium band bursts)")
    # 2. (pending) a shotgun at 3 units holds its fire, at 2 it fires
    for d, want in ((3.0, False), (2.0, True)):
        acts = close.run(close.bot(weapon="shotgun"), 2.5,
                         [PlayerState(2, 1, "human", close.A + Vec(-d, 0, 0), alive=True, yaw=0.0)])
        if any(a.fire for t, a, _ in acts if t > 0.6) != want:
            fails.append(f"shotgun at {d} units: fired = {not want}")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("spec pending OK (2 expectations await review)")


if __name__ == "__main__":
    main()
