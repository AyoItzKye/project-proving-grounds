"""Construct's pit: the Mid zone, most of the map, centres on the pit floor. A callout of a man on the top floor in Mid
must not send listeners to the pit, and the Slayer hunters go where the team last saw him, not to the zone's centre."""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.director import Director  # noqa: E402
from brain.maps import get_map  # noqa: E402


def main():
    m = get_map("h3_construct")
    d = Director(0, m, {}, random.Random(1))
    top = Vec(-2.0, -5.0, 12.5)                     # over the pit, on the top floor
    zone = d.zones.zone(top)
    assert zone.center.z < 4.2, f"test premise: {zone.name}'s centre at z {zone.center.z:.1f} is not the pit"
    said = d.said_at(top)
    assert abs(said.z - top.z) < 2.0, f"a callout from z {top.z} put him at z {said.z:.1f} ({zone.name})"
    low = Vec(zone.center.x + 1.0, zone.center.y, zone.center.z)
    assert d.said_at(low) == zone.center, "a man on the zone's own floor is called at its centre"
    d.report(10.0, 1, "seen", top)
    assert d.threat_at[zone.name] == top, "the hunt target is not where he was seen"
    print("pit targets OK (Mid centre z %.1f, callout from the top floor at z %.1f)" % (zone.center.z, said.z))


if __name__ == "__main__":
    main()
