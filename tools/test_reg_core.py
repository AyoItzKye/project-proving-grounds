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


def check_h3_deployed():
    # Halo 3's thrown equipment for snap.deployed (#9): the deployed tag "objects\equipment\X\X" (not the X_equipment
    # pickup, not a grenade), its thrower's team from the player handle at +0xBC, kept first-seen time
    import struct
    from brain.live import LiveH3, NONE

    class FakeH3:
        deployed, _deployed_kind, _h3_names, DEPLOYED_KINDS, DEPLOYED_OWNER = (
            LiveH3.deployed, LiveH3._deployed_kind, LiveH3._h3_names, LiveH3.DEPLOYED_KINDS, LiveH3.DEPLOYED_OWNER)

        def __init__(s):
            s._h3_tag_names = ["objects\\equipment\\tripmine\\tripmine",
                               "objects\\equipment\\tripmine_equipment\\tripmine_equipment",
                               "objects\\weapons\\grenade\\frag_grenade\\frag_grenade"]
            s.mem, ents = {}, bytearray()
            for k, (tag_ix, owner, pos) in enumerate([(0, 0xEC7F0005, (1.0, 2.0, 3.0)), (1, NONE, (5.0, 5.0, 5.0)),
                                                      (2, 0xEC750005, (9.0, 9.0, 9.0))]):
                addr = 0x1000 + k * 0x100
                ents += struct.pack("<HBBIQQ", 0x1234, 0, 3, 0, 0, addr)
                head = bytearray(0xC0)
                struct.pack_into("<I", head, 0, 0xE0000000 | tag_ix)
                struct.pack_into("<3f", head, 0x50, *pos)
                struct.pack_into("<I", head, 0xBC, owner)
                s.mem[addr] = bytes(head)
            s.mem[0x10] = bytes(ents)
            s.g = s

        def _array(s, slot):
            return 0x10, 3, 0x18

        def read(s, addr, n):
            return s.mem[addr][:n]

    live = FakeH3()
    got = live.deployed([dict(index=5, team=1), dict(index=2, team=0)], 12.0)
    again = live.deployed([dict(index=5, team=1)], 15.0)
    want = [("trip_mine", (1.0, 2.0, 3.0), 1, 12.0)]
    seen = [(d["kind"], (d["pos"].x, d["pos"].y, d["pos"].z), d["team"], d["t"]) for d in got]
    out = [] if seen == want else [f"h3_deployed: read {seen} (want {want}: the thrown mine only, player 5's team)"]
    if [d["t"] for d in again] != [12.0]:
        out.append(f"h3_deployed: the mine's first-seen time {[d['t'] for d in again]} (want it kept, 12.0)")
    return out


def check_flood_shotgun():
    # Halo 4 Flood survivors: the magnum on a sword Flood on his way in, the shotgun out before he is in its reach
    # (Cliffside, trace 20261106-144807: 41% of the Flood that reached a survivor found the magnum out, swapped
    # to 1.3 s before; then at RUSH_R 10 u the Wraparound trace 20261106-160121: the shotgun out from 10 u, 0 shots at
    # 3-10 u, flagged as worse). Against a gunner the magnum still wins at Medium band (PvP unchanged)
    M = get_map("h4_z05_cliffside")
    out = []

    def held(tier, mine, foe_w, d, locked=False):
        b = Bot(1, 0, make_profile(tier, "rusher", random.Random(1)), M, random.Random(1))
        b.game = "h4"
        me = PlayerState(1, 0, "human", Vec(20, 0, 1), weapon=mine, weapons=["shotgun", "magnum"])
        me.ammo, me.mag = [24, 60], [6, 12]
        foe = PlayerState(6, 1, "foe", Vec(20 + d, 0, 1), weapon=foe_w)
        b.per.beliefs[6] = Belief(foe.pos, Vec(), 10.0, True, "eyes")
        b.switch_ok_at, b.notes = (11.5 if locked else 0.0), []      # (locked: swapped 0.5 s ago)
        w = b.choose_weapon(10.0, me, "fight", 6, Snapshot(10.0, [me, foe], mode="infection"))
        return mine if w < 0 else me.weapons[w]

    for tier in ("average", "top"):
        for d in (3.0, 4.5):
            if held(tier, "shotgun", "sword", d) != "shotgun":
                out.append(f"flood_shotgun: {tier}, shotgun out, a sword Flood {d} u off: swapped to the magnum")
        if held(tier, "shotgun", "sword", 9.0) != "magnum":
            out.append(f"flood_shotgun: {tier}, shotgun out, a sword Flood 9 u off: kept the shotgun (want the magnum)")
        if held(tier, "magnum", "sword", 8.0) != "magnum":
            out.append(f"flood_shotgun: {tier}, magnum out, a sword Flood 8 u off: swapped (want the magnum on him)")
        if held(tier, "magnum", "sword", 5.0, locked=True) != "shotgun":
            out.append(f"flood_shotgun: {tier}, magnum out 0.5 s after a swap, a sword Flood 5 u off: kept the magnum")
        if held(tier, "shotgun", "magnum", 7.0) != "magnum":
            out.append(f"flood_shotgun: {tier}, shotgun out, a magnum man 7 u off: kept the shotgun (want the magnum)")
    return out


def check_flood_sprint():
    # Halo 4's sprint and a sword (a Blood Cavern Flood playtest, Nov 6 16:48: shotgun out, a Flood 1.2-6 u off,
    # survivors held sprint 74% of those ticks, the view on the way, not on him, the gun silent): a gun never sprints at
    # a sword or hammer; at a gunner a close-range gun sprints in only on a move at him (the dodge's 45 deg diagonal
    # counts); a sword still sprints at a sword
    from brain.bot import WEAPON_RANGE
    from brain.equipment import Kit
    M = get_map("h4_ca_blood_cavern")
    out = []

    def wish(mine, foe_w, d, fwd, strafe, away=False):
        b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
        b.goal = ("fight", 6)
        me = PlayerState(1, 0, "me", Vec(0, 0, 0), weapon=mine)
        foe = PlayerState(6, 1, "foe", Vec(d, 0, 0), yaw=0.0 if away else math.pi, weapon=foe_w)
        x = dict(fight=True, target=foe, seen=[foe], travel=False, cracked=False, carrying=False, push_at=None)
        return b.kit.sprint_wish(b, x, me, Action(forward=fwd, strafe=strafe, yaw=0.0))

    cases = [("shotgun", "sword", 3.0, 1.0, 0.0, None), ("shotgun", "sword", 3.0, 0.0, 1.0, None),
             ("shotgun", "gravity_hammer", 4.0, 1.0, 0.0, None),
             ("shotgun", "assault_rifle", 3.0, 1.0, 0.0, "sprint to close the gap"),
             ("shotgun", "assault_rifle", 3.0, 0.7, 0.7, "sprint to close the gap"),
             ("shotgun", "assault_rifle", 3.0, 0.0, 1.0, None), ("shotgun", "assault_rifle", 3.0, -0.7, 0.0, None),
             ("sword", "sword", 3.0, 1.0, 0.0, "sprint to close the gap")]
    for mine, foe_w, d, f, st, want in cases:
        got = wish(mine, foe_w, d, f, st)
        if got != want:
            out.append(f"flood_sprint: {mine} v {foe_w} {d} u, stick ({f}, {st}): {got!r} (want {want!r})")
    far = max(8.0, WEAPON_RANGE.get("magnum", (5.0, 25.0))[1]) + 2.0
    if wish("magnum", "sword", far, 1.0, 0.0, away=True) is not None:
        out.append(f"flood_sprint: magnum after a sword {far} u off looking away: sprinted (want none)")
    if wish("magnum", "assault_rifle", far, 1.0, 0.0, away=True) != "sprint after him":
        out.append(f"flood_sprint: magnum after a gunner {far} u off looking away: no sprint (EQ-SPRINT-01)")
    if not Kit.moving_at(Action(forward=0.7, strafe=-0.7, yaw=0.0), PlayerState(1, 0, "me", Vec(0, 0, 0)), Vec(3, 0, 0)):
        out.append("flood_sprint: a diagonal run in (45 deg) read as not at him")
    return out


def check_glimpse_keep():
    # a defender's fight on a man lost from sight a moment (Blood Cavern, Nov 6 16:48, Zealot343: a tick behind a
    # pillar cut the fight 3.27 -> 1.32 under its post's 1.72 and it walked to its post, the Flood 4 u off): kept for
    # GLIMPSE_S, then the post's leash as before
    from brain.bot import GLIMPSE_S
    M = get_map("h4_ca_blood_cavern")
    out = []
    b = Bot(6, 0, make_profile("top", "grudger", random.Random(6)), M, random.Random(6))
    post = Vec(-11.06, -1.65, 0.62)
    b.order = Order("defender", post)
    me = PlayerState(6, 0, "me", Vec(1.15, -5.08, 0.5))
    foe = Vec(5.4, -5.9, 0.7)                      # 4.3 u off us, 17 u off the post
    b.per.beliefs[9] = Belief(foe, Vec(), 19.5, False, "eyes")
    for gone, kept in ((0.1, True), (GLIMPSE_S + 1.0, False)):
        b.per.last_seen[9] = 19.6 - gone
        scores = {("fight", 9): 3.27, ("objective", post): 1.72}
        b.keep_role(scores, me, Snapshot(19.6, [me], {}, mode="infection"), [])
        if (scores[("fight", 9)] == 3.27) != kept:
            out.append(f"glimpse_keep: out of sight {gone:.1f} s, 4 u off: fight {scores[('fight', 9)]:.2f} "
                       f"({'want it kept' if kept else 'want the leash'})")
    return out


def check_lift_one_way():
    # a low gravity lift's ride is one way (Blood Cavern flag, Nov 6 16:50: bots kept trying to enter the back
    # lift's exit end: its 2.8 u ride, read as a jump, was walked back down into its top)
    from brain.maps import anchor_launches
    from brain.terrain import jump_ways
    out = []
    lift = [{"kind": "lift", "name": "ca_cavern_back_lift", "pos": [-6.374, -0.126, 0.715]}]
    ride = {"take_off": [-5.65, 0.21, 1.11], "land": [-7.44, 0.12, 3.93], "apex": 4.46, "air_s": 1.85, "human": 1}
    hop = dict(ride, take_off=[-1.65, 0.21, 1.11], land=[-3.44, 0.12, 3.93])    # 4.7 u off the lift: no ride
    a, h = anchor_launches([ride, hop], lift)
    if jump_ways(a, None, 0.8) != "one-way" or not a.get("ride") or a["take_off"] != ride["take_off"]:
        out.append(f"lift_one_way: Blood Cavern's back lift ride: {jump_ways(a, None, 0.8)}, ride {a.get('ride')}, "
                   f"take-off {a['take_off']}")
    if h.get("ride"):
        out.append("lift_one_way: a climb 4.7 u off the lift marked a ride")
    return out


def check_spire_phase_links():
    # Spire's phase rules (a playtest run, Nov 6: the man cannons appear in phase 3 only; in phase 2 the spire lifts
    # take you to the lower building's roof): their people's links are closed before phase 3 and open in it
    from brain import invasion
    name = "reach_35_island/variants/v3977bae2"
    M = get_map(name)
    T = terrain(M)
    inv = invasion.layout(M["objects"])
    out = []
    a, b = Vec(-142.14, -391.64, -53.68), Vec(-167.44, -398.01, -24.33)      # man cannon 1's pad to its landing
    for ph, shut in ((2, True), (3, False)):
        invasion.phase_link_gates(T, inv, ph, name)
        cost = float(T._field(b, True, True, False, None, False)[T._node(a)])
        if (cost >= T.BARRIER_COST) != shut:
            out.append(f"spire_phase_links: phase {ph}, cannon 1's way up costs {cost:.0f} (want {'closed' if shut else 'open'})")
    invasion.phase_link_gates(T, inv, 3, name)
    return out


def check_spire_climbs():
    # the Spire core run: the attackers' runners spread over the ways up (a playtest tour, Nov 6: all of them funnelled
    # into one way up; 12 of 16 climbs by lift 2), and a gun on the way is no detour off it (the flag: the core was not
    # their priority)
    from brain import invasion
    from brain.director import Director
    name = "reach_35_island/variants/v3977bae2"
    M = get_map(name)
    out = []
    core = Vec(-178.24, -405.33, -22.9)
    starts = [Vec(-150, -395, -56.5), Vec(-158, -378, -57.5), Vec(-196, -385, -57.3), Vec(-185, -380, -57.0),
              Vec(-175, -396, -60.4), Vec(-170, -398, -60.4)]
    ps = [PlayerState(i + 1, 0, f"b{i}", p) for i, p in enumerate(starts)]
    bots = {p.id: bot(p.id, M) for p in ps}
    d = Director(0, M, bots, random.Random(2))
    snap = Snapshot(500.0, ps, mode="invasion")
    snap.inv_phase, snap.inv_attackers, snap.inv_core = 3, 0, core
    climbs = invasion.climbs_for(name)
    used = {}
    vias = [d.climb_via(bots[p.id], snap, core, used) for p in ps]
    ways = {min(range(len(climbs)), key=lambda k: dist(v[0], climbs[k])) for v in vias if v}
    if len(ways) < 3:
        out.append(f"spire_climbs: 6 runners took {len(ways)} ways up (want 3+): {[v[0] if v else None for v in vias]}")
    rb = bots[1]
    rb.order, rb.grab_point = Order("runner", core), core
    me = ps[0]
    gun = me.pos + Vec(3.0, 0, 0)          # (3 u: a detour; one at his feet, under PRESS_ITEM_R, is taken)
    scores = {("item", gun): 2.1, ("objective", core): 2.0}     # (live: 2.1 over 1.82)
    rb.keep_role(scores, me, snap, [])
    if scores[("item", gun)] >= scores[("objective", core)]:
        out.append(f"spire_climbs: a gun 3 u off the core run scores {scores[('item', gun)]:.2f} over the run's "
                   f"{scores[('objective', core)]:.2f}")
    return out


def check_nade_clear():
    # no grenade with a teammate (a person too) within 4 u of where it goes, or walking into it within a second (the
    # Spire flag Nov 6, grenade team kills; replayed, 29 of the 51
    # deaths with an own-team throw aimed by them in the 3 s before had every such throw held)
    me = PlayerState(1, 0, "me", Vec(0, 0, 0))
    at = Vec(10, 0, 0)
    out = []
    for mate, want in ((PlayerState(0, 0, "person", Vec(11.2, 0, 0)), False),
                       (PlayerState(2, 0, "b", Vec(15, 0, 0), vel=Vec(-2.0, 0, 0)), False),
                       (PlayerState(2, 0, "b", Vec(16, 0, 0)), True),
                       (PlayerState(3, 1, "foe", Vec(10.5, 0, 0)), True)):
        got = Bot.nade_clear(me, at, Snapshot(1.0, [me, mate]))
        if got != want:
            out.append(f"nade_clear: {mate.name} at {mate.pos} moving {mate.vel}: {got} (want {want})")
    return out


def check_corner_drop():
    # a diagonal drop squeezing between two cells shut at our height is priced as a lid (Blood Cavern playtests,
    # Nov 6: six survivors pushed 1660 rows at (-4.7, 2.5, 3.9) on the drop to the new hold by the back lift)
    from brain.terrain import LID_COST
    T = terrain(get_map("h4_ca_blood_cavern"))
    out = []
    l, j, i = T._node(Vec(-4.83, 2.67, 3.55))
    lb, jb, ib = T._node(Vec(-4.58, 2.92, 0.71))
    a, b = (l * T.nh + j) * T.nw + i, (lb * T.nh + jb) * T.nw + ib
    w = T.graph[a, b]
    if w < LID_COST:
        out.append(f"corner_drop: the diagonal drop past the parapet costs {w:.1f} (want {LID_COST}+)")
    path = T.path_ahead(Vec(-4.67, 2.48, 3.93), Vec(-4.33, -2.33, 0.68), n=400, jump=True, human=True)
    if any(abs(p.x + 4.58) < 0.13 and abs(p.y - 2.92) < 0.13 and p.z < 1.5 for p in path[:3]):
        out.append("corner_drop: the route to the back-lift hold still drops past the parapet first")
    return out


def check_escort_stops():
    # the map-free escort brain ends with its match (live Nov 6, installed s180: an Installation 04 escort brain lived on
    # into the next match and drove its bots beside that match's brain; botcore ends play.py, not this child): reads that
    # fail for 3 s end it, as live_bots
    import time
    import brain.live as bl
    import escort_bots
    import botctl

    class Gone:
        def __init__(s):
            pass

        def players(s):
            raise RuntimeError("no Halo: Reach game thread")

    saved = bl.LiveReach, botctl.shm, sys.argv, sys.stdout
    bl.LiveReach, botctl.shm = Gone, lambda: None
    sys.argv = ["escort_bots.py", "8", "--game", "reach"]
    sys.stdout = open(os.devnull, "w")
    t = time.time()
    try:
        escort_bots.main()
    finally:
        sys.stdout.close()
        bl.LiveReach, botctl.shm, sys.argv, sys.stdout = saved
    took = time.time() - t
    return [] if took < 5.0 else [f"escort_stops: the escort brain ran {took:.1f} s with the game gone (want under 5)"]


def check_ff_sides():
    # Reach Firefight's AI by side (GitHub #12 "bots on the elites side will kill AI allies"): the unit's side byte
    # +0x1CA, live Beachhead Versus Nov 6: Spartan players 1, Elite players 7, the Covenant 3. The Covenant go on the
    # Elite players' team, human-side AI on the Spartans', and with no one playing Elites the Covenant stay -1
    import struct
    from brain.live import LiveReach, NONE

    class FakeReach:
        ai_units, UNIT_TEAM, ACTOR_AT, ACTOR_CHARACTER = LiveReach.ai_units, LiveReach.UNIT_TEAM, LiveReach.ACTOR_AT, LiveReach.ACTOR_CHARACTER
        DEAD_AT = LiveReach.DEAD_AT                      # (the destroyed bit, GitHub #29: zero here, every unit alive)

        def ai_rank(s, u):
            return None                                  # (no actor array here: brain/live.py ai_rank)

        def __init__(s, sides):
            s.mem, ents, s.g = {}, bytearray(), s
            for k, (side, player) in enumerate(sides):
                addr = 0x1000 + k * 0x400
                e = bytearray(0x18)
                struct.pack_into("<H", e, 0, 0x1234)
                struct.pack_into("<Q", e, 0x10, addr)
                ents += e
                u = bytearray(0x214)
                struct.pack_into("<I", u, 0x14, NONE)
                struct.pack_into("<I", u, 0x1D0, player)
                u[0x1CA] = side
                s.mem[addr] = bytes(u)
            s.mem[0x10], s.n = bytes(ents), len(sides)

        def _array(s, slot):
            return 0x10, s.n, 0x18

        def read(s, addr, n):
            return s.mem[addr][:n]

        def _vitals(s, *a, **kw):
            return 1.0, 1.0

    h = lambda i: (0x1234 << 16) | i
    versus = FakeReach([(1, 0), (7, 1), (3, NONE), (2, NONE)])     # a Spartan, an Elite (players 0, 1), two AI
    got = [d["team"] for d in versus.ai_units([dict(unit=h(0), team=0), dict(unit=h(1), team=1)])]
    out = [] if got == [1, 0] else [f"ff_sides: Versus AI teams {got} (want [1, 0]: the Covenant with the Elite, "
                                    f"the human AI with the Spartan)"]
    classic = FakeReach([(1, 0), (3, NONE)])
    got = [d["team"] for d in classic.ai_units([dict(unit=h(0), team=0)])]
    if got != [-1]:
        out.append(f"ff_sides: Classic, Spartans only: Covenant team {got} (want [-1], everyone's enemy)")
    return out


def check_mine_keep_clear():
    # the live frame (Rat's Nest Team King s178, trace 20261106-070330, 168.5-169.3 s): bot 11 backed toward team 1's
    # trip mine at (-4.5, -5.4) facing away (yaw 2.249, forward -1), turning as it went, and set it off at 2.0 u (its
    # shield gone). Kit.steer_clear sidestepped by the old facing and only inside 2.0 u. Replayed: 1.2 s at 3 u/s, the
    # command's own facing turning, the mine must stay outside its reach (2.3 u: it went off at 2.0)
    from brain.equipment import Kit
    kit = Kit(make_profile("top", "objector", random.Random(11)), "h3")
    mine = Vec(-4.5, -5.4, -9.4)
    pos, yaw = Vec(-7.29, -3.46, -9.4), 2.249
    closest = 99.0
    for k in range(36):                       # 30 Hz, the brain's tick
        me = PlayerState(11, 0, "b11", pos, yaw=yaw)
        snap = Snapshot(168.5 + k / 30.0, [me], mode="king")
        snap.deployed = [dict(kind="trip_mine", pos=mine, team=1, t=161.9)]
        turn = yaw - 0.035 * k                # (it was turning toward the hill: 2.249 -> 1.224 in 0.3 s live)
        act = Action(forward=-1.0, yaw=turn)
        kit.steer_clear(me, snap, act)
        c, sn = math.cos(act.yaw), math.sin(act.yaw)
        wx, wy = act.forward * c - act.strafe * sn, act.forward * sn + act.strafe * c
        n = math.hypot(wx, wy) or 1.0
        pos = Vec(pos.x + wx / n * 0.1, pos.y + wy / n * 0.1, pos.z)
        yaw = act.yaw
        closest = min(closest, dist(pos, mine))
    # inside the keep-out, pushing into a wall (168.88 s live: 2.55 u off it, the command north-east at 0.6, the body
    # sliding south-east along the wall onto it): the command goes straight out, away from the mine
    me = PlayerState(11, 0, "b11", Vec(-6.73, -4.16, -9.4), yaw=0.899)
    snap = Snapshot(168.9, [me], mode="king")
    snap.deployed = [dict(kind="trip_mine", pos=mine, team=1, t=161.9)]
    act = Action(forward=0.6, yaw=0.913)
    kit.steer_clear(me, snap, act)
    c, sn = math.cos(act.yaw), math.sin(act.yaw)
    wx, wy = act.forward * c - act.strafe * sn, act.forward * sn + act.strafe * c
    ox, oy = me.pos.x - mine.x, me.pos.y - mine.y
    if (wx * ox + wy * oy) / ((math.hypot(wx, wy) * math.hypot(ox, oy)) or 1.0) < 0.95:
        return [f"mine_keep_clear: 2.55 u from the mine the step is ({wx:.2f}, {wy:.2f}), not away from it"]
    return [] if closest > 2.3 else [f"mine_keep_clear: came {closest:.2f} u from an enemy trip mine (want 2.3+)"]


def check_mine_route():
    # Terrain.nav round an enemy mine (Kit.hazards, 3.0 u) on Rat's Nest's own nav: from bot 11's live start
    # (-7.29, -3.46) to the hill way point it walked to (-3.6, -0.1), a mine put on the plain way's middle. Walked
    # along the waypoints: the plain way goes over it, the hazard way round it and still gets there. (Its live mine lay
    # 3.17 u off this way: that bot slid onto it along a wall, Kit.steer_clear's push-out, check mine_keep_clear)
    T = terrain(get_map("h3_armory"))
    goal = Vec(-3.6, -0.1, -9.4)

    def walk(hazards, mine=None):
        p, closest, path = Vec(-7.29, -3.46, -9.4), 99.0, []
        for _ in range(300):
            w = T.nav(p, goal, hazards=hazards)
            if w is None or dist(p, goal) < 0.6:
                break
            d = Vec(w.x - p.x, w.y - p.y, 0.0)
            n = math.hypot(d.x, d.y)
            if n < 1e-6:
                break
            p = Vec(p.x + d.x / n * 0.2, p.y + d.y / n * 0.2, w.z)
            path.append(p)
            if mine is not None:
                closest = min(closest, math.hypot(p.x - mine.x, p.y - mine.y))
        return closest, dist(p, goal), path

    _, _, plain = walk(())
    if len(plain) < 6:
        return [f"mine_route: the plain way is {len(plain)} steps (want a real walk)"]
    mine = plain[len(plain) // 2]
    round_, left, _ = walk(((round(mine.x, 1), round(mine.y, 1), round(mine.z, 1), 3.0),), mine)
    if round_ < 2.3 or left > 1.0:          # (it went off at 2.0 u live; the 3 u nodes, cut a little at corners)
        return [f"mine_route: with a mine on the way at {mine}: {round_:.2f} u off it, {left:.2f} u from the goal "
                f"(want 2.3+ and there)"]
    return []


def check_dry_rearm():
    # the live think row (Beachhead Firefight Nov 6, trace 20261106-074751, bot 3 dry from 159 s: grenade launcher and
    # magnum both 0): its scores, fight 3.45 over the guns lying 6 u off at 3.0, replayed through Bot.dry_fights: the
    # gun wins; a man at arm's length (a melee) still wins; with rounds left nothing changes
    M = get_map("reach_ff50_park")
    at = Vec(-162.0, 58.0, -33.5)
    out = []
    for foe_off, ammo, want in ((3.45, [0, 0], "item"), (1.5, [0, 0], "fight"), (3.45, [4, 0], "fight")):
        b = bot(3, M, tier="top", style="rusher")
        me = PlayerState(3, 0, "b3", at, weapon="grenade_launcher", weapons=["grenade_launcher", "magnum"], ammo=ammo)
        b.per.beliefs[1200] = Belief(at + Vec(foe_off, 0.0, 0.0), Vec(), 170.0, True, "eyes")
        scores = {("objective", Vec(-160.2, 59.1, -33.5)): 1.72, ("fight", 1200): 3.45,
                  ("item", Vec(-167.0, 56.2, -33.5)): 3.0}
        b.dry_fights(scores, me)
        got = max(scores, key=scores.get)[0]
        if got != want:
            out.append(f"dry_rearm: rounds {ammo}, the man {foe_off} u off: best {got} {scores} (want {want})")
    return out


def check_ff_dlc():
    # Reach's DLC Firefight maps lie under levels\dlc (live Unearthed: levels\dlc\ff_unearthed\ff_unearthed): read as
    # Firefight, and play.py sends Firefight with no map data to the escort brain instead of quitting (no bots joined)
    from brain.live import LiveReach

    class Fake:
        firefight, CACHE_HEADER = LiveReach.firefight, 0

        def __init__(s, path):
            s.path, s.g = path, s
            s.base = 0

        def read(s, addr, n):
            return (s.path + bytes(128))[:n]

    out = []
    # (Installation 04, live Nov 6 s179: levels\dlc\cex_ff_halo\cex_ff_halo, read as not Firefight: no bots; and every
    # Reach PvP map the project knows stays PvP)
    pvp = [d[6:] for d in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "maps"))
           if d.startswith("reach_") and not d.startswith("reach_ff")]
    for path, want in ((b"levels\\dlc\\ff_unearthed\\ff_unearthed", True), (b"levels\\firefight\\ff50_park\\ff50_park", True),
                       (b"levels\\dlc\\cex_ff_halo\\cex_ff_halo", True),
                       *((f"levels\\dlc\\{n}\\{n}".encode(), False) for n in pvp)):
        if Fake(path).firefight() != want:
            out.append(f"ff_dlc: {path} read as Firefight {not want} (want {want})")
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "play.py"), encoding="utf-8").read()
    if 'escort = not have_map and (o.game == "odst" or (o.game == "reach" and' not in src:
        out.append("ff_dlc: play.py does not send Reach Firefight without map data to the escort brain")
    return out


def check_melee_swing():
    # the live frame (Beachhead Firefight Nov 6, trace 20261106-075931, 83.3 s): bot 1 swung at Elite 1353 1.22 u off
    # with bot 3 first in the swing, 1.13 u off 19 deg to the side. Replayed through Bot.melee_check: held; held too with
    # the Elite dead (the swing at the air after the kill); kept with only the Elite there
    M = get_map("reach_ff50_park")
    b = bot(1, M, tier="top", style="rusher")
    me = PlayerState(1, 0, "b1", Vec(-170.06, 59.56, -33.5))
    mate = PlayerState(3, 0, "b3", Vec(-170.63, 58.58, -33.5))
    elite = PlayerState(1353, -1, "ai", Vec(-170.99, 58.77, -33.43))
    out = []
    for who, want in (([me, mate, elite], False), ([me, mate], False), ([me, elite], True)):
        act = Action(yaw=-2.428, melee=True)
        b.melee_check(me, Snapshot(83.3, who, mode="firefight"), act)
        if act.melee != want:
            out.append(f"melee_swing: with {[p.id for p in who[1:]]} the press {'kept' if act.melee else 'held'} "
                       f"(want {'kept' if want else 'held'})")
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
          "h2a_flag_use": check_h2a_flag_use, "forge_items": check_forge_items, "h3_deployed": check_h3_deployed,
          "ff_sides": check_ff_sides, "escort_stops": check_escort_stops, "flood_shotgun": check_flood_shotgun,
          "flood_sprint": check_flood_sprint, "glimpse_keep": check_glimpse_keep, "lift_one_way": check_lift_one_way,
          "corner_drop": check_corner_drop, "spire_phase_links": check_spire_phase_links, "spire_climbs": check_spire_climbs,
          "nade_clear": check_nade_clear,
          "mine_keep_clear": check_mine_keep_clear, "mine_route": check_mine_route, "dry_rearm": check_dry_rearm, "ff_dlc": check_ff_dlc, "melee_swing": check_melee_swing,
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
