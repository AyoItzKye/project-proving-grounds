"""CTF attack waves that never gather pause (Director.wave_tick, WAVE_FAILS / WAVE_SKIP_S). High Ground in the sim: the
rally was fought over, gatherers died one by one, 13 waves gathered and 2 went in, 0 captures in 4 x 300 s; with the
pause 11 pickups and a capture, the other CTF maps unchanged (98 pickups either way, logs/tmp/nov12/ctf_fail_ab.txt).

1. a wave that ends still gathering, once: the normal WAVE_COOL_S pause
2. the second running: the waves pause WAVE_SKIP_S
3. a wave that went in clears the count
4. switch off (WAVE_FAILS huge): never the long pause
5. the sim's spawn split: High Ground's spawns (94 marked team 0, 2 team 1) go to the nearer flag's team on both sides

usage: python -I test_wave_giveup.py      -> "wave give-up OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.director as DD  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec, dist  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402

M = get_map("h3_deadlock")
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def end_wave(d, now, went=False):
    flag = M["flags"][1]
    d.wave = dict(t0=now - DD.WAVE_GATHER_S - DD.WAVE_GO_S - 1.0, rally=flag, target=flag, go=now if went else None,
                  prongs=[()], ids=set())
    flags = {1: FlagState(1, flag, flag)}             # (their flag home: the wave was live)
    d.wave_tick(now, Snapshot(now, [PlayerState(1, 0, "b", Vec(0, 0, 0))], flags=flags, mode="ctf"))
    return d.wave_cool - now


d = Director(0, M, {}, random.Random(1))
check("1. one wave that never went: the short pause", abs(end_wave(d, 100.0) - DD.WAVE_COOL_S) < 0.01)
check("2. the second running: the long pause", abs(end_wave(d, 200.0) - DD.WAVE_SKIP_S) < 0.01)
end_wave(d, 300.0)
end_wave(d, 400.0, went=True)
check("3. a wave that went in clears the count", abs(end_wave(d, 500.0) - DD.WAVE_COOL_S) < 0.01)
DD.WAVE_FAILS = 99
d2 = Director(0, M, {}, random.Random(1))
long_ = [end_wave(d2, 100.0 * k) for k in range(1, 5)]
DD.WAVE_FAILS = 2
check("4. switch off: never the long pause", all(abs(x - DD.WAVE_COOL_S) < 0.01 for x in long_), long_)

from brain.sim import Sim  # noqa: E402
sim = Sim("ctf", per_team=4, seed=1, map_name="h3_deadlock")
f0, f1 = M["flags"][0], M["flags"][1]
pts = {t: [sim.spawn_point(t) for _ in range(40)] for t in (0, 1)}
near_own = {t: sum(1 for p in pts[t] if dist(p, M["flags"][t]) < dist(p, M["flags"][1 - t])) / 40 for t in (0, 1)}
check("5. High Ground: each team spawns on its own half", min(near_own.values()) > 0.9, near_own)
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("wave give-up OK")
