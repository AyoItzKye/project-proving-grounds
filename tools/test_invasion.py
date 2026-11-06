"""Reach Invasion (brain/invasion.py): each map's setup read from its scenario (attackers, territories per phase, the
core's stand and delivery point, barriers from the kit's collision models), the one-way shields as one-way on the nav
(Boneyard: out of the Spartan base through a door, never in), a gate blocking while it stands and not once it opens, the
phase and sides from respawns, and the director's Invasion roles.

usage: python -I test_invasion.py      -> "invasion OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import invasion  # noqa: E402
from brain.core import Vec, Snapshot, PlayerState, dist  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def cost(T, a, b):
    """Walking cost from a to b on the plain nav graph (Dijkstra field from b)."""
    f = T._field(b)
    return float(f[T._node(a)])


def spire_top_checks():
    """Spire's core run on the spire top, in the sim (live: the attackers roamed 3 u from the core with its goal banned
    since the way up; the carrier stood 200 s on the top facing the jump's landing and backing to its take-off at 0.3
    speed): a ban from the way up is over at the core, and the carrier is off the top within 2 s."""
    from brain.sim import Sim
    out = []
    for case in ("ban", "carry"):
        s = Sim(mode="invasion", per_team=(1, 1), seed=1, map_name="reach_35_island")
        m = s.objmodes
        m.phase, m.phase_t = 3, 0.0
        for p in s.players:
            if p.team == 0:
                p.pos, p.alive = Vec(-30, -300, -60), False
                s.state[p.id]["respawn_at"] = 1e9
                continue
            p.pos, me, b = Vec(-176.2, -402.9, -24.1), p, s.bots[p.id]
            if case == "carry":
                p.has_flag, m.core["carrier"] = True, p.id
            else:
                b.goal_ban = {b._goal_key(("objective", m.core["pos"])): 30.0}
        if case == "carry":
            # off the core's plateau by the ramp, never back over LiDAR link 140 (3.5 s of hops read as one 7.5 u jump:
            # live game 4, the carrier stood 45 s at the plateau's south lip trying it and died)
            from brain import invasion as inv_
            T_ = s.T
            w = T_.nav(Vec(-176.09, -406.58, -23.4), inv_.layout(s.m["objects"])["phases"][3][0], human=True)
            if (w - Vec(-170.37, -400.95, -24.08)).flat() < 1.0:
                out.append(f"Spire: from the plateau's south lip the carrier's way is the 7.5 u jump to the east side ({w})")
        s.run(5.0 if case == "ban" else 2.0)     # (old code: off the top at 4.7 s, after a random wiggle)
        if case == "ban" and b.goal[0] != "objective":
            out.append(f"Spire: 2.3 u from the core with the core's goal banned since the way up, the attacker chose "
                       f"{b.goal[0]}")
        # (since the top's walked ways joined the nav, the carrier crosses the top to the player's drop by the
        # delivery point, 65.7 to the drop at its feet's 71.3: under way within 2 s, off the top within 12)
        if case == "carry" and (me.pos - Vec(-176.2, -402.9, -24.1)).flat() < 1.5:
            out.append(f"Spire: the core carrier has not moved off its spot on the spire top in 2 s ({me.pos})")
        if case == "carry":
            s.run(10.0)
            if me.pos.z > -50:
                out.append(f"Spire: the core carrier is still on the spire top after 12 s ({me.pos})")
    # phase 3's attackers' ground at (-189, -420): every attacker stood there most of phase 3 (live, 0 core carriers)
    # pushing at the way back of LiDAR link 218, a person's 4.67 s flight that rose 7.2 u over its take-off (a launch,
    # kept as a two-way jump): away from the spot within 10 s
    s = Sim(mode="invasion", per_team=(1, 1), seed=3, map_name="reach_35_island")
    s.objmodes.phase, s.objmodes.phase_t = 3, 0.0
    for p in s.players:
        if p.team == 0:
            p.pos, p.alive = Vec(-30, -300, -60), False
            s.state[p.id]["respawn_at"] = 1e9
        else:
            p.pos, me = Vec(-189.0, -420.0, -57.9), p
    s.run(10.0)
    if (me.pos - Vec(-189.0, -420.0, -57.9)).flat() < 3.0:
        out.append(f"Spire phase 3: an attacker at (-189, -420) is still there after 10 s ({me.pos})")
    return out


def main():
    testdata.need_lidar("reach_35_island", "reach_70_boneyard", "reach_dlc_invasion")
    fails = []
    lay = {}
    for name in ("reach_70_boneyard", "reach_35_island", "reach_dlc_invasion"):
        inv = invasion.layout(get_map(name)["objects"])
        if inv is None or len(inv["phases"][1]) != 2 or len(inv["phases"][2]) != 2 or len(inv["phases"][3]) != 1:
            fails.append(f"{name}: no Invasion setup, or not 2 + 2 territories and one delivery point")
            continue
        lay[name] = inv
    bone = lay.get("reach_70_boneyard")
    if bone:
        if bone["attackers"] != 1 or (bone["core"] - Vec(308.4, 103.0, -9.5)).flat() > 0.5:
            fails.append(f"Boneyard: attackers {bone['attackers']}, core {bone['core']}")
        ways = [b for b in bone["barriers"] if b["kind"] == "one_way"]
        if len(ways) != 10:
            fails.append(f"Boneyard: {len(ways)} one-way shields, want 10")
        m = get_map("reach_70_boneyard")
        T = terrain(m)
        door = next(b for b in ways if (b["pos"] - Vec(305.0, 115.0, -5.0)).flat() < 0.1)
        on_floor = lambda x, y, z: Vec(x, y, T.nav_z(x, y, z))
        dp = door["pos"]                                          # facing 0: its front (+x) is the base's inside
        inside, outside = on_floor(dp.x + 1.2, dp.y, dp.z), on_floor(dp.x - 1.2, dp.y, dp.z)
        before_in, before_out = cost(T, outside, inside), cost(T, inside, outside)
        invasion.apply_barriers(T, bone)
        after_in, after_out = cost(T, outside, inside), cost(T, inside, outside)
        if not after_out < 10:
            fails.append(f"one-way door: out of the base costs {after_out:.1f} (was {before_out:.1f}): should stay open")
        if not after_in > before_in + 5:
            fails.append(f"one-way door: into the base {before_in:.1f} -> {after_in:.1f}: should go around or be blocked")
        gate = next(b for b in bone["barriers"] if b["kind"] == "gate" and b["name"] == "frigate_laser_field_med")
        mid = (gate["a"] + gate["b"]) * 0.5
        nx, ny = gate["b"].y - gate["a"].y, gate["a"].x - gate["b"].x
        n = (nx * nx + ny * ny) ** 0.5
        gz = gate["pos"].z
        p, q = on_floor(mid.x + nx / n * 1.2, mid.y + ny / n * 1.2, gz), on_floor(mid.x - nx / n * 1.2, mid.y - ny / n * 1.2, gz)
        closed = cost(T, p, q)
        invasion.apply_barriers(T, bone, {gate["key"]: False})
        opened = cost(T, p, q)
        if not opened < closed:
            fails.append(f"gate: crossing costs {closed:.1f} closed, {opened:.1f} open: opening should make it cheaper")
        invasion.clear_barriers(T, bone)
        if abs(cost(T, outside, inside) - before_in) > 1e-3:
            fails.append("clearing the barriers did not give the plain nav back")
        # the phase and the sides from respawns: blue (team 1) respawning in the attackers' phase 2 zone
        sp = [(1, bone["res"][1][2][0]), (1, bone["res"][1][2][1]), (0, bone["res"][0][2][0])]
        if invasion.phase_from_spawns(bone, sp[:2]) != 2:
            fails.append("phase from respawns: want 2")
        # defenders respawning at their opening (nearest the attackers' phase 3 zone) say nothing: the Watch passes
        # only the attackers' respawns, and theirs at the round start read phase 1
        if invasion.phase_from_spawns(bone, [(0, bone["res"][1][1][0])] * 3) != 1:
            fails.append("phase from the attackers' opening respawns: want 1")
        if invasion.roles_from_spawns(bone, sp, 2) != {1: True, 0: False}:
            fails.append(f"roles from respawns: {invasion.roles_from_spawns(bone, sp, 2)}")
        # a real opening (live): red's spawns at (263, 71) lie nearer the attackers' phase 3 zone than any
        # defender zone; at a round start only phase 1 zones count, so red defends and blue attacks
        opening = [(0, Vec(263.3, 71.7, -5.0)), (0, Vec(263.8, 70.2, -5.0)), (0, Vec(253.4, 99.6, -4.0)),
                   (1, Vec(226.1, 50.3, -6.3)), (1, Vec(216.6, 85.2, -9.4))]
        if invasion.roles_from_spawns(bone, opening, 1) != {0: False, 1: True}:
            fails.append(f"roles at the real opening: {invasion.roles_from_spawns(bone, opening, 1)}")
        swapped = [(0, bone["res"][1][1][0]), (1, bone["res"][0][1][0])]          # round 2: red attacks
        if invasion.roles_from_spawns(bone, swapped) != {0: True, 1: False}:
            fails.append("roles after the sides swap")
        # the live watcher across a round change: sides from the first spawns, then the swap at round 2 at once
        class FakeLive:
            def core(s, raw, stand, key="core"):
                return []

            def present(s, pts, names=None):
                return set(range(len(pts)))
        W = invasion.Watch(bone, T)
        lv = FakeLive()
        def tick(t, where):              # where: {player: (team, Vec) or None for dead}
            ps = [PlayerState(i, tm, f"p{i}", pos or Vec(), Vec(), 0.0, 0.0, pos is not None, 1.0, 1.0, "dmr")
                  for i, (tm, pos) in where.items()]
            sn = Snapshot(t, ps)
            W.update(lv, sn, t, raw=[])
            return sn
        att1, def1 = bone["res"][bone["attackers"]][1], bone["res"][bone["defenders"]][1]
        r1 = {i: (i % 2, (def1 if i % 2 == 0 else att1)[i % 3]) for i in range(8)}     # red defends round 1
        sn = tick(0.0, r1)
        if sn.inv_attackers != 1 or sn.inv_phase != 1 or sn.mode != "invasion":
            fails.append(f"watcher round 1: attackers {sn.inv_attackers}, phase {sn.inv_phase}")
        for t in range(1, 30):                    # deaths and respawns in round 1
            tick(float(t), {**r1, t % 8: (t % 2, None)} if t % 3 else r1)
        tick(40.0, {i: (i % 2, None) for i in range(8)})
        r2 = {i: (i % 2, (att1 if i % 2 == 0 else def1)[i % 3]) for i in range(8)}     # round 2: red attacks
        sn = tick(41.0, r2)
        if sn.inv_attackers != 0 or sn.inv_phase != 1:
            fails.append(f"watcher after the side swap: attackers {sn.inv_attackers} (want 0), phase {sn.inv_phase}")
        # respawns in the attackers' phase 2 zone with their score still 0: phase 1 (live Spire, round 2: the vote
        # said 2, the attackers held phase 2's empty territories for 197 s); score 1: phase 2
        class ScoreLive(FakeLive):
            sc = 0

            def match_state(s):
                return {"score": {1: s.sc, 0: 0}}
        W, lv = invasion.Watch(bone, T), ScoreLive()
        sn = tick(0.0, r1)
        att2 = bone["res"][bone["attackers"]][2]
        for t in range(1, 12):
            sn = tick(float(t), {**{i: (i % 2, def1[i % 3]) for i in range(0, 8, 2)},
                                 **{i: (1, att2[i % len(att2)] if t % 2 else None) for i in range(1, 8, 2)}})
        if sn.inv_phase != 1:
            fails.append(f"watcher: attackers respawning in their phase 2 zone with the score 0 read phase {sn.inv_phase}")
        lv.sc = 1
        sn = tick(13.0, r1)
        if sn.inv_phase != 2:
            fails.append(f"watcher: the attackers' score 1 read phase {sn.inv_phase}, want 2")
        invasion.clear_barriers(T, bone)
        # the director's Invasion roles: attackers hold a territory, defenders post on both
        from brain.director import Director
        from brain.profiles import make_profile
        from brain.bot import Bot
        rng = random.Random(1)
        players, bots = [], {}
        for i in range(8):
            team = i % 2
            pos = bone["res"][team][1][i % 3]
            players.append(PlayerState(i, team, f"b{i}", pos, Vec(), 0.0, 0.0, True, 1.0, 1.0, "dmr", is_bot=True))
        snap = Snapshot(10.0, players, mode="invasion", inv_phase=1, inv_attackers=1,
                        inv_zones=bone["phases"][1], inv_delivery=bone["phases"][3][0])
        for team in (0, 1):
            members = {}
            for p in players:
                if p.team == team:
                    members[p.id] = Bot(p.id, team, make_profile("strong", "objector", rng), m, rng=rng)
            d = Director(team, m, members, rng)
            d.assign_roles(10.0, snap)
            roles = sorted(d.roles.values())
            near = [b for b in members.values() if b.order.point is not None
                    and min((b.order.point - z).flat() for z in bone["phases"][1]) < 6.0]
            if len(near) < 2:
                fails.append(f"team {team} ({'attack' if team == 1 else 'defend'}): {roles}, {len(near)} sent to the territories")
    # an attacker on the loose core holds Use (live: a bot stood 0.4 u from it for minutes, never took it)

    core = Vec(308.4, 103.0, -9.5)
    att, dfd = (PlayerState(k, t, "b", Vec(308.0, 102.9, -9.5), Vec(), 0.0, 0.0, True, 1, 1, "ar") for k, t in ((1, 1), (2, 0)))
    snap = Snapshot(1.0, [att, dfd], mode="invasion", inv_phase=3, inv_attackers=1, inv_core=core)
    if not Bot.on_loose_objective(att, snap) or Bot.on_loose_objective(dfd, snap):
        fails.append("core pickup: the attacker on the core must take it, the defender not")
    # Use only within the pickup's reach: pickups came 0.07-0.59 u off the objective (Breakpoint, Spire); held from 1.6
    # u it swapped the attackers' guns for the one by Spire's stand and, with take, turned their view off the defenders
    # in the fight there (live, game 065836: no core carrier in 256 s of phase 3)
    if Bot.on_loose_objective(PlayerState(1, 1, "b", Vec(307.0, 102.9, -9.5)), snap) is not None:
        fails.append("1.4 u off the core: Use held (want it only within the pickup's reach, under 0.9 u)")
    # the pull rule (guide 07; Breakpoint live: both bomb carriers chased down by the stand's defenders): a runner 10 u
    # from the loose core with a mate waits while a defender is known by it, and goes once two defenders are dead
    from brain.bot import Belief, Order
    from brain.profiles import make_profile
    rb = Bot(1, 1, make_profile("top", "objector", random.Random(1)), get_map("reach_70_boneyard"), random.Random(1))
    rb.order = Order("runner", core)
    me1 = PlayerState(1, 1, "r", core + Vec(-10, 0, 0))
    mate = PlayerState(2, 1, "m", core + Vec(-11, 1, 0))
    rb.per.beliefs[7] = Belief(core + Vec(2, 0, 0), Vec(), 50.0, True, "eyes")
    for extra, want in (([], "hold"), ([PlayerState(8, 0, "d", core, alive=False), PlayerState(9, 0, "e", core, alive=False)],
                                       "objective")):
        rb.stage_since = None
        sn = Snapshot(50.0, [me1, mate, PlayerState(7, 0, "x", core + Vec(2, 0, 0))] + extra, mode="invasion",
                      inv_phase=3, inv_attackers=1, inv_core=core)
        rb.grab_point = Bot.loose_point(me1, sn)
        scores = {("objective", core): 1.7}
        rb.keep_role(scores, me1, sn, [7])
        if max(scores, key=scores.get)[0] != want:
            fails.append(f"Invasion runner by the loose core ({len(extra)} dead): {scores}, want {want}")
    # a man in sight at arm's length is fought whatever the post (live Spire: an attacker and a defender walked 14 s
    # side by side at 0.4 u to the same territory, the post scoring 2.0 over the fight's 1.7)
    zone = core + Vec(25, 0, 0)
    pb = Bot(1, 1, make_profile("top", "objector", random.Random(2)), get_map("reach_70_boneyard"), random.Random(2))
    pb.order = Order("defender", zone)
    me1 = PlayerState(1, 1, "a", core)
    pb.per.beliefs[7] = Belief(core + Vec(0.4, 0, 0), Vec(), 50.0, True, "eyes")
    pb.per.recognized.add(7)
    sn = Snapshot(50.0, [me1, PlayerState(7, 0, "d", core + Vec(0.4, 0, 0))], mode="invasion", inv_phase=1,
                  inv_attackers=1, inv_zones=[zone], inv_zone_r=[2.5])
    picks = {pb.decide(50.0, me1, sn)[0] for _ in range(6)}
    if picks != {"fight"}:
        fails.append(f"a defender 0.4 u away in sight, on the way to a post 25 u off: chose {picks}, want fight")
    # the last steps onto a stand it cannot get onto from this side: straight in and hops, then round to another side
    import math
    from brain.bot import Action
    # the core run's escorts: the lead one ahead toward the delivery point, the other behind (guide 07)
    deliver = get_map("reach_70_boneyard") and invasion.layout(get_map("reach_70_boneyard")["objects"])["phases"][3][0]
    TB, cp = terrain(get_map("reach_70_boneyard")), core
    for _ in range(12):                       # on the way from the core toward the delivery point, open ground
        w = TB.nav(cp, deliver)
        cp = Vec(w.x, w.y, w.z)
    carrier = PlayerState(3, 1, "c", cp, has_flag=True)
    placed = 0
    for eid, ahead in ((4, True), (5, False)):
        eb = Bot(eid, 1, make_profile("top", "objector", random.Random(eid)), get_map("reach_70_boneyard"), random.Random(eid))
        eb.order = Order("escort", carrier.pos, target=3)
        sn = Snapshot(70.0, [carrier, PlayerState(eid, 1, "e", carrier.pos + Vec(0, 2, 0))], mode="invasion", inv_phase=3,
                      inv_attackers=1, inv_core=carrier.pos, inv_core_carrier=3, inv_delivery=deliver)
        q = eb.live_point(sn.player(eid), sn)
        placed += q is not None and q != carrier.pos          # (no floor there: the escort keeps to the carrier)
        if q is not None and q != carrier.pos and ((dist(q, deliver) < dist(carrier.pos, deliver)) != ahead):
            fails.append(f"Invasion escort {eid}: at {q}, want {'ahead of' if ahead else 'behind'} the carrier")
    if not placed:
        fails.append("Invasion escorts: neither placed off the carrier")
    # Spire since: the walked ramp onto the core's plateau is in the nav (moves_review pramp27): from the
    # north-east edge where bots jumped 365 times live, a runner follows the nav, it does not push straight in
    sc = Vec(-178.24, -405.33, -22.9)
    nb = Bot(4, 1, make_profile("top", "objector", random.Random(4)), get_map("reach_35_island"), random.Random(4))
    nb.order, nb.goal, nb.grab_point, nb.now = Order("runner", sc), ("objective", sc), sc, 50.0
    used = []
    nb.move_to(PlayerState(4, 1, "r", Vec(-176.8, -403.3, -24.1)), sc, Action(yaw=0.0),
               lambda p, q, **kw: used.append(q) or q)
    if not used:
        fails.append("Spire core from its north-east edge: pushed straight in, the nav's ramp not followed")
    # the fallback when the nav has no way up (the tests below): straight in and hops, then round to another side
    T_spire = nb.T()
    T_spire.reaches = lambda *a, **k: False
    # (Spire, live: the south-west side of the core's stand, where bots pushed 50 s)
    sb = Bot(5, 1, make_profile("top", "objector", random.Random(5)), get_map("reach_35_island"), random.Random(5))
    sb.order, sb.goal = Order("runner", sc), ("objective", sc)
    here = PlayerState(5, 1, "r", Vec(-179.3, -406.8, -24.1))
    sb.grab_point, heads = sc, []
    want = math.degrees(math.atan2(sc.y - here.pos.y, sc.x - here.pos.x))
    for k in range(50):                       # 5 s pushing, never moving
        sb.now = 60.0 + k * 0.1
        a = Action(yaw=math.radians(want))
        sb.move_to(here, sc, a, lambda p, q, **kw: q)
        heads.append(math.degrees(math.atan2(a.strafe, a.forward)))
    g = getattr(sb, "grab_round", None)
    side = abs(math.degrees(math.atan2(math.sin(math.atan2(g.y - sc.y, g.x - sc.x) - math.atan2(here.pos.y - sc.y, here.pos.x - sc.x)),
                                        math.cos(math.atan2(g.y - sc.y, g.x - sc.x) - math.atan2(here.pos.y - sc.y, here.pos.x - sc.x))))) if g else 0
    if abs(heads[0]) > 10 or side < 90:
        fails.append(f"stand it cannot get onto: heading {heads[0]:.0f}, then to {g} ({side:.0f} degrees round): want straight in, "
                     f"then another side of the stand")
    # ... and sliding along the ring, 0.01 u closer a tick (live, bot 9: a clock reset at every 0.1 u, no hop in 4
    # s): a running jump within 2.5 s (back off, run, jump)
    sb2 = Bot(6, 1, make_profile("top", "objector", random.Random(6)), get_map("reach_35_island"), random.Random(6))
    sb2.order, sb2.goal, sb2.grab_point = Order("runner", sc), ("objective", sc), sc
    hopped, pos = False, Vec(-176.9, -403.1, -24.1)
    for k in range(25):
        sb2.now = 80.0 + k * 0.1
        pos = pos + (sc - pos) * (0.01 / (sc - pos).flat())
        a = Action(yaw=0.0)
        sb2.move_to(PlayerState(6, 1, "r", Vec(pos.x, pos.y, -24.1)), sc, a, lambda p, q, **kw: q)
        hopped |= bool(a.jump)
    if not hopped:
        fails.append("sliding along the stand 0.01 u a tick: no hop in 2.5 s")
    # close in and blocked: 0.62 u east of the core, where a runner pushed 45 s holding Use and looking past it (live
    # Spire; the pickups came from its west side at 0.25 u): round to another side within 5 s ...
    east = PlayerState(7, 1, "r", Vec(-177.62, -405.2, -23.35))
    sb3 = Bot(7, 1, make_profile("top", "objector", random.Random(7)), get_map("reach_35_island"), random.Random(7))
    sb3.order, sb3.goal, sb3.grab_point = Order("runner", sc), ("objective", sc), sc
    for k in range(50):
        sb3.now = 90.0 + k * 0.1
        sb3.move_to(east, sc, Action(yaw=math.pi), lambda p, q, **kw: q)
    if getattr(sb3, "grab_round", None) is None:
        fails.append("0.62 u off the core's stand, blocked 5 s: never round to another side")
    del T_spire.reaches                       # (the class's own again)
    # ... and Use held with the view on the core (Reach's Use takes what the view is on), through think()
    from brain.core import angles_to, eye, wrap
    vb = Bot(8, 1, make_profile("top", "objector", random.Random(8)), get_map("reach_35_island"), random.Random(8))
    vb.order = Order("runner", sc)
    wy, wp = angles_to(eye(east), sc)
    held = on = 0
    yaw, pitch = math.pi, 0.0
    for k in range(90):
        t = 120.0 + k / 30
        me = PlayerState(8, 1, "r", east.pos, yaw=yaw, pitch=pitch)
        a = vb.think(t, 1 / 30, Snapshot(t, [me], mode="invasion", inv_phase=3, inv_attackers=1, inv_core=sc),
                     lambda p, q: True, lambda p, q, **kw: q, [])
        yaw, pitch = a.yaw, a.pitch
        if k >= 60:
            held += bool(a.action)
            on += abs(wrap(a.yaw - wy)) < 0.15 and abs(a.pitch - wp) < 0.12
    if held < 25 or on < 25:
        fails.append(f"0.62 u off the loose core: Use on {held} of 30 ticks, the view on it {on} (want both)")
    # Spire: the core's platform is not among its cell's four floors; the path still ends up there, not 35 u under it
    T3 = terrain(get_map("reach_35_island"))
    core3, p = Vec(-178.24, -405.33, -22.9), Vec(-161, -349, -55)   # (the core object, 0.5 u over its stand)
    for _ in range(300):
        w = T3.nav(p, core3, jump=True, human=True)
        if ((w.x - p.x) ** 2 + (w.y - p.y) ** 2 + (w.z - p.z) ** 2) ** 0.5 < 0.05:
            break
        p = Vec(w.x, w.y, w.z)
    if ((p.x - core3.x) ** 2 + (p.y - core3.y) ** 2 + (p.z - core3.z) ** 2) ** 0.5 > 3.0:
        fails.append(f"Spire: the way to the core ends at {p}")
    fails += spire_top_checks()
    # the core carrier looks where it goes: no gun to answer with, and on the spire top its walk swung with its view
    # from a radar dot to its path and back until it went over the east edge with the core (live)
    import random as _r
    from brain.bot import Belief, Bot
    from brain.profiles import make_profile
    m = get_map("reach_35_island")
    cb = Bot(1, 1, make_profile("top", "objector", _r.Random(2)), m, _r.Random(2))
    top = Vec(-171.0, -408.5, -24.3)
    cb.now, cb.wp = 500.0, Vec(-169.4, -409.1, -24.3)
    cb.per.beliefs[10] = Belief(top + Vec(0.0, 12.0, 0.0), Vec(), 500.0, False, "radar")
    me = PlayerState(1, 1, "carrier", top, has_flag=True)
    cb.look_point(me, Vec(-150.0, -420.0, -60.0))
    if not cb.att or cb.att[0] != "path":
        fails.append(f"the core carrier with a radar dot near: looked at {cb.att} (want its way)")
    # ... at eye height, 8 u on toward its way (Bot.ahead): not at its waypoint, not at its goal
    look = cb.look_point(me, Vec(-150.0, -420.0, -60.0))
    d, way = Vec(look.x - top.x, look.y - top.y, 0.0), Vec(cb.wp.x - top.x, cb.wp.y - top.y, 0.0)
    if abs(d.flat() - 8.0) > 0.05 or abs(look.z - (top.z + 0.27)) > 0.01 or \
            (d.x * way.x + d.y * way.y) / (d.flat() * way.flat()) < 0.999:
        fails.append(f"the core carrier's look point {look} (want eye height, 8 u on toward its way {cb.wp})")
    # property (Code Master TS-11): whatever it knows of (seen or not, shot by, heard, on radar; within 25 u each
    # way, 0-3 s old), the carrier looks at its way, never watches
    prng = _r.Random(7)
    for _k in range(80):
        cb.per.beliefs.clear()
        cb.per.beliefs[11] = Belief(top + Vec(prng.uniform(-25, 25), prng.uniform(-25, 25), prng.uniform(-3, 3)),
                                    Vec(), 500.0 - prng.uniform(0.0, 3.0), prng.random() < 0.5,
                                    prng.choice(("eyes", "hit", "heard", "radar")))
        cb.look_point(me, Vec(-150.0, -420.0, -60.0))
        if not cb.att or cb.att[0] != "path":
            fails.append(f"the core carrier knowing of {cb.per.beliefs[11]}: looked at {cb.att} (want its way)")
            break
    # a detached plasma turret is carried in a third weapon slot: never the core (the player's flag, Spire: the
    # player's turret read as the core carried 36 s into phase 1, bots ran turrets to the delivery point)
    from brain.live import LiveReach
    lr = LiveReach.__new__(LiveReach)
    turret = 0xAA0001
    lr._weapons_held = lambda players: ([(turret, 0x111, 0, (-132.8, -365.6, -57.8))],
                                        {turret: dict(index=0, team=0, pos=(-132.8, -365.6, -57.8))})
    lr._third, lr._attached = {turret}, set()
    if lr.core([], core3):
        fails.append("Spire: a carried turret (third weapon slot) read as the core")
    # Breakpoint: phase 2 is a bomb run (the second core marker is its stand), played as the core run to a phase 2 marker
    bp = lay.get("reach_dlc_invasion")
    if bp:
        if bp.get("bomb") is None or (bp["bomb"] - Vec(-14.4, -2.8, -3.6)).flat() > 0.5:
            fails.append(f"Breakpoint's bomb stand {bp.get('bomb')}")
        else:
            class Live2:
                def core(s, raw, stand, key="core"):    # (the carried bomb also reads as the core: third slot)
                    return [dict(pos=(stand.x, stand.y, stand.z), carrier=None if key == "bomb" else 3)]

                def present(s, pts, names=None):
                    return set()

                def match_state(s):
                    return {"score": {}}
            W2 = invasion.Watch(bp, terrain(get_map("reach_dlc_invasion")))
            W2.phase, W2.sides_set = 2, True
            sn = Snapshot(5.0, [])
            W2.update(Live2(), sn, 5.0, raw=[])
            if (sn.inv_phase != 3 or sn.inv_core is None or (sn.inv_core - bp["bomb"]).flat() > 0.1
                    or sn.inv_delivery not in bp["phases"][2]):
                fails.append(f"Breakpoint phase 2: phase {sn.inv_phase}, carry {sn.inv_core} to {sn.inv_delivery}")
            # phase 3 after the detonation: the vault doors (gates at the plant markers) are open even when an object is
            # still read there; the way to the core goes in through a door, not over the vault's roof (live: the
            # attackers stood 4 u over the core for 250 s)
            class Live4(Live2):
                def present(s, pts, names=None):
                    return set(range(len(pts)))
            TB2 = terrain(get_map("reach_dlc_invasion"))
            W3 = invasion.Watch(bp, TB2)
            W3.phase, W3.sides_set, W3.gates_t = 3, True, -9.0
            W3.update(Live4(), Snapshot(20.0, []), 20.0, raw=[])
            p, top = Vec(23.4, 3.6, -6.6), -99.0
            for _ in range(80):
                w = TB2.nav(p, bp["core"], jump=True, human=True)
                q = Vec(w.x, w.y, w.z)
                if ((q.x - p.x) ** 2 + (q.y - p.y) ** 2 + (q.z - p.z) ** 2) ** 0.5 < 0.05:
                    break
                p, top = q, max(top, q.z)
            if (p - bp["core"]).flat() > 1.5 or top > -6.2:
                fails.append(f"Breakpoint phase 3: the way into the vault ends at {p}, highest z {top:.1f} (over the roof)")
            # armed on its marker, with the core (the same kind of object) waiting in the vault: the bomb is the one
            # read, armed; the attackers do not take it again, the defenders go onto it (live: the core was read as the
            # bomb and the attackers chased it 280 s)
            plant0 = bp["phases"][2][0]

            class Live3(Live2):
                def core(s, raw, stand, key="core"):
                    return [dict(pos=(bp["core"].x, bp["core"].y, bp["core"].z), carrier=None),
                            dict(pos=(plant0.x, plant0.y, plant0.z), carrier=None)]
            W2.bomb_last = plant0
            sn = Snapshot(9.0, [])
            W2.update(Live3(), sn, 9.0, raw=[])
            att, dfd = (PlayerState(k, t, "b", plant0 + Vec(0.5, 0, 0), Vec(), 0, 0, True, 1, 1, "ar") for k, t in ((1, 1), (2, 0)))
            if ((sn.inv_core - plant0).flat() > 0.1 or not sn.inv_armed or Bot.loose_point(att, sn) is not None
                    or Bot.loose_point(dfd, sn) is None or not Bot.on_loose_objective(dfd, sn)):
                fails.append(f"Breakpoint armed bomb: read {sn.inv_core}, armed {sn.inv_armed}, attacker takes "
                             f"{Bot.loose_point(att, sn)}, defender {Bot.loose_point(dfd, sn)}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("invasion OK")


if __name__ == "__main__":
    main()
