"""The carry as a team play and the score posture in the objective layouts (wave 2: the sim's carriers on The Pit died 3-6
s after the pull at the stand, 6-7 of theirs within 15 u and 0-0.4 of ours within 10; the audit's WRONG items,
docs/oct31/audit.md: ODST-OBJ-01, CTF-MULTI-16 / ASS-MULTI-12, the posture rules ODD-CORE-11, ASS-MULTI-11/12,
ASS-NEUT-02, KOTH-STATIC-11, TERR-SYM-07, STOCK-05). Director.role_slots / mode_slots on built snapshots:

1. CTF, 8 of us, our bot carries their flag, ours home: 3 escorts on him, our defenders kept, a screen between him and
   their base (SCREEN_BACK), the pushers ahead of him on his way home (SCREEN_AHEAD), none on to their base
2. their man carries our flag, theirs home: of the hunters one goes ahead of him on his way to their stand (cutoff)
3. the last minute behind (all_in) with their flag ours: no defender, everyone else on the carrier (CTF-MULTI-16)
4. the ferry: a Scorpion's driver is never sent for our carrier (no seat for him), a Warthog's is (ODST-OBJ-01)
5. Assault ahead, the clock running out (hide_and_hold), no carrier of ours: no runner, two on our goal (ASS-MULTI-11);
   behind (all_in) carrying: everyone else escorts, nobody on our goal (ASS-MULTI-12); carrying normally: one on our
   goal, not two (ASS-NEUT-02)
6. Stockpile ahead late: everyone guards our goal (STOCK-05)
7. Territories ahead late, two of three zones ours: every slot holds a zone we own, none takes the third (TERR-SYM-07)
8. King ahead late: the scorer at the hill's edge on our side, not its middle (KOTH-STATIC-11)
9. Oddball ahead late: the carrier's spot is kept, not moved off the enemies (ODD-CORE-11)

usage: python -I test_carry_play.py      -> "carry play OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.match import Posture  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_cyberdyne")
RED, BLUE = M["flags"][0], M["flags"][1]
MID = M["points"]["mid"]


def team(n=8, state="even", m=M):
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), m, random.Random(i)) for i in range(1, n + 1)}
    d = Director(0, m, bots, random.Random(0))
    d.posture = Posture({"all_in": 0.9, "hide_and_hold": 0.15}.get(state, 0.5), state)
    d.split, d.split_until = False, 1e9
    return d, bots


def main():
    fails = []
    # 1. a carry
    d, bots = team()
    car = BLUE + (RED - BLUE) * 0.35
    ps = [PlayerState(i, 0, f"b{i}", RED + Vec(i * 0.5, 0, 0)) for i in range(2, 9)]
    ps += [PlayerState(1, 0, "car", car, has_flag=True)] + [PlayerState(20 + k, 1, f"e{k}", BLUE) for k in range(8)]
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, car, "carried", 1)}
    slots = d.role_slots(10.0, Snapshot(10.0, ps, flags, mode="ctf"), 7)[:7]
    roles = [r for r, q, f in slots]
    screen = [q for r, q, f in slots if r == "screen"]
    mids = [q for r, q, f in slots if r == "mid"]
    full = d.role_slots(10.0, Snapshot(10.0, ps, flags, mode="ctf"), 7)
    pushes = [q for r, q, f in full if r == "mid"]
    if roles.count("escort") != 3 or "defender" not in roles:
        fails.append(f"a carry, 8 of us: roles {roles} (want 3 escorts and our defenders)")
    if not screen or abs(dist(screen[0], car) - getattr(D, "SCREEN_BACK", 8.0)) > 1.0 or dist(screen[0], BLUE) >= dist(car, BLUE):
        fails.append(f"a carry: screen {screen} (want {getattr(D, "SCREEN_BACK", 8.0)} u from him toward their base)")
    if not pushes or dist(pushes[0], RED) >= dist(car, RED) or abs(dist(pushes[0], car) - getattr(D, "SCREEN_AHEAD", 12.0)) > 1.0:
        fails.append(f"a carry: pushers at {pushes[:1]} (want {getattr(D, "SCREEN_AHEAD", 12.0)} u ahead of him on his way home)")
    # 2. the cut-off
    d, bots = team()
    thief = RED + (BLUE - RED) * 0.2
    ps = [PlayerState(i, 0, f"b{i}", RED + Vec(i * 0.5, 2, 0)) for i in range(1, 9)]
    ps += [PlayerState(20, 1, "thief", thief, has_flag=True)] + [PlayerState(21 + k, 1, f"e{k}", BLUE) for k in range(7)]
    flags = {0: FlagState(0, RED, thief, "carried", 20), 1: FlagState(1, BLUE, BLUE, "home")}
    hunters = [q for r, q, f in d.role_slots(20.0, Snapshot(20.0, ps, flags, mode="ctf"), 8) if r == "hunter"]
    ahead = [q for q in hunters if dist(q, thief) > 3.0]
    if not ahead or dist(ahead[0], BLUE) >= dist(thief, BLUE):
        fails.append(f"their carrier: hunters {hunters[:3]} (want one ahead of him toward their stand)")
    # 3. all in with their flag
    d, bots = team(state="all_in")
    ps = [PlayerState(i, 0, f"b{i}", RED + Vec(i * 0.5, 0, 0)) for i in range(2, 9)]
    ps += [PlayerState(1, 0, "car", car, has_flag=True)] + [PlayerState(20 + k, 1, f"e{k}", BLUE) for k in range(8)]
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, car, "carried", 1)}
    roles = [r for r, q, f in d.role_slots(30.0, Snapshot(30.0, ps, flags, mode="ctf"), 8) if r != "runner"][:7]
    if roles.count("escort") != 7 or "defender" in roles:
        fails.append(f"all in, carrying: roles {roles} (want 7 escorts, no defender)")
    # 4. the ferry
    car = BLUE + (RED - BLUE) * 0.05               # (far from home: a ferry's job)
    flags = {0: FlagState(0, RED, RED, "home"), 1: FlagState(1, BLUE, car, "carried", 1)}
    for kind, want in (("scorpion", False), ("warthog", True)):
        d, bots = team(n=3)
        bots[2].seat = "driver"
        w = car + Vec(15.0, 0.0, 0.0)
        ps = [PlayerState(1, 0, "car", car, has_flag=True), PlayerState(2, 0, "drv", w, vehicle=50),
              PlayerState(3, 0, "b3", RED)]
        v = dict(handle=50, kind=kind, pos=(w.x, w.y, w.z), riders=1, occupied=True, team=0, up=(0.0, 0.0, 1.0))
        snap = Snapshot(40.0, ps, flags, mode="ctf", vehicles=[v])
        d.ferry_orders(40.0, snap, list(bots.values()), {b.id: snap.player(b.id) for b in bots.values()})
        if (bots[2].order.role == "ferry") != want:
            fails.append(f"ferry by a {kind}: {bots[2].order.role} (want {'ferry' if want else 'no ferry'})")
    # 5-6. Assault and Stockpile by posture
    S = get_map("reach_30_settlement")
    g0, g1 = S["points"]["mid"] + Vec(-20, 0, 0), S["points"]["mid"] + Vec(20, 0, 0)
    bomb = S["points"]["mid"]
    for mode, state, carry, check in (("assault", "hide_and_hold", False, "ahead"), ("assault", "all_in", True, "behind"),
                                      ("assault", "even", True, "carrying"), ("stockpile", "hide_and_hold", False, "guard")):
        d, bots = team(n=6, state=state, m=S)
        ps = [PlayerState(i, 0, f"b{i}", g0 + Vec(i, 0, 0), has_flag=carry and i == 1) for i in range(1, 7)]
        items = [dict(pos=ps[0].pos if carry else bomb, carrier=1 if carry else None, team=8, kind="bomb")]
        snap = Snapshot(50.0, ps, mode=mode, obj_items=items, obj_goals={0: [g0], 1: [g1]})
        roles = [(r, q) for r, q, f in d.mode_slots(50.0, snap, 6)[:5]]
        names = [r for r, q in roles]
        on_goal = sum(1 for r, q in roles if r == "defender" and dist(q, g0) < 4.0)
        ok = {"ahead": "runner" not in names and on_goal >= 2,
              "behind": names.count("escort") == 5 and on_goal == 0,
              "carrying": on_goal == 1,
              "guard": all(r == "defender" for r in names)}[check]
        if not ok:
            fails.append(f"{mode} {state}{' carrying' if carry else ''}: roles {names}, on our goal {on_goal}")
    # 7. Territories ahead late, holding two of three
    d, bots = team(n=4, state="hide_and_hold", m=S)
    z = [S["points"]["mid"] + Vec(dx, 0, 0) for dx in (-15, 0, 15)]
    ps = [PlayerState(i, 0, f"b{i}", z[0] + Vec(i, 0, 0)) for i in range(1, 5)]
    snap = Snapshot(60.0, ps, mode="territories", obj_zones=[(z[0], 3.0, 0), (z[1], 3.0, 0), (z[2], 3.0, 1)])
    slots = d.mode_slots(60.0, snap, 4)[:4]
    if any(r != "defender" or dist(q, z[2]) < 4.0 for r, q, f in slots):
        fails.append(f"territories ahead late, two of three ours: {[(r, round(dist(q, z[2]))) for r, q, f in slots]}")
    # 8. King ahead late
    d, bots = team(n=4, state="hide_and_hold")
    hill = MID
    ps = [PlayerState(i, 0, f"b{i}", hill + Vec(10.0, 0.0, 0.0)) for i in range(1, 5)]
    snap = Snapshot(70.0, ps, mode="king", hill=hill, hill_r=3.0)
    post = d.role_slots(70.0, snap, 4)[0][1]
    if not 1.5 < dist(post, hill) < 3.0 or post.x <= hill.x:
        fails.append(f"king ahead late: the scorer's post {dist(post, hill):.1f} u from the middle (want at our edge)")
    # 9. Oddball ahead late
    d, bots = team(n=4)
    ps = [PlayerState(1, 0, "car", MID, has_flag=True)] + [PlayerState(20, 1, "e", M["holds"][0][0])]
    snap = Snapshot(80.0, ps, mode="oddball", ball=MID, ball_carrier=1)
    first = d.carry_point(snap)
    d.posture = Posture(0.15, "hide_and_hold")
    ps[1] = PlayerState(20, 1, "e", first)          # an enemy right on that spot now
    later = d.carry_point(Snapshot(81.0, ps, mode="oddball", ball=MID, ball_carrier=1))
    if dist(first, later) > 0.1:
        fails.append("oddball ahead late: the carrier's spot moved")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("carry play OK (3 escorts, a screen, pushers ahead; a cut-off; all in carrying; no tank ferry; Assault,"
          " Stockpile, Territories, King and Oddball by the score posture)")


if __name__ == "__main__":
    main()
