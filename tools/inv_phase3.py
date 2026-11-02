"""Reach Invasion's phase 3 (the core run) on its own in the simulator (brain/sim.py + brain/sim_modes.py): every player
put at its team's phase-3 spawn, the gates open, then SECONDS of play; per seed when the core was picked up, by whom,
whether it was delivered, and the attackers' closest approach. For checking each Invasion map's core run quickly (a
whole sim game reaches phase 3 at 400 s or never).

usage: python -I inv_phase3.py <map> [--seeds 1,2,3] [--seconds 180] [--per-team 6] [--trace out.jsonl]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import invasion  # noqa: E402
from brain.core import dist  # noqa: E402
from brain.sim import Sim  # noqa: E402


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def one(map_name, seed, seconds, per_team, trace=None):
    sim = Sim("invasion", per_team=per_team, seed=seed, map_name=map_name)
    om = sim.objmodes
    om.phase, om.phase_t, om.held = 3, sim.now, {}
    invasion.apply_barriers(sim.T, om.inv, {b["key"]: False for b in om.inv["barriers"] if b["kind"] == "gate"})
    for p in sim.players:
        p.pos = sim.spawn_point(p.team)
    core = om.core["pos"]
    best = 1e9
    f = open(trace, "w") if trace else None
    steps = int(seconds / 0.5)
    picked = delivered = None
    for _ in range(steps):
        sim.run(0.5, trace=f)
        for p in sim.players:
            if p.alive and p.team == 1:
                best = min(best, dist(p.pos, core))
        for t, e in om.events:
            if "picked up" in e and picked is None:
                picked = (t, e)
            if "delivered" in e and delivered is None:
                delivered = t
        if delivered is not None:
            break
    if f:
        f.close()
    return picked, delivered, best, om.events


def main():
    map_name = sys.argv[1]
    seeds = [int(x) for x in arg("--seeds", "1,2,3").split(",")]
    seconds, per_team = float(arg("--seconds", 180)), int(arg("--per-team", 6))
    ok = 0
    for seed in seeds:
        picked, delivered, best, ev = one(map_name, seed, seconds, per_team, arg("--trace", None) if seed == seeds[0] else None)
        ok += picked is not None
        print(f"{map_name} seed {seed}: picked {picked}, delivered {delivered}, attackers' closest to the core "
              f"{best:.1f} u", flush=True)
    print(f"{map_name}: core picked up in {ok} of {len(seeds)}")


if __name__ == "__main__":
    main()
