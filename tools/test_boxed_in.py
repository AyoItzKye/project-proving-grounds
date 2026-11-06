"""Offline check: a bot sealed in a pocket (walls on every side within Bot.BOXED_R) that has walked Bot.BOXED_S s
without leaving 1.2 u throws a grenade at its feet (live Boneyard 20261105-044042: two defenders respawned inside the
closed crate at (254.7, 88.4, -4.0), 217 s and 22 s there); nowhere open (a stair's foot, the ramp's foot) does.

usage: python -I test_boxed_in.py      -> "boxed in OK"
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


def throws(m, at, seconds):
    """Whether the bot, walking on the spot at `at` for `seconds`, threw a grenade down."""
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    t = 100.0
    while t < 100.0 + seconds:
        act = Action(forward=0.9, strafe=0.2)
        if b.boxed_in(t, PlayerState(1, 0, "bot", at, yaw=0.0), act):
            return act.grenade and act.pitch < -1.3
        t += 0.1
    return False


def throws_in_think(m, at, seconds, weapon="plasma_repeater"):
    """The whole tick (Bot.think, as live): a defender respawned in the crate (B10 bot 1 at 43.7 s, (254.7, 88.4, -4.0)),
    Invasion phase 1, going where its order sends it, its feet held by the crate's walls. The press that leaves think:
    a grenade with the view down (no later guard cancels it)."""
    from brain.bot import Order
    from brain.core import Snapshot
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    b.order = Order("defender", Vec(251.2, 95.0, -4.0))
    t, yaw = 43.7, 0.0
    while t < 43.7 + seconds:
        me = PlayerState(1, 0, "bot", at, yaw=yaw, weapon=weapon)
        a = b.think(t, 0.1, Snapshot(t, [me], mode="invasion", inv_phase=1, inv_attackers=1,
                                     inv_zones=[Vec(251.2, 95.0, -4.0), Vec(255.8, 82.0, -4.0)], inv_zone_r=[0.86, 0.86]),
                    lambda p, q: True, lambda p, q, **kw: q, [])
        yaw = a.yaw
        if a.grenade and a.pitch < -1.3:
            return round(t - 43.7, 1)
        t += 0.1
    return None


def throw_kinds(m, at):
    """Live B20 (Spartan 2 in the crate from its respawn at 124.1 s, 190+ s there): 21 one-tick presses at the floor,
    no frag went off. Now: each press held 0.3 s, and the tries go at the feet, off the nearest wall, up at the lid."""
    b = Bot(1, 0, make_profile("top", "rusher", random.Random(1)), m, random.Random(1))
    t, held, pitches = 100.0, 0, []
    while t < 100.0 + Bot.BOXED_S + 13.0:
        act = Action(forward=0.9, strafe=0.2)
        was = getattr(b, "box_tries", 0)
        if b.boxed_in(t, PlayerState(1, 0, "bot", at, yaw=0.0), act):
            held += 1
            if getattr(b, "box_tries", 0) != was:
                pitches.append(round(act.pitch, 2))
        t += 0.05
    return held, pitches


def main():
    m = get_map("reach_70_boneyard/variants/v86d95e85")
    crate = Vec(254.7, 88.4, -4.0)
    assert not throws(m, crate, Bot.BOXED_S - 1.0), "a grenade before BOXED_S s in the crate"
    assert throws(m, crate, Bot.BOXED_S + 1.0), "no grenade after BOXED_S s sealed in the crate"
    for open_spot in (Vec(264.2, 86.3, -5.0), Vec(251.0, 82.0, -9.75), Vec(258.4, 107.5, -5.6)):
        assert not throws(m, open_spot, 30.0), f"a grenade where it is open: {open_spot}"
    held, pitches = throw_kinds(m, crate)
    assert held >= 3 * 5, f"each press held 0.3 s (6 ticks of 0.05 s): {held} pressed ticks for {len(pitches)} tries"
    assert len(pitches) >= 3 and pitches[0] < -1.3 and abs(pitches[1]) < 0.2 and pitches[2] > 0.5,         f"the tries at the feet, off the wall, at the lid: pitches {pitches}"
    k = throws_in_think(m, crate, Bot.BOXED_S + 6.0)
    assert k is not None, "through Bot.think in the crate: no grenade at its feet"
    print(f"boxed in OK (through think: the grenade {k} s after the respawn)")


if __name__ == "__main__":
    main()
