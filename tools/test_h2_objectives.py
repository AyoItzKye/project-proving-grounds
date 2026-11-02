"""Halo 2's Assault bombs by their tag names (brain/live.py LiveH2.objective_items: its Assault played as Slayer before),
on a stub of the game's memory:

1. a bomb lying on a team's stand: that stand; carried away (in a player's weapon slots): the carrier, its place his,
   still that stand; another weapon object (a battle rifle) is no bomb
2. modes.Watch on Ascension's places: the carried bomb's carrier has the objective; its goal is the enemy's plate
3. King's active hill by its number (decoded live on Lockout)

usage: python -I test_h2_objectives.py      -> "h2 objectives OK"
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain import modes  # noqa: E402
from brain.core import PlayerState, Snapshot, Vec  # noqa: E402
from brain.live import LiveH2  # noqa: E402
from brain.maps import get_map  # noqa: E402


class Mem:
    def __init__(s):
        s.slots = {}                       # unit object address -> 4 weapon handles

    def read(s, addr, n):
        base = addr - LiveH2.SLOTS_AT
        return struct.pack("<4I", *s.slots.get(base, (0xFFFFFFFF,) * 4))


def main():
    fails = []
    objs = get_map("h2_ascension")["objects"]
    lay = modes.layout(objs)
    stands = {k: pos for k, (pos, r, t) in enumerate(p for p in lay["bomb"] if p[2] in (0, 1, 8))}
    home = stands[0]
    live = LiveH2.__new__(LiveH2)
    live.g = Mem()
    bomb_at = [(home.x, home.y, home.z)]
    live.objects = lambda types: [(7, 2, "objects\\weapons\\multiplayer\\assault_bomb\\assault_bomb", bomb_at[0]),
                                  (8, 2, "objects\\weapons\\rifle\\battle_rifle\\battle_rifle", (0.0, 0.0, 0.0))]
    live.object = lambda h: 0x1000 * h if h != 0xFFFFFFFF else None
    players = [dict(index=3, unit=5, pos=(10.0, 10.0, 1.0))]
    got1 = live.objective_items(players, stands, "assault")
    live.g.slots[0x5000] = (7, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
    bomb_at[0] = (99.0, 99.0, 0.0)
    got2 = live.objective_items(players, stands, "assault")
    if (len(got1) != 1 or got1[0]["stand"] != 0 or got1[0]["carrier"] is not None
            or len(got2) != 1 or got2[0]["carrier"] != 3 or got2[0]["pos"] != (10.0, 10.0, 1.0) or got2[0]["stand"] != 0):
        fails.append(f"1. lying {got1}, carried {got2} (want stand 0 then carrier 3 at his place, stand 0)")
    w = modes.Watch("assault", objs, "h2")
    team = lay["bomb"][0][2]
    me = PlayerState(3, team if team in (0, 1) else 0, "c", Vec(10.0, 10.0, 1.0), alive=True)
    snap = Snapshot(5.0, [me])
    w.update(live, snap, 5.0, players)
    goal = modes.carry_goal("assault", snap, me.team, me.pos)
    enemy = [p for p, r, t in lay["bomb_goal"] if t == 1 - me.team]
    if not me.has_flag or goal is None or not any((goal - p).flat() < 0.1 for p in enemy):
        fails.append(f"2. Watch: carrier has it {me.has_flag}, his goal {goal} (want the enemy's plate)")
    # 3. King's active hill (LiveH2.king_hill, live Lockout): the number at +0x29C of the block halo2.dll+0xE80500
    #    points to, as the map's "King Hill <n>" flag; a number off the map's hills: None
    class KingMem:
        base = 0x10000000

        def __init__(s):
            s.k = 3

        def u64(s, a):
            return 0x5000 if a == s.base + LiveH2.KING_HILL[0] else 0

        def read(s, a, n):
            return struct.pack("<i", s.k) if a == 0x5000 + LiveH2.KING_HILL[1] else None
    k = LiveH2.__new__(LiveH2)
    k.g = KingMem()
    lock = get_map("h2_lockout")["objects"]
    k.set_map(lock)
    corners = [f["pos"] for f in lock["netgame_flags"] if f["type"] == "King Hill 3"]
    want = [sum(c[i] for c in corners) / len(corners) for i in range(3)]
    got = k.king_hill()
    k.g.k = 9
    if (got is None or max(abs(a - b) for a, b in zip(got[0], want)) > 1e-6 or got[1] < 3.0
            or k.king_hill() is not None):
        fails.append(f"3. king_hill: hill 3 -> {got} (want {want}), hill 9 -> {k.king_hill()} (want None)")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print("h2 objectives OK (Halo 2's bombs by tag name, carried to the enemy's plate)")


if __name__ == "__main__":
    main()
