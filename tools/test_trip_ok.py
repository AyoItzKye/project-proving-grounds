"""Offline check: no ground vehicle for a trip to a goal far over the bot, an aircraft still (live Spire
20261105-060020 phase 3: attackers sat in the Warthog at the spire's foot for the core 37 u up, no pickup).

usage: python -I test_trip_ok.py      -> "trip ok OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.bot import Bot  # noqa: E402
from brain.core import PlayerState, Vec  # noqa: E402


def main():
    me = PlayerState(1, 0, "bot", Vec(-181.0, -397.0, -60.8))
    core, field = Vec(-178.2, -405.3, -22.9), Vec(-130.0, -330.0, -60.0)
    hog, falcon, ghost = dict(kind="warthog"), dict(kind="falcon"), dict(kind="ghost")
    assert not Bot.trip_ok(hog, me, core) and not Bot.trip_ok(ghost, me, core), "on wheels to the spire's top"
    assert Bot.trip_ok(falcon, me, core), "a Falcon flies up"
    assert Bot.trip_ok(hog, me, field), "a Warthog across the field"
    print("trip ok OK")


if __name__ == "__main__":
    main()
