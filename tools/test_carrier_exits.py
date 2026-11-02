"""Map brain INTER-LIFT-03 / MOVE-02: a carrier (flag, ball, bomb) rides a lift, a man cannon or a big drop, or steps
onto a teleporter, only to an exit a teammate holds (Bot.uncovered through exit_watched: exit_held, pad_held). On the
real level drops test_exit_held finds (one with a short way round, one with none):

1. Carrying, nobody of ours at the landing and no enemy known: the way round (first drop) or a wait at the edge that
   ends after 6 s (second); with a teammate at the landing: it drops at once.
2. Not carrying: drops at once (unchanged); carrying the Invasion core in phase 3 (assaulting): drops at once (its
   man cannons and lifts are the way: the player, live Spire).
3. Bot.think fills what the rule reads: teammates alive (not itself, not an enemy) and whether it carries.

usage: python -I test_carrier_exits.py      -> "carrier_exits OK (...)"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(1, HERE)
import test_exit_held as X  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402


def carrier(m, T, mates=(), assault=False):
    b = X.fresh(m, T, "top")
    b.carrying_now, b.mates_now, b.assaulting = True, list(mates), assault
    return b


def main():
    fails, now = [], 100.0
    m = drops = None
    for name in X.MAPS:
        m = get_map(name)
        drops = X.find_drops(m, random.Random(3))
        if len(drops) == 2:
            break
    if not drops or len(drops) != 2:
        sys.exit("FAIL: no map with both kinds of test drop")
    for kind, (T, a, b) in drops.items():
        if not X.step(X.fresh(m, T, "top"), T, a, b, now).jump:
            fails.append(f"{kind}: not carrying, no enemy: did not drop")
        bot = carrier(m, T)
        act = X.step(bot, T, a, b, now)
        if act.jump:
            fails.append(f"{kind}: carrying, nobody of ours at the landing: dropped")
        elif kind == "round" and getattr(bot, "round_until", 0.0) <= now:
            fails.append("round: carrying, did not take the way round")
        elif kind == "wait":
            t, jumped = now, None
            while t < now + 8.0 and jumped is None:
                t += 0.5
                if X.step(bot, T, a, b, t).jump:
                    jumped = t - now
            if jumped is None or not 6.0 <= jumped <= 7.0:
                fails.append(f"wait: carrying, dropped after {jumped} s, not after the 6 s wait")
        if not X.step(carrier(m, T, mates=[b + Vec(0.8, 0.0, 0.0)]), T, a, b, now).jump:
            fails.append(f"{kind}: carrying, a teammate at the landing: did not drop")
        if not X.step(carrier(m, T, assault=True), T, a, b, now).jump:
            fails.append(f"{kind}: the Invasion core's carrier in phase 3 held back")
    T, a, b = drops["round"]
    tb = X.fresh(m, T, "top")
    snap = Snapshot(now, [PlayerState(1, 0, "bot", a, yaw=0.0, has_flag=True), PlayerState(2, 0, "mate", b),
                          PlayerState(3, 1, "foe", b + Vec(1, 0, 0)), PlayerState(4, 0, "dead", b, alive=False)])
    tb.think(now, 1 / 30, snap, T.los, lambda p, q, **k: T.nav(p, q, **k), [])
    if getattr(tb, "carrying_now", None) is not True or getattr(tb, "mates_now", None) != [b]:
        fails.append(f"Bot.think: carrying {getattr(tb, 'carrying_now', None)}, mates {getattr(tb, 'mates_now', None)}")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("carrier_exits OK (a carrier goes round or waits 6 s unless a teammate holds the exit; others and the "
          "Invasion core's carrier as before)")


if __name__ == "__main__":
    main()
