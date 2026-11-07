"""The Nov 7 pass: the collaborator's fork ported (a sniper kept while it has a shot, magazines learned in fights, the
animated head as the aim point), the DMR over the AR (Reach, Halo 4), the Spire run's flags (the blitz keeps the climb
spread and the vehicle calls, a climb kept to its pad, a pilot's wait not read as stuck, a pilot waiting for a person,
a Falcon onto the spire top from outside), Halo 4's Mantis (read as a vehicle, rockets, the stomp) and the bot adds that
a paused game swallowed (botctl.idle, play.add_bot).

usage: python -I test_nov7_fixes.py      -> "nov 7 fixes OK"
"""
import math
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
from brain import invasion, vehicles  # noqa: E402
from brain.bot import Bot, Order, head_point  # noqa: E402
from brain.core import Action, PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.live import LiveH4F  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

SPIRE = "reach_35_island/variants/v3977bae2"
CORE = Vec(-178.24, -405.33, -22.9)


def bot(i, m, team=0, tier="top"):  # (a fresh tick: notes as think starts them)
    b = Bot(i, team, make_profile(tier, "rusher", random.Random(i)), m, random.Random(i))
    b.notes = []
    return b


def ps(i, pos, team=0, **kw):
    return PlayerState(i, team, f"p{i}", pos, **kw)


def main():
    fails = []
    m = get_map("reach_35_island")
    b = bot(1, m)
    b.game = "reach"

    # a sniper with 4 rounds is not "low" (it went for the nearest AR); dry, it rearms
    me = ps(1, Vec(0, 0, 0), weapon="sniper", weapons=["sniper", "magnum"], ammo=[4, 24], mag=[4, 8])
    b.ammo_max = {"sniper": 16}
    snap = Snapshot(10.0, [me])
    snap.ground_weapons = [("assault_rifle", Vec(3, 0, 0))]
    if b.rearm_point(me, snap) is not None:
        fails.append("a sniper with 4 rounds went for another gun")
    me.ammo = [0, 0]
    if b.rearm_point(me, snap) is None:
        fails.append("a dry bot did not rearm")

    # magazines learned whatever the tick, every gun
    me.weapons, me.mag = ["dmr", "assault_rifle"], [15, 32]
    b.learn_mags(me)
    if b.mag_max != {"dmr": 15, "assault_rifle": 32}:
        fails.append(f"magazines learned: {b.mag_max}")

    # the DMR over the AR: in hand at every range, never dropped for one, the AR given up for one
    me = ps(1, Vec(0, 0, 0), weapon="assault_rifle", weapons=["dmr", "assault_rifle"], ammo=[60, 300], mag=[15, 32])
    foe = ps(9, Vec(3, 0, 0), team=1)
    b.per.beliefs[9] = type("B", (), dict(pos=foe.pos, vel=Vec(), t=10.0, seen=True))()
    b.switch_ok_at = 0.0
    snap = Snapshot(10.0, [me, foe])
    k = b.choose_weapon(10.0, me, "fight", 9, snap)
    if k != 0:
        fails.append(f"Reach, DMR and AR, a man 3 u off: slot {k} (want the DMR, 0)")
    if b.drop_slot(["dmr", "magnum"], [60, 24], "assault_rifle") != 1:
        fails.append("an AR picked up dropped the DMR")
    if b.drop_slot(["assault_rifle", "magnum"], [300, 24], "dmr") != 0:
        fails.append("a DMR picked up kept the AR")
    b3 = bot(3, get_map("h3_construct") if os.path.isdir(os.path.join(HERE, "..", "maps", "h3_construct")) else m)
    b3.game = "h3"
    if b3.drop_slot(["dmr", "magnum"], [60, 24], "assault_rifle") == 1 and False:
        pass                                          # (Halo 3: no rule, values decide)

    # the animated head as the aim point: Reach's head on the believed place; Halo 4's only with our view point
    t = ps(9, Vec(10, 0, 0), team=1, head_pos=Vec(10.1, 0.05, 0.58))
    o, p = head_point(ps(1, Vec(0, 0, 0)), t, Vec(11, 0, 0))
    if o is not None or p is None or abs(p.x - 11.1) > 1e-6 or abs(p.z - 0.58) > 1e-6:
        fails.append(f"Reach head point: {o}, {p}")
    t4 = ps(9, Vec(10, 0, 0.38), team=1, head_pos=Vec(10, 0, 0.63), view_pos=Vec(10, 0, 0.98))
    if head_point(ps(1, Vec(0, 0, 0.38)), t4, t4.pos) != (None, None):
        fails.append("Halo 4: a head used without our own view point")
    me4 = ps(1, Vec(0, 0, 0.38), view_pos=Vec(0, 0, 0.98))
    o, p = head_point(me4, t4, t4.pos)
    if o is None or abs(o.z - 0.98) > 1e-6 or abs(p.z - 0.63) > 1e-6:
        fails.append(f"Halo 4 head pair: {o}, {p}")
    if head_point(ps(1, Vec(0, 0, 0), vehicle=5), t, t.pos) != (None, None):
        fails.append("a head point from a vehicle")

    # a climb via is kept to its pad (not dropped 5 u short, nor for being nearer the core than it)
    M = get_map(SPIRE)
    rb = bot(2, M)
    c3 = invasion.climbs_for(SPIRE)[4]                 # cannon 3
    rb.order, rb.via_left = Order("runner", CORE, via=(c3,)), [c3]
    near = ps(2, Vec(c3.x + 3.0, c3.y, c3.z))          # 3 u off it, nearer the core than its start
    if rb.objective_point(near) != c3:
        fails.append("a cannon via dropped 3 u short of the pad")
    rb.now = 10.0                                       # on the pad: held there for the launch, given up after 2.5 s
    pad = ps(2, Vec(c3.x + 0.5, c3.y, c3.z))
    if rb.objective_point(pad) != c3:
        fails.append("a cannon via dropped on reaching its pad (turned away before the launch)")
    rb.now = 11.5
    if rb.objective_point(pad) != c3:
        fails.append("a cannon via dropped after 1.5 s on its pad")
    rb.now = 13.0
    if rb.objective_point(pad) != CORE:
        fails.append("a cannon via kept 3 s on a pad that never launched")
    rb.via_left = [c3]
    if rb.objective_point(ps(2, Vec(c3.x + 6.0, c3.y, c3.z + 8.0))) != CORE:
        fails.append("a cannon via not passed once launched")
    lane = Vec(-150.0, -380.0, -57.0)                   # an ordinary via: dropped within 5 u, as before
    rb.via_left = [lane]
    if rb.objective_point(ps(2, Vec(-152.0, -380.0, -57.0))) != CORE:
        fails.append("an ordinary via kept within 5 u")

    # the blitz: Invasion phase 3 goers spread over the ways up; a landed aircraft calls them
    starts = [Vec(-150, -395, -56.5), Vec(-158, -378, -57.5), Vec(-196, -385, -57.3), Vec(-185, -380, -57.0),
              Vec(-175, -396, -60.4), Vec(-170, -398, -60.4)]
    pl = [ps(i + 1, p) for i, p in enumerate(starts)]
    bots = {p.id: bot(p.id, M) for p in pl}
    d = Director(0, M, bots, random.Random(2))
    snap = Snapshot(500.0, pl, mode="invasion")
    snap.inv_phase, snap.inv_attackers, snap.inv_core, snap.inv_core_carrier = 3, 0, CORE, None
    d.blitz = dict(t0=499.0, target=CORE, rally=CORE, why="core", go=499.0, prongs=(), regather=CORE,
                   waits={p.id: -1.0 for p in pl})       # (the wave released: in with it)
    d.desperate = lambda now, snap: (CORE, "core")
    d.blitz_tick(500.0, snap)
    climbs = invasion.climbs_for(SPIRE)
    ways = {min(range(len(climbs)), key=lambda k: (bb.order.via[0] - climbs[k]).length())
            for bb in bots.values() if bb.order.via}
    if len(ways) < 3:
        fails.append(f"blitz goers: {len(ways)} ways up (want 3+)")
    fal = dict(handle=77, kind="falcon", pos=(-181.0, -383.0, -57.0), occupied=True, riders=1, team=0, up=(0, 0, 1))
    person = ps(0, Vec(-181.0, -383.0, -57.0), vehicle=77, is_bot=False)
    snap2 = Snapshot(501.0, [person] + pl, mode="invasion", vehicles=[fal])
    snap2.inv_phase, snap2.inv_attackers, snap2.inv_core, snap2.inv_core_carrier = 3, 0, CORE, None
    d.air_track = {77: [(500.5, Vec(-181.0, -383.0, -57.0))]}
    d.terrain = lambda: type("T", (), dict(height_over=lambda self, x, y, z: 0.2))()
    d.blitz["ids"] = set(bots)
    d.assign_roles(501.0, snap2)
    riders = [bb.id for bb in bots.values() if bb.order.role == "ride" and bb.order.target == 77]
    if not riders:
        fails.append("a landed Falcon called nobody while the whole team was in a blitz")
    elif any(bb.id in riders for bb in d.blitz_team(snap2)):
        fails.append("a bot called to a seat stayed in the blitz")

    # a pilot's wait is not being stuck; it waits for a person beside its aircraft
    pb = bot(4, M)
    pme = ps(4, Vec(-174.5, -386.6, -60.0), vehicle=77)
    pb.drive_pos, pb.drive_since = Vec(-174.5, -386.6, -60.0), 100.0
    pb.hold_for_crew(106.0, pme, Action(), True)
    if pb.drive_since != 106.0:
        fails.append("waiting for crew still counted as stuck")
    pb.seat_since = 105.0
    sp = vehicles.spec("falcon")
    near_person = ps(0, Vec(-170.0, -384.0, -60.0), is_bot=False)
    fal2 = dict(fal, pos=(-174.5, -386.6, -60.0))
    snap3 = Snapshot(106.0, [pme, near_person], vehicles=[fal2])
    if not pb.crew_coming(106.0, pme, fal2, sp, snap3, []):
        fails.append("a pilot left with a person standing 5 u off")
    near_person.is_bot = True
    if pb.crew_coming(106.0, pme, fal2, sp, snap3, []):
        fails.append("a pilot waited for a bot standing still 5 u off")

    # onto the spire top from outside: under the top, straight out, level; just outside, up first; over the top, free
    fb = bot(5, M)
    fb.air_dest = CORE
    env = vehicles.envelope("reach_35_island")
    ax, ay = env["axis"]

    def steer(pos, yaw=0.0):
        me5 = ps(5, pos, vehicle=77)
        act = Action()
        act.yaw, act.forward, act.pitch = yaw, 1.0, 0.0
        fb.spire_approach(me5, act, Snapshot(1.0, [me5], vehicles=[dict(fal, pos=(pos.x, pos.y, pos.z))]))
        return act
    a = steer(Vec(ax + 4.0, ay + 1.0, -30.0), yaw=math.pi)
    out = math.atan2(1.0, 4.0)
    if abs(math.remainder(a.yaw - out, 2 * math.pi)) > 0.05 or a.vertical != 0.0 or a.pitch != 0.0:
        fails.append(f"under the top: yaw {a.yaw:.2f} (out {out:.2f}), vertical {a.vertical}, pitch {a.pitch}")
    a = steer(Vec(ax + 12.0, ay, -35.0), yaw=math.pi)
    if a.forward != 0.0 or a.vertical != 1.0:
        fails.append(f"just outside the top's edge heading in: forward {a.forward}, vertical {a.vertical}")
    a = steer(Vec(ax + 30.0, ay, -40.0), yaw=math.pi)
    if a.forward != 1.0:
        fails.append("far out: steered by spire_approach")

    # Halo 4's Mantis: its giants are vehicles there (H2A not); the stomp and the rockets
    lv = LiveH4F.__new__(LiveH4F)
    lv.g = type("G", (), dict(dll="halo4.dll"))()
    if lv.VEHICLE_TYPES != (1, 13):
        fails.append(f"Halo 4 vehicle types {lv.VEHICLE_TYPES}")
    lv.g.dll = "groundhog.dll"
    if lv.VEHICLE_TYPES != (1,):
        fails.append(f"H2A vehicle types {lv.VEHICLE_TYPES}")
    if vehicles.kind_of("storm_mantis") != "mantis" or not vehicles.driver_armed(dict(kind="storm_mantis")):
        fails.append("the Mantis: not read as an armed mantis")
    mb = bot(6, get_map("h4_z11_valhalla") if os.path.isdir(os.path.join(HERE, "..", "maps", "h4_z11_valhalla")) else m)
    mv = dict(handle=88, kind="storm_mantis", pos=(0.0, 0.0, 0.0), occupied=True, riders=1, team=0)
    mme = ps(6, Vec(0, 0, 0), vehicle=88)
    close = ps(9, Vec(3.0, 0, 0), team=1)
    act = Action()
    bel = type("B", (), dict(pos=close.pos, vel=Vec(), t=1.0, seen=True))()
    mb.mantis_weapons(1.0, mme, mv, Snapshot(1.0, [mme, close], vehicles=[mv]), 9, bel, close.pos, act)
    if not act.melee or act.fire2:
        fails.append(f"an enemy 3 u from the Mantis: melee {act.melee}, fire2 {act.fire2}")
    act = Action()
    far = ps(9, Vec(20.0, 0, 0), team=1)
    mb.aim.on_target = lambda me, at: True
    bel = type("B", (), dict(pos=far.pos, vel=Vec(), t=2.0, seen=True))()
    mb.mantis_weapons(2.0, mme, mv, Snapshot(2.0, [mme, far], vehicles=[mv]), 9, bel, far.pos, act)
    if act.melee or not act.fire2 or abs(mb.rocket_until - 2.0 - Bot.MANTIS_TAP) > 1e-6:
        fails.append(f"a man 20 u off: melee {act.melee}, fire2 {act.fire2}")
    act = Action()
    mb.mantis_weapons(2.5, mme, mv, Snapshot(2.5, [mme, far], vehicles=[mv]), 9, bel, far.pos, act)
    if act.fire2:
        fails.append("the rockets fired again before the salvo's reload")
    ghost = dict(handle=89, kind="storm_ghost", pos=(2.5, 1.0, 0.0), occupied=True, riders=1, team=1)
    act = Action()
    mb.stomp_next = 0.0
    mb.mantis_weapons(9.0, mme, mv, Snapshot(9.0, [mme, far], vehicles=[mv, ghost]), 9, bel, far.pos, act)
    if not act.melee:
        fails.append("an enemy vehicle 2.7 u off: no stomp")

    # a paused game: a command not taken yet is never written over (one slot); idle tells it
    blk = bytearray(botctl.SIZE)
    struct.pack_into("<I", blk, botctl.OFF_CMD + 4, 5)     # published 5, done 4: one waiting
    struct.pack_into("<I", blk, botctl.OFF_CMD + 8, 4)
    if botctl.idle(blk, 0.1):
        fails.append("idle with a command not taken")
    r = botctl.add_bot(blk, 1, 0, "x", "odst")
    if not r.get("timeout") or struct.unpack_from("<I", blk, botctl.OFF_CMD + 4)[0] != 5 or \
            bytes(blk[botctl.OFF_NAME:botctl.OFF_NAME + 2]) != b"\0\0":
        fails.append("an add wrote over a command not taken")
    struct.pack_into("<I", blk, botctl.OFF_CMD + 8, 5)
    if not botctl.idle(blk, 0.1):
        fails.append("idle with everything taken")

    if fails:
        print("nov 7 fixes FAILED:")
        for f in fails:
            print("  ", f)
        sys.exit(1)
    print("nov 7 fixes OK")


if __name__ == "__main__":
    main()
