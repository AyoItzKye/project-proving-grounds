"""Invasion phase 3's core waves (Director.regather / core_wave_tick). Live Boneyard B14 / B18 (traces in
logs/tmp/invasion_regress/traces, 20261105-082153 and -101023): every respawned attacker went at the core alone from
its respawn 50 u off: 34 deaths in 248 s (B18), the median 13 u from the core, 37 s a life, no pickup.

1. The blitz going, one attacker alive, just respawned at (268, 76, -4.9) (B18's respawn): it waits at the regather
   point (REGATHER_D short of the core), not straight in.
2. Three goers at the regather point: the wave goes, all of them runners at the core.
3. Alone REGATHER_S s: it goes anyway.
4. One already near the core (it came in with a wave) is never called back.
5. No blitz: the normal plan's runners wait for their wave the same way.

usage: python -I test_core_waves.py      -> "core waves OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.sim import Sim  # noqa: E402

CORE = Vec(308.91, 103.03, -9.37)
SPAWN = Vec(268.0, 76.0, -4.9)


def main():
    fails = []
    sp = Sim(mode="invasion", per_team=(4, 4), seed=1, tiers=["top"], map_name="reach_70_boneyard/variants/v86d95e85")
    d = sp.directors[1]
    ids = sorted(d.bots)

    def snap(t, where):
        ps = [PlayerState(i, 1, str(i), where.get(i, SPAWN), alive=i in where) for i in ids]
        return Snapshot(t, ps, mode="invasion", inv_phase=3, inv_attackers=1, inv_core=CORE, inv_core_carrier=None,
                        inv_delivery=sp.objmodes.inv["phases"][3][0])

    def blitz_go(t):
        d.blitz = dict(t0=t, target=CORE, rally=d.blitz_rally(SPAWN, CORE), why="the core", go=t, prongs=[])
    t = 600.0
    blitz_go(t)
    d.blitz_tick(t, snap(t, {ids[0]: SPAWN}))
    o = d.bots[ids[0]].order
    if o.role != "defender" or o.point is None or abs(dist(o.point, CORE) - getattr(D, "REGATHER_D", 22.0)) > 4.0:
        fails.append(f"1. a lone respawned attacker: {o.role} at {o.point} (want to wait {getattr(D, "REGATHER_D", 22.0)} u short of the core)")
    pt = d.blitz["regather"]
    d.blitz_tick(t + 1, snap(t + 1, {i: pt for i in ids[:3]}))
    roles = [d.bots[i].order.role for i in ids[:3]]
    if any(r != "runner" for r in roles):
        fails.append(f"2. three at the regather point: {roles} (want all runners)")
    blitz_go(t + 50)
    d.blitz_tick(t + 50, snap(t + 50, {ids[1]: SPAWN}))
    d.blitz_tick(t + 50 + getattr(D, "REGATHER_S", 8.0) + 0.5, snap(t + 50 + getattr(D, "REGATHER_S", 8.0) + 0.5, {ids[1]: SPAWN}))
    if d.bots[ids[1]].order.role != "runner":
        fails.append(f"3. alone {getattr(D, "REGATHER_S", 8.0)} s: {d.bots[ids[1]].order.role} (want it in anyway)")
    blitz_go(t + 100)
    d.blitz_tick(t + 100, snap(t + 100, {ids[2]: CORE + Vec(5.0, 0.0, 0.0)}))
    if d.bots[ids[2]].order.role != "runner":
        fails.append("4. one 5 u off the core was called back")
    d.blitz = None
    for i in ids:
        d.roles[i] = "runner"
    d.core_wave_tick(t + 200, snap(t + 200, {ids[3]: SPAWN}))
    if d.bots[ids[3]].order.role != "defender":
        fails.append(f"5. no blitz, a lone runner from its respawn: {d.bots[ids[3]].order.role} (want it to wait)")
    if fails:
        print("core waves FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("core waves OK")


if __name__ == "__main__":
    main()
