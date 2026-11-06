"""Energy sword: with a gun along, the gun at range, the sword out before the man is in reach and kept until he is well
away, never for a man on another floor; with the sword in hand and him out of reach, run him down (forward, no
side-stepping away)."""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Belief, Bot  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402

A = Vec(-2.0, 7.7, 6.4)          # Construct, red side's walk, one floor


def slot(bot, held, foe, now):
    bot.per.beliefs[2] = Belief(foe, Vec(), now, True, "eyes")
    bot.per.recognized.add(2)
    bot.switch_ok_at = 0.0
    me = PlayerState(1, 0, "bot", A, alive=True, weapon=held, weapons=["battle_rifle", "sword"], ammo=[108, -1],
                     mag=[36, -1])
    got = bot.choose_weapon(now, me, "fight", 2, Snapshot(now, [me, PlayerState(2, 1, "human", foe, alive=True)]))
    return (held if got < 0 else me.weapons[got])


def main():
    m = get_map("h3_construct")
    bot = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    bot.game, bot.notes = "h3", []
    fails = []
    for held, d, dz, want in (("sword", 11.0, 0.0, "battle_rifle"), ("battle_rifle", 5.0, 0.0, "sword"),
                              ("sword", 7.0, 0.0, "sword"), ("battle_rifle", 7.0, 0.0, "battle_rifle"),
                              ("battle_rifle", 3.0, 4.5, "battle_rifle"), ("sword", 1.2, 0.0, "sword")):
        got = slot(bot, held, Vec(A.x + d, A.y, A.z + dz), 5.0)
        if got != want:
            fails.append(f"holding the {held}, a man {d} u off (dz {dz}): {got} (want the {want})")
    # with the sword out and him 4 u off: run at him
    rush = Bot(4, 0, make_profile("top", "rusher", random.Random(4)), m, random.Random(4))
    rush.game = "h3"
    foe = Vec(A.x + 4.0, A.y, A.z)
    fwd, strafe = [], []
    t = 0.0
    while t < 2.0:
        me = PlayerState(4, 0, "bot", A, alive=True, weapon="sword", weapons=["sword"], ammo=[-1], mag=[-1], yaw=0.0)
        a = rush.think(t, 1 / 30, Snapshot(t, [me, PlayerState(2, 1, "human", foe, alive=True, yaw=3.14)]),
                       lambda p, q: True, lambda p, q, **k: q, [])
        if rush.goal == ("fight", 2):
            fwd.append(a.forward)
            strafe.append(abs(a.strafe))
        t += 1 / 30
    if not fwd or sum(fwd) / len(fwd) < 0.6 or sum(strafe) / len(strafe) > 0.3:
        fails.append(f"sword rush: forward {sum(fwd) / max(len(fwd), 1):.2f}, strafe {sum(strafe) / max(len(strafe), 1):.2f}")
    # in reach: lunge the moment the reticle is red (bot.red_reticle: the sword's 6 deg cone plus his body), by where it
    # looks, not the aim plan's crosshair; not 0.35 rad off (a swing at the air: owner, issue #3), not behind
    def lunges(off, d, ticks=3):
        lb = Bot(5, 0, make_profile("top", "rusher", random.Random(5)), m, random.Random(5))
        lb.game = "h3"
        man = Vec(A.x + d, A.y, A.z)
        lb.per.beliefs[2] = Belief(man, Vec(), 0.0, True, "eyes")
        lb.per.recognized.add(2)
        lb.per.last_seen[2] = 0.0
        presses = 0
        for k in range(ticks):
            t = k / 30
            me = PlayerState(5, 0, "bot", A, alive=True, weapon="sword", weapons=["sword"], ammo=[-1], mag=[-1], yaw=off)
            a = lb.think(t, 1 / 30, Snapshot(t, [me, PlayerState(2, 1, "human", man, alive=True, yaw=3.14)]),
                         lambda p, q: True, lambda p, q, **kw: q, [])
            presses += bool(a.fire)
        return presses
    for off, d, want in ((0.18, 1.4, True), (0.35, 1.4, False), (0.0, 0.8, True), (3.0, 1.0, False), (0.0, 2.4, False)):
        if bool(lunges(off, d)) != want:
            fails.append(f"sword, a man {d} u off and {off:.2f} rad off its look: lunged {not want} (want {want})")
    if fails:
        sys.exit("\n".join("FAIL: " + f for f in fails))
    print("sword OK")


if __name__ == "__main__":
    main()
