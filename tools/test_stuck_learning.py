"""Offline checks for stuck-spot learning (Lockdown's learned spots grew 65 -> 118 in two games): one
bot's reports never teach a spot, three reports from two bots do, a match teaches at most
STUCK_PER_MATCH new spots, the LiDAR tools' second-report rule is unchanged, and a bot does not
learn while fighting or when the edge guard holds it at a void.

usage: python -I test_stuck_learning.py      -> "stuck learning OK"
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import Action, PlayerState, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402
from brain.terrain import Terrain  # noqa: E402

MAP = get_map("bloodgulch")


def fresh():
    m = get_map("bloodgulch")
    T = Terrain(m["heightmap"], m["bases"])
    T.set_spawns([p for mode in m["spawns"].values() for team in mode.values() for p in team])
    return T


def spot(T, x, y):
    return Vec(x, y, T.nav_z(x, y))


def main():
    T = fresh()
    a = spot(T, 70.0, -120.0)
    for _ in range(5):
        T.learn_stuck(a, who=1)                  # one bot, five times
    assert not T.stuck, "one bot's reports taught a spot"
    T.learn_stuck(a, who=2)
    assert len(T.stuck) == 1, "three reports from two bots did not teach the spot"

    T = fresh()
    for k in range(T.STUCK_PER_MATCH + 5):       # many real spots in one match: capped
        p = spot(T, 40.0 + 3.0 * k, -100.0)
        for who in (1, 2, 1):
            T.learn_stuck(p, who=who)
    assert len(T.stuck) == T.STUCK_PER_MATCH, f"{len(T.stuck)} spots in one match"

    T = fresh()
    b = spot(T, 60.0, -110.0)
    T.learn_stuck(b)
    T.learn_stuck(b)
    assert len(T.stuck) == 1, "LiDAR tools: the second report no longer teaches"

    # a fighting bot pushing in place for 2 s learns nothing
    import brain.maps as M
    T = M.terrain(MAP)
    n0 = len(T.stuck)
    for pid in (1, 2, 3):
        bot = Bot(pid, 0, make_profile("strong", "flanker", random.Random(pid)), MAP, random.Random(pid))
        bot._terrain = T
        bot.goal = ("fight", 7)
        bot.planned_jump = False
        me = PlayerState(pid, 0, "bot", spot(T, 70.0, -120.0))
        for k in range(30):
            bot.unstuck(k * 0.1, me, Action(forward=1.0))
    assert len(T.stuck) == n0, "fighting bots taught a stuck spot"

    # a wedged bot (the game takes its input, it does not move) jumps out, toward where it came from
    import math
    bot = Bot(9, 0, make_profile("novice", "camper", random.Random(9)), MAP, random.Random(9))
    bot._terrain = T
    bot.goal, bot.planned_jump = ("hunt", None), False
    came, wedge = spot(T, 70.0, -120.0), spot(T, 71.0, -120.0)   # it walked in from 1 unit west
    for k in range(10):                                          # moving freely up to the wedge
        bot.unstuck(k * 0.1, PlayerState(9, 0, "bot", came + Vec(0.1 * k, 0, 0)), Action(forward=1.0))
    held, toward = 0, False
    run = 0
    for k in range(10, 130):                                     # 12 s pressing forward (east), not moving
        act = Action(forward=1.0, yaw=0.0)
        bot.unstuck(k * 0.1, PlayerState(9, 0, "bot", wedge), act)
        run = run + 1 if act.jump else 0
        held = max(held, run)
        mx = math.cos(act.yaw) * act.forward - math.sin(act.yaw) * act.strafe
        toward |= act.jump and mx < -0.7                         # jumping west, back the way it came
    assert held >= 3, f"wedged bot never held a jump ({held} ticks)"
    assert toward, "wedged bot never jumped back the way it came"
    # hopping in place is no headway (live CE Battle Creek, Nov 11: bots hopped at a ledge's lip 32 s, z swinging
    # 0.64 u, each hop read as moving): pressing on, xy still, z up and down 0.65 u every 0.6 s, it wiggles within 3 s
    bot = Bot(10, 0, make_profile("novice", "camper", random.Random(10)), MAP, random.Random(10))
    bot._terrain = T
    bot.goal, bot.planned_jump = ("hunt", None), False
    lip, wiggled = spot(T, 71.0, -120.0), None
    for k in range(60):
        hop = Vec(0, 0, 0.65 * abs(math.sin(k * 0.1 * math.pi / 0.6)))
        bot.unstuck(k * 0.1, PlayerState(10, 0, "bot", lip + hop), Action(forward=1.0, yaw=0.0))
        if wiggled is None and getattr(bot, "wiggle_until", 0.0) > k * 0.1:
            wiggled = k * 0.1
    assert wiggled is not None and wiggled <= 3.0, f"a bot hopping in place never read stuck (wiggle at {wiggled})"
    print("stuck learning OK")


if __name__ == "__main__":
    main()
