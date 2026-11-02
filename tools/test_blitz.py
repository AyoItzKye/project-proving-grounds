"""The team blitz ("Code the blitz right now"):

1. When it is desperate: CTF the last minute behind, not even; never in Slayer (its posture push) or Territories (holding
   is the score); King with the enemy one push from the limit only with a man of theirs on the hill, not in CTF;
   Stockpile at the nearest flag not in our goal, two holding the goal while one lies in it, none with it empty;
   Invasion attacking in the phase's last minute or with a wave wiped (2 of 3 dead in 60 s), the territory of that
   phase or the core, a blitz on seen through; not a wave going in, not one down, never defending, never with the core
   in our hands
2. CTF on Blood Gulch, the last minute behind (the sim, 4 v 4 Legendary), one of the team at mid: it rallies short of
   their flag, then goes in together as runners at it, split over two prongs, inside BLITZ_GATHER_S + a few s
3. A blitzing runner's side fight 9 u off its line weighs a seventh (the urgency); before, the CTF leash's third
4. Spire phase 3: the rally at the spire's foot, no forced ways up (the nav picks them)
5. The trace: a CTF blitz in the world line, listed by tools/observer.py events

usage: python -I test_blitz.py      -> "blitz OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.match import Posture  # noqa: E402
from brain.sim import Sim  # noqa: E402


def main():
    fails = []
    # 1. when it is desperate
    s = Sim(mode="slayer", per_team=(3, 3), seed=1, tiers=["top"], map_name="bloodgulch")
    d = s.directors[0]
    snap = s.snapshot() if hasattr(s, "snapshot") else None
    s.step()
    snap = s.last_snap if hasattr(s, "last_snap") else snap
    if snap is None:
        from brain.core import Snapshot as Snp
        snap = Snp(s.now, list(s.players), mode="slayer")
    d.posture = Posture(0.9, "all_in")
    if d.desperate(s.now, snap) is not None:
        fails.append("Slayer, the last minute behind: a blitz (want none: the posture's push, slayer_slots)")
    sn = Snapshot(s.now, list(s.players), mode="ctf", flags=s.flags)
    if d.desperate(s.now, sn) is None:
        fails.append("CTF, the last minute behind: not desperate")
    terr = Snapshot(s.now, list(s.players), mode="territories", obj_zones=[(Vec(9.0, 0.0, 0.0), 3.0, 1)])
    if d.desperate(s.now, terr) is not None:
        fails.append("Territories, the last minute behind: a blitz (want none: holding is the score)")
    d.posture = Posture(0.5, "even")
    if d.desperate(s.now, sn) is not None:
        fails.append("CTF, even: desperate")
    hill = Vec(0.0, 0.0, 0.0)
    foe = next(p for p in s.players if p.team == 1)
    seer = next(iter(d.bots.values()))
    for mode, state, on_hill, want in (("king", "enemy_near_win", True, True), ("king", "enemy_near_win", False, False),
                                       ("ctf", "enemy_near_win", False, False)):
        seer.per.beliefs.pop(foe.id, None)
        if on_hill:          # (one of them in the hill, seen just now)
            seer.per.beliefs[foe.id] = Belief(hill, Vec(), s.now, True, "eyes")
        sn = Snapshot(s.now, list(s.players), mode=mode, hill=hill if mode == "king" else None, hill_r=3.0)
        d.posture = Posture(0.2, state)
        got = d.desperate(s.now, sn)
        if (got is not None) != want or (want and dist_ok(got[0], hill) is False):
            fails.append(f"{mode}, {state}, a man on the hill {on_hill}: {got} (want {'the hill' if want else 'none'})")
    seer.per.beliefs.pop(foe.id, None)
    # Stockpile: the nearest flag not in our goal; two of the team hold the goal while a flag lies in it
    goal, kept, loose = Vec(-20.0, 0.0, 0.0), Vec(-20.5, 0.0, 0.0), Vec(15.0, 0.0, 0.0)
    st = Snapshot(s.now, list(s.players), mode="stockpile", obj_goals={0: [goal], 1: [Vec(30.0, 0.0, 0.0)]},
                  obj_items=[dict(pos=kept, carrier=None, team=8), dict(pos=loose, carrier=None, team=8)])
    d.posture = Posture(0.9, "all_in")
    got = d.desperate(s.now, st)
    team = d.blitz_team(st)
    holds = d.blitz_holds(st, team)
    if got is None or not dist_ok(got[0], loose) or len(holds) != 2 or any(dist(q, goal) > 3.5 for q in holds.values()):
        fails.append(f"Stockpile: target {got}, holds {holds} (want the loose flag, two at our goal)")
    st.obj_items = st.obj_items[1:]
    if d.blitz_holds(st, team):
        fails.append("Stockpile, nothing in our goal: holders kept back")
    zones = [Vec(10.0, 0.0, 0.0), Vec(-10.0, 0.0, 0.0)]
    core = Vec(5.0, 5.0, 3.0)
    ours = [p.id for p in s.players if p.team == 0]
    p1 = dict(inv_phase=1, inv_attackers=0, inv_zones=zones)
    p3 = dict(inv_phase=3, inv_phase_t=5.0, inv_attackers=0, inv_core=core, inv_zones=zones)
    for kw, dead, on, want in ((dict(p1, inv_phase_t=25.0), 0, False, None),            # a wave going in: the pile-on's
                               (dict(p1, inv_phase_t=190.0), 0, False, "territory, phase 1"),   # the last minute
                               (dict(p1, inv_phase_t=25.0), 2, False, "territory, phase 1"),    # a wave wiped
                               (dict(p1, inv_phase_t=25.0), 1, False, None),            # one down
                               (dict(p1, inv_phase_t=25.0), 0, True, "territory, phase 1"),     # a blitz on: seen through
                               (dict(p1, inv_phase_t=190.0, inv_attackers=1), 2, False, None),  # defending
                               (dict(p3), 0, False, None),
                               (dict(p3), 2, False, "core")):
        d.died_at = {i: s.now - 10.0 for i in ours[:dead]}
        d.blitz = dict(why="the territory, phase 1") if on else None
        got = d.desperate(s.now, Snapshot(s.now, list(s.players), mode="invasion", **kw))
        if (got is None) != (want is None) or (got is not None and want not in got[1]):
            fails.append(f"Invasion {kw['inv_phase']}, {kw['inv_phase_t']} s, attackers {kw['inv_attackers']}, {dead} "
                         f"dead, blitz on {on}: {got} (want {want})")
    carrier = PlayerState(99, 0, "carrier", core, alive=True, has_flag=True)
    got = d.desperate(s.now, Snapshot(s.now, list(s.players) + [carrier], mode="invasion", inv_phase=3,
                                      inv_phase_t=190.0, inv_attackers=0, inv_core=core, inv_core_carrier=99))
    if got is not None:
        fails.append(f"Invasion phase 3 with the core in our hands: {got} (want none: the carrier's plan)")
    d.died_at, d.blitz = {}, None

    # 2. CTF, the last minute behind, the team strung out (one of it at mid): rally, then all go in two prongs
    s = Sim(mode="ctf", per_team=(4, 4), seed=2, tiers=["top"], map_name="bloodgulch")
    lone = next(p for p in s.players if p.team == 0)
    lone.pos = s.m["points"]["mid"]
    real = D.posture
    D.posture = lambda score, team, *a, **k: Posture(0.9, "all_in") if team == 0 else Posture(0.5, "even")
    try:
        went, rallied, orders, vias = None, False, {}, set()
        for _ in range(int(14.0 / 0.0333)):
            s.step()
            bz = getattr(s.directors[0], "blitz", None)
            if bz is not None and bz.get("go") is None:
                rallied = True
            if bz is not None and bz.get("go") is not None and went is None:
                went = s.now
            if went is not None and s.now - went > 0.5:
                for b in s.bots.values():
                    if b.team == 0 and b.id in bz.get("ids", ()):
                        orders[b.id] = (b.order.role, b.order.point)
                        vias |= {tuple(round(v, 1) for v in (q.x, q.y)) for q in b.order.via}
                break
    finally:
        D.posture = real
    flag = s.directors[0].straight_objective(s.snapshot()) if hasattr(s, "snapshot") else None
    if not rallied or went is None:
        fails.append(f"CTF, the last minute behind: rallied {rallied}, went {went} (want a rally, then go)")
    elif any(r != "runner" for r, p in orders.values()) or len(orders) < 3 or len(vias) < 2:
        fails.append(f"CTF blitz on the go: orders {orders}, prongs {vias} (want every bot a runner, two prongs)")

    # 3. a blitzing runner's urgency
    b = Bot(1, 0, __import__("brain.profiles", fromlist=["make_profile"]).make_profile("top", "rusher", random.Random(4)),
            s.m, random.Random(4))
    me = PlayerState(1, 0, "runner", Vec(0.0, 0.0, 0.0))
    goal = Vec(40.0, 0.0, 0.0)
    foe = Vec(2.0, 9.0, 0.0)
    b.order = Order("runner", goal)
    b.per.beliefs[5] = Belief(foe, Vec(), 50.0, True, "eyes")
    sn = Snapshot(50.0, [me, PlayerState(5, 1, "foe", foe)], mode="ctf")
    plain = {("fight", 5): 3.0}
    b.keep_role(plain, me, sn, {5})
    b.blitz_until = 51.0
    rush = {("fight", 5): 3.0}
    b.keep_role(rush, me, sn, {5})
    if abs(rush[("fight", 5)] - 0.45) > 1e-6 or not plain[("fight", 5)] > 0.45:
        fails.append(f"a side fight 9 u off the line: plain {plain[('fight', 5)]:.2f}, blitzing {rush[('fight', 5)]:.2f} "
                     f"(want 0.45 blitzing, more plain)")

    # 4. Spire phase 3: rally at the foot, the ways up the nav's
    sp = Sim(mode="invasion", per_team=(4, 4), seed=3, tiers=["top"], map_name="reach_35_island")
    dd = sp.directors[sp.objmodes.inv["attackers"]]
    stand = sp.objmodes.inv["core"]
    rally = dd.blitz_rally(Vec(-178.0, -363.0, -55.0), stand)
    prongs = dd.blitz_prongs(rally, stand)
    if rally.z > -45.0 or prongs:
        fails.append(f"Spire: rally {rally}, prongs {prongs} (want the foot, no forced ways up)")

    # 5. the trace: the world line's blitz, and observer.py events lists it (the way to see it in a live game)
    import contextlib
    import io
    import tempfile
    sys.path.insert(0, HERE)
    import observer
    s = Sim(mode="ctf", per_team=(4, 4), seed=2, tiers=["top"], map_name="bloodgulch")
    D.posture = lambda score, team, *a, **k: Posture(0.9, "all_in") if team == 0 else Posture(0.5, "even")
    out = io.StringIO()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "blitz.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                s.run(3.0, trace=f)
            with contextlib.redirect_stdout(out):
                observer.cmd_events(path, 0.0, 1e9)
    finally:
        D.posture = real
    if "team 0 blitz (all_in): go" not in out.getvalue():
        fails.append("trace: no \"team 0 blitz (all_in): go\" in observer.py events")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"blitz OK (desperate by mode; CTF rally then go in {went:.1f} s, {len(orders)} runners on {len(vias)} prongs; "
          f"urgency; Spire rally z {rally.z:.0f}, no forced ways up; in the trace)")


def dist_ok(a, b):
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z)) < 0.5


if __name__ == "__main__":
    main()
