"""Aircraft attack runs (the player's Shrine flag, 20261104-154714: "Guy in banshee isnt using any weapons"), flown closed
loop on Halo 3 Sandtrap by tools/air_replay.py:

1. a Banshee against two men by the Elephant's spot for 60 s: it makes runs (4+), fires on them (15+ fire ticks a run),
   pulls up under 400 ticks a minute and never touches the floor. The old pull-up (6.8 u over every floor within 6 u of
   its line) fired on most ticks and held the dives off him
2. a pilot's goals: no gun trips and no retreats from the seat (live: 1221 of its 2852 choices)
3. shot at on a run's way out: a jink (a swerve off its line)
4. its target: two men bunched beat one alone at the same range (the bolts splash)
5. under a deck high over it (Exile's crashed ship) heading out over low ground: no pull-up (a ceiling is no floor)

usage: python -I test_air_runs.py      -> "air runs OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import air_replay  # noqa: E402
from brain.bot import Action, Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_shrine")
FOES = [(4, 1, Vec(8.3, -37.2, -19.8)), (8, 1, Vec(0.3, -37.9, -22.5))]   # the 99.8 s frame's blue men by mid


def main():
    fails = []
    # 1. runs, flown
    m = air_replay.fly(M, Vec(-13.1, -26.2, -5.7), -0.8, lambda t: FOES, 60.0, team=0, seed=1)
    if m["runs"] < 4 or m["fire"] / max(1, m["runs"]) < 15 or m["pulls_per_min"] > 400 or m["under"]:
        fails.append(f"Banshee runs on Sandtrap: {m}")
    # 2. a pilot's goals
    b = Bot(9, 0, make_profile("top", "flanker", random.Random(9)), M, random.Random(9))
    b.order, b.seat = Order("mid", Vec(15.4, -20.8, -20.1)), "driver"
    me = PlayerState(9, 0, "pilot", Vec(-13.1, -26.2, -5.7), vehicle=77, weapon="none")
    v = dict(handle=77, kind="banshee", pos=(-13.1, -26.2, -5.7), occupied=True, riders=1, team=0)
    b.fetch = (Vec(-0.0, -5.1, -18.2), "rockets", 1e9)            # the team's power-weapon run, as live
    snap = Snapshot(50.0, [me], vehicles=[v], mode="slayer")
    goals = set()
    for k in range(20):
        b.next_decide, b.goal = 0.0, ("roam", None)
        goals.add(b.decide(50.0 + k, me, snap)[0])
    if goals & {"item", "retreat"}:
        fails.append(f"a Banshee pilot's goals: {goals} (want no item / retreat)")
    # 3. a jink when shot on the way out
    b = Bot(9, 0, make_profile("top", "flanker", random.Random(3)), M, random.Random(3))
    b.order = Order("mid", Vec(0, 0, 0))
    foe = Vec(8.3, -37.2, -19.8)
    b.air_run, b.notes = ["out", 4, 59.5, 1.0], []
    yaws = []
    for k, (sh, hp) in enumerate(((1.0, 1.0), (0.7, 1.0), (0.7, 1.0))):
        me = PlayerState(9, 0, "pilot", Vec(-5.0, -30.0, -8.0), yaw=1.0, shield=sh, health=hp, vehicle=77)
        a = Action()
        b.air_pass(60.0 + k * 0.1, me, 4, Belief(foe, Vec(), 60.0, True, "eyes"), foe, a)
        yaws.append(a.yaw)
    if abs(yaws[0] - 1.0) > 1e-6 or abs(abs(yaws[1] - 1.0) - 0.4) > 1e-6 or not any("jink" in n for n in b.notes):
        fails.append(f"shot at on the way out: yaws {[round(y, 2) for y in yaws]} (want 1.0, then 1.0 +- 0.4)")
    # 4. its target: two bunched vs one alone at the same range
    b = Bot(9, 0, make_profile("top", "flanker", random.Random(4)), M, random.Random(4))
    me = PlayerState(9, 0, "pilot", Vec(0.0, 0.0, 10.0), vehicle=77)
    v = dict(handle=77, kind="banshee", pos=(0.0, 0.0, 10.0), occupied=True, riders=1, team=0, fwd=(1, 0, 0))
    ps = [me, PlayerState(20, 1, "alone", Vec(0.0, -20.0, 0.0)), PlayerState(21, 1, "a", Vec(0.0, 20.0, 0.0)),
          PlayerState(22, 1, "b", Vec(1.5, 20.0, 0.0))]
    for p in ps[1:]:
        b.per.beliefs[p.id] = Belief(p.pos, Vec(), 1.0, True, "eyes")
    pick = b.vehicle_pick(me, v, "driver", [20, 21, 22], Snapshot(1.0, ps, vehicles=[v]))
    if pick not in (21, 22):
        fails.append(f"the Banshee's target: {pick} (want 21, one of the two bunched)")
    # 5. under Exile's crashed ship (a deck 5 u over it, 1 u beside), heading out over the low ground: no pull-up. Its
    # deck read as a floor to climb over (and a slope beside it as one under it): it climbed into it (bot 8, 36.7 s)
    E = get_map("h4_ca_blood_crash")
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), E, random.Random(1))
    b.seat, b.notes = "driver", []
    at = Vec(5.93, 16.4, 13.72)
    me = PlayerState(1, 0, "pilot", at, vel=Vec(6.0, 0.0, 0.0), yaw=0.0, vehicle=9)
    a = Action(yaw=0.0)
    a.forward, a.pitch = 1.0, 0.0
    b.air_guard(me, a, Snapshot(10.0, [me], vehicles=[dict(handle=9, kind="storm_banshee_mp", pos=(at.x, at.y, at.z),
                                                            occupied=True, riders=1, team=0)]))
    if any("pull up" in n for n in b.notes):
        fails.append(f"under Exile's ship heading over the low ground: {b.notes} (want no pull-up)")
    # 6. Spire (the owner's Forge run, Nov 6: vehicles.AIR_ENVELOPE): his ceiling, and the bomb runs into Invasion phase
    # 2's objective rooms, attacking with nobody in them, defending only with enemies in them; flown, the passes go in
    # and the fuel rod (Reach's bomb) is let go
    from brain import vehicles
    S = get_map("reach_35_island")
    env = vehicles.envelope("reach_35_island/variants/v3977bae2")
    rooms = [Vec(*r) for r in env["bombs"][2]]
    b = Bot(9, 0, make_profile("top", "flanker", random.Random(6)), S, random.Random(6))
    b.seat = "driver"
    me = PlayerState(9, 0, "pilot", Vec(-150.0, -400.0, -15.0), vehicle=77)
    inv = dict(mode="invasion", inv_phase=2, inv_attackers=0)
    if b.bomb_room(60.0, me, Snapshot(60.0, [me], **inv)) != rooms[0]:
        fails.append("bomb_room attacking, nobody in the rooms: not the nearest room")
    if b.bomb_room(60.0, me, Snapshot(60.0, [me], **dict(inv, inv_attackers=1))) is not None:
        fails.append("bomb_room defending, nobody in the rooms: a room (want none)")
    b.per.beliefs[30] = Belief(rooms[1] + Vec(1, 0, 0), Vec(), 59.0, True, "eyes")
    if b.bomb_room(60.0, me, Snapshot(60.0, [me], **dict(inv, inv_attackers=1))) != rooms[1]:
        fails.append("bomb_room defending, a man in room 2: not room 2")
    a = Action(pitch=0.3)
    b.notes = []
    b.air_roof_guard(me, a, Snapshot(60.0, [me], vehicles=[dict(handle=77, kind="banshee", pos=(-150.0, -400.0, -15.0),
                                                                 occupied=True, riders=1, team=0)]))
    if a.pitch > -0.3:
        fails.append(f"over the owner's Spire ceiling (z -17.2) at -15: pitch {a.pitch} (want nose down)")
    bm = air_replay.fly(S, Vec(-150.0, -400.0, -44.0), math.pi, lambda t: [], 40.0, team=0, seed=2, snap_kw=inv)
    if bm["room"] < 200 or bm["rods"] < 1:
        fails.append(f"Spire phase 2 bomb runs, flown 40 s: {bm['room']} pass ticks, {bm['rods']} fuel rods (want 200+, 1+)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"air runs OK ({m['runs']} runs in 60 s, {m['fire'] / m['runs']:.0f} fire ticks a run, "
          f"{m['pulls_per_min']:.0f} pull-up ticks a minute, nose {m['nose_err_deg_p25_50_75']} deg off him in range)")


if __name__ == "__main__":
    main()
