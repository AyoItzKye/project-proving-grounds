"""Vehicles driven with a job, riders called, tanks kept and aimed as the player does ("this guy with the warthog has no
gunner or passenger or anything", "When these bots get into these vehicles they have to have a goal in mind", "why the
fuck did he just abandon the scorpion", "this guy is missing all his scorpion shots",):

1. a bot's Warthog with only its driver calls the runner beside it to the gun and the next one aboard; a defender by
   it (his post far off) and a bot whose objective is close are not called (director.rider_calls); the driver says
   "Get in, <zone>!" (no threat marked there)
1b. a Warthog at our defenders' post: the nearest defender takes its gun, the next no passenger seat
2. its driver waits for a called rider walking up from 12 u, past the 8 s just-in wait, 6 s from the call
   (Bot.crew_coming)
3. jobs (director.vehicle_jobs): a driver with a runner aboard takes him to his objective (taxi); with their carrier
   out an armed vehicle hunts him; with ours out it escorts him
3c. their carrier away in a vehicle: even our unarmed Mongoose goes after him (guide 17 PUR rules)
3d. their Banshee seen: our free bot takes our Banshee first, else the Warthog (CTF's transport first; guide 19 VC-01/02)
4. a runner riding as a passenger gets out 10 u from their flag (RIDE_OUT_R)
5. a taxi does not circle a fight off its trip (its gunner shoots on the move)
6. a Scorpion driver at the end of its trip does not get out, and wedged twice takes another way, still in
7. a Scorpion leads a man crossing 25 u off by its fast shell (under 3 deg), not by a rocket's flight; a Wraith lobs its
   mortar over a man 40 u off (its pitch 5+ deg over the line to him)
7b. a Banshee hunting their carrier does not set down on him (a plain trip's end does)
8. a Chopper drives straight at a man ahead with its guns (one with rockets: no splatter run), and boosts into him inside
   8 u (Bot.ram_boost)
9. a gunned Warthog runs a Ghost down head on (Halo 3; guide 17 H2-PUR-02 / H4-PUR-01: it only circled)

usage: python -I test_vehicle_jobs.py      -> "vehicle jobs OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, angles_to  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("bloodgulch")
T = terrain(M)
RED, BLUE = M["flags"][0], M["flags"][1]
A = Vec(RED.x - 10.0, RED.y + 10.0, T.ground(RED.x - 10.0, RED.y + 10.0))   # (by red base: blue far off)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def bot(i, seed=None, tier="top"):
    b = Bot(i, 0, make_profile(tier, "objector", random.Random(seed or i)), M, random.Random(seed or i))
    b._terrain = T
    return b


def see(b, pid, pos, t, vel=None):
    b.per.beliefs[pid] = Belief(pos, vel or Vec(), t, True, "eyes")
    b.per.recognized.add(pid)
    b.per.last_seen[pid] = t


def hog(**kw):
    return dict(dict(handle=9, kind="warthog", pos=(A.x, A.y, A.z), riders=1, occupied=True, team=0, fwd=(1.0, 0.0, 0.0),
                     up=(0.0, 0.0, 1.0), gunner=False, turrets=[], manned=[]), **kw)


def drive(b, t, v, me, others):
    a = Action(yaw=me.yaw)
    b.drive(t, 1 / 30, me, Snapshot(t, [me] + others, vehicles=[v], mode="ctf",
                                    flags={0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, BLUE, "home")}),
            a, lambda p, q, **k: q)
    return a


def main():
    fails = []
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, BLUE, "home")}
    # 1. riders called
    drv, r1, r2, dfd, near = bot(1), bot(2), bot(3), bot(4), bot(5)
    bots = {b.id: b for b in (drv, r1, r2, dfd, near)}
    d = Director(0, M, bots, random.Random(1))
    drv.seat, drv.seat_for, drv.seat_since = "driver", 9, 0.0
    ps = [PlayerState(1, 0, "drv", A, vehicle=9), PlayerState(2, 0, "r1", A + Vec(6.0, 0.0, 0.0)),
          PlayerState(3, 0, "r2", A + Vec(0.0, 9.0, 0.0)), PlayerState(4, 0, "dfd", A + Vec(-4.0, 0.0, 0.0)),
          PlayerState(5, 0, "near", A + Vec(0.0, -5.0, 0.0))]
    for b, role, pt in ((drv, "mid", BLUE), (r1, "runner", BLUE), (r2, "escort", BLUE), (dfd, "defender", A + Vec(-40.0, 0.0, 0.0)),
                        (near, "mid", A + Vec(0.0, -15.0, 0.0))):
        b.order = Order(role, pt)
        d.roles[b.id] = role
    snap = Snapshot(10.0, ps, flags, mode="ctf", vehicles=[hog()])
    d.rider_calls(10.0, snap, list(bots.values()), {b.id: snap.player(b.id) for b in bots.values()})
    got = {b.id: b.order.role for b in bots.values()}
    if got[2] != "ride" or got[3] != "board" or got[4] != "defender" or got[5] != "mid":
        fails.append(f"rider calls: runner {got[2]}, escort {got[3]}, defender {got[4]}, a bot with its objective 15 u "
                     f"off {got[5]} (want ride, board, defender, mid)")
    calls = [d.text(c) for c in d.voice.queue + d.voice.in_flight if c.kind == "pickup"]
    if not calls or not calls[0].startswith("Get in") or d.threat:
        fails.append(f"the driver's call: {calls}, threat map {d.threat} (want \"Get in, <zone>!\", no threat)")
    # 1b. a Warthog at our defenders' post: the nearest defender takes its gun, no defender its passenger seat (Spire
    # at 683 s: "Sentinel doesnt have a gunner on his warthog", every teammate a defender)
    bots = {i: bot(i) for i in (1, 2, 3)}
    d = Director(0, M, bots, random.Random(3))
    bots[1].seat = "driver"
    for i in (1, 2, 3):
        bots[i].order = Order("defender", A + Vec(2.0, 0.0, 0.0))
        d.roles[i] = "defender"
    ps = [PlayerState(1, 0, "drv", A, vehicle=9), PlayerState(2, 0, "d2", A + Vec(3.0, 0.0, 0.0)),
          PlayerState(3, 0, "d3", A + Vec(5.0, 0.0, 0.0))]
    snap = Snapshot(11.0, ps, flags, mode="ctf", vehicles=[hog()])
    d.rider_calls(11.0, snap, list(bots.values()), {b.id: snap.player(b.id) for b in bots.values()})
    if (bots[2].order.role, bots[3].order.role) != ("ride", "defender"):
        fails.append(f"a Warthog at our defenders' post: {bots[2].order.role}, {bots[3].order.role} (want the nearest on "
                     f"its gun, the other at his post)")
    # 1c. a lone driver with no job and the gun empty goes for the nearest teammate who would take the gun (Spire 230307
    # at 94.7 s: a defender drove alone to his post, every teammate posted farther than CALL_R off): a defender 40 u
    # off, at his post; parked by him; given up after PICKUP_WAIT s by him without boarding (the next one then); Easy
    # never fetches
    bots = {i: bot(i) for i in (1, 2, 3)}
    d = Director(0, M, bots, random.Random(4))
    bots[1].seat = "driver"
    far1, far2 = A + Vec(40.0, 0.0, 0.0), A + Vec(0.0, 45.0, 0.0)
    for i, pt in ((1, A), (2, far1), (3, far2)):
        bots[i].order = Order("defender", pt)
        d.roles[i] = "defender"
    ps = [PlayerState(1, 0, "drv", A, vehicle=9), PlayerState(2, 0, "d2", far1), PlayerState(3, 0, "d3", far2)]
    snap = Snapshot(20.0, ps, flags, mode="slayer", vehicles=[hog()])
    pl = {b.id: snap.player(b.id) for b in bots.values()}
    d.vehicle_jobs(20.0, snap, list(bots.values()), pl)
    got1 = (bots[1].vjob, getattr(bots[1], "drive_to", None))
    ps[0] = PlayerState(1, 0, "drv", far1 + Vec(-4.0, 0.0, 0.0), vehicle=9)
    snap = Snapshot(21.0, ps, flags, mode="slayer", vehicles=[hog(pos=(far1.x - 4.0, far1.y, far1.z))])
    pl = {b.id: snap.player(b.id) for b in bots.values()}
    d.rider_calls(21.0, snap, list(bots.values()), pl)
    called = bots[2].order.role
    bots[2].order = Order("defender", far1)              # (he never came)
    d.vehicle_jobs(21.0, snap, list(bots.values()), pl)
    a = drive(bots[1], 21.5, hog(pos=(far1.x - 4.0, far1.y, far1.z)), ps[0], ps[1:])
    d.vehicle_jobs(30.0, snap, list(bots.values()), pl)
    got2 = getattr(bots[1], "drive_to", None)
    if got1 != ("pickup", far1) or called != "ride" or abs(a.forward) > 0.01 or got2 != far2:
        fails.append(f"lone driver: job {got1} (want pickup at the defender 40 u off), the defender by it {called} (want "
                     f"ride), throttle by him {a.forward:.2f} (want 0), after waiting {got2} (want the next one {far2})")
    easy = bot(1, tier="novice")
    easy.seat, easy.order = "driver", Order("defender", A)
    d = Director(0, M, {1: easy, 2: bots[2]}, random.Random(5))
    d.roles = {1: "defender", 2: "defender"}
    snap = Snapshot(40.0, ps[:2], flags, mode="slayer", vehicles=[hog()])
    ps[0] = PlayerState(1, 0, "drv", A, vehicle=9)
    snap = Snapshot(40.0, ps[:2], flags, mode="slayer", vehicles=[hog()])
    d.vehicle_jobs(40.0, snap, [easy, bots[2]], {1: ps[0], 2: ps[1]})
    if easy.vjob == "pickup":
        fails.append("an Easy driver went to fetch a gunner (want: it never plans)")
    # 2. the driver waits for the called rider, past its 8 s just-in wait, 6 s from the call
    me = PlayerState(1, 0, "drv", A, vehicle=9)
    walker = PlayerState(2, 0, "r1", A + Vec(12.0, 0.0, 0.0))
    drv.seat_since = 0.0
    drv.called_aboard = {9: ((2,), 10.0)}
    from brain import vehicles
    w1 = drv.crew_coming(12.0, me, hog(), vehicles.spec("warthog"), Snapshot(12.0, [me, walker], vehicles=[hog()]), [])
    w2 = drv.crew_coming(16.5, me, hog(), vehicles.spec("warthog"), Snapshot(16.5, [me, walker], vehicles=[hog()]), [])
    if not w1 or w2:
        fails.append(f"driver wait for a called rider 12 u off: at 2 s {w1}, at 6.5 s {w2} (want True, False)")
    # 3. jobs
    for name, extra, want in (("a runner aboard", [PlayerState(2, 0, "r1", A, vehicle=9)], ("taxi", BLUE)),
                              ("their carrier out", [PlayerState(7, 1, "c", A + Vec(30.0, 5.0, 0.0), has_flag=True)],
                               ("hunt", A + Vec(30.0, 5.0, 0.0))),
                              ("our person carrying", [PlayerState(8, 0, "you", A + Vec(-20.0, 4.0, 0.0), has_flag=True,
                                                                   is_bot=False)], ("escort", A + Vec(-20.0, 4.0, 0.0)))):
        drv, r1 = bot(1), bot(2)
        drv.seat, drv.order, r1.order = "driver", Order("mid", BLUE + Vec(0.0, 20.0, 0.0)), Order("runner", BLUE)
        d = Director(0, M, {1: drv, 2: r1}, random.Random(2))
        ps = [PlayerState(1, 0, "drv", A, vehicle=9)] + extra
        if not any(p.id == 2 for p in ps):
            ps.append(PlayerState(2, 0, "r1", A + Vec(40.0, 0.0, 0.0)))
        v = hog(riders=sum(p.vehicle == 9 for p in ps), gunner=True)
        snap = Snapshot(20.0, ps, flags, mode="ctf", vehicles=[v])
        d.vehicle_jobs(20.0, snap, [drv, r1], {1: snap.player(1), 2: snap.player(2)})
        dt = getattr(drv, "drive_to", None)
        if drv.vjob != want[0] or dt is None or (dt - want[1]).flat() > 0.5:
            fails.append(f"job with {name}: {drv.vjob} to {dt} (want {want[0]} to {want[1]})")
    # 3c. their carrier away in a vehicle: our Mongoose's driver (no gun) goes after him too
    drv = bot(1)
    drv.seat, drv.order = "driver", Order("mid", BLUE)
    d = Director(0, M, {1: drv}, random.Random(4))
    run = A + Vec(30.0, 0.0, 0.0)
    ps = [PlayerState(1, 0, "drv", A, vehicle=9), PlayerState(7, 1, "c", run, has_flag=True, vehicle=12)]
    vs = [hog(kind="mongoose"), dict(hog(handle=12, kind="ghost", pos=(run.x, run.y, run.z)), team=1)]
    snap = Snapshot(21.0, ps, flags, mode="ctf", vehicles=vs)
    d.vehicle_jobs(21.0, snap, [drv], {1: snap.player(1)})
    if drv.vjob != "hunt":
        fails.append(f"their carrier away in a Ghost: our Mongoose's job {drv.vjob} (want hunt)")
    # 3d. what they field picks our first vehicle: their Banshee seen, our free bot takes our Banshee, not the Warthog
    for seen_banshee, want in ((False, "warthog"), (True, "banshee")):
        b1 = bot(1)
        d = Director(0, M, {1: b1}, random.Random(5))
        sky = A + Vec(0.0, 30.0, 10.0)
        ps = [PlayerState(1, 0, "b1", A), PlayerState(7, 1, "pilot", sky, vehicle=13)]
        vs = [dict(hog(handle=21, pos=(A.x + 6, A.y, A.z)), occupied=False, riders=0, team=-1),
              dict(hog(handle=22, kind="banshee", pos=(A.x - 6, A.y, A.z)), occupied=False, riders=0, team=-1),
              dict(hog(handle=13, kind="banshee", pos=(sky.x, sky.y, sky.z)), team=1)]
        if seen_banshee:
            see(b1, 7, sky, 22.0)
        snap = Snapshot(22.0, ps, flags, mode="ctf", vehicles=vs)
        d.roles = {1: "free"}
        d.crew_orders(22.0, snap, {1: snap.player(1)}, [b1])
        got = {21: "warthog", 22: "banshee"}.get(b1.order.target) if b1.order.role == "drive" else None
        if got != want:
            fails.append(f"crew pick{' with their Banshee seen' if seen_banshee else ''}: {got} (want {want})")
    # 4. a runner passenger out by their flag
    rp = bot(2)
    rp.order, rp.seat, rp.seat_for, rp.seat_since = Order("runner", BLUE), "passenger", 9, 0.0
    at = BLUE + Vec(6.0, 0.0, 0.0)
    a = drive(rp, 5.0, hog(pos=(at.x, at.y, at.z), riders=2), PlayerState(2, 0, "rp", at, vehicle=9),
              [PlayerState(1, 0, "drv", at, vehicle=9)])
    far = A
    b_ = drive(bot(3), 5.0, hog(riders=2), PlayerState(3, 0, "rq", far, vehicle=9), [PlayerState(1, 0, "drv", far, vehicle=9)])
    if not a.action:
        fails.append("a runner riding by their flag (6 u): stayed in (want out)")
    # 5. a taxi does not circle a fight
    tx = bot(1)
    tx.seat, tx.seat_for, tx.seat_since, tx.vjob = "driver", 9, 0.0, "taxi"
    tx.order, tx.drive_to = Order("runner", BLUE), BLUE
    foe = PlayerState(7, 1, "f", A + Vec(0.0, 10.0, 0.0))
    see(tx, 7, foe.pos, 30.0)
    a = drive(tx, 30.0, hog(riders=3, gunner=True), PlayerState(1, 0, "tx", A, vehicle=9),
              [foe, PlayerState(2, 0, "g", A, vehicle=9, gunner_seat=True)])
    if tx.att and tx.att[0] == "circle":
        fails.append("a taxi with a gunner circled a fight off its trip")
    # 6. a Scorpion kept: at the end of its trip, and wedged
    tk = bot(1)
    tank = dict(hog(kind="scorpion"), riders=1)
    tk.order = Order("escort", BLUE)
    me = PlayerState(1, 0, "tk", A, vehicle=9)
    tk.drive_to = A + Vec(2.0, 0.0, 0.0)
    out = 0
    for k in range(10):
        a = drive(tk, 40.0 + k / 30, tank, me, [])
        out += a.action
    if out or tk.crew_ride != 9:
        fails.append(f"a Scorpion at the end of its trip: pressed get-out {out} ticks (crew_ride {tk.crew_ride})")
    tk.drive_to = A + Vec(40.0, 0.0, 0.0)
    out, notes = 0, []
    for k in range(int(12 / (1 / 30))):            # never moving: wedged
        tk.notes = []
        a = drive(tk, 50.0 + k / 30, tank, me, [])
        out += a.action
        notes += tk.notes
    if out or not any("another way" in n for n in notes):
        fails.append(f"a wedged Scorpion: get-out ticks {out}, notes {sorted(set(notes))[:4]} (want none, another way)")
    # 7. tank aim
    for kind, dist_, vel, check in (("scorpion", 25.0, Vec(0.0, 3.0, 0.0), "lead"), ("wraith", 40.0, Vec(), "lob")):
        g = bot(1, tier="top")
        v = dict(hog(kind=kind), riders=1)
        g.seat, g.seat_for, g.seat_since, g.crew_ride = "driver", 9, 0.0, 9
        g.drive_to = A + Vec(dist_, 0.0, 0.0)
        man = A + Vec(dist_, 0.0, 0.0)
        man = Vec(man.x, man.y, T.ground(man.x, man.y))
        yaw, pitch = 0.0, 0.0
        for k in range(60):
            t = 60.0 + k / 30
            see(g, 7, man, t, vel)
            me = PlayerState(1, 0, "g", A, yaw=yaw, pitch=pitch, vehicle=9)
            a = drive(g, t, v, me, [PlayerState(7, 1, "f", man, vel=vel)])
            yaw, pitch = a.yaw, a.pitch
        direct_yaw, direct_pitch = angles_to(A, man)
        if check == "lead" and abs(math.degrees(wrap(yaw - direct_yaw))) > 3.0:
            fails.append(f"Scorpion on a man crossing 25 u off at 3 u/s: {math.degrees(wrap(yaw - direct_yaw)):.1f} deg "
                         f"off his bearing (want under 3: its shell is fast)")
        if check == "lob" and math.degrees(pitch - direct_pitch) < 5.0:
            fails.append(f"Wraith on a man 40 u off: pitch {math.degrees(pitch - direct_pitch):.1f} deg over the line "
                         f"(want 5+: a lobbed mortar)")
    # 7b. a Banshee hunting their carrier does not set down on him (its trip's end lands it, a job's does not)
    for job, want in ((None, True), ("hunt", False)):
        pl = bot(1)
        up = A + Vec(0.0, 0.0, 8.0)
        v = dict(hog(kind="banshee", pos=(up.x, up.y, up.z)), riders=1)
        pl.seat, pl.seat_for, pl.seat_since, pl.vjob = "driver", 9, 0.0, job
        pl.order, pl.drive_to = Order("mid", BLUE), A + Vec(5.0, 0.0, 0.0)
        drive(pl, 65.0, v, PlayerState(1, 0, "pl", up, vehicle=9), [])
        if bool(getattr(pl, "landing", False)) != want:
            fails.append(f"a Banshee 5 u from where it goes, job {job}: landing {getattr(pl, 'landing', None)} (want {want})")
    # 8. a Chopper charges and boosts
    c = bot(1, tier="top")
    v = dict(hog(kind="brute_chopper"), riders=1)
    c.seat, c.seat_for, c.seat_since, c.crew_ride = "driver", 9, 0.0, 9
    c.drive_to = A + Vec(40.0, 0.0, 0.0)
    boosted, att = False, None
    for k in range(60):
        t = 70.0 + k / 30
        man = A + Vec(12.0 - 8.0 * k / 60, 0.3, 0.0)
        see(c, 7, man, t)
        c.notes = []
        a = drive(c, t, v, PlayerState(1, 0, "c", A, yaw=0.0, vehicle=9),
                  [PlayerState(7, 1, "f", man, weapon="rockets", weapons=["rockets"])])   # (no splatter run: rockets)
        att = c.att[0] if c.att else None
        if (man - A).flat() > 9.0 and k > 3 and (abs(a.strafe) > 0.05 or a.forward < 0.9):
            fails.append(f"Chopper, a man {(man - A).flat():.0f} u ahead: forward {a.forward:.2f} strafe {a.strafe:.2f} "
                         f"(want straight at him)")
            break
        boosted = boosted or a.fire2
    if not boosted or att not in ("charge", "splatter", "through"):
        fails.append(f"Chopper closing on a man ahead: boosted {boosted}, doing {att} (want a boost into him)")
    # 9. a gunned Warthog runs down a Ghost head on (Halo 3), its gunner on
    H3 = get_map("h3_cyberdyne")
    TH = terrain(H3)
    q = H3["points"]["mid"]
    w = Bot(1, 0, make_profile("top", "rusher", random.Random(9)), H3, random.Random(9))
    w._terrain = TH
    w.seat, w.seat_for, w.seat_since, w.order = "driver", 9, 0.0, Order("mid", q + Vec(30.0, 0.0, 0.0))
    w.drive_to = q + Vec(30.0, 0.0, 0.0)
    ghost_at = q + Vec(10.0, 0.0, 0.0)
    see(w, 7, ghost_at, 90.0)
    vs = [dict(hog(pos=(q.x, q.y, q.z)), riders=2, gunner=True),
          dict(hog(handle=12, kind="ghost", pos=(ghost_at.x, ghost_at.y, ghost_at.z)), team=1)]
    a = Action(yaw=0.0)
    me = PlayerState(1, 0, "w", q, yaw=0.0, vehicle=9)
    w.drive(90.0, 1 / 30, me, Snapshot(90.0, [me, PlayerState(2, 0, "g", q, vehicle=9, gunner_seat=True),
                                            PlayerState(7, 1, "gh", ghost_at, vehicle=12)], vehicles=vs, mode="slayer"),
            a, lambda p, q_, **k: q_)
    if not w.att or w.att[0] != "splatter":
        fails.append(f"a gunned Warthog, a Ghost 10 u ahead: {w.att and w.att[0]} (want a run at it)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("vehicle jobs OK (riders called and waited for, taxi / hunt / escort, out at the flag, tanks kept and aimed,"
          " the Chopper's charge and boost)")


if __name__ == "__main__":
    main()
