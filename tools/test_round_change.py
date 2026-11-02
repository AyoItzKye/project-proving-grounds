"""Invasion's round change (live Spire, trace 094415: at 530-537 s all 16 players dead, back by 539.8 s; once half were
back the spawn picks by the old phase 3 went out for the rest, their respawns left the new-round count, the round
never read, and the brain played phase 3 all of round 2, everyone spawning there):

1. spawn_check sends no pick while a round's change is pending (invasion.Watch.round_wait_until), half the lobby alive
2. the Watch reads the new round from the respawn burst even when stale picks placed most of it: phase 1 again
3. with no picks out (part 1), the new round reads with its sides: the team spawning in the attackers' phase 1 zone
   attacks; and nearly everyone dead at once sets the wait, the new round clears it

usage: python -I test_round_change.py      -> "round change OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import live_bots  # noqa: E402
from brain import invasion  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

M = get_map("reach_35_island")
T = terrain(M)
SPAWNS = invasion.honor_spawns("reach_35_island")


def man(pid, team, pos, alive=True):
    return PlayerState(pid, team, f"p{pid}", pos, alive=alive)


def main():
    fails = []
    inv = invasion.layout(M["objects"])
    labels = list(inv["res"])
    att_lb = inv["attackers"]
    def_lb = next(lb for lb in labels if lb != att_lb)
    zone = lambda lb: (inv["res"][lb].get(1) or [])[0]
    a_pos, d_pos = zone(att_lb), zone(def_lb)

    # 1. no pick while the round's change is pending
    sent = []

    class W:
        sides_set, placed, round_wait_until = True, set(), 120.0
    w = W()
    players = [man(k, k % 2, d_pos if k % 2 == 0 else a_pos, alive=k % 4 < 2 or k > 11) for k in range(16)]
    players[5] = man(5, 1, Vec(), alive=False)
    snap = Snapshot(110.0, players, mode="invasion", inv_phase=3, inv_attackers=0, inv_zones=[a_pos])
    live_bots.spawn_check(lambda *a: sent.append(a), {5: type("B", (), {})()}, snap, 110.0, {}, SPAWNS, w,
                          random.Random(1), T)
    if sent or w.placed:
        fails.append(f"a round's change pending, half alive: sent {sent}, placed {w.placed} (want nothing)")

    def round_two(placed_ids):
        wt = invasion.Watch(inv, T)
        wt.sides_set, wt.phase, wt.attackers = True, 3, 0
        wt.alive = {k: True for k in range(16)}             # (all alive in round 1 already: not new spawns)
        alive = [man(k, k % 2, a_pos if k % 2 == 0 else d_pos) for k in range(16)]     # round 1: team 0 attacked
        wt.update(None, Snapshot(100.0, alive, mode="invasion"), 100.0)
        for t in range(101, 106):
            wt.update(None, Snapshot(float(t), [man(k, k % 2, Vec(), alive=False) for k in range(16)],
                                     mode="invasion"), float(t))
        waiting = getattr(wt, "round_wait_until", -1.0) > 106.0
        wt.placed = set(placed_ids)
        back = [man(k, k % 2, d_pos if k % 2 == 0 else a_pos) for k in range(16)]      # round 2: team 1 attacks
        wt.update(None, Snapshot(111.0, back, mode="invasion"), 111.0)
        return wt, waiting

    # 2. stale picks placed 12 of the 16: the burst still reads the new round
    wt, waiting = round_two(range(12))
    if wt.phase != 1:
        fails.append(f"12 of 16 placed by stale picks: phase {wt.phase} after the respawn burst (want 1)")
    # 3. no picks out: phase 1 with the new sides; the wait set by the deaths, cleared by the new round
    wt, waiting = round_two(())
    if wt.phase != 1 or wt.attackers != 1:
        fails.append(f"round 2: phase {wt.phase}, attackers {wt.attackers} (want 1 and team 1)")
    if not waiting or getattr(wt, "round_wait_until", -1.0) >= 0:
        fails.append(f"the wait: set {waiting}, after the new round {getattr(wt, 'round_wait_until', None)} (want set, then cleared)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("round change OK (no picks during the change; the new round read with 12 of 16 placed; phase 1, team 1 "
          "attacking)")


if __name__ == "__main__":
    main()
