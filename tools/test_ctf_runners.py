"""CTF runners keep going (the player's Halo 3 Sandtrap CTF, Nov 11 11:18, his team all Legendary: "the legendary team
isnt even going anywhere near the flag 99% of the time, they keep straggling between attempting to go for the enemy
flag and also running back to base"; live: near their flag 10% of the time, orders changed 3.9 times a bot-minute).
His team's director replayed on that match's first 100 s (tools/fixtures/shrine_ctf_111849.json.gz: everyone's
place, the flags and vehicles as read live), the old play (director.KEEP_RUNNERS off) against the new:

1. a turn-back: a runner (the director's role) given an order whose point is TURN_BACK u or more farther from their
   flag than he is, while both flags are home: none (the old play: the attack wave's gather relabelled runners "mid",
   a cancelled wave and the next pass's deal by the living left them "mid", sent to the push point behind them; a
   power vehicle's crew took one every pass)
2. the old play turns runners back here (the test sees the fault)
(With our flag carried the collapse on their carrier is everyone's, runners too: research 12 section 3.5, guarded by
tools/test_ctf_effort.py.)

usage: python -I test_ctf_runners.py      -> "ctf runners OK"
"""
import gzip
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import director as D  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import FlagState, PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

FIX = json.load(gzip.open(os.path.join(HERE, "fixtures", "shrine_ctf_111849.json.gz"), "rt", encoding="utf-8"))
TEAM = 0
TURN_BACK = 5.0
M = get_map(FIX["map"])


def snap_of(r):
    ps = [PlayerState(q[0], q[1], f"p{q[0]}", Vec(q[3], q[4], q[5]), alive=bool(q[2]), is_bot=bool(q[6]),
                      has_flag=bool(q[7]), vehicle=q[8]) for q in r["world"]]
    fl = {int(k): FlagState(int(k), M["flags"][int(k)], Vec(v[1], v[2], v[3]), v[0], v[4])
          for k, v in (r.get("flags") or {}).items() if v}
    veh = [dict(handle=v[0], kind=v[1], pos=(v[2], v[3], v[4]), riders=v[5], team=v[6], occupied=bool(v[5]))
           for v in r["vehicles"]]
    return Snapshot(r["t"], ps, fl, score={int(k): v for k, v in r["score"].items()}, mode=r["mode"], vehicles=veh)


def flat(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def run(keep):
    D.KEEP_RUNNERS = keep
    bots = {int(i): Bot(int(i), m[0], make_profile(m[1], m[2], random.Random(int(i))), M, random.Random(int(i)))
            for i, m in FIX["bots"].items() if m[0] == TEAM}
    d = D.Director(TEAM, M, bots, random.Random(0))
    home_back = []
    was_runner = {}
    for r in FIX["rows"]:
        snap = snap_of(r)
        d.update(r["t"], snap)
        own, theirs = snap.flags.get(TEAM), snap.flags.get(1 - TEAM)
        if own is None or theirs is None:
            continue
        for b in bots.values():
            me = snap.player(b.id)
            o = b.order
            if (me.alive and was_runner.get(b.id) and not me.has_flag and own.state == "home" and theirs.state == "home"
                    and o.point is not None and o.role not in ("ride", "board")
                    and flat(o.point, theirs.pos) > flat(me.pos, theirs.pos) + TURN_BACK):
                home_back.append((round(r["t"], 1), b.id, o.role, round(flat(me.pos, theirs.pos), 1)))
        was_runner = {b.id: d.roles.get(b.id) == "runner" for b in bots.values()}
    return home_back


def main():
    fails = []
    keep0 = D.KEEP_RUNNERS
    try:
        old = run(False)
        new = run(True)
    finally:
        D.KEEP_RUNNERS = keep0
    for name, back in (("old", old), ("new", new)):
        print(f"{name}: runners turned back, both flags home: {len(back)} {back[:5]}")
    if new:
        fails.append(f"1: runners turned back with both flags home {new[:5]}")
    if not old:
        fails.append("2: the old play turned no runner back: the replay does not show the fault")
    if fails:
        sys.exit("FAIL " + "; ".join(fails))
    print("ctf runners OK")


if __name__ == "__main__":
    main()
