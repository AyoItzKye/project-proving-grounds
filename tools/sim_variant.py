"""Run the simulator once for A/B tests of a rule (one seed per run: a single seed is mostly noise,
compare several), optionally with Terrain's stuck-learning settings overridden, and print the learned
stuck spots before and after.

usage: python -I sim_variant.py <map> <seconds> <seed> <trace.jsonl> [votes bots per_match]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.maps import get_map, terrain  # noqa: E402
from brain.terrain import Terrain  # noqa: E402

name, seconds, seed, trace = sys.argv[1:5]
if len(sys.argv) > 7 and hasattr(Terrain, "STUCK_VOTES"):
    Terrain.STUCK_VOTES, Terrain.STUCK_BOTS, Terrain.STUCK_PER_MATCH = map(int, sys.argv[5:8])
before = len(terrain(get_map(name)).stuck)
sys.argv = ["sim", "--trace", trace, "--map", name, "--seconds", seconds, "--limit", "50", "--seed", seed]
from brain import sim  # noqa: E402
sim.main()
print(f"LEARNED {name} seed {seed}: {before} -> {len(terrain(get_map(name)).stuck)}")
