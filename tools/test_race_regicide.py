"""Race (CE, Reach), Rocket Race (Reach) and Regicide (Halo 4), brain/modes.py: the variants read as their modes, the
gates in the game's order, every player's progress by CE's own touch rules (halo-64 game_engine_race.c), the King of
Regicide marked as a VIP, the director's hunter on him, and a simulated CE race whose bots finish laps gate by gate.

usage: python -I test_race_regicide.py      -> "race / regicide OK"
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import modes  # noqa: E402
from brain.core import Vec, Snapshot, PlayerState  # noqa: E402
from brain.maps import get_map  # noqa: E402


class Stub:
    def __init__(s, name="", icon=1, engine=2, race_type=0, hill=None):
        s.name, s.icon, s.eng, s.rt, s.hill = name, icon, engine, race_type, hill

    def variant_name(s):
        return s.name

    def engine_icon(s):
        return s.icon

    def engine(s):
        return s.eng

    def race_type(s):
        return s.rt

    def rally_dest(s):
        return s.hill[0] if s.hill else None


def player(i, pos, team=None, yaw=0.0, pitch=0.0, shield=1.0, alive=True, vehicle=-1):
    p = PlayerState(i, i if team is None else team, f"p{i}", pos, yaw=yaw, pitch=pitch, shield=shield, alive=alive)
    p.vehicle = vehicle
    return p


def main():
    fails = []
    # 1. names and engines: MCC's own files (Reach race_054.bin "RACE" icon 13, rocket_race_hog_054.bin
    # "$hr_gvar_Rocket_Hog_Race" icon 14; Halo 4 H4_REGICIDE_132.bin "Regicide"; CE 32_race.bin engine 5)
    for name, want in (("RACE", "race"), ("$hr_gvar_Rocket_Hog_Race", "rally"), ("Rocket Race", "rally"),
                       ("Regicide", "regicide"), ("Extraction", None), ("Team Slayer", None)):
        if modes.detect(name) != want:
            fails.append(f"{name!r} -> {modes.detect(name)} (want {want})")
    for game, stub, want in (("ce", Stub(engine=5), "race"), ("ce", Stub(engine=2), None), ("ce", Stub(engine=4), None),
                             ("reach", Stub("", icon=12), "race"), ("reach", Stub("RALLY", icon=12), "rally"),
                             ("reach", Stub("TEAM SLAYER", icon=1), None), ("h4", Stub("Regicide"), "regicide")):
        if modes.mode_of(game, stub) != want:
            fails.append(f"mode_of({game}, {stub.name!r} icon {stub.icon} engine {stub.eng}) -> "
                         f"{modes.mode_of(game, stub)} (want {want})")
    for m in ("race", "rally", "regicide"):
        if m not in modes.OBJECT_MODES:
            fails.append(f"{m} not in OBJECT_MODES: the live loop never watches it")

    # 2. the gates in order: CE by the flag's index, Reach by its spawn order (Boneyard's race_flags, seq 1..6)
    bg = get_map("bloodgulch")["objects"]
    ids = sorted(f["id"] for f in bg["netgame_flags"] if f["type"] == "race - track")
    got = [next(f["id"] for f in bg["netgame_flags"] if f["type"] == "race - track" and modes._v(f["pos"]) == g)
           for g, *_ in modes.race_gates(bg)]
    if got != ids:
        fails.append(f"Blood Gulch gates in order {got} (want {ids})")
    by = get_map("reach_70_boneyard")["objects"]
    seq = [next(f.get("seq") for f in by["netgame_flags"] if f["type"] == "race_flag" and modes._v(f["pos"]) == g)
           for g, *_ in modes.race_gates(by)]
    if seq != [1, 2, 3, 4, 5, 6]:
        fails.append(f"Boneyard race_flags by spawn order {seq} (want 1..6: objects.json 'seq')")
    if len(modes.race_gates(by, "rally")) != 8:
        fails.append(f"Boneyard rally flags {len(modes.race_gates(by, 'rally'))} (want 8)")

    # 3. CE's rules: in order (touching gate 2 first counts for nothing), a lap on the first gate after all of them
    gates = [(Vec(10.0 * k, 0, 0), 1.5, 0.6, 0.6) for k in range(3)]
    r = modes.Race(gates, "normal", ce=True)
    for k in (2, 0, 2, 1, 2, 0):
        r.step([(7, gates[k][0], True, False)])
    if r.laps.get(7) != 1 or r.next_gate(7) != 0:
        fails.append(f"normal race 2,0,2,1,2,0: laps {r.laps.get(7)}, next {r.next_gate(7)} (want 1 lap, next 0)")
    r = modes.Race(gates, "normal", ce=True)
    r.step([(7, Vec(0, 1.3, 0), True, False)])          # 1.3 u off: inside the game's 1.5, not TOUCH_K's 1.05
    if r.got.get(7):
        fails.append("a touch counted at 1.3 u on foot (the brain counts only well inside the game's 1.5 u)")
    r.step([(7, Vec(0, 1.6, 0), True, True)])           # riding: the vehicle's 2.5 u
    if r.got.get(7) != {0}:
        fails.append("a vehicle 1.6 u off gate 0 did not touch it (CE: 2.5 u riding)")
    r = modes.Race(gates, "any", ce=True)
    r.step([(7, gates[2][0], True, False)])
    if r.got.get(7) != {2} or r.next_gate(7, gates[2][0]) != 1:
        fails.append(f"any order: got {r.got.get(7)}, next {r.next_gate(7, gates[2][0])} (want {{2}}, the nearest: 1)")

    # 4. the live watch (CE Race): the next gate moves on as a racer takes it; Rocket Race on the game's destination
    w = modes.Watch("race", bg, "ce")
    g0, g1 = modes.race_gates(bg)[0][0], modes.race_gates(bg)[1][0]
    snap = Snapshot(0.0, [player(1, Vec(g0.x + 30, g0.y, g0.z))])
    w.update(Stub(engine=5), snap, 0.0, [])
    if snap.mode != "race" or snap.race_next.get(1) != g0:
        fails.append(f"CE race start: mode {snap.mode}, next {snap.race_next.get(1)} (want race, gate 0 at {g0})")
    snap = Snapshot(0.1, [player(1, g0)])
    w.update(Stub(engine=5), snap, 0.1, [])
    if snap.race_next.get(1) != g1:
        fails.append(f"after gate 0: next {snap.race_next.get(1)} (want gate 1 at {g1})")
    rally = modes.race_gates(by, "rally")
    w = modes.Watch("rally", by, "reach")
    snap = Snapshot(0.0, [player(1, Vec(0, 0, 0))])
    w.update(Stub(hill=((rally[3][0].x, rally[3][0].y, rally[3][0].z), 1.0)), snap, 0.0, [])
    if snap.mode != "race" or snap.race_next.get(1) != rally[3][0]:
        fails.append(f"Rocket Race with the destination read: next {snap.race_next.get(1)} (want rally flag 3)")
    snap = Snapshot(0.1, [player(1, Vec(0, 0, 0))])
    w.update(Stub(hill=((999.0, 999.0, 0.0), 1.0)), snap, 0.1, [])    # a read naming no rally flag: the sweep
    near = min(rally, key=lambda g: (g[0] - Vec(0, 0, 0)).flat())[0]
    if snap.race_next.get(1) != near:
        fails.append(f"Rocket Race, destination unread: next {snap.race_next.get(1)} (want the nearest rally flag)")

    # 5. Regicide: the King by the points the brain saw (a kill credited to the man aiming at him; the King's killer
    # takes his bounty: live Adrift's scoreboard, Owl864 with 2 kills killed the King and led with 50)
    w = modes.Watch("regicide", {}, "h4")
    a, b, c = Vec(0, 0, 0), Vec(20, 0, 0), Vec(0, 20, 0)
    w.update(Stub(), Snapshot(0.0, [player(1, a, yaw=0.0), player(2, b), player(3, c, yaw=math.pi)]), 0.0, [])
    snap = Snapshot(0.25, [player(1, a, yaw=0.0), player(2, b, alive=False), player(3, c, yaw=math.pi)])
    w.update(Stub("Regicide"), snap, 0.25, [])
    if snap.mode != "regicide" or snap.vips != (1,):
        fails.append(f"kill credit: mode {snap.mode}, {snap.vips} (want regicide, (1,): he aimed at the man who died)")
    w.update(Stub(), Snapshot(0.5, [player(1, a), player(2, b, yaw=math.pi), player(3, c)]), 0.5, [])
    snap = Snapshot(0.75, [player(1, a, alive=False), player(2, b, yaw=math.pi), player(3, c)])
    w.update(Stub(), snap, 0.75, [])
    if snap.vips != (2,):
        fails.append(f"regicide: {snap.vips} (want (2,): 10 + the bounty 20 for killing the King beats his 10)")

    # 6. the director hunts the King (SLAY-REG-01), a bot races its own next gate (Bot: race_next every tick)
    from brain.sim import Sim
    sim = Sim("slayer", per_team=2, seed=5, map_name="bloodgulch")
    snap = sim.snapshot()
    king = next(p for p in sim.players if p.team == 1)
    snap.mode, snap.vips = "regicide", (king.id,)
    d = sim.directors[0]
    slots = d.role_slots(0.0, snap, 2)
    if not slots or slots[0][0] != "hunter" or dist(slots[0][1], king.pos) > 0.1:
        fails.append(f"Regicide director: first slot {slots[:1]} (want a hunter on the King at {king.pos})")
    # (on foot: the sim has no vehicle model. Rat Race, seed 5, 240 s: 9 laps on the new code; Blood Gulch's 100 u
    # hops take a lap past 240 s on foot)
    sim = Sim("race", per_team=2, seed=5, map_name="ratrace")
    sim.run(180)
    om = sim.objmodes
    laps = sum(om.race.laps.values()) if om is not None else 0
    progress = (sum(len(g) for g in om.race.got.values()) + len(om.race.gates) * laps) if om is not None else 0
    roles = {b.order.role for b in sim.bots.values()}
    if laps < 2 or roles != {"runner"} or sum(sim.score.values()) != laps:
        fails.append(f"CE race sim on Rat Race (180 s, 2v2): {progress} gates, {laps} laps, score {dict(sim.score)}, "
                     f"roles {roles} (want 2+ laps scored, every bot a runner)")
    print(f"race sim: {progress} gates taken in order, {laps} laps, score {dict(sim.score)}, events {om.events[:4]}")

    # 7. Blood Gulch's gate 3 on the rock, live frames of bot 15 (trace_bloodgulch_20261104-104256): out of its Ghost under
    # the gate (CE's exit plays 0.9 s in the seat: one press a second, not a "failed" try a tick and the 30 s block),
    # then on foot 11.8 u off on the walk round to the climb (it went back for a Warthog), then in that Warthog by the
    # rock again (live: wedged 11 s, never out)
    gate = Vec(71.166, -92.553, 4.665)
    veh = lambda h, kind, pos, occ=False: dict(handle=h, kind=kind, pos=pos, occupied=occ, riders=int(occ), team=-1,
                                               fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), gunner=False, turrets=[],
                                               manned=[], dead=False, left=False)
    sim = Sim("race", per_team=1, seed=5, map_name="bloodgulch")
    sim.run(0.5)
    b = next(iter(sim.bots.values()))
    snap = sim.snapshot()
    me = snap.player(b.id)
    snap.race_next = {me.id: gate}
    tick = lambda t: b.plan(t, 1 / 30, snap, sim.los, sim.nav, [], None)
    t0 = sim.now + 5.0
    me.pos, me.vehicle = Vec(68.9, -98.0, 1.8), 77
    snap.vehicles = [veh(77, "ghost_mp", (68.9, -98.0, 1.8), True), veh(88, "mp_warthog", (69.8, -95.3, 1.9))]
    b.seat, b.seat_for, b.seat_since, b.enter_riders = "driver", 77, t0 - 3.0, 0
    pressed = sum(bool(tick(t0 + k / 30).action) for k in range(27))
    me.pos, me.vehicle = Vec(82.3, -96.4, 1.8), -1
    snap.vehicles = [veh(88, "mp_warthog", (69.8, -95.3, 1.9)), veh(77, "ghost_mp", (68.9, -98.0, 1.8))]
    b.next_decide = 0.0
    tick(t0 + 7.9)
    walk = b.goal[0]
    me.pos, me.vehicle = Vec(69.8, -95.3, 1.9), 88
    snap.vehicles = [veh(88, "mp_warthog", (69.8, -95.3, 1.9), True)]
    again = sum(bool(tick(t0 + 13.7 + k / 30).action) for k in range(30))
    if not 1 <= pressed <= 6 or walk != "objective" or not again:
        fails.append(f"Blood Gulch rock gate: exit presses in 0.9 s {pressed} (want 1-6: a press a second), on foot "
                     f"11.8 u off goal {walk} (want objective, no vehicle back), back in a Warthog by it: {again} presses "
                     f"(want an exit)")
    if fails:
        print("FAIL")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("race / regicide OK")


def dist(a, b):
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))


if __name__ == "__main__":
    main()
