"""Objective mode reads (brain/modes.py Watch audit):

1. One Bomb (guide 19 ASS-ONE-01, "wrong" in docs/oct31/audit.md): the game's one bomb on team 0's stand for 10 s of
   reads: team 0 attacks this round, so its own goal is no goal (obj_goals has only the defenders'), and team 0's
   director posts nobody on it; two-bomb Assault and Neutral Bomb keep both goals; a side swap waits for the window.
2. Headhunter (HH-01): the skulls lying loose (Reach's skull weapon objects, LiveReach.loose_named) are the mode's
   items, so director.mode_slots sends a runner to the nearest; before, nothing filled them live.

usage: python -I test_modes_reading.py      -> "modes_reading OK (...)"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
from brain import modes  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec, dist  # noqa: E402

fails = []
A, B, GA, GB = (0.0, 0.0, 0.0), (40.0, 0.0, 0.0), (2.0, 0.0, 0.0), (38.0, 0.0, 0.0)


def flag(kind, pos, team):
    return {"type": kind, "pos": list(pos), "team": team}


class FakeLive:
    def __init__(s, items=(), skulls=()):
        s.items, s.skulls = list(items), list(skulls)

    def objective_items(s, raw, stands, mode):
        return [dict(it) for it in s.items]

    def loose_named(s, name):
        return list(s.skulls) if name == "skull" else []


def run(watch, live, secs, t0=0.0):
    snap = None
    for k in range(int(secs / 0.5) + 1):
        snap = Snapshot(t0 + 0.5 * k, [PlayerState(0, 0, "a", Vec()), PlayerState(1, 1, "b", Vec(40, 0, 0))])
        watch.update(live, snap, t0 + 0.5 * k, raw=[])
    return snap


def one_bomb():
    objs = {"netgame_flags": [flag("as_bomb", A, 0), flag("as_bomb", B, 1), flag("as_goal", GA, 0), flag("as_goal", GB, 1)]}
    w = modes.Watch("assault", objs)
    live = FakeLive([dict(pos=A, carrier=None, stand=0)])
    snap = run(w, live, 5.0)
    if sorted(snap.obj_goals) != [0, 1]:
        fails.append(f"One Bomb judged on 5 s of reads: goals {sorted(snap.obj_goals)}")
    snap = run(w, live, 8.0, 5.5)
    if sorted(snap.obj_goals) != [1]:
        fails.append(f"One Bomb, team 0's bomb 13 s: goals {sorted(snap.obj_goals)} (want only the defenders', 1)")
    else:
        from brain.sim import Sim
        sim = Sim("assault", per_team=4, seed=5, map_name="reach_30_settlement")
        d = sim.directors[0]
        s2 = sim.snapshot()
        mine = (s2.obj_goals.get(0) or [None])[0]
        s2.obj_goals = {1: s2.obj_goals.get(1) or []}       # the read above, on a real map: team 0 attacks
        held = [q for r, q, f in d.mode_slots(sim.now, s2, 4) if r == "defender" and mine is not None and dist(q, mine) < 6.0]
        if held:
            fails.append(f"One Bomb attackers still post {len(held)} defenders on their own goal")
    live.items = [dict(pos=B, carrier=None, stand=1)]          # the sides swap: team 1's bomb now
    snap = run(w, live, 5.0, 14.0)
    if sorted(snap.obj_goals) != [0, 1]:
        fails.append(f"One Bomb side swap: goals {sorted(snap.obj_goals)} during the window (want both)")
    snap = run(w, live, 21.0, 19.5)
    if sorted(snap.obj_goals) != [0]:
        fails.append(f"One Bomb after the swap: goals {sorted(snap.obj_goals)} (want 0's only)")
    w2 = modes.Watch("assault", objs)
    snap = run(w2, FakeLive([dict(pos=A, carrier=None, stand=0), dict(pos=B, carrier=None, stand=1)]), 15.0)
    if sorted(snap.obj_goals) != [0, 1]:
        fails.append(f"two-bomb Assault: goals {sorted(snap.obj_goals)}")
    objs3 = {"netgame_flags": [flag("as_bomb", (20.0, 0.0, 0.0), 8), flag("as_goal", GA, 0), flag("as_goal", GB, 1)]}
    snap = run(modes.Watch("assault", objs3), FakeLive([dict(pos=(20.0, 0.0, 0.0), carrier=None, stand=0)]), 15.0)
    if sorted(snap.obj_goals) != [0, 1]:
        fails.append(f"Neutral Bomb: goals {sorted(snap.obj_goals)}")


def headhunter():
    objs = {"netgame_flags": [flag("hh_drop_point", (10.0, 0.0, 0.0), 8)]}
    w = modes.Watch("headhunter", objs)
    snap = run(w, FakeLive(skulls=[(5.0, 1.0, 0.0)]), 1.0)
    if [(it["pos"].x, it["kind"], it["carrier"]) for it in snap.obj_items] != [(5.0, "skull", None)]:
        fails.append(f"Headhunter skulls not read: {snap.obj_items}")
    from brain.live import LiveReach
    if not hasattr(LiveReach, "loose_named"):
        fails.append("LiveReach has no loose_named reader")
    from brain.sim import Sim
    sim = Sim("headhunter", per_team=4, seed=5, map_name="reach_30_settlement")
    d = sim.directors[0]
    s2 = sim.snapshot()
    skull = s2.players[0].pos + Vec(3, 0, 0)
    s2.obj_items = [dict(pos=skull, carrier=None, kind="skull", team=8)]
    if not any(r == "runner" and dist(q, skull) < 0.01 for r, q, f in d.mode_slots(sim.now, s2, 4)):
        fails.append("Headhunter: no runner for a skull lying near the team")


def main():
    for part in (one_bomb, headhunter):
        try:
            part()
        except Exception as e:
            fails.append(f"{part.__name__}: {type(e).__name__}: {e}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("modes_reading OK (One Bomb's attackers lose their own goal, two-bomb and Neutral keep both, a swap waits; "
          "Headhunter skulls read and run for)")


if __name__ == "__main__":
    main()
