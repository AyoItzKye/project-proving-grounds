"""Health packs where health does not come back by itself (brain/games.py; Bot.best_item, HEALTH_PACK_HURT):

1. Blood Gulch (CE): its health packs are map items (maps.POWER); a bot at a third of its health goes for the nearest
   one, one barely hurt does not
2. the same bot and pack in Halo 3 (health comes back whole): never
3. ODST's Firefight maps carry their packs (Crater h100: 2, Mombasa Streets sc100: 6)

usage: python -I test_health_packs.py      -> "health packs OK"
"""
import copy
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import games  # noqa: E402
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def pick(m, health):
    b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), m, random.Random(1))
    packs = [it for it in m["items"] if it["kind"] == "health"]
    me = PlayerState(1, 0, "me", type(packs[0]["pos"])(packs[0]["pos"].x + 8.0, packs[0]["pos"].y, packs[0]["pos"].z),
                     health=health, shield=0.0)
    got = b.best_item(10.0, me)
    return got, packs


def main():
    fails = []
    bg = get_map("bloodgulch")
    got, packs = pick(bg, 0.3)
    if not packs:
        fails.append("1. Blood Gulch has no health pack items")
    elif got is None or min(abs(got[0].x - p["pos"].x) + abs(got[0].y - p["pos"].y) for p in packs) > 0.01:
        fails.append(f"1. CE, a third of health left: {got} (want a health pack)")
    got, _ = pick(bg, 0.9)
    if got is not None and any(abs(got[0].x - p["pos"].x) + abs(got[0].y - p["pos"].y) < 0.01 for p in packs):
        fails.append("1. CE, barely hurt: went for a health pack")
    h3 = copy.copy(bg)
    h3["name"] = "h3_" + bg["name"]          # (the same map read as a Halo 3 one: its health comes back)
    b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), h3, random.Random(1))
    if b.game != "h3" or games.needs_health_packs("h3"):
        fails.append(f"2. a Halo 3 map read as game {b.game}")
    else:
        me = PlayerState(1, 0, "me", type(packs[0]["pos"])(packs[0]["pos"].x + 8.0, packs[0]["pos"].y, packs[0]["pos"].z),
                         health=0.3, shield=0.0)
        got = b.best_item(10.0, me)
        if got is not None and any(abs(got[0].x - p["pos"].x) + abs(got[0].y - p["pos"].y) < 0.01 for p in packs):
            fails.append("2. Halo 3, a third of health left: went for a health pack")
    for name, want in (("odst_h100", 2), ("odst_sc100", 6)):
        n = sum(1 for it in get_map(name)["items"] if it["kind"] == "health")
        if n != want:
            fails.append(f"3. {name}: {n} health packs (want {want})")
    # 4. the motion tracker's range by game (games.radar_range): CE's tag 20 u; a game with none known keeps 25
    for name, want in (("bloodgulch", 20.0), ("h3_construct", 25.0)):
        b = Bot(1, 0, make_profile("top", "objector", random.Random(1)), get_map(name), random.Random(1))
        if abs(b.per.radar_range - want) > 1e-6:
            fails.append(f"4. {name}: motion tracker {b.per.radar_range} u (want {want})")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print("health packs OK (CE and ODST: a hurt bot goes for one; Halo 3 never)")


if __name__ == "__main__":
    main()
