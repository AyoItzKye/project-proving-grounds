"""The Grenadier's anti-vehicle mission and its grenades.

1. A Grenadier with a rifle that sees an enemy riding a vehicle goes for the rocket launcher it knows of, before the
   fight; a Rusher in the same spot does not (it is the Grenadier's job)
2. ... the same with a launcher lying on the ground (a dead player's), for a Grenadier at Easy (it sees it)
3. Armed with rockets, the Grenadier fights the vehicle's crew before a closer man on foot, with the rockets out
4. A Defender Grenadier leaves its post for the launcher (the mission outranks the post)
5. Grenade openers are decided once per fight: a Legendary Grenadier opens far more fights with a grenade than a
   Camper (the old per-tick roll gave about 99% against 75%)

usage: python -I test_anti_vehicle.py      -> "anti vehicle OK"
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot, Order  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.equipment import Kit  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

MAP = get_map("bloodgulch")
T = terrain(MAP)
A = Vec(70.0, -120.0, T.nav_z(70.0, -120.0))
DT = 1 / 30
ROCKETS = A + Vec(0.0, 14.0, 0.0)


def ground(v):
    return Vec(v.x, v.y, T.nav_z(v.x, v.y))


def bot(pers, tier="top", weapons=("assault_rifle",), seed=1, items=True):
    b = Bot(1, 0, make_profile(tier, pers, random.Random(seed)), dict(MAP), random.Random(seed))
    b.kit = Kit(b.p, "reach")
    b.can_melee = True
    b.weapon, b.weapons, b.kind = weapons[0], list(weapons), ""
    if items:
        b.map["items"] = [dict(name="rockets", kind="weapon", pos=ground(ROCKETS), value=1.0, reachable=True)]
    else:
        b.map["items"] = []
    return b


def run(b, seconds, foes, ground_weapons=()):
    out, t, yaw = [], 0.0, math.pi
    while t < seconds:
        me = PlayerState(b.id, 0, "bot", A, yaw=yaw, alive=True, weapon=b.weapon, weapons=list(b.weapons))
        snap = Snapshot(t, [me] + foes, vehicles=[dict(handle=77, kind="warthog", pos=foes[0].pos, occupied=True)],
                        ground_weapons=list(ground_weapons))
        a = b.think(t, DT, snap, T.los, lambda p, q, **k: q, [])
        yaw = a.yaw
        out.append((t, a, b.goal, list(b.notes)))
        t += DT
    return out


def warthog(d=16.0, pid=2):
    return PlayerState(pid, 1, "human", ground(A + Vec(-d, 0.0, 0.0)), alive=True, weapon="assault_rifle", yaw=0.0, vehicle=77)


def main():
    fails = []
    # 1. a known launcher spawn: the Grenadier goes for it, the Rusher does not
    for pers, want in (("spammer", True), ("rusher", False)):
        acts = run(bot(pers), 2.0, [warthog()])
        went = any(g[0] == "item" and (g[1] - ground(ROCKETS)).flat() < 0.5 for _, _, g, _ in acts[-15:])
        if went != want:
            fails.append(f"{pers}: went for the rockets = {went}, want {want} (goals {sorted({g[0] for _, _, g, _ in acts})})")
    # 2. a launcher on the ground in sight, an Easy Grenadier (no map knowledge, only what it sees)
    loose = ground(A + Vec(4.0, 6.0, 0.0))
    acts = run(bot("spammer", tier="novice", items=False), 2.0, [warthog()], ground_weapons=[("rockets", loose)])
    if not any(g[0] == "item" and (g[1] - loose).flat() < 0.5 for _, _, g, _ in acts[-15:]):
        fails.append(f"Easy Grenadier did not take the rockets on the ground: {sorted({g[0] for _, _, g, _ in acts})}")
    # 3. armed: the crew first, rockets out (an infantry man closer than the vehicle)
    b = bot("spammer", weapons=("assault_rifle", "rockets"))
    man = PlayerState(3, 1, "human", ground(A + Vec(-10.0, 5.0, 0.0)), alive=True, weapon="assault_rifle", yaw=0.0)
    acts = run(b, 2.5, [warthog(), man])
    targets = [g[1] for _, _, g, _ in acts[-30:] if g[0] == "fight"]
    if not targets or max(set(targets), key=targets.count) != 2 or not any(a.weapon == 1 for _, a, _, _ in acts):
        fails.append(f"armed Grenadier: fight targets {sorted(set(targets))}, rockets out {any(a.weapon == 1 for _, a, _, _ in acts)}")
    # 4. a Defender Grenadier: the mission beats the post
    b = bot("spammer")
    b.order = Order("defender", A + Vec(0.0, -2.0, 0.0))
    acts = run(b, 2.0, [warthog()])
    if not any(g[0] == "item" for _, _, g, _ in acts[-15:]):
        fails.append(f"Defender Grenadier stayed on its post: {sorted({g[0] for _, _, g, _ in acts})}")
    # 5. grenade openers decided once per fight
    rate = {}
    for pers in ("spammer", "camper"):
        opened = 0
        for seed in range(60):
            b = bot(pers, seed=seed, items=False)
            foe = PlayerState(2, 1, "human", ground(A + Vec(-12.0, 0.0, 0.0)), alive=True, weapon="assault_rifle", yaw=0.0)
            acts = run(b, 1.0, [foe])
            # (the opener only: a pressure or flush grenade carries its note; with NADE_RATE 1.0, one in the first
            # second came for a Camper 26% of the time)
            opened += any(a.grenade and not any(n.startswith("grenade:") for n in ns) for _, a, _, ns in acts)
        rate[pers] = opened / 60
    if not rate["spammer"] > 2.0 * rate["camper"]:
        fails.append(f"grenade openers: Grenadier {rate['spammer']:.0%}, Camper {rate['camper']:.0%} (want over twice)")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print(f"anti vehicle OK (openers: Grenadier {rate['spammer']:.0%}, Camper {rate['camper']:.0%})")


if __name__ == "__main__":
    main()
