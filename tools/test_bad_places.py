"""Bad places and big recordings (a place read mid-change, 2 million units out, made an 11 million sample sight line, the
brain died of memory and nothing filed the flags; each flag also copied the whole 457 MB recording):

1. live_bots.place_ok: three finite numbers under 100,000 u
2. live_bots.snapshot: a player read at NaN or millions of units out keeps his last good place (still alive); one never
   seen before is not alive; a vehicle read at NaN is left out
3. Terrain: a sight line millions of units long is no sight and costs nothing; nav and path_ahead from or to a NaN place
   give no way instead of a crash
4. bug_reports.catch_up: a growing recording copied on by what was added only; a shorter source copied whole

usage: python -I test_bad_places.py      -> "bad places OK"
"""
import math
import os
import shutil
import sys
import tempfile
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
import bug_reports  # noqa: E402
import live_bots  # noqa: E402


def fake_live(players, vehicles=()):
    return types.SimpleNamespace(players=lambda: [dict(p) for p in players], flags=lambda raw, stands=None: [],
                                 objects=lambda types_: list(vehicles))


def person(i, pos, bot=False):
    return dict(index=i, name=f"p{i}", team=0, unit=0x10000 + i, pos=pos, aim=(1.0, 0.0, 0.0), shield=1.0, health=1.0,
                weapon="dmr", vehicle=-1)


def main():
    fails = []
    # 1. place_ok
    for p, want in (((1.0, 2.0, 3.0), True), ((float("nan"), 0.0, 0.0), False), ((2.2e6, 0.0, 0.0), False),
                    (None, False), ((1.0, 2.0), False)):
        if live_bots.place_ok(p) != want:
            fails.append(f"1. place_ok{p} != {want}")
    # 2. snapshot
    live_bots.MAP = dict(base="test", flags={}, name="test")
    prev = {}
    s1 = live_bots.snapshot(fake_live([person(0, (10.0, 0.0, 0.0)), person(1, (20.0, 0.0, 0.0))]), 1.0, prev, {1})
    prev = {p.id: p.pos for p in s1.players if p.alive}
    s2 = live_bots.snapshot(fake_live([person(0, (float("nan"), 0.0, 0.0)), person(1, (2.2e6, 0.0, 0.0)),
                                       person(2, (float("inf"), 0.0, 0.0))],
                                      [(0x70007, 1, "warthog", (float("nan"), 0.0, 0.0))]), 1.1, prev, {1})
    got = {p.id: (p.alive, (p.pos.x, p.pos.y, p.pos.z)) for p in s2.players}
    if got.get(0) != (True, (10.0, 0.0, 0.0)) or got.get(1) != (True, (20.0, 0.0, 0.0)) or got.get(2, (False,))[0]:
        fails.append(f"2. players after a bad read: {got} (want 0 and 1 at their last places, 2 not alive)")
    if s2.vehicles:
        fails.append(f"2. a vehicle read at NaN is in the snapshot: {s2.vehicles}")
    # 3. the terrain
    T = terrain(get_map("reach_forge_halo"))
    a = Vec(60.9, 210.1, 44.65)
    t0 = time.perf_counter()
    try:
        far = T._ray(a, Vec(2.2e6, 210.1, 44.65), 0.4)
    except MemoryError as e:
        far = e
    took = time.perf_counter() - t0
    if far is not False or took > 0.05:
        fails.append(f"3. a 2 million u sight line: {far} in {took:.3f} s (want no sight, at once)")
    nan = Vec(float("nan"), 0.0, 0.0)
    try:
        w, ahead = T.nav(a, nan), T.path_ahead(nan, a)
        if w is not None or ahead != []:
            fails.append(f"3. a way to / from NaN: nav {w}, path_ahead {ahead[:3]} (want none)")
    except Exception as e:
        fails.append(f"3. a way to / from NaN crashed: {type(e).__name__}: {e}")
    # 4. catch_up
    tmp = tempfile.mkdtemp(prefix="halo_catchup_")
    try:
        src, dst = os.path.join(tmp, "trace.jsonl"), os.path.join(tmp, "copy.jsonl")
        open(src, "wb").write(b"a" * 100)
        bug_reports.catch_up(src, dst)
        open(src, "ab").write(b"b" * 50)
        whole, bug_reports.shutil.copyfile = bug_reports.shutil.copyfile, None   # (a whole copy would fail now)
        try:
            bug_reports.catch_up(src, dst)
        finally:
            bug_reports.shutil.copyfile = whole
        if open(dst, "rb").read() != b"a" * 100 + b"b" * 50:
            fails.append("4. the copy after the recording grew is not the recording")
        open(src, "wb").write(b"c" * 10)                  # another recording, shorter
        bug_reports.catch_up(src, dst)
        if open(dst, "rb").read() != b"c" * 10:
            fails.append("4. a shorter recording was not copied whole")
    except Exception as e:
        fails.append(f"4. catch_up: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        sys.exit("bad places FAILED:\n  " + "\n  ".join(fails))
    print("bad places OK")


if __name__ == "__main__":
    main()
