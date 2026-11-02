"""Offline check of how the Halo 3 / ODST / Reach / Halo 4 readers name guns (brain/live.py objects, _learn,
weapon_name) against fake game memory laid out as each game's: these games keep no tag names, so a kind is learned
from a map copy lying on its placement.

- A starting gun everyone holds is named from a map copy on its spawn. After f703acf the readers never named a
  kind anyone had held, so on Construct (BR starts) every gun read "unknown" all match (trace,
  31,824 ticks; the trace named the AR starts): no zoom, no range rules, default cadence.
- A gun someone held and dropped on another kind's spawn never names that kind (the rockets mislabel f703acf
  fixed: a rifle dropped on the rocket spawn made every rifle read "rockets", the player's Ivory Tower game).

usage: python -I test_weapon_names.py      -> "weapon names OK"
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.live import NONE, LiveH3, LiveH4F, LiveODST, LiveReach  # noqa: E402

GUN, LAUNCHER, RIFLE = 0xE1000101, 0xE1000202, 0xE1000303
GUN_SPAWN, ROCKET_SPAWN = (5.0, 5.0, 1.0), (10.0, 5.0, 1.0)


class Mem:
    def __init__(s):
        s.blocks = {}

    def put(s, addr, data):
        s.blocks[addr] = bytes(data)

    def read(s, addr, n):
        for a, d in s.blocks.items():
            if a <= addr < a + len(d):
                out = d[addr - a:addr - a + n]
                return out + bytes(n - len(out))
        return bytes(n)


# each reader's layout: entries array index (s._array arg), type byte offset in an entry, object head size, tag /
# parent / position offsets in the head (parent None: the game has none usable, Halo 4 skips held guns instead)
LAYOUT = {LiveH3: (0x38, 3, 0x5C, 0, 0x10, 0x50), LiveODST: (0x20, 3, 0x5C, 0, 0x10, 0x50),
          LiveReach: (0x10, 4, 0x50, 0, 0x14, 0x44), LiveH4F: (0x18, 4, 0x50, 8, None, 0x40)}


def reader(cls, gun_name):
    """A reader over fake memory: 0 a gun in a player's hands, 1 the map's copy of that gun on its spawn, 2 a rifle
    a bot held and dropped on the rocket spawn, 3 the map's rocket launcher on that spawn."""
    arr, typ_at, head_n, tag_at, parent_at, pos_at = LAYOUT[cls]
    r = object.__new__(cls)
    r.g, r._names = Mem(), {}
    r._placements = [(gun_name, GUN_SPAWN), ("rockets", ROCKET_SPAWN)]
    objs = [(GUN, 0x12340001, (40.0, 40.0, 1.0)), (GUN, NONE, GUN_SPAWN), (RIFLE, NONE, (10.1, 5.0, 1.0)),
            (LAUNCHER, NONE, ROCKET_SPAWN)]
    ents = bytearray(0x18 * len(objs))
    handles = {}
    for i, (tag, parent, pos) in enumerate(objs):
        salt, addr = 0x100 + i, 0x10000 * (i + 1)
        struct.pack_into("<H", ents, 0x18 * i, salt)
        ents[0x18 * i + typ_at] = 2                                   # a weapon
        struct.pack_into("<Q", ents, 0x18 * i + 0x10, addr)
        head = bytearray(max(head_n, 0x300))                          # (Reach reads the magazine at +0x2CA: 0 here)
        struct.pack_into("<I", head, tag_at, tag)
        if parent_at is not None:
            struct.pack_into("<I", head, parent_at, parent)
        struct.pack_into("<3f", head, pos_at, *pos)
        r.g.put(addr, head)
        handles[i] = (salt << 16) | i
    r.g.put(0x900000, ents)
    r._array = lambda off: (0x900000, len(objs), 0x18) if off == arr else (0, 0, 0)
    r.object = lambda h: next((0x10000 * (i + 1) for i, x in handles.items() if x == h), None)
    return r, handles


def turrets(fails):
    """A Reach gun riding on a vehicle (a Warthog's chaingun, a Falcon's side guns: vehicles of their own) is named by
    the map's own tag name (live Spire: every gunner read "unknown", so the chaingun's aim height never applied:
    "Gunner bot still shooting too high"); the vehicle under it keeps the name it has."""
    sys.path.insert(0, HERE)
    import reach_tag_names
    names = reach_tag_names.cached("35_island", "reach")
    idx = lambda end: next(i for i, n in enumerate(names) if n.endswith(end))
    hog, gun = 0xE1000000 | idx("\\warthog\\warthog"), 0xE1000000 | idx("\\warthog_chaingun\\warthog_chaingun")
    r = object.__new__(LiveReach)
    r.g, r._names, r._tag_name_list = Mem(), {hog: "warthog"}, names
    ents = bytearray(0x18 * 2)
    for i, (tag, parent) in enumerate(((hog, NONE), (gun, 0x100 << 16))):     # the gun's parent: the Warthog
        struct.pack_into("<H", ents, 0x18 * i, 0x100 + i)
        ents[0x18 * i + 4] = 1                                                # a vehicle
        struct.pack_into("<Q", ents, 0x18 * i + 0x10, 0x10000 * (i + 1))
        head = bytearray(0x50)
        struct.pack_into("<I", head, 0, tag)
        struct.pack_into("<I", head, 0x14, parent)
        r.g.put(0x10000 * (i + 1), head)
    r.g.put(0x900000, ents)
    r._array = lambda off: (0x900000, 2, 0x18) if off == 0x10 else (0, 0, 0)
    got = [name for _, _, name, _ in r.objects((1,))]
    if got != ["warthog", "warthog_chaingun"]:
        fails.append(f"LiveReach: a Warthog and its chaingun read {got} (want the gun by the map's own tag name)")


def h3_equipment(fails):
    """Halo 3 equipment is named from its spot: lying within 1.5 u of it (it settles off it; a gun 1.2 u off it is not),
    and the one a player just took from the equipment spot within 3 u of him, not the gun spot nearer him (guide 20
    review: 8 of 14 pickups read "unknown", and the bot never used what it carried)."""
    REGEN, FLARE, LOOSE_EQ, LOOSE_GUN, UNIT, TAKEN = (30.0, 5.0, 1.0), (20.0, 5.0, 1.0), 0xE1000505, 0xE1000606, 7, 9
    r = object.__new__(LiveH3)
    r.g, r._names = Mem(), {}
    r._placements = [("regenerator_equipment", REGEN), ("superflare_equipment", FLARE), ("battle_rifle", (21.5, 5.5, 1.0))]
    ents = bytearray(0x18 * 2)
    for i, (typ, tag, pos) in enumerate(((3, LOOSE_EQ, (31.2, 5.0, 1.0)), (2, LOOSE_GUN, (30.0, 6.2, 1.0)))):
        struct.pack_into("<H", ents, 0x18 * i, 0x100 + i)
        ents[0x18 * i + 3] = typ
        struct.pack_into("<Q", ents, 0x18 * i + 0x10, 0x10000 * (i + 1))
        head = bytearray(0x5C)
        struct.pack_into("<I", head, 0, tag)
        struct.pack_into("<I", head, 0x10, NONE)
        struct.pack_into("<3f", head, 0x50, *pos)
        r.g.put(0x10000 * (i + 1), head)
    r.g.put(0x900000, ents)
    player, unit, eq = bytearray(0xF4), bytearray(0x300), bytearray(0x10)
    struct.pack_into("<H", player, 0, 1)
    struct.pack_into("<I", player, 0x28, UNIT)
    struct.pack_into("<4I", unit, 0x268, NONE, NONE, NONE, NONE)
    struct.pack_into("<b", unit, 0x262, -1)
    struct.pack_into("<I", unit, 0x10, NONE)
    struct.pack_into("<3f", unit, 0x50, 22.0, 6.0, 1.0)       # 2.2 u from the flare spot, 0.7 from the rifle's
    struct.pack_into("<I", unit, 0x288, TAKEN)
    struct.pack_into("<I", eq, 0, 0xE1000707)
    r.g.put(0x500000, player)
    r.g.put(0x600000, unit)
    r.g.put(0x700000, eq)
    r._array = lambda off: (0x900000, 2, 0x18) if off == 0x38 else (0x500000, 1, 0xF4) if off == 0x10 else (0, 0, 0)
    r.object = lambda h: {UNIT: 0x600000, TAKEN: 0x700000, (0x100 << 16): 0x10000, (0x101 << 16) | 1: 0x20000}.get(h)
    r.objects((2, 3))
    if r._names.get(LOOSE_EQ) != "regenerator_equipment" or LOOSE_GUN in r._names:
        fails.append(f"LiveH3: equipment 1.2 u off its spot named {r._names.get(LOOSE_EQ)!r} (want the regenerator), "
                     f"a gun 1.2 u off it {r._names.get(LOOSE_GUN)!r} (want none)")
    got = r.players()[0].get("equipment")
    if got != "flare":
        fails.append(f"LiveH3: equipment just taken 2.2 u from the flare spot reads {got!r} (want 'flare')")


def main():
    fails = []
    turrets(fails)
    h3_equipment(fails)
    for cls, gun in ((LiveH3, "battle_rifle"), (LiveODST, "smg"), (LiveReach, "dmr"), (LiveH4F, "battle_rifle")):
        r, h = reader(cls, gun)
        r.weapon_name(h[0])                    # players hold the starting gun (players() asks every tick)
        r.weapon_name(h[2])                    # a bot held the rifle before it swapped it for the rockets
        if cls is LiveH4F:
            r._held = {h[0]}                   # (Halo 4's players(): the guns in hands right now)
        r.objects((2,))                        # the ground scan (tools/live_bots.py snapshot, every 0.5 s)
        name = r.weapon_name(h[0])
        if name != gun:
            fails.append(f"{cls.__name__}: the starting {gun} reads {name!r} (a map copy lies on its spawn)")
        if r._names.get(RIFLE) == "rockets":
            fails.append(f"{cls.__name__}: a rifle dropped on the rocket spawn named every rifle 'rockets'")
        if r._names.get(LAUNCHER) != "rockets":
            fails.append(f"{cls.__name__}: the rocket launcher on its spawn was not learned ({r._names.get(LAUNCHER)!r})")
    # a gun the map never places (Epitaph's spawn assault rifle): Halo 3 names it by its full magazine
    for cls, want in ((LiveH3, "assault_rifle"), (LiveODST, "unknown"), (LiveReach, "unknown")):
        r, h = reader(cls, "battle_rifle")
        r._placements = []
        r._mag_seen = {GUN: 32}
        name = r.weapon_name(h[0])
        if name != want:
            fails.append(f"{cls.__name__}: an unplaced gun with a 32-round magazine reads {name!r} (want {want!r})")
    r, h = reader(LiveH3, "battle_rifle")
    r._placements, r._mag_seen = [], {GUN: 8}            # (the magnum's and the missile pod's size: not a name)
    if r.weapon_name(h[0]) != "unknown":
        fails.append("LiveH3: an 8-round magazine named a gun (two guns share it)")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("weapon names OK")


if __name__ == "__main__":
    main()
