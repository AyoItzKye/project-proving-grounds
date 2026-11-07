"""Vehicles v2 (brain/vehicles.py, bot.drive, Director.vehicle_orders): every game's vehicle names map to a kind (Halo 3's
"behemoth" is the Elephant), the door a bot walks to for the driver's seat and for the gun, the seat it takes from who
was in the vehicle, a gunner that shoots and never steers, a teammate sent to an empty Warthog gun with the driver
waiting, and a driver sent to pick up the flag carrier and run him home.

usage: python -I test_vehicles.py      -> "vehicles OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import vehicles  # noqa: E402
from brain.bot import Bot, Order  # noqa: E402
from brain.core import Vec, Snapshot, PlayerState, Action  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def main():
    fails = []
    want = {"vehicles\\warthog\\mp_warthog": "warthog", "rwarthog": "rwarthog", "warthog_gauss": "gauss",
            "ghost_mp": "ghost", "behemoth": "elephant", "olifaunt": "olifaunt", "banshee_mp": "banshee",
            "falcon": "falcon", "machinegun": "turret", "c gun turret_mp": "turret", "mongoose": "mongoose",
            "brute_chopper": "chopper", "scorpion": "scorpion", "security_camera": None, "forklift": None}
    for name, kind in want.items():
        if vehicles.kind_of(name) != kind:
            fails.append(f"{name!r} -> {vehicles.kind_of(name)}, want {kind}")
    v = dict(handle=7, kind="warthog", pos=(10.0, 10.0, 0.0), fwd=(1.0, 0.0, 0.0), occupied=False, riders=0, team=-1)
    d, g = Bot.seat_point(v, "driver"), Bot.seat_point(v, "gunner")
    if not (d.y > 10.5 and abs(d.x - 10.3) < 0.2) or not (g.x < 8.5 and abs(g.y - 10.0) < 0.1):
        fails.append(f"doors: driver {d}, gunner {g} (want front left and behind)")
    # a Falcon's two side guns: by its left door, then its right one
    fv = dict(v, kind="falcon")
    gl, gr = Bot.seat_point(fv, "gunner", side=1), Bot.seat_point(fv, "gunner", side=-1)
    if not (abs(gl.x - 10.0) < 0.1 and gl.y > 11.4) or not (abs(gr.x - 10.0) < 0.1 and gr.y < 8.6):
        fails.append(f"Falcon guns: left {gl}, right {gr} (want 1.6 u off each side door)")
    m = get_map("bloodgulch")
    rng = random.Random(3)
    prof = make_profile("strong", "rusher", rng)
    # a bot that got into a Warthog with its driver already in: the gun; it aims and never steers
    b = Bot(1, 0, prof, m, rng=rng)
    me = PlayerState(1, 0, "g", Vec(10, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=7)
    b.enter_riders = 1
    snap = Snapshot(1.0, [me], vehicles=[dict(v, occupied=True, riders=2, team=0)])
    act = Action()
    b.drive(1.0, 1 / 30, me, snap, act, lambda a, c, **k: c)
    if b.seat != "gunner" or act.forward != 0.0:
        fails.append(f"gunner: seat {b.seat}, forward {act.forward}")
    # the director: our person drives a Warthog alone: the nearest free bot is sent to its gun
    driver = PlayerState(0, 0, "person", Vec(10, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=7)
    walker = PlayerState(2, 0, "w", Vec(20, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)
    snap = Snapshot(2.0, [driver, walker], vehicles=[dict(v, occupied=True, riders=1, team=0)])
    wb = Bot(2, 0, prof, m, rng=rng)
    dr = Director(0, m, {2: wb}, random.Random(1))
    dr.vehicle_orders(2.0, snap, [wb])
    if wb.order.role != "ride" or wb.order.target != 7:
        fails.append(f"hop on the gun: order {wb.order}")
    # walking to the gun it looks where it goes (the view stayed frozen: live Boneyard, a bot walked 6.4 s to a
    # vehicle looking 168 degrees away): the Warthog 10 u behind it, after 2 s its view is round toward it
    import math
    from brain.core import wrap
    hog7 = dict(v, handle=7, pos=(60.0, -120.0, 0.2), occupied=True, riders=1, team=0)
    lw = PlayerState(2, 0, "w", Vec(70.0, -120.0, 0.2), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)
    lb = Bot(2, 0, prof, m, rng=random.Random(6))
    lb.order = Order("ride", Vec(60.0, -120.0, 0.2), target=7)
    goals = set()
    for t in range(60):
        sn = Snapshot(10.0 + t / 30, [lw], vehicles=[hog7])
        a = lb.think(10.0 + t / 30, 1 / 30, sn, lambda p, q: True, lambda p, q, **k: q, [])
        lw.yaw, lw.pitch = a.yaw, a.pitch
        goals.add(lb.goal[0])
    if "vehicle" not in goals or abs(wrap(lw.yaw - math.pi)) > 1.0:
        fails.append(f"walking to a vehicle behind it: goals {goals}, view {lw.yaw:.2f} rad (want about pi)")
    # our carrier on foot far from home, a bot driving a Warthog 20 u off: ferry him home
    carrier = PlayerState(3, 0, "c", Vec(60, -120, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", has_flag=True, is_bot=True)
    drv = PlayerState(4, 0, "d", Vec(70, -110, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=9, is_bot=True)
    hog = dict(handle=9, kind="warthog", pos=(70.0, -110.0, 0.0), fwd=(1, 0, 0), occupied=True, riders=1, team=0)
    snap = Snapshot(3.0, [carrier, drv], mode="ctf", vehicles=[hog])
    db, cb = Bot(4, 0, prof, m, rng=rng), Bot(3, 0, prof, m, rng=rng)
    db.seat = "driver"
    dr = Director(0, m, {4: db, 3: cb}, random.Random(2))
    dr.vehicle_orders(3.0, snap, [db, cb])
    if db.order.role != "ferry" or db.order.target != 3:
        fails.append(f"ferry: driver order {db.order}")
    # a whole decide with vehicles as the live snapshot gives them (positions are tuples; live, Boneyard: the brain
    # stopped on the first long trip with a Ghost about)
    fb = Bot(5, 0, make_profile("top", "flanker", rng), m, rng=rng)
    walker = PlayerState(5, 0, "f", Vec(40.0, -80.0, 0.3), Vec(), 0.0, 0.0, True, 1, 1, "ar")
    ghost = dict(handle=11, kind="ghost_mp", pos=(41.0, -81.0, 0.3), fwd=None, occupied=False, riders=0, team=-1)
    snap = Snapshot(5.0, [walker], vehicles=[ghost])
    fb.order = Order("runner", Vec(95.0, -159.0, 0.0))
    fd = Director(0, m, {5: fb}, random.Random(4))
    try:
        for t in range(60):
            fb.think(5.0 + t / 30, 1 / 30, snap, lambda a, b: True, lambda a, c, **k: c, fd.callouts, fd.item_up)
    except Exception as e:
        fails.append(f"decide() with a live-style vehicle list: {type(e).__name__}: {e}")
    # Reach seats (tools/vehicle_seats.py): driver 0, a Warthog's gun is its turret's seat 0, passengers by index
    if (vehicles.reach_seat("warthog", "driver"), vehicles.reach_seat("warthog", "gunner"),
            vehicles.reach_seat("warthog", "passenger"), vehicles.reach_seat("ghost_mp", "gunner"),
            vehicles.reach_seat("machinegun", "gunner")) != ((0, False), (0, True), (1, False), None, (0, False)):
        fails.append("reach seats")
    # a manned gun (Reach: the gunner rides the turret, read as gunner=True) wants no other gunner
    if vehicles.needs_gunner(dict(hog, riders=2, gunner=True), None) or not vehicles.needs_gunner(dict(hog, riders=1, gunner=False), None):
        fails.append("needs_gunner with the gun seat read")
    # a person honks from a Warthog: the nearest bot on foot takes the gun, our objective holder gets the passenger
    # seat, before any other bot
    person = PlayerState(0, 0, "person", Vec(10, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=7)
    near = PlayerState(2, 0, "n", Vec(13, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)
    hold = PlayerState(3, 0, "h", Vec(18, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True, has_flag=True)
    other = PlayerState(4, 0, "o", Vec(12, 11, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)
    snap = Snapshot(6.0, [person, near, hold, other], mode="ctf", honks=[7],
                    vehicles=[dict(v, occupied=True, riders=1, team=0, gunner=False)])
    bots = {k: Bot(k, 0, prof, m, rng=rng) for k in (2, 3, 4)}
    dr = Director(0, m, bots, random.Random(5))
    dr.honk_orders(6.0, snap, list(bots.values()), {k: snap.player(k) for k in bots})
    roles = {k: (b.order.role, b.order.target) for k, b in bots.items()}
    if roles[4] != ("ride", 7) or roles[3] != ("board", 7) or roles[2][0] == "board":
        fails.append(f"honk: {roles} (want 4 on the gun, the holder 3 in the passenger seat, 2 not)")
    # full Warthog, our holder beside it: the bot passenger gets out for him
    pas = PlayerState(5, 0, "p", Vec(10, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=7, is_bot=True)
    hold2 = PlayerState(3, 0, "h", Vec(12, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True, has_flag=True)
    snap = Snapshot(7.0, [person, pas, hold2], mode="ctf", vehicles=[dict(v, occupied=True, riders=3, team=0, gunner=True)])
    pb, hb = Bot(5, 0, prof, m, rng=rng), Bot(3, 0, prof, m, rng=rng)
    pb.seat = "passenger"
    dr = Director(0, m, {5: pb, 3: hb}, random.Random(6))
    dr.honk_orders(7.0, snap, [pb, hb], {5: pas, 3: hold2})
    if pb.order.role != "give_seat" or hb.order.role != "board":
        fails.append(f"give up the seat: passenger {pb.order.role}, holder {hb.order.role}")
    # the person's horn (a Nov 6 request: aimed at a bot, the horn calls it): the bot the person's view is
    # on gets the call over a nearer one, and the call holds its seconds (live_bots.horn_call)
    sys.path.insert(0, HERE)
    import live_bots
    live_bots.HORN.update(down=False, call=None)
    drv = PlayerState(0, 0, "person", Vec(10, 10, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=7)     # facing +x
    aimed = PlayerState(4, 0, "o", Vec(38, 12, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)     # 4 deg off his view
    side = PlayerState(2, 0, "n", Vec(12, 14, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)      # near, 63 deg off
    hv = [dict(v, occupied=True, riders=1, team=0, gunner=False)]
    got = [live_bots.horn_call(t, [drv, aimed, side], hv, 0, horn) for t, horn in ((1.0, False), (1.1, True), (1.2, True),
                                                                                  (5.0, False), (12.0, False))]
    if got[0] or got[1] != {7: 4} or got[3] != {7: 4} or got[4]:
        fails.append(f"horn: calls {got} (want none, then {{7: 4}} held past the release, gone after {live_bots.HORN_HOLD} s)")
    bots = {k: Bot(k, 0, prof, m, rng=rng) for k in (2, 4)}
    dr = Director(0, m, bots, random.Random(7))
    dr.honk_orders(6.0, Snapshot(6.0, [drv, aimed, side], honks=[7], honk_at={7: 4}, vehicles=hv),
                   list(bots.values()), {2: side, 4: aimed})
    if bots[4].order.role != "ride" or bots[2].order.role == "ride":
        fails.append(f"horn at bot 4: 4 {bots[4].order.role}, 2 {bots[2].order.role} (want 4 on the gun, 28 u off)")
    # a Falcon of ours set down: the bots on foot within LAND_CALL_R take both guns, one 15 u off does not; up in the
    # air it calls nobody (a Nov 6 request: bots get in an aircraft that lands close to them)
    from brain.director import LAND_CALL_R
    T = dr.terrain()
    gz = T.ground(30.0, -60.0)
    pilot = PlayerState(0, 0, "person", Vec(30, -60, gz + 0.3), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=9)
    feet = [PlayerState(k, 0, "f", Vec(30 + dx, -60, gz), Vec(), 0.0, 0.0, True, 1, 1, "ar", is_bot=True)
            for k, dx in ((2, 4.0), (4, 6.0), (6, 15.0))]
    for up, want in ((0.3, {2: "ride", 4: "ride", 6: None}), (9.0, {2: None, 4: None, 6: None})):
        bots = {k: Bot(k, 0, prof, m, rng=rng) for k in (2, 4, 6)}
        dr = Director(0, m, bots, random.Random(8))
        fal = [dict(fv, handle=9, pos=(30.0, -60.0, gz + up), occupied=True, riders=1, team=0, gunner=False)]
        for t in (10.0, 10.5):
            dr.honk_orders(t, Snapshot(t, [pilot] + feet, vehicles=fal), list(bots.values()), {q.id: q for q in feet})
        roles = {k: (b.order.role if b.order.role in ("ride", "board") else None) for k, b in bots.items()}
        if roles != want:
            fails.append(f"Falcon {up} u over the floor: orders {roles} (want {want}, LAND_CALL_R {LAND_CALL_R})")
    # a Falcon gunner by his objective gets out only once it is down (live Spire 20261106-185412 at 965 s: out 20 u up)
    for up, out in ((20.0, False), (0.3, True)):
        gb = Bot(3, 0, prof, m, rng=rng)
        gb.order = Order("runner", Vec(32, -60, gz))
        me = PlayerState(3, 0, "g", Vec(30, -60, gz + up), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=9)
        gb.enter_riders = 1
        fal = [dict(fv, handle=9, pos=(30.0, -60.0, gz + up), occupied=True, riders=2, team=0, gunner=True)]
        left = False
        for t in range(90):
            a = Action()
            gb.drive(1.0 + t / 30, 1 / 30, me, Snapshot(1.0 + t / 30, [me], vehicles=fal), a, lambda x, c, **k: c)
            left = left or a.action
        if left != out:
            fails.append(f"Falcon gunner {up} u up by his objective: got out {left} (want {out})")
    # a Reach Warthog gunner aims from the chaingun's mount, 0.536 u behind the origin (vehicles.GUN_FORWARD): at a man 10 u
    # to its left the view goes 3 deg back toward him from where the origin's line would (a Spire playtest, Nov 6: the
    # turret gunner's aim was still off to the right sometimes)
    from brain.bot import Belief
    gb = Bot(3, 0, make_profile("top", "rusher", random.Random(3)), m, rng=random.Random(3))
    gb.game, gb.enter_riders = "reach", 1
    foe = PlayerState(8, 1, "f", Vec(10, 20, 0), Vec(), 0.0, 0.0, True, 1, 1, "ar")
    yaw = 1.5708
    for t in range(60):
        me = PlayerState(3, 0, "g", Vec(10, 10, 0), Vec(), yaw, 0.0, True, 1, 1, "ar", vehicle=7)
        me.turret = "warthog_chaingun"
        gb.per.beliefs[8] = Belief(foe.pos, Vec(), 1.0 + t / 30, True, "eyes")
        a = Action()
        gb.drive(1.0 + t / 30, 1 / 30, me, Snapshot(1.0 + t / 30, [me, foe], vehicles=[dict(v, occupied=True, riders=2, team=0,
                                                                                           fwd=(1.0, 0.0, 0.0))]),
                 a, lambda x, c, **k: c)
        yaw = a.yaw
    want = math.atan2(10.0, 0.536)
    if abs(yaw - want) > abs(yaw - math.pi / 2) or abs(yaw - want) > 0.02:
        fails.append(f"Warthog gunner at a man 10 u to its left: yaw {yaw:.3f} (want {want:.3f}, from the chaingun's mount)")
    # the vehicle's own ground (Terrain.vnav): Boneyard's attacker spawn to the core run's end, every step on ground with
    # room for a Warthog until the last few units
    # (and Blood Gulch base to base: the flag under its base is off that ground, the drive ends beside it; Sidewinder's
    # flag sits 10+ u inside its base)
    from brain.maps import terrain
    for name, a, b, near in (("reach_70_boneyard", (226, 50, -6), (300, 107.5, -7), 10),   # (the delivery point: indoors)
                             ("bloodgulch", (29, -91, 0.2), (95.7, -159.4, -0.3), 8),
                             ("sidewinder", (28, -30, -4), (30, -46, -4), 16)):
        T = terrain(get_map(name))
        p, goal, off = Vec(*a), Vec(*b), 0
        for _ in range(300):                  # waypoint to waypoint, as a driver follows them
            w = T.vnav(p, goal)
            if (w - p).flat() < 0.05 or (p - goal).flat() < 6:
                break
            p = w
            off += not T.vroomy[T._node(p)]
        if (p - goal).flat() > near or off > 2:
            fails.append(f"vehicle path on {name} ended {p} ({off} hops off the vehicle's ground)")
    # a driver wedged: backs off twice, then holds Use to get out (one tick never left a Reach Warthog)
    wb = Bot(1, 0, prof, get_map("reach_70_boneyard"), rng=random.Random(2))
    wb.seat_for, wb.seat, wb.seat_since, wb.drive_to = 9, "driver", 0.0, Vec(300, 107, -7)
    me = PlayerState(1, 0, "d", Vec(240, 78.3, -8.4), Vec(), 0.0, 0.0, True, 1, 1, "ar", vehicle=9, is_bot=True)
    car = dict(handle=9, kind="warthog", pos=(240, 78.3, -8.4), occupied=True, riders=1, team=0, fwd=(1, 0, 0))
    seq = []
    for k in range(120):                      # 12 s at 10 Hz, never moving
        t = k * 0.1
        a = Action()
        wb.drive(t, 0.1, me, Snapshot(t, [me], vehicles=[car]), a, lambda x, y, **kw: y)
        seq.append("R" if a.forward < 0 else "E" if a.action else "D")
    s = "".join(seq)
    if s.count("RRRR") < 2 or "EEEEEEE" not in s or s.index("EEEEEEE") < s.rindex("RRRR"):
        fails.append(f"wedged driver: {s} (want backing off twice, then Use held)")
    # a Reach vehicle the scenario never places (Forge World's: the map variant's) is named by the map's tag names
    from brain.live import LiveReach
    from brain.vehicles import kind_of
    lr = LiveReach.__new__(LiveReach)
    lr._names, lr._vplacements = {}, []
    # (live Forge World: a vehicle's index can fall 2 past its own name, on its shader and texture)
    lr._tag_name_list = ["objects\\weapons\\rifle\\dmr\\dmr", "objects\\vehicles\\human\\warthog\\warthog",
                         "objects\\vehicles\\covenant\\ghost\\ghost", "objects\\vehicles\\human\\mongoose\\mongoose",
                         "objects\\vehicles\\human\\mongoose\\shaders\\goose",
                         "objects\\vehicles\\human\\mongoose\\bitmaps\\mongoose_diffuse"]
    lr._learn_vehicle(0xE0410001, (5.0, 5.0, 0.0))
    lr._learn_vehicle(0xE0420002, (9.0, 5.0, 0.0))
    lr._learn_vehicle(0xE0430000, (1.0, 5.0, 0.0))
    lr._learn_vehicle(0xE0440005, (3.0, 5.0, 0.0))
    got = {t: lr._names.get(t) for t in (0xE0410001, 0xE0420002, 0xE0430000, 0xE0440005)}
    if got != {0xE0410001: "warthog", 0xE0420002: "ghost", 0xE0430000: None, 0xE0440005: "mongoose"} \
            or kind_of("ghost") != "ghost":
        fails.append(f"Forge vehicles by tag name: {got}")
    # a rider's speed is its vehicle's (live_bots.snapshot): his raw position is relative to the vehicle, and the old
    # diff against last tick's vehicle place read about -30x his map position (the player's gunner shot along one
    # line)
    sys.path.insert(0, HERE)
    sys.path.insert(0, HERE)
    import live_bots

    class FakeLive:
        def __init__(s, car_at, rider_raw):
            s.car_at, s.rider_raw = car_at, rider_raw

        def players(s):
            return [dict(index=1, team=0, name="p", pos=s.rider_raw, aim=(1.0, 0.0, 0.0), shield=1.0, health=1.0,
                         weapon="ar", weapons=[], ammo=[], mag=[], vehicle=7, unit=0)]

        def flags(s, raw, stands=None):
            return []

        def objects(s, kinds):
            return [(7, 1, "objects\\vehicles\\warthog\\warthog", s.car_at)]
    snap = live_bots.snapshot(FakeLive((40.3, 25.0, 3.0), (0.1, 0.0, 0.5)), 1.0, {1: Vec(40.0, 25.0, 3.0)}, set())
    v = snap.players[0].vel
    if abs(v.x - 9.0) > 1e-6 or abs(v.y) > 1e-6 or abs(v.z) > 1e-6:
        fails.append(f"rider's speed {v} (want the Warthog's 9 u/s forward)")
    snap = live_bots.snapshot(FakeLive((40.3, 25.0, 3.0), (0.1, 0.0, 0.5)), 1.0, {1: Vec(36.0, 25.0, 3.0)}, set())
    if snap.players[0].vel.length() > 1e-6:
        fails.append(f"boarding tick speed {snap.players[0].vel} (want none: he jumped from his feet to the seat)")
    # an empty Warthog by a long trip is a ride (Halo 4 / H2A names, h2a_warthog: tag names)
    walker = PlayerState(9, 0, "bot", Vec(0.0, 0.0, 0.0), alive=True)
    if vehicles.ride_score(dict(kind="h2a_warthog", pos=(3.0, 0.0, 0.0), occupied=False), walker, Vec(80.0, 0.0, 0.0),
                           80.0) <= 0.0:
        fails.append("an empty H2A Warthog 3 u off a long trip is not a ride")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("vehicles OK")


if __name__ == "__main__":
    main()
