"""Invasion attackers keep to the objective and come at it more than one way. On the simulator's Spire (team 1 attacks):

1. power weapon runs for an attacker on the clock (director.press_fetch_ok): a gun 56 u off its way is not run for, one
   5 u off it is, and none in the phase's last minute or its overtime (the game's clock at 0)
2. overtime (Director.overtime): the blitz starts again with no cool-down and goes in at once (no rally)
3. the ways in (director.push_lanes): an attack from 60 u out has a flank either side as well as the straight way;  and the
   attackers posted at the territory are spread over them (assign_roles)
4. an attacker covering the territory (mid) keeps to its spot: an item 30 u off it loses to the objective (keep_role)
5. armor lock with a grenade still at its feet is held past half a second (equipment: the hold's danger check)

usage: python -I test_attack_push.py      -> "attack push OK (...)"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain import director as D  # noqa: E402
from brain.bot import Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.sim import Sim  # noqa: E402


def main():
    fails = []
    sp = Sim(mode="invasion", per_team=(4, 4), seed=3, tiers=["top"], map_name="reach_35_island")
    inv = sp.objmodes.inv
    d = sp.directors[1]
    zone = inv["phases"][2][0]
    me = PlayerState(40, 1, "attacker", zone + Vec(30.0, 30.0, 0.0), is_bot=True)

    def snap(**kw):
        base = dict(mode="invasion", inv_phase=2, inv_attackers=1, inv_zones=list(inv["phases"][2]), inv_zone_r=[2.5, 2.5])
        base.update(kw)
        return Snapshot(kw.pop("t", 30.0), [me], **base)
    # 1. runs on the clock
    off_way = me.pos + Vec(40.0, -40.0, 0.0)                       # behind it: ~56 u more than the straight way
    on_way = me.pos + (zone - me.pos) * 0.5 + Vec(2.0, -2.0, 0.0)   # on the way in
    d.inv_target = zone
    if d.press_fetch_ok(me, off_way, snap()) or not d.press_fetch_ok(me, on_way, snap()):
        fails.append("1. runs: want none 56 u off the way, one on the way")
    for name, sn in (("the last minute", snap(time_left=40.0)), ("overtime", snap(time_left=0.0))):
        if d.press_fetch_ok(me, on_way, sn):
            fails.append(f"1. runs in {name}: one sent (want none)")
    # 2. overtime: again at once, no rally
    sp.step()
    live = sp.snapshot()
    live.time_left, live.inv_phase_t = 0.0, 200.0
    d.blitz, d.blitz_cool = None, live.time + 10.0                  # (a blitz just ended: its cool-down running)
    d.blitz_tick(live.time, live)
    bz = getattr(d, "blitz", None)
    if bz is None or bz.get("go") is None:
        fails.append(f"2. overtime right after a blitz: {bz and ('rally' if bz.get('go') is None else 'go')} "
                     f"(want a blitz going in at once)")
    # 3. the ways in: the attackers 60 u out on the open ground (the sim's team), a push with flanks
    d.blitz = None
    target = zone
    lanes = d.push_lanes(live, target)
    if len(lanes) < 2:
        team = [p for p in live.players if p.team == 1]
        c = Vec(sum(p.pos.x for p in team) / len(team), sum(p.pos.y for p in team) / len(team), 0.0)
        fails.append(f"3. ways into the territory from the team at {(c - target).flat():.0f} u: {len(lanes)} (want a flank too)")
    d.inv_target, d.next_roles = target, -1.0
    live.inv_phase, live.inv_attackers = 2, 1
    live.inv_zones, live.inv_zone_r = list(inv["phases"][2]), [2.5, 2.5]
    d.assign_roles(live.time, live)
    vias = {b.order.via for b in d.bots.values() if b.order.point is not None and dist(b.order.point, target) < D.LANE_NEAR}
    if len(lanes) >= 2 and len(vias) < 2:
        fails.append(f"3. the attackers at the territory took {len(vias)} way(s) in of {len(lanes)} (want spread)")
    # 4. a mid keeps to its spot
    b = next(iter(d.bots.values()))
    b.order = Order("mid", zone + Vec(8.0, 0.0, 0.0))
    p = PlayerState(b.id, 1, "mid", b.order.point, is_bot=True)
    scores = {("item", b.order.point + Vec(30.0, 0.0, 0.0)): 1.2, ("objective", b.order.point): 0.7}
    b.keep_role(scores, p, snap(), set())
    if scores[("item", b.order.point + Vec(30.0, 0.0, 0.0))] >= scores[("objective", b.order.point)]:
        fails.append(f"4. a mid's item 30 u off: {scores} (want the objective over it)")
    # 5. armor lock held with a grenade at its feet (its own, the only kind read live: Bot.nade_at): one press, held
    import test_equipment as TE
    lb = TE.bot("strong", "reach", "armor_lock")
    lb.nade_at = (TE.A + Vec(0.6, 0.0, 0.0), 1.8)
    acts = TE.run(lb, 0.0, 1.6, [], me_kw=lambda t: dict(ability_on=t > 0.25))
    held = [bool(a.equipment or a.ability) for _, a, _ in acts]
    presses = sum(1 for k in range(1, len(held)) if held[k] and not held[k - 1]) + (1 if held and held[0] else 0)
    if presses != 1 or sum(held) * TE.DT < 1.0:
        fails.append(f"5. armor lock, its grenade at its feet: {presses} presses, held {sum(held) * TE.DT:.2f} s of 1.6 "
                     f"(want one press held while it is there)")
    if fails:
        print("\n".join(fails))
        sys.exit(1)
    print(f"attack push OK (runs on the way only; overtime at once; {len(lanes)} ways in, {len(vias)} taken)")


if __name__ == "__main__":
    main()
