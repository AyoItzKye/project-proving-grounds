"""King: take a hill they hold (the sims engineer's difficulty pyramid, docs/oct31/sims.md: Easy, running everyone onto
the hill, out-held Heroic 123-15 and Legendary 121-8 hill seconds while losing the kills about 2 to 1; the King plan
put one scorer on the hill and the rest on overlooks, and a scorer waited outside a hill held by theirs for a "clear"
that never came). Director.role_slots / Bot.keep_role on h3_construct's middle as the hill:

1. two of theirs seen in the hill: three of us go in (one more than them), the rest on the spots that see it
2. nobody of theirs on it: one scorer, the rest watching (no blob on a hill we hold)
3. the sighting 5 s old: back to one scorer (KING_TAKE_HOLD)
4. a hill defender with a teammate beside it and a man of theirs in the hill goes in, not waiting outside

usage: python -I test_king_take.py      -> "king take OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("h3_construct")
HILL = M["points"]["mid"]


def team(foes_in, t=50.0, seen_at=None):
    bots = {i: Bot(i, 0, make_profile("strong", "objector", random.Random(i)), M, random.Random(i)) for i in range(1, 5)}
    d = Director(0, M, bots, random.Random(0))
    ps = [PlayerState(i, 0, f"b{i}", HILL + Vec(12.0 + i, 0.0, 0.0)) for i in bots]
    for k in range(foes_in):
        q = HILL + Vec(0.5 * k, 0.5, 0.0)
        ps.append(PlayerState(20 + k, 1, f"e{k}", q))
        bots[1].per.beliefs[20 + k] = Belief(q, Vec(), seen_at if seen_at is not None else t, True, "eyes")
    return d, bots, Snapshot(t, ps, mode="king", hill=HILL, hill_r=3.0)


def on_hill(slots):
    return sum(1 for r, q, f in slots[:4] if r == "defender" and (q - HILL).flat() < 0.5)


def main():
    fails = []
    d, bots, snap = team(2)
    got = on_hill(d.role_slots(50.0, snap, 4))
    if got != 3:
        fails.append(f"two of theirs in the hill: {got} of us sent in (want 3)")
    d, bots, snap = team(0)
    got = on_hill(d.role_slots(50.0, snap, 4))
    if got != 1:
        fails.append(f"nobody of theirs on it: {got} on the hill (want 1)")
    d, bots, snap = team(2, t=50.0, seen_at=44.0)
    got = on_hill(d.role_slots(50.0, snap, 4))
    if got != 1:
        fails.append(f"the sighting 6 s old: {got} on the hill (want 1)")
    # 4. keep_role
    b = Bot(1, 0, make_profile("strong", "objector", random.Random(9)), M, random.Random(9))
    b.order, b.posture = Order("defender", HILL), 0.5
    me = PlayerState(1, 0, "b", HILL + Vec(6.0, 0.0, 0.0))
    mate = PlayerState(2, 0, "m", HILL + Vec(7.0, 1.0, 0.0))
    foe = PlayerState(20, 1, "e", HILL + Vec(0.5, 0.0, 0.0))
    b.per.beliefs[20] = Belief(foe.pos, Vec(), 60.0, True, "eyes")
    scores = {("objective", HILL): 1.0}
    b.keep_role(scores, me, Snapshot(60.0, [me, mate, foe], mode="king", hill=HILL, hill_r=3.0), [20])
    if max(scores, key=scores.get)[0] == "hold":
        fails.append(f"a hill defender with a mate beside it, theirs in the hill: it held outside ({scores})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("king take OK (three in against two, one scorer on a quiet hill, back to one after the hold, in with company)")


if __name__ == "__main__":
    main()
