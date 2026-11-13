"""The player's Triplicate Oddball, Nov 12 (live 20261112-204733, "almost a gold standard match"): "Sometimes bots get into
passenger seats or gunner seats when there is no driver, getting in a car should look like this typically if youre not an
objective carrier: Driver, Gunner, Passenger" and "sometimes the bots would just be standing there looking at the ball like
they cant pick it up" (all 9 such spells: Use held throughout; all 26 pickups: a fresh press; Halo 2 takes on a press).

1. Bot.seat_ok (SEAT_ORDER): a "ride" or "board" order into an empty Warthog: no; with somebody in it: yes; the
   objective's holder: yes; its own "drive" order: yes; a turret (a gun only): yes; switched off: yes
2. Bot.decide: a bot told to ride an empty Warthog does not go for it; the same Warthog with its driver in: it does
3. Bot.take (TAKE_TAP): in Halo 2 Use is tapped (a fresh press several times a second); in Reach and Halo 3 it is held

usage: python -I test_seat_order.py      -> "seat order OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import brain.bot as BB  # noqa: E402
from brain.bot import Action, Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


M = get_map("h2_triplicate")


def hog(riders, kind="warthog"):
    return dict(handle=500, kind=kind, pos=(3.0, 0.0, 0.0), riders=riders, occupied=riders > 0, team=0 if riders else -1,
                fwd=(1.0, 0.0, 0.0), up=(0.0, 0.0, 1.0))


def bot(role, carrying=False):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b.order = Order(role, Vec(3.0, 0.0, 0.0), target=500)
    return b, PlayerState(1, 0, "b", Vec(0.0, 0.0, 0.0), alive=True, has_flag=carrying, weapon="battle_rifle")


b, me = bot("ride")
check("1. ride into an empty Warthog: no", not b.seat_ok(hog(0), me))
check("1. ride with its driver in: yes", b.seat_ok(hog(1), me))
b, me = bot("board")
check("1. board into an empty Warthog: no", not b.seat_ok(hog(0), me))
b, me = bot("board", carrying=True)
check("1. the ball's holder into an empty Warthog: yes", b.seat_ok(hog(0), me))
b, me = bot("drive")
check("1. its own drive order: yes", b.seat_ok(hog(0), me))
b, me = bot("ride")
turret = next((k for k, v in BB.vehicles.VEHICLES.items() if v.get("seats") and "driver" not in v["seats"]), None)
check(f"1. a turret ({turret}), nobody in it: yes", turret is None or b.seat_ok(hog(0, turret), me), turret)
BB.SEAT_ORDER = False
check("1. switched off: yes", b.seat_ok(hog(0), me))
BB.SEAT_ORDER = True

for riders, want in ((0, False), (1, True)):
    b, me = bot("ride")
    v = hog(riders)
    snap = Snapshot(20.0, [me], mode="oddball", vehicles=[v])
    b.now, b.notes, b.vehicles_now = 20.0, [], [v]
    g = b.decide(20.0, me, snap)
    check(f"2. told to ride a Warthog with {riders} in it: goes for it {want}", (g == ("vehicle", 500)) == want, g)


def presses(game, seconds=1.0):
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b.game = game
    me = PlayerState(1, 0, "b", Vec(0.0, 0.0, 0.0), alive=True)
    downs, edges, last = 0, 0, False
    t = 0.0
    while t < seconds:
        b.now = t
        act = Action()
        b.take(me, act, Vec(0.5, 0.0, 0.0))
        downs += bool(act.action)
        edges += bool(act.action) and not last
        last = bool(act.action)
        t += 1 / 30
    return downs, edges


d, e = presses("h2")
check("3. Halo 2: Use tapped, a fresh press 3+ times a second", e >= 3 and d < 30, (d, e))
for g in ("reach", "h3"):
    d, e = presses(g)
    check(f"3. {g}: Use held", e == 1 and d >= 29, (d, e))
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("seat order OK")
