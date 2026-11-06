"""An Invasion attack keeps its territory while it is at it (Director.invasion_slots: INV_STALL). Live Boneyard B20 R2
(trace logs/tmp/invasion_regress/traces/trace_reach_70_boneyard_20261105-114155.jsonl, 591-847 s): the defence piled
onto the territory under attack, the other always looked emptier, the Spartans' target flipped six times in 250 s,
17.9 s in a zone, phase 1 lost; B19 R2 kept one all round and took it.

1. Target picked 40 s ago, four defenders by it and none by the other, one of us 5 u from it: kept.
2. The same, but none of us within 8 u of it for INV_STALL s: the attack moves to the other.

usage: python -I test_territory_commit.py      -> "territory commit OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.sim import Sim  # noqa: E402

Z0, Z1 = Vec(251.217, 94.975, -4.0), Vec(255.81, 81.954, -3.998)


def main():
    fails = []
    sp = Sim(mode="invasion", per_team=(4, 4), seed=1, tiers=["top"], map_name="reach_70_boneyard/variants/v86d95e85")
    d = sp.directors[0]
    ours = sorted(d.bots)
    foes = [i for i in range(16) if i not in ours][:4]

    def snap(t, near):
        ps = [PlayerState(i, 0, str(i), (Z1 + Vec(5.0, 0.0, 0.0)) if near else Vec(268.0, 60.0, -5.0)) for i in ours]
        ps += [PlayerState(i, 1, str(i), Z1 + Vec(1.0 * k, 1.0, 0.0)) for k, i in enumerate(foes)]
        return Snapshot(t, ps, mode="invasion", inv_phase=1, inv_attackers=0, inv_zones=[Z0, Z1], inv_zone_r=[0.88, 0.88],
                        inv_phase_t=100.0)
    t = 300.0
    d.inv_target, d.inv_target_t = Z1, t - 40.0
    d.invasion_slots(t, snap(t, True), len(ours))
    if d.inv_target is not Z1 and (d.inv_target - Z1).flat() > 0.5:
        fails.append("1. at the territory with four defenders on it: the attack switched to the other")
    d.inv_target, d.inv_target_t = Z1, t - 40.0
    stall = getattr(D, "INV_STALL", 25.0)
    d.invasion_slots(t + stall + 1.0, snap(t + stall + 1.0, False), len(ours))
    if (d.inv_target - Z0).flat() > 0.5:
        fails.append("2. none of us near it for INV_STALL s: the attack did not move to the emptier one")
    if fails:
        print("territory commit FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("territory commit OK")


if __name__ == "__main__":
    main()
