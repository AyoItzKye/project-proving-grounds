"""Regression checks for live-proven behaviors that had no test of their own (docs/WORKING_BEHAVIORS.md, rows marked
test_reg_core). Each check is cheap (built snapshots on the real maps' data, no simulator run) and fails if the behavior
it guards breaks:

air_kill_zone     a Banshee at speed flying at a Spire kill zone (hard box) or soft kill zone, the level open ahead:
                  air_guard turns or climbs off it (Terrain.oob_avoid wired into the pilot's probe); the same flight with
                  no volumes known is left alone (live Nov 3-4: kill zones read from the kits, brain/oob.py)
air_clearance     a Banshee at speed with a wall beside it inside its CLEARANCE near radius, open ahead: air_guard eases
                  off away from that side; in open air it does not (vehicles.CLEARANCE; live Avalanche Oct 31)
air_wall          a Banshee at speed heading at a solid face with open air over or beside it: air_guard climbs or turns
                  (Terrain.fly_clear; live Avalanche Oct 31 air stalls 4/13 s)
banshee_take      Slayer, a free bot by an empty Banshee and nothing else: crew_orders sends it to drive the Banshee
                  (bots take aircraft; live Reach Banshee flights Oct 28-Nov 4)
warthog_gunner    our Warthog with only its driver: vehicle_orders puts the nearest free teammate on the gun (Order
                  "ride"), and with two riders called the gun is filled before the passenger seat (live Oct 25 Boneyard
                  gunners 5, 6, 8; H2A Bloodline Nov 3 gunner fired 18% of 8662 rows)
ctf_carry         CTF: our bot carrying their flag is a runner sent home to the capture point (live Reach / H3 / H4
                  captures Oct 24-31)
core_carry        Invasion phase 3: our attacker carrying the core is a runner sent to the delivery point (live Spire
                  S9 / S12 / S14, Boneyard B22-B26 Nov 5)
koth_company      King: a hill defender alone with a man of theirs in the hill waits outside for company (stage); with a
                  teammate beside it it goes in (KOTH-STATIC-10, KING_TAKE_IN; live Reach King Oct 26-30)
zone_rules        held_zone (keep_in_zone): an Invasion attacker's territory, an Infection zone and the hill are held
                  from inside; a Territories post is NOT (240bb99: the rule cost Territories 4 takes against 9)
territories_posts Territories: the director posts bots on the territories (captures need a bot standing in them)
release_gate      tools/make_release.py and tools/build_installer.py stop before building when test_regressions fails

usage: python -I test_reg_core.py [check ...]      -> "reg core OK (n checks)"; exit 1 on any failure
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import oob as O  # noqa: E402
from brain import vehicles  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import Action, FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

SPEED = 9.0           # u/s: a Banshee in flight


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def bot(i, m, tier="top", style="objector", seed=None, team=0):
    return Bot(i, team, make_profile(tier, style, random.Random(seed or i)), m, random.Random(seed or i))


def fly(M, T, pos, yaw, kind="banshee"):
    """One air_guard tick for a pilot at pos heading yaw at SPEED, full throttle, long since boarded."""
    b = bot(1, M, "top", "rusher", seed=1)
    b._terrain, b.seat, b.notes, b.landing, b.air_dest = T, "driver", [], False, None
    b.seat_since, b.now = -100.0, 10.0
    vel = Vec(math.cos(yaw) * SPEED, math.sin(yaw) * SPEED, 0.0)
    me = PlayerState(1, 0, "pilot", pos, vel=vel, yaw=yaw, alive=True, vehicle=9)
    act = Action(yaw=yaw)
    act.forward, act.pitch = 1.0, 0.0
    b.air_guard(me, act, Snapshot(10.0, [me], vehicles=[dict(handle=9, kind=kind, pos=(pos.x, pos.y, pos.z),
                                                               occupied=True, riders=1, team=0)]))
    return act, b.notes


def floor_under(T, p):
    return p.z - T.height_over(p.x, p.y, p.z)


def look(kind="banshee"):
    return max(4.0, min(60.0, 2.0 + vehicles.clearance(kind)["ttc"] * SPEED))


def check_air_kill_zone():
    M = get_map("reach_35_island")
    T = terrain(M)
    vols = O.volumes("reach_35_island")
    out, L = [], look()
    try:
        for kind in ("hard", "soft"):
            mine = [v for v in vols if v["kind"] == kind]
            found = None
            for x, y, z, r, band in O.air_discs(mine):
                for k in range(16):
                    yaw = k * math.pi / 8
                    p = Vec(x - math.cos(yaw) * (r + 6.0), y - math.sin(yaw) * (r + 6.0), z)
                    if not T.inside(p.x, p.y):
                        continue
                    fl = floor_under(T, p)
                    if p.z - fl < 3.0 or T.fly_clear(p, yaw, L, floor=fl) < L or \
                            T.fly_clear(p, yaw, L, floor=fl, dzs=(1.0, 2.0, 3.0)) < L:
                        continue          # (the level itself in the way, or no air under it: not this check's case)
                    T.set_oob([], version=1, volumes=mine)
                    if T.fly_clear(p, yaw, L, floor=fl, avoid=T.oob_avoid()) >= L:
                        continue
                    found = (p, yaw)
                    break
                if found:
                    break
            if found is None:
                out.append(f"air_kill_zone: no {kind} kill zone on Spire with open air at it (data changed?)")
                continue
            p, yaw = found
            T.set_oob([], version=1, volumes=mine)
            act, notes = fly(M, T, p, yaw)
            moved = abs(wrap(act.yaw - yaw)) > 0.05 or act.pitch >= 0.45 or act.forward < 0.0 or abs(act.strafe) > 0.05
            if not moved or not any(n.startswith("air: wall ahead") for n in notes):
                out.append(f"air_kill_zone: a Banshee flying at Spire's {kind} kill zone from {p} heading {yaw:.2f}: yaw "
                           f"{act.yaw:.2f} pitch {act.pitch:.2f} notes {notes} (want it turned or climbing off)")
            T.set_oob([], version=2, volumes=[])
            act, notes = fly(M, T, p, yaw)
            if any(n.startswith("air: wall ahead") for n in notes):
                out.append(f"air_kill_zone: with no kill zones known the same flight reacted {notes} (want untouched)")
    finally:
        T.set_oob([], version=3, volumes=[])
    return out


def side_spot(T, near, L, rng, z_over=(4.0, 12.0)):
    """A spot in the air with a solid thing beside it inside near*0.6, open ahead and over: (pos, yaw, side offset)."""
    from brain.bot import AIR_SIDES
    x0, y0, x1, y1 = T.window
    for _ in range(3000):
        x, y = rng.uniform(x0 + 5, x1 - 5), rng.uniform(y0 + 5, y1 - 5)
        g = T.ground(x, y)
        if not math.isfinite(g):
            continue
        for over in z_over:
            p = Vec(x, y, g + over)
            fl = floor_under(T, p)
            if p.z - fl < 3.0:
                continue
            for k in range(8):
                yaw = k * math.pi / 4
                if T.fly_clear(p, yaw, L, floor=fl) < L or T.fly_clear(p, yaw, L, floor=fl, dzs=(1.0, 2.0, 3.0)) < L:
                    continue
                d, o = min((T.fly_clear(p, yaw + o, near, floor=fl), o) for o in AIR_SIDES)
                if d < near * 0.6 and abs(o) == math.pi / 2:
                    return p, yaw, o
    return None


def check_air_clearance():
    out, L = [], look()
    near = vehicles.clearance("banshee")["near"]
    M = get_map("h3_sidewinder")
    T = terrain(M)
    T.set_oob([], version=1, volumes=[])
    got = side_spot(T, near, L, random.Random(7))
    if got is None:
        return ["air_clearance: no spot on Sidewinder with a wall beside and open air ahead (data changed?)"]
    p, yaw, o = got
    act, notes = fly(M, T, p, yaw)
    away = wrap(o + math.pi)
    turned = wrap(act.yaw - yaw)
    if "air: too near something, easing off" not in notes or turned * away <= 0.0:
        out.append(f"air_clearance: a Banshee at {p} heading {yaw:.2f}, a wall {o:+.2f} rad beside it inside {near} u: "
                   f"turned {turned:+.3f} rad, notes {notes} (want eased off away from it)")
    # open air: 20 u over the highest floor near the map's middle, nothing within near: untouched
    x0, y0, x1, y1 = T.window
    mid = Vec((x0 + x1) / 2, (y0 + y1) / 2, 0.0)
    top = T.top_near(mid.x, mid.y, 12.0)
    q = Vec(mid.x, mid.y, top + 20.0)
    act, notes = fly(M, T, q, 0.3)
    if any(n.startswith("air: too near") or n.startswith("air: wall ahead") for n in notes):
        out.append(f"air_clearance: in open air 20 u over Sidewinder's middle: {notes} (want untouched)")
    return out


def check_air_wall():
    out, L = [], look()
    M = get_map("h3_sidewinder")
    T = terrain(M)
    T.set_oob([], version=1, volumes=[])
    rng = random.Random(3)
    x0, y0, x1, y1 = T.window
    for _ in range(4000):
        x, y = rng.uniform(x0 + 5, x1 - 5), rng.uniform(y0 + 5, y1 - 5)
        g = T.ground(x, y)
        if not math.isfinite(g):
            continue
        p = Vec(x, y, g + 4.0)
        fl = floor_under(T, p)
        yaw = rng.uniform(-math.pi, math.pi)
        d = T.fly_clear(p, yaw, L, floor=fl)
        if p.z - fl < 3.0 or not 3.0 < d < L - 2.0:
            continue
        act, notes = fly(M, T, p, yaw)
        moved = abs(wrap(act.yaw - yaw)) > 0.05 or act.pitch >= 0.45 or act.forward < 0.0 or abs(act.strafe) > 0.05
        if not moved or not any(n.startswith("air: wall ahead") for n in notes):
            out.append(f"air_wall: a Banshee at {p} heading {yaw:.2f}, a wall {d:.1f} u ahead: yaw {act.yaw:.2f} pitch "
                       f"{act.pitch:.2f} notes {notes} (want climbing over, turning or backing off)")
        return out
    return ["air_wall: no spot on Sidewinder with a wall ahead (data changed?)"]


def hog(A, **kw):
    return dict(dict(handle=9, kind="warthog", pos=(A.x, A.y, A.z), riders=1, occupied=True, team=0,
                     fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), gunner=False, turrets=[], manned=[]), **kw)


def check_banshee_take():
    M = get_map("bloodgulch")
    T = terrain(M)
    red = M["flags"][0]
    A = Vec(red.x - 10.0, red.y + 10.0, T.ground(red.x - 10.0, red.y + 10.0))
    b1 = bot(1, M)
    b1._terrain = T
    d = Director(0, M, {1: b1}, random.Random(5))
    ps = [PlayerState(1, 0, "b1", A)]
    vs = [dict(hog(A, handle=22, kind="banshee", pos=(A.x - 8, A.y, A.z)), occupied=False, riders=0, team=-1)]
    snap = Snapshot(22.0, ps, mode="slayer", vehicles=vs)
    d.roles = {1: "free"}
    d.crew_orders(22.0, snap, {1: snap.player(1)}, [b1])
    if (b1.order.role, b1.order.target) != ("drive", 22):
        return [f"banshee_take: a free bot 8 u from an empty Banshee: order {b1.order.role} -> {b1.order.target} "
                f"(want drive -> 22)"]
    return []


def check_warthog_gunner():
    out = []
    M = get_map("bloodgulch")
    T = terrain(M)
    red, blue = M["flags"][0], M["flags"][1]
    A = Vec(red.x - 10.0, red.y + 10.0, T.ground(red.x - 10.0, red.y + 10.0))
    flags = {0: FlagState(0, red, red, "home"), 1: FlagState(1, blue, blue, "home")}
    # 1. a driver alone, a free teammate 15 u off with nothing to do: put on the gun, the driver waits for him
    drv, mate = bot(1, M), bot(2, M)
    for b in (drv, mate):
        b._terrain = T
    bots = {1: drv, 2: mate}
    d = Director(0, M, bots, random.Random(1))
    drv.seat, drv.seat_for, drv.seat_since = "driver", 9, 0.0
    drv.order, mate.order = Order("mid", blue), Order("free")
    d.roles = {1: "mid", 2: "free"}
    ps = [PlayerState(1, 0, "drv", A, vehicle=9), PlayerState(2, 0, "mate", A + Vec(15.0, 0.0, 0.0))]
    snap = Snapshot(10.0, ps, flags, mode="ctf", vehicles=[hog(A)])
    d.vehicle_orders(10.0, snap, list(bots.values()))
    if (mate.order.role, mate.order.target) != ("ride", 9):
        out.append(f"warthog_gunner: our Warthog with only its driver, a free teammate 15 u off: his order "
                   f"{mate.order.role} -> {mate.order.target} (want ride -> 9, the gun)")
    # 2. two riders called: the gun first, then the passenger seat
    drv, r1, r2 = bot(1, M), bot(2, M), bot(3, M)
    bots = {1: drv, 2: r1, 3: r2}
    d = Director(0, M, bots, random.Random(2))
    drv.seat, drv.seat_for, drv.seat_since = "driver", 9, 0.0
    for b, role in ((drv, "mid"), (r1, "runner"), (r2, "runner")):
        b._terrain = T
        b.order = Order(role, blue)
        d.roles[b.id] = role
    ps = [PlayerState(1, 0, "drv", A, vehicle=9), PlayerState(2, 0, "r1", A + Vec(5.0, 0.0, 0.0)),
          PlayerState(3, 0, "r2", A + Vec(0.0, 8.0, 0.0))]
    snap = Snapshot(11.0, ps, flags, mode="ctf", vehicles=[hog(A)])
    d.rider_calls(11.0, snap, list(bots.values()), {b.id: snap.player(b.id) for b in bots.values()})
    if (r1.order.role, r2.order.role) != ("ride", "board"):
        out.append(f"warthog_gunner: two runners by our driver's Warthog: {r1.order.role}, {r2.order.role} "
                   f"(want ride for the nearer: the gun first, board for the next)")
    return out


def check_ctf_carry():
    M = get_map("h3_cyberdyne")
    red, blue = M["flags"][0], M["flags"][1]
    bots = {i: bot(i, M) for i in range(1, 5)}
    d = Director(0, M, bots, random.Random(0))
    car = blue + (red - blue) * 0.3
    ps = [PlayerState(1, 0, "car", car, has_flag=True)] + [PlayerState(i, 0, f"b{i}", red + Vec(i, 0, 0)) for i in (2, 3, 4)]
    ps += [PlayerState(20 + k, 1, f"e{k}", blue) for k in range(4)]
    flags = {0: FlagState(0, red, red, "home"), 1: FlagState(1, blue, car, "carried", 1)}
    snap = Snapshot(10.0, ps, flags, mode="ctf")
    d.assign_roles(10.0, snap)
    o, cap = bots[1].order, d.capture_point(snap)
    if o.role != "runner" or o.point is None or dist(o.point, cap) > 1.0 or dist(cap, red) > dist(cap, blue):
        return [f"ctf_carry: our carrier's order {o.role} -> {o.point} (want runner to our capture point {cap}, by our base)"]
    return []


def check_h2a_flag_use():
    # H2A takes a CTF flag with Use, as a gun (native f_interaction); the brain only pressed Use on bombs, cores and
    # Stockpile flags, so runners stood on red's flag and never took it (live Lockdown Multi Flag CTF, Nov 6 s177)
    M = get_map("h2a_ca_lockout")
    red, blue = Vec(0.3, 8.96, 3.15), Vec(-10.7, -8.82, -3.08)
    me = PlayerState(2, 1, "runner", red + Vec(0.3, 0.2, 0.0))
    flags = {0: FlagState(0, red, red, "home"), 1: FlagState(1, blue, blue, "home")}
    snap = Snapshot(10.0, [me], flags, mode="ctf")
    got = Bot.use_flag_point(me, snap, "h2a")
    out = [] if got is not None and dist(got, red) < 0.01 else [f"h2a_flag_use: on red's flag, Use point {got} (want it)"]
    if Bot.use_flag_point(me, snap, "h3") is not None:
        out.append("h2a_flag_use: Halo 3 takes flags by walking onto them, no Use point wanted")
    if bot(2, M, team=1).game != "h2a":
        out.append("h2a_flag_use: the bot's game on an H2A map is not h2a")
    return out


def check_forge_items():
    # a Forge creation with no .mvar file: its items are the guns lying in it, by the map's own tag names (#11); a gun
    # in someone's hands and a gun the brain has no power rank for are not items
    import struct
    from brain.forge import live_items
    from brain.live import LiveReach

    class FakeLive:
        _own_name, objects, _learn, _was_held = (LiveReach._own_name, LiveReach.objects, LiveReach._learn,
                                                  LiveReach._was_held)

        def __init__(s):
            s._names, s.mem, s._placements = {}, {}, []
            names = ["objects\\weapons\\support_high\\rocket_launcher\\rocket_launcher",
                     "objects\\weapons\\rifle\\sniper_rifle\\sniper_rifle", "objects\\weapons\\rifle\\dmr\\dmr"]
            s._tag_name_list = names
            rows = [(0, 0xFFFFFFFF, (5.0, 6.0, 7.0)), (1, 0x00010002, (1.0, 1.0, 1.0)), (2, 0xFFFFFFFF, (2.0, 2.0, 2.0))]
            ents = bytearray()
            for k, (tag_ix, parent, pos) in enumerate(rows):
                addr = 0x1000 + k * 0x100
                ents += struct.pack("<HHB3xQQ", 0x1234, 0, 2, 0, addr)
                head = bytearray(0x50)
                struct.pack_into("<I", head, 0, 0xE0000000 | tag_ix)
                struct.pack_into("<I", head, 0x14, parent)
                struct.pack_into("<3f", head, 0x44, *pos)
                s.mem[addr] = bytes(head)
            s.mem[0x10] = bytes(ents)
            s.g = s

        def _array(s, slot):
            return 0x10, 3, 0x18

        def read(s, addr, n):
            return s.mem[addr][:n]

    live = FakeLive()
    got = live_items(live)
    out = []
    if [(it["name"], tuple(round(c, 1) for c in (it["pos"].x, it["pos"].y, it["pos"].z))) for it in got] != \
            [("rockets", (5.0, 6.0, 7.0))]:
        out.append(f"forge_items: {[(it['name'], it['pos']) for it in got]} (want the loose rockets only)")
    if live._names.get(0xE0000000) != "rockets":
        out.append(f"forge_items: the live reader's name for the rockets' tag {live._names} (want rockets)")
    # the ground weapons (snap.ground_weapons): a gun with no map placement under it is named by its own tag name, so
    # a bot out of ammo can go for it (they read "unknown" and were left out)
    fresh = FakeLive()
    seen = sorted(n for h, t, n, p in fresh.objects((2,)))
    if seen != ["dmr", "rockets", "sniper"]:
        out.append(f"forge_items: loose guns off any placement read {seen} (want dmr, rockets, sniper)")
    return out


def check_core_carry():
    from brain import invasion
    M = get_map("reach_70_boneyard")
    lay = invasion.layout(M["objects"])
    deliver = lay["phases"][3][0]
    rng = random.Random(1)
    bots = {i: Bot(i, 1, make_profile("strong", "objector", rng), M, rng=rng) for i in (1, 3, 5)}
    d = Director(1, M, bots, rng)
    start = lay["res"][1][1][0]
    ps = [PlayerState(1, 1, "car", start + Vec(1.0, 0.0, 0.0), has_flag=True)]
    ps += [PlayerState(i, 1, f"b{i}", start + Vec(0.0, i, 0.0)) for i in (3, 5)]
    ps += [PlayerState(10 + i, 0, f"e{i}", deliver + Vec(i, 0.0, 0.0)) for i in range(3)]
    snap = Snapshot(10.0, ps, mode="invasion", inv_phase=3, inv_attackers=1, inv_core=ps[0].pos, inv_core_carrier=1,
                    inv_delivery=deliver)
    d.assign_roles(10.0, snap)
    o = bots[1].order
    if o.role != "runner" or o.point is None or dist(o.point, deliver) > 1.0:
        return [f"core_carry: our core carrier's order {o.role} -> {o.point} (want runner to the delivery point {deliver})"]
    return []


def check_koth_company():
    out = []
    M = get_map("h3_construct")
    hill = M["points"]["mid"]
    for mate_by, want_hold in ((False, True), (True, False)):
        b = Bot(1, 0, make_profile("strong", "objector", random.Random(9)), M, random.Random(9))
        b.order, b.posture = Order("defender", hill), 0.5
        me = PlayerState(1, 0, "b", hill + Vec(6.0, 0.0, 0.0))
        foe = PlayerState(20, 1, "e", hill + Vec(0.5, 0.0, 0.0))
        ps = [me, foe] + ([PlayerState(2, 0, "m", hill + Vec(7.0, 1.0, 0.0))] if mate_by else
                          [PlayerState(2, 0, "m", hill + Vec(60.0, 0.0, 0.0))])
        b.per.beliefs[20] = Belief(foe.pos, Vec(), 60.0, True, "eyes")
        scores = {("objective", hill): 1.0}
        b.keep_role(scores, me, Snapshot(60.0, ps, mode="king", hill=hill, hill_r=3.0), [20])
        held = max(scores, key=scores.get)[0] == "hold"
        if held != want_hold:
            out.append(f"koth_company: a hill defender {'with' if mate_by else 'without'} a teammate beside it, theirs in "
                       f"the hill: {'held outside' if held else 'went in'} ({scores}) (want "
                       f"{'wait outside for company' if want_hold else 'go in'})")
    return out


def check_zone_rules():
    out = []
    M = get_map("reach_70_boneyard")
    z = M["points"]["mid"]
    b = bot(1, M, team=1)
    b.order = Order("defender", z)
    b.stay_at = None
    cases = (("invasion", dict(inv_attackers=1, inv_phase=1, inv_zones=[z], inv_zone_r=[2.0]), True),
             ("infection", dict(obj_zones=[(z, 3.0, None)]), True),
             ("king", dict(hill=z, hill_r=3.0), True),
             ("territories", dict(obj_zones=[(z, 3.0, None)]), False),
             ("invasion", dict(inv_attackers=0, inv_phase=1, inv_zones=[z], inv_zone_r=[2.0]), False))
    for mode, kw, want in cases:
        got = b.held_zone(Snapshot(0.0, [], mode=mode, **kw)) is not None
        if got != want:
            out.append(f"zone_rules: held_zone in {mode} {kw.get('inv_attackers', '')}: {got} (want {want}; Territories "
                       f"off since 240bb99: both teams' holders fought inside one zone and it stayed contested)")
    return out


def check_territories_posts():
    M = get_map("reach_30_settlement")
    from brain import modes
    lay = modes.layout(M["objects"]) if hasattr(modes, "layout") else None
    zones = [(p, r, t) for p, r, t in (lay or {}).get("territory", [])]
    if len(zones) < 3:
        return [f"territories_posts: Settlement territories read {zones} (want 5)"]
    bots = {i: bot(i, M) for i in range(1, 7)}
    d = Director(0, M, bots, random.Random(0))
    mid = M["points"]["mid"]
    ps = [PlayerState(i, 0, f"b{i}", mid + Vec(i, 0, 0)) for i in bots] + \
         [PlayerState(20 + k, 1, f"e{k}", mid + Vec(-20, k, 0)) for k in range(6)]
    snap = Snapshot(10.0, ps, mode="territories", obj_zones=[(p, r, -1) for p, r, t in zones])
    d.assign_roles(10.0, snap)
    on = sum(1 for b in bots.values() if b.order.point is not None
             and min(dist(b.order.point, p) for p, r, t in zones) < r_max(zones) + 0.5)
    if on < 2:
        return [f"territories_posts: 6 bots in Territories, {on} posted on a territory (roles "
                f"{sorted(d.roles.values())}) (want 2+)"]
    return []


def r_max(zones):
    return max(r for p, r, t in zones)


def check_release_gate():
    """make_release / build_installer refuse to build while tools/test_regressions.py fails (the gate runs first)."""
    import inspect
    import types
    sys.path.insert(0, HERE)
    import build_installer
    import make_release
    out, real = [], make_release.subprocess.run
    for code, want_stop in ((1, True), (0, False)):
        make_release.subprocess.run = lambda *a, **k: types.SimpleNamespace(returncode=code)
        try:
            make_release.regress_gate()
            stopped = False
        except SystemExit:
            stopped = True
        finally:
            make_release.subprocess.run = real
        if stopped != want_stop:
            out.append(f"release_gate: test_regressions exit {code}: build {'stopped' if stopped else 'went on'}")
    for mod in (make_release, build_installer):
        src = inspect.getsource(mod.main)
        first = src.find("regress_gate()")
        if first < 0 or (mod is make_release and first > src.find("build(")) or \
                (mod is build_installer and first > src.find("linux_bundle()")):
            out.append(f"release_gate: {mod.__name__}.main does not run the gate before building")
    return out


CHECKS = {"air_kill_zone": check_air_kill_zone, "air_clearance": check_air_clearance, "air_wall": check_air_wall,
          "banshee_take": check_banshee_take, "warthog_gunner": check_warthog_gunner, "ctf_carry": check_ctf_carry,
          "h2a_flag_use": check_h2a_flag_use, "forge_items": check_forge_items,
          "core_carry": check_core_carry, "koth_company": check_koth_company, "zone_rules": check_zone_rules,
          "territories_posts": check_territories_posts, "release_gate": check_release_gate}


def main():
    names = sys.argv[1:] or list(CHECKS)
    fails = []
    for n in names:
        try:
            got = CHECKS[n]()
        except Exception as e:           # (a crash in a check is that behavior's failure, the others still run)
            got = [f"{n}: crashed: {type(e).__name__}: {e}"]
        print(f"{'ok  ' if not got else 'FAIL'} {n}", flush=True)
        fails += got
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"reg core OK ({len(names)} checks)")


if __name__ == "__main__":
    main()
