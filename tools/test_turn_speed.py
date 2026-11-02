"""Turn speed by difficulty.

1. Easy < Normal < Heroic < Legendary, every tier's bots carry theirs (make_profile)
2. a 180 asked for in one tick turns only turn x dt; a small turn passes untouched
3. the walk is re-aimed: a step planned in the wanted view still goes the same way in the world from the view it gets;
   in a vehicle the throttle is left alone
4. a whole 180 at each tier's speed, tick by tick through Bot.think's filter: Legendary about 0.18 s, Easy about 0.67 s
5. a flick (Aim.step) plans no swing quicker than the turn speed

usage: python -I test_turn_speed.py      -> "turn speed OK"
"""
import math
import os
import random
import sys
from types import SimpleNamespace as NS

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Aim, Bot  # noqa: E402
from brain.core import Action, Vec, wrap  # noqa: E402
from brain.profiles import TURN, make_profile  # noqa: E402

DT = 1 / 30


def heading(yaw, act):
    return yaw + math.atan2(act.strafe, act.forward)


def main():
    fails = []
    order = ["novice", "average", "strong", "top"]
    # 1
    if [TURN[t] for t in order] != sorted(TURN[t] for t in order) or len(set(TURN.values())) != 4:
        fails.append(f"1. turn speeds out of order: {[round(math.degrees(TURN[t])) for t in order]}")
    for t in order:
        p = make_profile(t, "rusher", random.Random(1))
        if p.turn != TURN[t]:
            fails.append(f"1. a {t} bot turns at {math.degrees(p.turn):.0f} deg/s")
    # 2, 3
    me = NS(yaw=0.0, pitch=0.0, vehicle=-1)
    bot = NS(p=NS(turn=TURN["average"]))
    act = Action(yaw=math.pi * 0.999, pitch=0.0, forward=1.0)
    want = heading(act.yaw, act)
    Bot.turn_cap(bot, me, act, DT)
    if not math.isclose(abs(wrap(act.yaw)), TURN["average"] * DT, rel_tol=1e-6):
        fails.append(f"2. a 180 in one tick turned {math.degrees(act.yaw):.1f} deg (want {math.degrees(TURN['average'] * DT):.1f})")
    if abs(wrap(heading(act.yaw, act) - want)) > 1e-6 or not math.isclose(math.hypot(act.forward, act.strafe), 1.0, rel_tol=1e-6):
        fails.append(f"3. the walk went {math.degrees(heading(act.yaw, act)):.1f} deg (want {math.degrees(want):.1f})")
    small = Action(yaw=0.05, pitch=0.01, forward=0.6, strafe=0.3)
    Bot.turn_cap(bot, me, small, DT)
    if (small.yaw, small.pitch, small.forward, small.strafe) != (0.05, 0.01, 0.6, 0.3):
        fails.append("2. a small turn was changed")
    car = Action(yaw=3.0, forward=1.0)
    Bot.turn_cap(bot, NS(yaw=0.0, pitch=0.0, vehicle=4), car, DT)
    if (car.forward, car.strafe) != (1.0, 0.0):
        fails.append("3. a vehicle's throttle was turned into a strafe")
    # ... and Bot.think puts every plan through it
    tb = Bot.__new__(Bot)
    tb.id, tb.p = 3, NS(turn=TURN["average"])
    tb.plan = lambda *a, **k: Action(yaw=math.pi * 0.999, pitch=0.0, forward=1.0)
    out = tb.think(0.0, DT, NS(player=lambda i: NS(yaw=0.0, pitch=0.0, vehicle=-1, alive=True)), None, None, None)
    if abs(wrap(out.yaw)) > TURN["average"] * DT * 1.0001:
        fails.append(f"2. Bot.think let a {math.degrees(out.yaw):.0f} degree turn through in one tick")
    # 4
    for t, lo, hi in (("top", 0.15, 0.22), ("novice", 0.6, 0.72)):
        b, yaw, ticks = NS(p=NS(turn=TURN[t])), 0.0, 0
        while abs(wrap(math.pi - yaw)) > 1e-3 and ticks < 200:
            a = Action(yaw=math.pi, pitch=0.0)
            Bot.turn_cap(b, NS(yaw=yaw, pitch=0.0, vehicle=-1), a, DT)
            yaw, ticks = a.yaw, ticks + 1
        if not lo <= ticks * DT <= hi:
            fails.append(f"4. a {t} 180 took {ticks * DT:.2f} s (want {lo}-{hi})")
    # 5
    p = make_profile("top", "rusher", random.Random(2))
    aim = Aim(p, random.Random(3))
    me2 = NS(pos=Vec(0, 0, 0), vel=Vec(0, 0, 0), yaw=0.0, pitch=0.0, weapon="dmr", team=0, crouching=False)
    aim.step(0.0, DT, me2, 7, Vec(-10, 0.5, 0), Vec(0, 0, 0), False)
    if aim.flick is None:
        fails.append("5. no flick onto a man behind")
    else:
        y0, _, y1, _, _, dur = aim.flick
        if 1.5 * abs(wrap(y1 - y0)) / dur > p.turn * 1.0001:
            fails.append(f"5. the flick peaks at {math.degrees(1.5 * abs(y1 - y0) / dur):.0f} deg/s "
                         f"(turn {math.degrees(p.turn):.0f})")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("turn speed OK (Easy 270, Normal 435, Heroic 650, Legendary 1000 deg/s; walking keeps its way)")


if __name__ == "__main__":
    main()
