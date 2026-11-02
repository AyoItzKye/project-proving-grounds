"""Holding with intent and the carrier's escorts (Spire Invasion at 437 s:: four of the core carrier's six escorts went to
a Warthog's gun or waited at a wheel, none of his within 25 u as he dropped off the top):

1. two of ours holding a post, three enemies seen on it: a holder calls "Need backup, <zone>!" (an urgent call) and
   the two nearest pushers within BACKUP_REACH go to it as its defenders; one past BACKUP_REACH and a runner do not
2. the same post with one enemy on it (we outnumber him), or with the sighting 4 s old, or in Assault (the attack
   scores there: plants 7 -> 3 in 6 sim games with backup): no call, nobody sent
3. our carrier out: his escort beside a Warthog that wants a gunner is not sent to its gun (hop on the gun) nor called
   aboard (rider_calls); a pusher there is

usage: python -I test_backup.py      -> "backup OK"
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

M = get_map("bloodgulch")
P = M["points"]["mid"]


def setup(foe_n, age=0.5, t=50.0, mode="territories"):
    roles = {1: ("defender", P, P + Vec(1, 0, 0)), 2: ("defender", P, P + Vec(-1, 1, 0)),
             3: ("mid", Vec(P.x + 30, P.y, P.z), P + Vec(20, 0, 0)), 4: ("mid", Vec(P.x + 30, P.y, P.z), P + Vec(15, 5, 0)),
             5: ("mid", Vec(P.x - 30, P.y, P.z), P + Vec(0, 60, 0)), 6: ("runner", M["flags"][1], P + Vec(6, 0, 0)),
             7: ("mid", Vec(P.x + 30, P.y, P.z), P + Vec(25, -5, 0))}
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), M, random.Random(i)) for i in roles}
    d = Director(0, M, bots, random.Random(1))
    ps = []
    for i, (role, pt, pos) in roles.items():
        bots[i].order = Order(role, pt)
        d.roles[i] = role
        ps.append(PlayerState(i, 0, f"b{i}", pos))
    for k in range(foe_n):
        q = P + Vec(3.0 + k, 4.0, 0.0)
        ps.append(PlayerState(20 + k, 1, f"e{k}", q))
        bots[1].per.beliefs[20 + k] = Belief(q, Vec(), t - age, True, "eyes")
    return d, bots, Snapshot(t, ps, mode=mode)


def main():
    fails = []
    # 1. contested
    d, bots, snap = setup(3)
    d.backup_orders(50.0, snap, list(bots.values()))
    sent = sorted(i for i in (3, 4, 5, 6, 7) if bots[i].order.role == "defender")
    if sent != [3, 4]:
        fails.append(f"three on a post two of ours hold: sent {sent} (want the two nearest pushers, 3 and 4)")
    calls = [c for c in d.voice.queue + d.voice.in_flight if c.kind == "backup"]
    if not calls or not calls[0].urgent or not d.text(calls[0]).startswith("Need backup"):
        fails.append(f"no urgent backup call queued ({[(c.kind, d.text(c)) for c in d.voice.queue]})")
    if bots[6].order.role != "runner":
        fails.append("the runner was pulled off its run for backup")
    # 2. not contested
    for n, age, mode, why in ((1, 0.5, "territories", "one enemy on it"), (3, 4.0, "territories", "a sighting 4 s old"),
                              (3, 0.5, "assault", "Assault (the attack scores there)")):
        d, bots, snap = setup(n, age, mode=mode)
        d.backup_orders(50.0, snap, list(bots.values()))
        if any(bots[i].order.role == "defender" for i in (3, 4, 5, 7)) or \
                any(c.kind == "backup" for c in d.voice.queue + d.voice.in_flight):
            fails.append(f"{why}: backup sent or called")
    # 3. our carrier's escort stays on him
    W = M["flags"][0] + Vec(10.0, 0.0, 0.0)
    bots = {i: Bot(i, 0, make_profile("top", "objector", random.Random(i)), M, random.Random(i)) for i in (1, 2, 3)}
    d = Director(0, M, bots, random.Random(2))
    bots[1].order, bots[2].order = Order("escort", W, target=9), Order("mid", M["flags"][1])
    d.roles = {1: "escort", 2: "mid", 3: "runner"}
    bots[3].order = Order("runner", M["flags"][0])
    ps = [PlayerState(1, 0, "esc", W + Vec(3, 0, 0)), PlayerState(2, 0, "mid", W + Vec(-3, 0, 0)),
          PlayerState(3, 0, "car", W + Vec(0, 20, 0), has_flag=True), PlayerState(9, 0, "you", W, vehicle=77, is_bot=False)]
    hog = dict(handle=77, kind="warthog", pos=(W.x, W.y, W.z), riders=1, occupied=True, team=0, gunner=False,
               up=(0.0, 0.0, 1.0))
    snap = Snapshot(60.0, ps, mode="ctf", vehicles=[hog])
    d.vehicle_orders(60.0, snap, list(bots.values()))
    if bots[1].order.role != "escort":
        fails.append(f"our carrier out: his escort sent to {bots[1].order.role} (want it on him)")
    if bots[2].order.role not in ("ride", "board"):
        fails.append(f"our carrier out: the pusher by the Warthog was not sent aboard ({bots[2].order.role})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("backup OK (contested post: call + the two nearest pushers; no call outnumbered or stale; the carrier's escort"
          " kept)")


if __name__ == "__main__":
    main()
