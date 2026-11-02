"""Offline checks for the player's report: a bot with a director order keeps fighting the enemy it
sees, keeps the fight through a short loss of sight, and a learned sight-line block never hides a
man close in front of it nor gets learned within one burst.

usage: python -I test_focus.py      -> "focus OK"
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

MAP = get_map("bloodgulch")
T = terrain(MAP)
on_ground = lambda x, y: Vec(x, y, T.nav_z(x, y))
A, B = on_ground(70.0, -120.0), on_ground(58.0, -120.0)     # open gulch, 12 units apart


def snap(now, me_pos, foe_pos, foe_alive=True, me_id=1, yaw=3.14159, pitch=0.0, foe_shield=1.0):
    me = PlayerState(me_id, 0, "bot", me_pos, yaw=yaw, pitch=pitch, alive=True)   # starts facing the foe
    foe = PlayerState(2, 1, "human", foe_pos, alive=foe_alive, shield=foe_shield)
    return Snapshot(now, [me, foe])


def run(bot, t0, t1, me_pos, foe_pos, los=T.los, foe_alive=True, hits=True):
    goals = []
    t, yaw, pitch, sh = t0, 3.14159, 0.0, 1.0
    bot.fires = 0
    while t < t1:
        a = bot.think(t, 1 / 30, snap(t, me_pos, foe_pos, foe_alive, bot.id, yaw, pitch, sh), los, lambda a, b, **k: b, [])
        yaw, pitch = a.yaw, a.pitch                  # the game turns the bot where it aims
        bot.fires += bool(a.fire)
        if a.fire and hits:                          # every other shot lands (the shield recharges)
            sh = sh - 0.1 if bot.fires % 2 else sh
            sh = 1.0 if sh <= 0.05 else sh
        goals.append(bot.goal[0])
        t += 1 / 30
    return goals


def main():
    random.seed(1)
    fails = []
    # 1. an objective order (the director) must not pull a bot out of a fight it can see
    bot = Bot(1, 0, make_profile("top", "objector", random.Random(1)), MAP, random.Random(1))
    bot.can_pickup = False        # (no run for a power item before it has noticed the man in front)
    bot.set_order(Order("mid", Vec(40.0, -80.0, 0.0)))   # runners skip far fights by design
    g = run(bot, 0.0, 6.0, A, B)
    share = g[90:].count("fight") / len(g[90:])        # after reaction time
    if share < 0.95:
        fails.append(f"fight share with an objective order {share:.2f} < 0.95")
    # 2. a 1 s loss of sight mid fight keeps the fight (no new double take, no goal switch)
    g = run(bot, 6.0, 7.0, A, B, los=lambda a, b: False)
    if g.count("fight") / len(g) < 0.95:
        fails.append(f"fight share during a 1 s loss of sight {g.count('fight') / len(g):.2f} < 0.95")
    # 3. a learned block never hides a foe 5 units in front
    near = on_ground(65.0, -120.0)
    for _ in range(T.BLOCK_VOTES):               # a block counts on its third dry episode
        T.learn_blocked(A, near)
    if T._blk_key(A, near) not in T.blocked:
        fails.append("three dry episodes did not learn the block")
    if not T.los(A, near):
        fails.append("learned block hides a foe 5 units away")
    T.blocked.discard(T._blk_key(A, near)); T.blocked.discard(T._blk_key(near, A))
    far = on_ground(40.0, -120.0)                # 30 units: one dry episode is a miss streak, not a wall
    T.learn_blocked(A, far)
    if T._blk_key(A, far) in T.blocked:
        fails.append("one dry episode learned a block")
    # 4. one burst of misses (shield hits the reader did not see) does not teach a wall
    before = len(T.blocked)
    bot2 = Bot(3, 0, make_profile("top", "rusher", random.Random(2)), MAP, random.Random(2))
    bot2.can_pickup = False
    bot2.goal, bot2.next_decide = ("hunt", B), 0.6    # told where he is: it looks there (this checks misses, not noticing)
    bot2._terrain = T
    run(bot2, 0.0, 2.9, A, B, hits=False)
    if bot2.fires < 2:
        fails.append(f"the burst test fired only {bot2.fires} shots")
    if len(T.blocked) != before:
        fails.append("a 2 s burst taught a blocked sight line")
    T.blocked.clear()
    # 5. shields keep being read in a shielded match after two players take a fall (body only)
    from brain.live import LiveReach
    L = LiveReach.__new__(LiveReach)
    L._last_dmg, L._bare, L._bare_players = {}, set(), set()
    L._vitals(1, 0.0, 0.0); L._vitals(1, 0.5, 0.0)
    for u in (2, 3):
        L._vitals(u, 0.0, 0.0); L._vitals(u, 0.0, 0.2)
    if L._vitals(4, 0.3, 0.0)[0] < 0.6:
        fails.append("two falls made a shielded match read as shieldless")
    S = LiveReach.__new__(LiveReach)                   # SWAT: no shield ever hit -> shieldless
    S._last_dmg, S._bare, S._bare_players = {}, set(), set()
    for u in (2, 3):
        S._vitals(u, 0.0, 0.0); S._vitals(u, 0.0, 0.2)
    if S._vitals(5, 0.0, 0.0)[0] != 0.0:
        fails.append("SWAT no longer reads as shieldless")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("focus OK")


if __name__ == "__main__":
    main()
