"""Jetpack fuel like a person (live Spire 20261105-143525 at 969.6 s: a Spartan still did not let its jetpack
recharge before using it). The trace (logs/tmp/jetfuel.py): bots 2, 4 and 8 pressed "jetpack up the ledge" for 4.0 s,
let go 0.6-0.7 s, pressed again, 930-970 s: every press after the first on a tank of 0.09-0.11 (the tag's model: the
0.1 minimum after 0.7 s of 0.15/s recharge), the game's on-state up only 27-36 of ~105 ticks a press, 0.1-1.5 u
climbed. Of the match's 275 presses, 66 started under half a tank.

1. plan: a ledge 6 u up 2 u ahead, nobody about: flown on a full tank, not on 0.12 (over the tag's 0.1 minimum);
   Reach and Halo 4
2. an emergency goes on what is left: a grenade at our feet on 0.12 (jetpack up out of the grenade)
3. act, the ledge kept ahead 20 s (a bot that cannot get up, as the trace's): every press starts on a tank of JET_FULL
   or more, none is held on an empty tank, and it flies again once refilled

usage: python -I test_jetpack_fuel.py      -> "jetpack fuel OK (...)"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.equipment as EQ  # noqa: E402
from brain.core import Action, Snapshot, Vec  # noqa: E402
from test_equipment import A, DT, bot, me_state, plan_now  # noqa: E402

JET_FULL = getattr(EQ, "JET_FULL", 0.9)
LEDGE = A + Vec(2.0, 0.0, 6.0)


def ledge_bot(game):
    b = bot("strong", game, "jetpack")
    b.wp, b.goal = LEDGE, ("objective", LEDGE)
    return b


def plan_at(b, level, **kw):
    b.kit.perceive(b, 1.0, me_state(b, A, 0.0, 0.0), Snapshot(1.0, [me_state(b, A, 0.0, 0.0)]))
    b.kit.energy.level = level
    return plan_now(b, [], (), b.goal, **kw)[4]


def main():
    fails, info = [], []
    for game in ("reach", "h4"):
        # 1
        got = plan_at(ledge_bot(game), 1.0)
        if got != "jetpack up the ledge":
            fails.append(f"{game}: a ledge 6 u up on a full tank: {got!r} (want flown)")
        got = plan_at(ledge_bot(game), 0.12)
        if got is not None:
            fails.append(f"{game}: a ledge on a tank of 0.12: {got!r} (want it left to refill)")
        # 2
        b = ledge_bot(game)
        b.nade_at = (A + Vec(1.0, 0.0, 0.0), 4.0)
        got = plan_at(b, 0.12)
        if got != "jetpack up out of the grenade":
            fails.append(f"{game}: a grenade at our feet on 0.12: {got!r} (want up out of it)")

        # 3
        b = ledge_bot(game)
        starts, dry, t, was = [], 0, 1.0, False
        while t < 21.0:
            me = me_state(b, A, 0.0, 0.0)
            snap = Snapshot(t, [me])
            b.kit.perceive(b, t, me, snap)
            lvl = b.kit.energy.level
            a = Action()
            b.kit.act(b, t, DT, me, snap, a)
            if a.equipment and not was:
                starts.append((round(t, 2), round(lvl, 2)))
            dry += a.equipment and lvl <= 0.0
            was, t = a.equipment, t + DT
        low = [p for p in starts if p[1] < JET_FULL]
        if low or dry or len(starts) < 2:
            fails.append(f"{game}: the ledge kept ahead 20 s: presses (t, tank) {starts}, {len(low)} under {JET_FULL}, "
                         f"{dry} ticks held on an empty tank (want none, and a second flight once refilled)")
        info.append(f"{game} {len(starts)} flights in 20 s")
    for f in fails:
        print("FAIL", f)
    if fails:
        sys.exit(1)
    print(f"jetpack fuel OK ({'; '.join(info)})")


if __name__ == "__main__":
    main()
