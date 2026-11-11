"""the player's Spire Invasion match ("doesnt feel fluid ... lack of urgency ... the elites kept using the plasma pistol
... a lack of a 'Pile on' logic ... leave the objective undefended or not reachable in time"; bug reports: "Bots drop
guns when they pick up the core", "Those elites defending the core ... expand their area of defense"): checks that fail
on the code before the fixes.

1. Reach weapons: an Elite with a plasma repeater keeps it over the plasma pistol at mid range
2. the core in hand (read "unknown"): no weapon switch (it dropped the core and the held Use swapped the rifle out)
3. a defender hunting the core's carrier goes for him, not after a man fighting 20 u the other way
4. the director's pile-on: attackers all into a territory a teammate is taking; defenders all but one on a territory
   being taken; the whole attacking team escorts our carrier; the core's guards stand on the spots that cover it
5. people's hops in a row recorded as one jump are not given to the bots as a jump

usage: python -I test_invasion_pileon.py      -> "invasion pile-on OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, path_rises, usable_links  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def bot(i, team, m, seed=1):
    b = Bot(i, team, make_profile("top", "objector", random.Random(seed)), m, rng=random.Random(seed))
    b.notes = []                      # (think() starts them each tick)
    return b


def urgency(fails, m, inv):
    """Phase 3, defending (match 221404: at 383 s five of eight Elites fought attackers at the
    base, at 390 s four went for a Banshee there while he took the core):
    7. a Normal defender posted on the core 35 u up leaves an attacker 6 u off in sight (not shooting it) for the core;
       in phase 2 the same man is still fought, and in phase 3 so is a man shooting it
    8. no defender takes the Banshee by it for the trip up, nor answers a call to drive it; in phase 2 some do"""
    core = inv["core"]
    base = Vec(-189.0, -390.0, -57.2)                         # by the Banshee (match 221404, 388 s)
    foe = PlayerState(8, 0, "spartan", base + Vec(6.0, 0, 0))

    def scores_for(phase, shot=False):
        b = Bot(4, 1, make_profile("average", "objector", random.Random(4)), m, rng=random.Random(4))
        b.order = Order("defender", core)
        b.per.beliefs[8] = Belief(foe.pos, Vec(), 10.0, True, "eyes")
        if shot:
            b.per.attacker_id, b.per.attacker_t = 8, 9.5
        me = PlayerState(4, 1, "elite", base)
        sn = Snapshot(10.0, [me, foe], mode="invasion", inv_phase=phase, inv_attackers=0,
                      inv_core=core if phase == 3 else None, inv_zones=[core])
        sc = {("fight", 8): 1.9, ("objective", core): 1.4}
        b.keep_role(sc, me, sn, [8])
        return max(sc, key=sc.get)[0], sc
    for phase, shot, want in ((3, False, "objective"), (2, False, "fight"), (3, True, "fight")):
        got, sc = scores_for(phase, shot)
        if got != want:
            fails.append(f"phase {phase} defender, a man 6 u off {'shooting it' if shot else 'in sight'}: {sc} (want {want})")
    banshee = dict(handle=77, kind="banshee", pos=(base.x + 2.0, base.y, base.z), occupied=False, riders=0, team=-1)
    # (a trip of its own is in a transport: a Banshee is no taxi since, vehicles.taxi_ok; the core rule is shown
    # with a Mongoose, the Banshee by the order to drive it)
    goose = dict(banshee, kind="mongoose")
    far_post = Vec(base.x + 40.0, base.y, base.z)

    def trips(phase, order="defender", n=40, ride=goose):
        k = 0
        for seed in range(n):
            b = Bot(5, 1, make_profile("top", "objector", random.Random(seed)), m, rng=random.Random(seed))
            post = core if phase == 3 else far_post
            b.order = Order("defender", post) if order == "defender" else Order(order, None, target=77)
            me = PlayerState(5, 1, "elite", base)
            sn = Snapshot(10.0, [me], mode="invasion", inv_phase=phase, inv_attackers=0,
                          inv_core=core if phase == 3 else None, inv_zones=[post], vehicles=[ride])
            k += b.decide(10.0, me, sn) == ("vehicle", 77)
        return k
    if trips(3):
        fails.append(f"phase 3 defenders by a Mongoose, the core 35 u up: {trips(3)} of 40 took it")
    if trips(3, "drive", ride=banshee):
        fails.append(f"phase 3 defenders called to drive the Banshee: {trips(3, 'drive', ride=banshee)} of 40 went for it")
    # (the control: a 40 u trip by a Warthog; a Mongoose only for MONGOOSE_TRIP, the player's rule, Nov 11)
    if not trips(2, ride=dict(banshee, kind="warthog")):
        fails.append("(test: in phase 2 no defender ever took the Warthog for a 40 u trip; the check proves nothing)")
    if trips(2, ride=banshee):
        fails.append(f"phase 2 defenders took the Banshee for a 40 u trip: {trips(2, ride=banshee)} of 40 (a power "
                     f"vehicle is no taxi)")
    power_runs(fails, m, inv)
    needle_rifle(fails, m, inv)


def needle_rifle(fails, m, inv):
    """10. a better gun lying close is taken: an Elite with a plasma repeater and plasma pistol, its post 30 u off, a man
    in sight 25 u away, a needle rifle 5 u from it: it takes the rifle; with the man 7 u off it does not"""
    zone = inv["phases"][1][0]
    here = zone + Vec(30.0, 0.0, 0.0)
    rifle = here + Vec(5.0, 0.0, 0.0)
    for foe_d, want in ((25.0, True), (7.0, False)):
        b = Bot(30, 1, make_profile("strong", "objector", random.Random(3)), m, rng=random.Random(3))
        b.order = Order("defender", zone)
        me = PlayerState(30, 1, "elite", here, weapon="plasma_repeater", weapons=["plasma_repeater", "plasma_pistol"],
                         ammo=[100, 100], mag=[100, 100])
        foe = PlayerState(31, 0, "spartan", here + Vec(0.0, foe_d, 0.0))
        b.per.beliefs[31] = Belief(foe.pos, Vec(), 10.0, True, "eyes")
        b.per.recognized.add(31)
        sn = Snapshot(10.0, [me, foe], mode="invasion", inv_phase=1, inv_attackers=0, inv_zones=[zone],
                      ground_weapons=[("needle_rifle", rifle)])
        b.decide(10.0, me, sn)
        weighed = getattr(b, "last_scores", {}).get(("item", rifle), 0.0)
        took = weighed >= max(v for k, v in b.last_scores.items() if k[0] != "fight") - 1e-9
        if took != want:
            fails.append(f"a needle rifle 5 u off, a man {foe_d} u away: weighed {weighed:.2f}, {b.last_scores} "
                         f"(want {'the rifle over its post' if want else 'no detour'})")


def power_runs(fails, m, inv):
    """9. a sniper lying loose: the nearest attacker on its level is sent (not one holding a sniper, not Easy, nobody 60
    u off) and leaves its territory post for it; once it is gone the run is off"""
    zone = inv["phases"][2][0]
    sniper = Vec(-161.7, -370.1, -54.4)
    poss = [sniper + Vec(15.0, 0, 0), sniper + Vec(8.0, 0, 0), sniper + Vec(60.0, 0, 0), sniper + Vec(5.0, 0, 0)]
    players = [PlayerState(20 + k, 1, f"a{k}", p, is_bot=True, weapons=["sniper"] if k == 1 else ["assault_rifle"],
                           weapon="sniper" if k == 1 else "assault_rifle") for k, p in enumerate(poss)]
    tiers = ["strong", "strong", "strong", "novice"]
    bots = {p.id: Bot(p.id, 1, make_profile(tiers[k], "objector", random.Random(k)), m, rng=random.Random(k))
            for k, p in enumerate(players)}
    d = Director(1, m, bots, random.Random(1))
    sn = Snapshot(30.0, players, mode="invasion", inv_phase=2, inv_attackers=1, inv_zones=[zone], inv_zone_r=[2.5],
                  ground_weapons=[("sniper", sniper)])
    d.power_runs(30.0, sn)
    sent = [k for k, b in bots.items() if getattr(b, "fetch", None)]
    if sent != [20]:
        fails.append(f"a sniper lying loose: sent {sent} (want #20, the nearest without one; #21 holds one, #23 is Easy)")
        return
    b = bots[20]
    b.order = Order("defender", zone)
    got = b.decide(30.0, players[0], sn)
    if got[0] != "item" or dist(got[1], sniper) > 0.5:
        fails.append(f"the attacker sent for the sniper, posted at the territory: decided {got} (want the sniper)")
    d.power_runs(32.0, Snapshot(32.0, players, mode="invasion", inv_phase=2, inv_attackers=1, inv_zones=[zone],
                                ground_weapons=[]))
    if getattr(b, "fetch", None) is not None:
        fails.append("the sniper taken: the run still on")


def main():
    testdata.need_lidar("reach_35_island")
    fails = []
    m = get_map("reach_35_island")
    inv = invasion.layout(m["objects"])
    p0 = Vec(-150.0, -370.0, -55.5)
    # 1. plasma repeater over plasma pistol at 7 u (a man with full shields)
    b = bot(1, 1, m)
    me = PlayerState(1, 1, "elite", p0, weapon="plasma_repeater", weapons=["plasma_repeater", "plasma_pistol"],
                     ammo=[100, 100], mag=[100, 100])
    foe = PlayerState(7, 0, "spartan", p0 + Vec(7, 0, 0), shield=1.0)
    b.per.beliefs[7] = Belief(foe.pos, Vec(), 10.0, True, "eyes")
    sn = Snapshot(10.0, [me, foe], mode="invasion", inv_phase=1, inv_attackers=1)
    if b.choose_weapon(10.0, me, "fight", 7, sn) != -1:
        fails.append(f"plasma repeater in hand, a man at 7 u: switched to {b.notes}")
    # 2. the core in hand reads "unknown": no switch
    b = bot(2, 1, m)
    me = PlayerState(2, 1, "carrier", p0, weapon="unknown", weapons=["unknown", "magnum"], ammo=[-1, 24], mag=[-1, 8])
    sn = Snapshot(10.0, [me], mode="invasion", inv_phase=3, inv_attackers=1, inv_core=p0)
    if b.choose_weapon(10.0, me, "objective", p0, sn) != -1:
        fails.append(f"the core in hand: switched ({b.notes})")
    # 3. a hunter of the carrier: the carrier 30 u one way, a man 20 u the other
    b = bot(3, 0, m)
    carrier = PlayerState(9, 1, "carrier", p0 + Vec(30, 0, 0))
    other = PlayerState(8, 1, "other", p0 + Vec(-20, 0, 0))
    me = PlayerState(3, 0, "defender", p0)
    b.order = Order("hunter", carrier.pos)
    b.per.beliefs[8] = Belief(other.pos, Vec(), 10.0, True, "eyes")
    sn = Snapshot(10.0, [me, carrier, other], mode="invasion", inv_phase=3, inv_attackers=1, inv_core=carrier.pos,
                  inv_core_carrier=9)
    scores = {("fight", 8): 2.0, ("objective", carrier.pos): 1.4}
    b.keep_role(scores, me, sn, [8])
    top = max(scores, key=scores.get)
    if top[0] != "objective" or dist(top[1], carrier.pos) > 1.0:
        fails.append(f"a hunter of the carrier: {scores}, want the carrier")
    # 4. the director's pile-on
    zones = inv["phases"][1]
    radii = [invasion.zone_radius(inv, z) for z in zones]

    def team(t, n, poss):
        players = [PlayerState(10 * t + k, t, f"b{t}{k}", poss[k], is_bot=True) for k in range(n)]
        bots = {p.id: bot(p.id, t, m, p.id) for p in players}
        return players, Director(t, m, bots, random.Random(1))

    far = [Vec(-140.0 - 2 * k, -320.0, -61.0) for k in range(7)]
    att, d_att = team(1, 7, [zones[0] + Vec(0.3, 0, 0)] + far[1:])        # one attacker in territory A
    dfd, d_dfd = team(0, 7, [Vec(-170.0, -380.0 - 2 * k, -57.0) for k in range(7)])
    sn = Snapshot(30.0, att + dfd, mode="invasion", inv_phase=1, inv_attackers=1, inv_zones=list(zones),
                  inv_zone_r=radii, inv_phase_t=30.0)
    d_att.inv_target = zones[0]
    slots = d_att.invasion_slots(30.0, sn, 7)[:7]
    inside = sum(1 for r, p, _ in slots if r == "defender" and dist(p, zones[0]) <= radii[0] + 0.3)
    if inside < 7:
        fails.append(f"attackers, a teammate in territory A: {inside} of 7 sent into it ({[(r, round(dist(p, zones[0]), 1)) for r, p, _ in slots]})")
    slots = d_dfd.invasion_slots(30.0, sn, 7)[:7]
    hunters = sum(1 for r, p, _ in slots if r == "hunter" and dist(p, zones[0]) < 0.5)
    if hunters < 6:
        fails.append(f"defenders, territory A being taken: {hunters} of 7 hunt in it")
    core = inv["core"]
    sn3 = Snapshot(200.0, att + dfd, mode="invasion", inv_phase=3, inv_attackers=1, inv_zones=list(inv["phases"][3]),
                   inv_zone_r=[3.5], inv_core=att[3].pos, inv_core_carrier=att[3].id, inv_delivery=inv["phases"][3][0])
    slots = d_att.invasion_slots(200.0, sn3, 7)[:7]
    if sum(1 for r, _, _ in slots if r == "escort") < 6:
        fails.append(f"attackers, our carrier: {[r for r, _, _ in slots]}, want the team escorting him")
    sn3l = Snapshot(200.0, att + dfd, mode="invasion", inv_phase=3, inv_attackers=1, inv_zones=list(inv["phases"][3]),
                    inv_zone_r=[3.5], inv_core=core, inv_delivery=inv["phases"][3][0])
    slots = d_dfd.invasion_slots(200.0, sn3l, 7)[:7]
    ring = sum(1 for r, p, _ in slots if r == "defender" and dist(p, core) <= 3.5)
    if ring > 1:          # (the old 3 u ring snapped onto the core on Spire's small plateau: three on it, in the open)
        fails.append(f"defenders, the core on its stand: {ring} posted on it or in the open 3 u round it "
                     f"({[(r, round(dist(p, core), 1)) for r, p, _ in slots]})")
    # 5. hops in a row (Spire link 140's path) are not a jump; one jump is
    hops = [-24.08, -24.05, -23.62, -23.43, -23.43, -23.62, -24.0, -24.08, -24.08, -23.78, -23.65, -23.83, -23.84, -23.45,
            -23.23, -23.17, -23.31, -23.41, -23.4]
    one = [0.0, 0.5, 0.8, 0.5, 0.0, -0.3]
    mk = lambda zs: dict(take_off=[0, 0, zs[0]], land=[5, 0, zs[-1]], human=1, path=[[k * 0.3, 0, z] for k, z in enumerate(zs)])
    if path_rises(hops) < 2 or path_rises(one) != 1 or len(usable_links([mk(hops), mk(one)])) != 1:
        fails.append(f"hop runs: rises {path_rises(hops)} / {path_rises(one)}, usable {len(usable_links([mk(hops), mk(one)]))}")
    # 6. stuck at the core's 1.2 u ring (where tonight's attackers hopped 10 s and more): a person's jump that lands
    #    on the stand, reachable from here, is the way up
    stuck = PlayerState(10, 1, "b", Vec(-176.5, -403.5, -24.1))
    sb = Bot(10, 1, make_profile("top", "rusher", random.Random(1)), m, rng=random.Random(1))
    land = sb.jump_onto(stuck, inv["core"])
    if land is None or (land - inv["core"]).flat() > 3.0 or land.z < stuck.pos.z + 0.4:
        fails.append(f"stuck at the core's ring: way up {land} (want a people's jump landing on the stand)")
    urgency(fails, m, inv)
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print("invasion pile-on OK")


if __name__ == "__main__":
    main()
