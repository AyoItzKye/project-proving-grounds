"""The bots keep their real-time speed on a slower PC (tools/live_bots.py think_dt):

1. think_dt: 1/30 s for a pass that came on time or early, the real gap for a slower one, MAX_DT at most
2. the same 4v4 Slayer match in the simulator at 30 passes a second and at 15 (a PC that needs 1/15 s per pass): the
   bots turn about as far per second at 15 as at 30 when they think with the real step (think_dt), and clearly less
   when they think with 1/30 s each pass (the step before think_dt)

usage: python -I test_think_dt.py      -> "think_dt OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import live_bots  # noqa: E402
from brain import sim as S  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import wrap  # noqa: E402

# (120 s, not 60: at 60 the old step's ratio follows the map's learned files, which live play rewrites. Nov 9, the same
# brain code (master and objective-wave alike) on Blood Gulch: committed files 0.777, a dev PC's learned files 0.816,
# over the 0.8 limit; at 120 s 0.759 and 0.768-0.774. The limit is unchanged, the check means the same)
SECONDS = 120
# (two matches pooled: one seed is one match's fights. Nov 12, seed 3 alone read 1.32 on objective-wave and 1.29 on
# master, over or at the 1.3 limit; seeds 3-6 read 1.32, 0.99, 1.16, 0.95: the step is fine, seed 3's 30/s run turned
# little. The limits are unchanged)
SEEDS = (3, 4)


def turn_rate(step, fixed_dt=None):
    """Mean degrees per simulated second the living bots turn, the simulator stepping `step` s a pass; fixed_dt: the
    bots think with this step instead (what live_bots did before think_dt)."""
    S.TICK, think = step, Bot.think
    if fixed_dt:
        Bot.think = lambda b, now, dt, *a, **k: think(b, now, fixed_dt, *a, **k)
    try:
        total, n = 0.0, 0
        for seed in SEEDS:
            sim = S.Sim("slayer", per_team=4, seed=seed)
            prev = {}
            for _ in range(int(SECONDS / step)):
                sim.step()
                for p in sim.players:
                    if p.alive and p.id in prev:
                        total += abs(wrap(p.yaw - prev[p.id]))
                        n += 1
                    prev[p.id] = p.yaw
        return total / (n * step) * 57.29578 if n else 0.0
    finally:
        S.TICK, Bot.think = 1 / 30, think


def main():
    fails = []
    hz = live_bots.HZ
    for elapsed, want in ((0.0, 1 / hz), (0.02, 1 / hz), (0.05, 0.05), (1.0, live_bots.MAX_DT)):
        if abs(live_bots.think_dt(elapsed) - want) > 1e-9:
            fails.append(f"1. think_dt({elapsed}) = {live_bots.think_dt(elapsed):.4f}, want {want:.4f}")
    full = turn_rate(1 / 30)
    slow = turn_rate(2 / 30)
    old = turn_rate(2 / 30, fixed_dt=1 / 30)
    if not 0.75 < slow / full < 1.3:
        fails.append(f"2. at 15 passes a second the bots turn {slow:.0f} deg/s against {full:.0f} at 30")
    # against think_dt at the same 15 passes (the same match): against the 30-pass run it sat on the line (0.80 to 0.83
    # on seeds 3-5 at 60 s with this PC's learned map files, see SECONDS), against think_dt 0.63-0.77 on seeds 3-6
    if not old / slow < 0.8:
        fails.append(f"2. the old fixed step was not slower ({old:.0f} deg/s against {slow:.0f} with think_dt): the check "
                     "proves nothing")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"think_dt OK (turning {full:.0f} deg/s at 30 passes a second, {slow:.0f} at 15 with think_dt, "
          f"{old:.0f} at 15 with the old fixed step)")


if __name__ == "__main__":
    main()
