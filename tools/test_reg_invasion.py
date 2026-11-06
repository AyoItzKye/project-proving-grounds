"""Invasion regression checks: one assert per behavior proven live on Nov 5 (Spire S9-S14, Boneyard B11-B28), each set up
from a live trace's frame (the positions, times and ids below are read from it; traces in the main repo's
logs/tmp/invasion_regress/traces and logs/bug_reports). Every check passes on the code that fixed it and fails on the
0.2.1 build (4031edb) with its own map data. The full cases live in the tests named in each check.

 1 zones      attackers take the zones and hold inside them (Bot.keep_in_zone; test_zone_hold): B12 195.3 s, Elite 12
              alone on phase 1's south territory fighting Spartan 5 4.6 u off stays in the box; B13 from 2.8 u off it
              fights its way in
 2 melee      no carrier melee with the core (test_core_melee): B12 527.13 s, bot 5 carrying, Elite 11 at arm's length
 3 spire      the core is gone for up the spire: the owner's Spire 20261105-201917 phase 3 (0.2.1), the attackers' spots
              under and round the spire: the nav way from each ends ON the core 35 u up (0.2.1's 4-level heightmap had
              no floor at the core's stand, every way ended under it); no Warthog for it (test_trip_ok, S7 060020)
 4 routes     the walkway, plank and run-up fixes: the plank route's end on the -6 walkway (B14 61.2 s, test_route_end),
              the line-up at the plank's take-off (B15 52.84 s, test_route_lineup), on the run line past the run-up
              (B18 580 s, test_runup_line), the banned plank's area (B21 79.3 s, test_ban_area)
 5 fair       team fairness (test_team_fair): S14 151837's join order (1-6 team 0, 7-12 team 1): equal think places,
              mirrored rosters
 6 stay       staying on a loose core (test_core_stay): Spire 143525 at 1071.3 s, defender #9 on the dropped core with
              its post moved 4.3 u off stays on it; attacker #6 1.6 u off it with a defender in sight takes it
 7 crate      the crate grenade (test_boxed_in): B20 Spartan 2 in Boneyard's sealed crate (254.7, 88.4, -4.0): each press
              held 0.3 s, the tries at the feet, off the wall, at the lid

usage: python -I test_reg_invasion.py      -> "reg_invasion OK (7 checks)"
"""
import math
import os
import random
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from brain import invasion, oob  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import JumpVec  # noqa: E402

BONE = "reach_70_boneyard"
BONE_V = "reach_70_boneyard/variants/v86d95e85"
SPIRE_V = "reach_35_island/variants/v3977bae2"


def bot(bid, team, pers, m):
    return Bot(bid, team, make_profile("top", pers, random.Random(bid)), get_map(m), random.Random(bid))


def turn(a, b):
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def zones():
    L = invasion.layout(get_map(BONE)["objects"])
    zs = L["phases"][1]
    zr = [invasion.zone_radius(L, z) for z in zs]
    zone = min(zs, key=lambda z: (z - Vec(255.81, 81.95, -4.0)).flat())
    r = zr[zs.index(zone)]
    for start, label in ((Vec(255.54, 81.76, -4.0), "B12 holder"), (Vec(253.4, 80.6, -4.0), "B13 from 2.8 u")):
        b = bot(12, 1, "rusher", BONE)
        b.order = Order("defender", zone)
        pos, yaw, last, fights = start, 0.0, [], 0
        for k in range(180):                                  # 6 s at 30 Hz, the feet moved by the stick (2.3 u/s)
            t = 195.0 + k / 30
            me = PlayerState(12, 1, "e", pos, yaw=yaw, weapon="plasma_repeater")
            foe = PlayerState(5, 0, "s", Vec(252.61 + 0.6 * math.sin(t * 2.0), 78.58, -3.98), weapon="assault_rifle")
            sn = Snapshot(t, [me, foe], mode="invasion", inv_phase=1, inv_attackers=1, inv_zones=list(zs),
                          inv_zone_r=list(zr), inv_phase_t=60.0)
            a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
            yaw, fights = a.yaw, fights + (b.goal[0] == "fight")
            h, sp = a.yaw + math.atan2(a.strafe, a.forward), min(1.0, math.hypot(a.forward, a.strafe))
            pos = Vec(pos.x + math.cos(h) * sp * 2.3 / 30, pos.y + math.sin(h) * sp * 2.3 / 30, pos.z)
            last.append((pos - zone).flat())
        assert fights >= 90, f"{label}: fought {fights} of 180 ticks (the frame is a fight)"
        worst = max(last) if label == "B12 holder" else max(last[-60:])
        assert worst <= r + 0.15, f"{label}: {worst:.2f} u off the territory's middle (its box {r:.2f})"


def melee():
    deliver = Vec(262.841, 138.845, -8.2)
    b = bot(5, 0, "objector", BONE)
    b.order = Order("runner", deliver)
    here, foe = Vec(300.7, 101.8, -10.0), Vec(300.0, 101.3, -10.0)
    presses = 0
    for k in range(30):
        t = 527.0 + k / 30
        sn = Snapshot(t, [PlayerState(5, 0, "c", here, has_flag=True, weapon="unknown", yaw=3.13),
                          PlayerState(11, 1, "e", foe)], mode="invasion", inv_phase=3, inv_attackers=0,
                      inv_core=here, inv_core_carrier=5, inv_delivery=deliver)
        presses += bool(b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, []).melee)
    assert presses == 0, f"core carrier, Elite 11 at arm's length: {presses} melee presses in 1 s (Reach drops the core)"


def spire():
    m = get_map(SPIRE_V)
    T = terrain(m)
    L = invasion.layout(m["objects"])
    invasion.apply_barriers(T, L, {b["key"]: False for b in L["barriers"] if b["kind"] == "gate"})   # phase 3
    o = oob.Oob(SPIRE_V)
    o.set_phase(T, 3)
    core = Vec(-178.24, -405.33, -22.9)                       # the world rows' core, 264.4 s on
    # the level's own floor under the core (the heightmap, no people's walks: the owner's PC had none up there):
    # 0.2.1's kept the lowest 4 levels, -62.6 / -58.8 / -57.0 / -55.9 inside the spire, and lost the stand's -23.4
    import numpy as np
    hm = np.load(os.path.join(HERE, "..", "maps", "reach_35_island", "heightmap.npz"))
    i, j = int((core.x - float(hm["x0"])) / float(hm["cell"])), int((core.y - float(hm["y0"])) / float(hm["cell"]))
    levels = [round(float(z), 2) for z in hm["floors"][:, j, i] if np.isfinite(z)]
    assert any(abs(z - L["core"].z) < 1.0 for z in levels), \
        f"the heightmap has no floor at the core's stand ({L['core'].z:.1f}): levels {levels}"
    spots = [Vec(-178.8, -406.32, -58.08), Vec(-180.99, -403.07, -55.15), Vec(-178.43, -404.64, -58.18),
             Vec(-180.29, -397.88, -55.8), Vec(-181.5, -361.9, -54.8), Vec(-182.9, -371.6, -57.1),
             Vec(-187.4, -371.8, -57.3)]                      # bots 1, 7, 11, 13 under the core; 11, 7, 11 coming
    short = []
    for q0 in spots:
        q = q0
        for _ in range(150):
            w = T.nav(q, core, jump=True, human=True)
            if w is None or ((w - q).flat() < 0.05 and abs(w.z - q.z) < 0.3):
                break
            q = Vec(w.x, w.y, w.z)
            if (q - core).flat() < 1.0 and abs(q.z - core.z) < 2.0:
                break
        if math.dist((q.x, q.y, q.z), (core.x, core.y, core.z)) >= 2.0:
            short.append(((q0.x, q0.y, q0.z), (round(q.x, 1), round(q.y, 1), round(q.z, 1))))
    assert not short, f"phase 3: the way to the core 35 u up ends short of it from {len(short)} of {len(spots)} " \
                      f"live attacker spots: {short[:3]}"
    me = PlayerState(1, 0, "bot", Vec(-181.0, -397.0, -60.8))      # S7 060020: the Warthog at the spire's foot
    assert hasattr(Bot, "trip_ok") and not Bot.trip_ok(dict(kind="warthog"), me, core), "on wheels to the spire's top"


def routes():
    # B14 61.2 s, Elite 12 landed at the plank route's end on the -6 walkway, walking on: the window does not turn it
    b = bot(12, 1, "objector", BONE_V)
    yaw = math.atan2(92.27 - 90.66, 248.72 - 249.19)
    b.planned_jump, b.jump_land, b.jump_until = False, Vec(249.55, 89.73, -5.94), 61.2 + 0.9
    act = Action(forward=1.0, strafe=0.0, yaw=yaw)
    b.edge_guard(61.2, PlayerState(12, 1, "e", Vec(249.19, 90.66, -6.0), yaw=yaw), act)
    assert act.forward >= 0.5, f"route end: the guard turned the walk round on the walkway (forward {act.forward:.2f})"
    # B15 52.84 s, Elite 7 at the plank's take-off moving north-west across the person's way: back to the run-up
    T = terrain(get_map(BONE_V))
    r = next([(Vec(*q[:3]), q[3]) for q in path] for src, dst, path, w in T.hroutes
             if math.hypot(path[0][0] - 250.71, path[0][1] - 80.39) < 0.3)
    b = bot(7, 1, "sniper", BONE_V)
    b.now = 52.8
    b.route, b.route_full, b.route_until, b.lineups, b.route_lineup = list(r), list(r), 70.0, 0, None
    b.route_key, b.route_end = (round(r[0][0].x, 1), round(r[0][0].y, 1)), r[-1][0]
    vel = Vec(-1.6, 1.4, 0.0)
    act = Action(yaw=math.atan2(vel.y, vel.x))
    b.move_to(PlayerState(7, 1, "e", Vec(251.05, 81.7, -9.7), vel=vel, yaw=act.yaw), Vec(251.217, 94.975, -4.0), act,
              lambda a, q, **kw: q)
    to = math.atan2(80.39 - 81.7, 250.71 - 251.05)
    assert not act.jump and turn(act.yaw + math.atan2(act.strafe, act.forward), to) <= 0.4, \
        f"plank line-up: at the take-off across the way, jump {act.jump}, not back to the run-up"
    # B18 580 s, Spartan 1 on the walkway's run line 1.1 u short of the drop's take-off: on, not back to the run-up
    J = JumpVec(272.42, 89.96, -10.18, sx=265.67, sy=89.63, rx=262.87, ry=90.05)
    b = bot(1, 0, "rusher", BONE_V)
    b.now = 580.0
    p = Vec(264.82, 90.31, -5.0)
    act = Action(yaw=-0.4)
    b.move_to(PlayerState(1, 0, "s", p, vel=Vec(1.5, -0.2, 0.0), yaw=-0.4), Vec(308.91, 103.03, -9.37), act,
              lambda a, q, **kw: J)
    h = act.yaw + math.atan2(act.strafe, act.forward)
    assert turn(h, math.atan2(89.63 - p.y, 265.67 - p.x)) <= 0.5, f"run-up: on the run line, heading {h:.2f} not on"
    # B21 79.3 s, Elite 9 1.9 u off the banned plank route's start: the walking way, no people's ways asked
    L = invasion.layout(get_map(BONE_V)["objects"])
    invasion.apply_barriers(T, L, {g["key"]: True for g in L["barriers"] if g["kind"] == "gate"})
    b = bot(9, 1, "objector", BONE_V)
    b.now, b.order = 100.0, Order("defender", Vec(251.217, 94.975, -4.0))
    b.jump_fails = {(250.7, 80.4): (2, 160.0)}
    kws = []
    b.move_to(PlayerState(9, 1, "e", Vec(251.03, 82.22, -9.8), yaw=0.0), Vec(251.217, 94.975, -4.0), Action(yaw=0.0),
              lambda a, q, **kw: kws.append(kw) or T.nav(a, q, **kw))
    assert kws and not any(k.get("human") for k in kws), f"ban area: by the banned plank the nav asked {kws}"


def fair():
    import live_bots
    assert hasattr(live_bots, "think_order") and hasattr(live_bots, "roster_pick"), \
        "no think_order / roster_pick: index order (team 1 last every pass), styles dealt over all bots"
    bots = {i: types.SimpleNamespace(game_team=0 if i <= 6 else 1) for i in range(1, 13)}   # S14's join order
    place = {0: [], 1: []}
    for n in (0, 1):
        for k, (i, b) in enumerate(live_bots.think_order(bots, n)):
            place[b.game_team].append(k)
    m0, m1 = (sum(v) / len(v) for v in place.values())
    assert abs(m0 - m1) < 1e-9, f"mean think place team 0 {m0:.2f}, team 1 {m1:.2f}"
    styles, tiers, seen = "rusher,flanker,camper,objector,spammer,grudger,sniper".split(","), ["top", "strong"], {}
    got = {0: [], 1: []}
    for i in range(1, 13):
        got[0 if i <= 6 else 1].append(live_bots.roster_pick(styles, tiers, seen, 0 if i <= 6 else 1))
    assert sorted(got[0]) == sorted(got[1]), f"rosters differ: {got}"


def stay():
    core, stand = Vec(-161.66, -422.55, -60.08), Vec(-178.24, -405.33, -22.9)
    deliver = Vec(-163.053, -432.088, -58.371)

    def run(bid, team, pers, order, start, secs, foes=(), fighting=None):
        b = bot(bid, team, pers, SPIRE_V)
        b.order = order
        if fighting is not None:
            b.goal = ("fight", fighting)
        pos, yaw, far, used = start, math.atan2(core.y - start.y, core.x - start.x), 0.0, None
        for k in range(int(secs * 30)):
            t = 1071.3 + k / 30
            me = PlayerState(bid, team, "b", pos, yaw=yaw, weapon="plasma_repeater",
                             weapons=["plasma_repeater", "plasma_pistol"], ammo=[200, 100], mag=[100, 100])
            them = [PlayerState(i, 1 - team, "e", p, yaw=math.atan2(pos.y - p.y, pos.x - p.x)) for i, p in foes]
            sn = Snapshot(t, [me] + them, mode="invasion", inv_phase=3, inv_attackers=1, inv_core=core,
                          inv_core_carrier=None, inv_delivery=deliver, inv_zones=[deliver], inv_zone_r=[1.5],
                          inv_phase_t=150.0)
            sn.inv_stand = stand
            a = b.think(t, 1 / 30, sn, lambda p, q: True, lambda p, q, **kw: q, [])
            if a.action and (pos - core).flat() < 0.9 and used is None:
                used = t
            h, n = a.yaw + math.atan2(a.strafe, a.forward), min(1.0, math.hypot(a.forward, a.strafe))
            pos = Vec(pos.x + 2.3 * n * math.cos(h) / 30, pos.y + 2.3 * n * math.sin(h) / 30, pos.z)
            yaw, far = a.yaw, max(far, (pos - core).flat())
        return far, used
    far, _ = run(9, 0, "objector", Order("defender", Vec(-159.64, -426.07, -59.12)), Vec(core.x + 0.09, core.y, -60.66), 4.0)
    assert far <= 1.0, f"defender #9 on the loose core, its post moved 4.3 u off: went {far:.1f} u off the core"
    _, used = run(6, 1, "flanker", Order("runner", core), Vec(core.x - 1.59, core.y, -60.66), 2.0,
                  foes=[(7, Vec(-156.0, -424.0, -60.6))], fighting=7)
    assert used is not None, "attacker #6 1.6 u off the loose core, defender #7 in sight: no pickup in 2 s"


def crate():
    b = bot(2, 0, "rusher", BONE_V)
    assert hasattr(b, "boxed_in"), "no boxed-in rule: a bot respawned in the sealed crate stays there"
    at, t, held, pitches = Vec(254.7, 88.4, -4.0), 124.1, 0, []
    while t < 124.1 + Bot.BOXED_S + 13.0:
        act = Action(forward=0.9, strafe=0.2)
        was = getattr(b, "box_tries", 0)
        if b.boxed_in(t, PlayerState(2, 0, "bot", at, yaw=0.0), act):
            held += 1
            if getattr(b, "box_tries", 0) != was:
                pitches.append(round(act.pitch, 2))
        t += 0.05
    assert held >= 15, f"the presses not held 0.3 s: {held} pressed ticks for {len(pitches)} tries (B20: one-tick ones)"
    assert len(pitches) >= 3 and pitches[0] < -1.3 and abs(pitches[1]) < 0.2 and pitches[2] > 0.5, \
        f"the tries at the feet, off the wall, at the lid: pitches {pitches}"


CHECKS = (("1 zones", zones), ("2 melee", melee), ("3 spire", spire), ("4 routes", routes), ("5 fair", fair),
          ("6 stay", stay), ("7 crate", crate))


def main():
    fails = []
    for name, f in CHECKS:
        try:
            f()
        except Exception as e:                 # (an AssertionError, or the code before the fix lacking the rule)
            fails.append(f"{name}: {type(e).__name__}: {e}")
    if fails:
        print("reg_invasion FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print(f"reg_invasion OK ({len(CHECKS)} checks)")


if __name__ == "__main__":
    main()
