"""A person's Firefight escort keeps its leash while he is down (Bot.keep_role: no lead, the order's point). Live ODST
h100, Nov 12: with pickups on, escorts set off for the weapon box 37 u away at every respawn of the host and broke off
when he was back (item and hunt flipping every 1.5-2 s, no gun reached, 8% of their decisions).

1. the host alive (lead): a gun 37 u off is weighed down, the escort stays (as before)
2. the host down (no lead): the same
3. a gun inside the leash (ESCORT_R of where it was put): still worth the trip
4. the director sends no escort on a power run past that leash (power_runs, FF_FETCH_R); one by it, yes

usage: python -I test_ff_escort_leash.py      -> "ff escort leash OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

M = get_map("odst_h100")
fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + (f"  ({got})" if not ok else ""))
    if not ok:
        fails.append(what)


def item_score(target, gun, mode="firefight"):
    b = Bot(2, 0, make_profile("top", "rusher", random.Random(1)), M, random.Random(1))
    b.game, b.can_pickup, b._terrain, b.now = "odst", True, terrain(M), 5.0
    host = PlayerState(0, 0, "host", Vec(-1.1, -10.2, 4.6))
    host.is_bot = False
    me = PlayerState(2, 0, "bot", Vec(-2.8, -10.2, 4.6), weapon="pistol", weapons=["pistol", "smg"], ammo=[30, 120],
                     mag=[8, 60])
    b.order = Order("escort", host.pos, target=target)
    b.decide(5.0, me, Snapshot(5.0, [me, host], mode=mode, ground_weapons=[("sniper", gun)]))
    return max((v for k, v in b.last_scores.items() if k[0] == "item"), default=0.0), b.last_scores


far, near = Vec(-39.9, -15.2, 1.7), Vec(-8.0, -12.0, 4.5)
s1, _ = item_score(0, far)
check("1. host alive: a gun 37 u off weighed down", s1 < 0.5, s1)
s2, sc = item_score(-1, far)
check("2. host down: the same", s2 < 0.5, sc)
s3, _ = item_score(-1, near)
check("3. a gun inside the leash: still worth it", s3 > 0.5, s3)

# 4. the director sends no escort on a power run past its leash (Director.power_runs, FF_FETCH_R); one by it, yes
import brain.director as D  # noqa: E402


def fetched(gun):
    m = dict(M, items=[dict(name="sniper", kind="weapon", value=0.8,
                            pos=gun, respawn=45)])
    b = Bot(2, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    b.order = Order("escort", Vec(-1.1, -10.2, 4.6), target=0)
    d = D.Director(0, m, {2: b}, random.Random(1))
    me = PlayerState(2, 0, "bot", Vec(-2.8, -10.2, 4.6), weapon="pistol", weapons=["pistol", "smg"])
    host = PlayerState(0, 0, "host", Vec(-1.1, -10.2, 4.6))
    host.is_bot = False
    d.power_runs(5.0, Snapshot(5.0, [me, host], mode="firefight", ground_weapons=[("sniper", gun)]))
    return getattr(b, "fetch", None) is not None


check("4. no power run to a gun 37 u past the escort's leash", not fetched(far))
check("4. a power run to one by it", fetched(Vec(-4.0, -6.0, 4.6)))
if fails:
    sys.exit("FAIL\n" + "\n".join(fails))
print("ff escort leash OK")
