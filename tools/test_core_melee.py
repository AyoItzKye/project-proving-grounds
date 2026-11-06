"""The Invasion core carrier (live Boneyard B12, logs/tmp/invasion_regress/traces/trace_reach_70_boneyard_20261105-065313):

1. Carrying the core with an enemy at arm's length: no melee press (Reach drops the core on one: B12 527.13 s and
   732.72 s, the weapon read back to a gun 0.15 s later; Spire 18 of 18). Breakpoint's bomb and a CTF flag still swing.
2. The core just dropped (weapon read a gun again, the carrier read lagging): Use on it at once when it lies at our feet
   (B12: the carrier fought 0.3 u off it 1.5 s and died, it lay loose 120 s).
3. The simulator drops the core on a carrier's melee (brain/sim.py Sim.melee).

usage: python -I test_core_melee.py      -> "core_melee OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

DELIVER = Vec(262.841, 138.845, -8.2)


def carrier_melees(mode="invasion", bomb=False, ticks=30):
    m = get_map("reach_70_boneyard")
    b = Bot(5, 0, make_profile("top", "objector", random.Random(5)), m, random.Random(5))
    b.order = Order("runner", DELIVER)
    me_p, foe_p = Vec(300.7, 101.8, -10.0), Vec(300.0, 101.3, -10.0)      # (B12 527.13 s: bot 5 and Elite 11)
    pressed = 0
    for k in range(ticks):
        t = 527.0 + k / 30
        me = PlayerState(5, 0, "c", me_p, has_flag=True, weapon="unknown" if mode == "invasion" else "flag", yaw=3.13)
        foe = PlayerState(11, 1, "e", foe_p)
        kw = dict(mode="invasion", inv_phase=3, inv_attackers=0, inv_core=me_p, inv_core_carrier=5,
                  inv_delivery=DELIVER) if mode == "invasion" else dict(mode="ctf")
        sn = Snapshot(t, [me, foe], **kw)
        sn.inv_bomb = bomb
        a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
        pressed += bool(a.melee)
    return pressed


def retake_after_drop():
    """Frames of B12 527.13-527.6: carrying, then the weapon read turns to a gun with the carrier read still on us for
    0.5 s, then the core loose 0.2 u off. Use within 0.3 s of the carrier read clearing?"""
    m = get_map("reach_70_boneyard")
    b = Bot(5, 0, make_profile("top", "objector", random.Random(5)), m, random.Random(5))
    b.order = Order("runner", DELIVER)
    here, core = Vec(300.1, 101.7, -10.0), Vec(299.96, 101.75, -9.4)
    first_use = None
    for k in range(60):
        t = 527.0 + k / 30
        dropped, cleared = t >= 527.28, t >= 527.4 + 0.4
        me = PlayerState(5, 0, "c", here, has_flag=not cleared, weapon="plasma_repeater" if dropped else "unknown", yaw=3.13)
        a = b.think(t, 1 / 30, Snapshot(t, [me], mode="invasion", inv_phase=3, inv_attackers=0,
                                        inv_core=here if not cleared else core,
                                        inv_core_carrier=5 if not cleared else None, inv_delivery=DELIVER),
                    lambda p, q: True, lambda p, q, **kw: q, [])
        if cleared and a.action and first_use is None:
            first_use = round(t - 527.8, 2)
    return first_use


def sim_drop():
    from brain.sim import Sim
    sim = Sim("invasion", per_team=2, seed=1, map_name="reach_70_boneyard")
    om = sim.objmodes
    p = sim.players[0]
    om.core["carrier"], p.has_flag = p.id, True
    sim.melee(p)
    return om.core["carrier"] is None and not p.has_flag


def main():
    fails = []
    n = carrier_melees()
    if n:
        fails.append(f"core carrier, Elite at arm's length: {n} melee presses in 1 s (want 0: Reach drops the core)")
    if not carrier_melees(bomb=True):
        fails.append("Breakpoint's bomb carrier: no melee (it does not drop the bomb)")
    if not carrier_melees(mode="ctf"):
        fails.append("CTF flag carrier: no melee (the flag swing)")
    u = retake_after_drop()
    if u is None or u > 0.3:
        fails.append(f"core dropped at our feet: Use {u} s after the carrier read cleared (want within 0.3 s)")
    if not sim_drop():
        fails.append("simulator: the carrier's melee did not drop the core")
    if fails:
        print("core_melee FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("core_melee OK")


if __name__ == "__main__":
    main()
