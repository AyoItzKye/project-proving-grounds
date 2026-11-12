"""A map variant's pieces that come and go in a match (brain/forge.py PieceWatch; GitHub issue 2, Tempest Invasion: a
wall the game put back for round 2 was open floor to the bots, who pressed into it for minutes): a Forge wall standing
up after the nav was built is a wall on the nav while it stands and open again once it is gone; a piece the nav was
built with that goes missing is filed as dynamic once, and the next match's nav leaves it out (brain/maps.py); a piece
never seen live this match (one only its .mvar file lists: a vehicle, a spawn) never counts as gone.

usage: python -I test_forge_dynamic.py      -> "forge dynamic OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.forge import PieceWatch, piece_key, _shapes  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

AXES = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))     # forward +y: the 4 u wall runs north-south


def cost(T, a, b):
    return float(T._field(b)[T._node(a)])


def main():
    T = terrain(get_map("reach_dlc_medium"))
    # open flat floor on Tempest (a 3 u walk costs 3.1 there)
    a0, b0 = Vec(-30.0, 10.0, 0.0), Vec(-27.0, 10.0, 0.0)
    a, b = Vec(a0.x, a0.y, T.nav_z(a0.x, a0.y, a0.z)), Vec(b0.x, b0.y, T.nav_z(b0.x, b0.y, b0.z))
    base = cost(T, a, b)
    assert base < 3.5, f"the test spot is not open floor on Tempest's nav ({base:.1f})"
    lo = _shapes()["ff_wall_2x4"]["min"]
    wall = ("ff_wall_2x4", (-28.5, 10.0, a.z - lo[2]), AXES)
    crate = ("ff_wall_2x4", (30.0, 30.0, 0.0), AXES)       # stamped in at the start (built), gone later
    w = PieceWatch([crate], game="reach")
    assert not w.update([crate], T) and abs(cost(T, a, b) - base) < 0.01, "nothing new: the nav as built"
    w.update([crate, wall], T)
    up = cost(T, a, b)
    assert up > base + 1.5, f"the wall that stood up is no wall on the nav ({base:.1f} -> {up:.1f})"
    w.update([crate], T)                       # one read missing it: still a wall (an object can be missed once)
    assert abs(cost(T, a, b) - up) < 0.01, "one missed read opened the wall"
    gone = w.update([], T)                     # second read without the wall (and the first without the crate)
    assert abs(cost(T, a, b) - base) < 0.01, f"the wall went and is still on the nav ({cost(T, a, b):.1f})"
    assert not gone, "the crate counted gone after one missed read"
    assert w.update([], T) == {piece_key(*crate[:2])}, "a built piece that went is not filed dynamic"
    assert not w.update([], T), "filed twice"
    w.update([wall], T)                         # back for the next round
    assert abs(cost(T, a, b) - up) < 0.01, "the wall put back for round 2 is no wall on the nav"
    # filed dynamic: the next match's watch has it as a wall while it stands (maps.py leaves it out of the stamps)
    w2 = PieceWatch([crate], dynamic={piece_key(*crate[:2])}, game="reach")
    assert piece_key(*crate[:2]) not in w2.built
    # a piece from the variant's .mvar that live reads never return (a vehicle, a spawn, a door: live Halo 3 filed 56
    # of those gone in 2 s): never seen, never gone
    hog = ("warthog", (50.0, 50.0, 0.0), AXES)
    w3 = PieceWatch([crate, hog], game="reach")
    assert not any(w3.update([crate], T) for _ in range(5)), "a piece live reads never return filed as gone"
    assert w3.update([], T) == set() and w3.update([], T) == {piece_key(*crate[:2])}, "a seen piece that went: not gone"
    zone_checks(T, a)
    print("forge dynamic OK")


def zone_checks(T, c):
    """Invasion with no setup of its own: a dead bot is sent to the zone the game gives it (live_bots.zone_spawn_check),
    within 2 u of its centre, clear of a player standing on it; once a death; again when the zone moves; not alive."""
    import random
    sys.path.insert(0, HERE)
    import live_bots

    class P:
        def __init__(s, i, pos, alive):
            s.id, s.pos, s.alive = i, pos, alive

    class Snap:
        def __init__(s, players):
            s.players = players

        def player(s, i):
            return next((p for p in s.players if p.id == i), None)

    sent, zone = [], [(c.x, c.y, c.z, 0.5)]
    send = lambda i, x, y, z, yaw: sent.append((i, Vec(x, y, z), yaw))
    snap = Snap([P(1, c, False), P(2, Vec(c.x, c.y, c.z), True)])     # a living player on the zone's centre
    state, rng = {}, random.Random(3)
    live_bots.zone_spawn_check(send, {1: None}, snap, lambda i: zone[0], state, rng, T, 1.0)
    assert len(sent) == 1 and sent[0][0] == 1 and sent[0][2] == 0.5, sent
    d = (sent[0][1] - c).flat()
    assert 0.5 <= d <= 2.0, f"the spot is {d:.2f} u from the zone (not clear of the player on it, or too far)"
    live_bots.zone_spawn_check(send, {1: None}, snap, lambda i: zone[0], state, rng, T, 1.5)
    assert len(sent) == 1, "sent twice in one death"
    zone[0] = (c.x + 1.0, c.y + 1.0, c.z, 1.0)                            # the phase moved its zone
    live_bots.zone_spawn_check(send, {1: None}, snap, lambda i: zone[0], state, rng, T, 2.0)
    assert len(sent) == 2 and sent[1][2] == 1.0, "a new zone was not sent"
    snap.players[0].alive = True
    live_bots.zone_spawn_check(send, {1: None}, snap, lambda i: zone[0], state, rng, T, 2.5)
    assert len(sent) == 2 and not state[1], "a living bot was sent somewhere"


if __name__ == "__main__":
    main()
