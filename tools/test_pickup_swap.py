"""Halo swaps the gun in hand for the one picked up: a bot about to take a gun with both slots full first holds the
one to throw away, an empty gun first, else the lowest ranked, and only then presses pick up."""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Vec  # noqa: E402
from brain.maps import get_map  # noqa: E402
from brain.profiles import make_profile  # noqa: E402


def main():
    m = get_map("h3_construct")
    bot = Bot(7, 0, make_profile("average", "sniper", random.Random(7)), m, random.Random(7))
    bot.game = "h3"
    gun = Vec(10.4, -3.0, 3.2)                       # a laser lying on the floor beside it
    me = PlayerState(7, 0, "bot", Vec(10.0, -3.0, 3.2), alive=True, weapon="battle_rifle",
                     weapons=["assault_rifle", "battle_rifle"], ammo=[0, 108], mag=[0, 36])
    assert bot.gun_to_drop(me, "item", gun) == 0, "the empty assault rifle is the one to swap out"
    assert bot.choose_weapon(0.0, me, "item", gun, None) == 0, "switch to the empty AR before the pickup"
    me.weapon = "assault_rifle"
    assert bot.choose_weapon(0.0, me, "item", gun, None) == -1, "holding the AR: keep it for the swap"
    full = PlayerState(7, 0, "bot", Vec(10.0, -3.0, 3.2), alive=True, weapon="assault_rifle",
                       weapons=["assault_rifle", "battle_rifle"], ammo=[200, 108], mag=[32, 36])
    assert bot.gun_to_drop(full, "item", gun) == min(range(2), key=lambda i: bot.rank(full.weapons[i])), \
        "both loaded: the lower ranked goes"
    assert bot.gun_to_drop(me, "item", Vec(20.0, -3.0, 3.2)) is None, "far from the gun: nothing to hold yet"
    assert bot.gun_to_drop(me, "objective", gun) is None

    # range classes: an AR alone takes a BR lying 4 u off into its free slot, not a spiker; with AR + BR a laser
    # replaces the AR
    from brain.core import Snapshot
    solo = PlayerState(7, 0, "bot", Vec(10.0, -3.0, 3.2), alive=True, weapon="assault_rifle",
                       weapons=["assault_rifle"], ammo=[200], mag=[32])
    br, spiker = Vec(13.0, -1.0, 3.2), Vec(11.0, -5.0, 3.2)
    snap = Snapshot(5.0, [solo])
    snap.ground_weapons = [("spike_rifle", spiker), ("battle_rifle", br)]
    assert bot.upgrade_point(solo, snap) == br, "an AR alone walks past the battle rifle"
    snap.ground_weapons = [("spike_rifle", spiker)]
    assert bot.upgrade_point(solo, snap) is None, "a spiker is no better than the AR"
    snap.ground_weapons = [("spartan_laser", gun)]
    assert bot.upgrade_point(full, snap) == gun
    assert full.weapons[bot.gun_to_drop(full, "item", gun)] == "assault_rifle", "the laser replaces the AR, not the BR"

    # rockets just taken (2 + 4 rounds) are not "low": no going back for the magnum it dropped; 2 left of the 6 it held
    # are
    rk = PlayerState(7, 0, "bot", Vec(10.0, -3.0, 3.2), alive=True, weapon="rockets",
                     weapons=["battle_rifle", "rockets"], ammo=[108, 6], mag=[36, 2])
    snap.ground_weapons = [("unknown", Vec(10.3, -3.0, 3.2))]          # its magnum, at its feet
    assert bot.rearm_point(rk, snap) is None, "fresh rockets: not low"
    rk.ammo = [108, 2]
    assert bot.rearm_point(rk, snap) is not None, "2 of 6 rockets left: low, a loose gun is worth taking"
    print("pickup swap OK")


if __name__ == "__main__":
    main()
