"""An Invasion attack piles onto its territory from the phase's start, whatever the round (Director.invasion_slots,
PUSH_AFTER). Live Boneyard B17-B25: the round 2 attack (the Spartans) had every attacker posted on one territory from
its first second (the side's director kept its pile-on, inv_push, from round 1) and took phase 1 in 7 of 9 rounds; the
round 1 attack (the Elites) split for its first 60 s (two in, one to the other territory, escorts and overlooks) and
took it in 2 of 9. Movement and speed were the same for both sides (sidecmp.py, speeds.py).

1. Phase 1, 5 s in, a fresh director, nobody of ours inside: every slot a post on the one territory.

usage: python -I test_round_plan.py      -> "round plan OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.sim import Sim  # noqa: E402

Z0, Z1 = Vec(251.217, 94.975, -4.0), Vec(255.81, 81.954, -3.998)


def main():
    sp = Sim(mode="invasion", per_team=(6, 6), seed=1, tiers=["top"], map_name="reach_70_boneyard/variants/v86d95e85")
    d = sp.directors[1]
    ours = sorted(d.bots)
    ps = [PlayerState(i, 1, str(i), Vec(224.0, 66.0, -7.0)) for i in ours]
    sn = Snapshot(10.0, ps, mode="invasion", inv_phase=1, inv_attackers=1, inv_zones=[Z0, Z1], inv_zone_r=[0.88, 0.88],
                  inv_phase_t=5.0)
    slots = d.invasion_slots(10.0, sn, len(ours))
    roles = [r for r, p, _ in slots]
    tgt = d.inv_target
    off = [p for r, p, _ in slots if p is not None and (p - tgt).flat() > 3.0]
    if any(r != "defender" for r in roles) or off:
        print(f"round plan FAIL:\n  5 s into phase 1: roles {roles}, {len(off)} slots off the target territory "
              f"(want every attacker posted on it)")
        sys.exit(1)
    print("round plan OK")


if __name__ == "__main__":
    main()
