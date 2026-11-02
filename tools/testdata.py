"""Data some tests need that the public release does not ship: each user's own LiDAR scans and what the bots learned
on their PC (maps/<map>/lidar.json and the learned files beside it), recordings in logs/, built binaries. A test that
needs one calls need() or need_lidar() first: without the data it prints SKIP with what would enable it and exits 0,
so a fresh copy of the project passes its own suite and a mapped PC still runs every test in full.
"""
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def need(*paths, why=""):
    """Every path (relative to the project) exists, else SKIP (exit 0)."""
    missing = [p for p in paths if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        name = os.path.basename(sys.argv[0])
        print(f"SKIP {name}: needs {', '.join(missing)}" + (f" ({why})" if why else ""))
        raise SystemExit(0)


def need_lidar(*maps):
    """Each map has its LiDAR scan (run LiDAR mapping on it), else SKIP."""
    need(*(f"maps/{m}/lidar.json" for m in maps), why="run LiDAR mapping on " + ", ".join(maps))
