"""Forge shields by the player's three groups (maps/_shapes/reach_shields.json; brain/forge.py): "two
way" (a bulletproof window you walk through both ways), "one way" (the same, one way only) and "no pass". Checks on
Forge World's own terrain with pieces placed as the player's were (the doors as read live at 62 x, 231 / 229 y):
1. the groups and through sides: shield doors pass along their facing, one-way doors against it (live: the player
   stood east of them, facing west, "if I was to walk forward through them, I would pass through")
2. a one-way piece lets a body through its way only; a no-pass piece neither way (a thick one: a solid box built into
   the nav); a two-way piece both ways
3. every shield stops a sight line (shots) that was open before it was placed
Fails on the code before (shields were left out of the nav and sight lines altogether).

usage: python -I test_forge_shields.py      -> "forge shields OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from brain.core import Vec  # noqa: E402
from brain.forge import apply_shields, shield_blocks, shield_groups, shields  # noqa: E402
from brain.maps import get_map, terrain  # noqa: E402

E, N, U = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
W, S = (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0)
PIECES = [("ff_shield_door_small", (62.0, 231.3, 44.3), (W, S, U)),          # faced west (live)
          ("ff_one_way_door_small", (62.0, 229.5, 44.7), (E, N, U)),         # faced east (live)
          ("frigate_laser_field_wall", (56.0, 222.0, 44.24), (E, N, U)),
          ("dlc_hangar_shield", (70.0, 214.0, 44.6), (N, W, U))]
Z = 44.65
RAYS = {"ff_shield_door_small": (Vec(63.5, 231.3, Z), Vec(60.5, 231.3, Z)),     # (east side, west side)
        "ff_one_way_door_small": (Vec(63.5, 229.5, Z), Vec(60.5, 229.5, Z)),
        "frigate_laser_field_wall": (Vec(57.5, 222.0, Z), Vec(54.5, 222.0, Z)),
        "dlc_hangar_shield": (Vec(76.5, 214.0, Z), Vec(68.5, 214.0, Z))}
# may a body go east -> west, west -> east
WANT = {"ff_shield_door_small": (True, False), "ff_one_way_door_small": (True, False),
        "frigate_laser_field_wall": (False, False), "dlc_hangar_shield": (True, True)}


def main():
    fails = []
    g = shield_groups()
    want = {"ff_shield_door_large": ("one_way", "forward"), "ff_one_way_door_garage": ("one_way", "back"),
            "dlc_hangar_shield_repair_s": ("two_way", None), "frigate_laser_field_gate": ("no_pass", None),
            "dlc_hangar_forcefield_solid": ("no_pass", None)}
    for name, w in want.items():
        if g.get(name) != w:
            fails.append(f"group of {name}: {g.get(name)}, want {w}")
    thick = shield_blocks(shields([("dlc_hangar_forcefield_solid", (0.0, 0.0, 0.0), (E, N, U)),
                                   ("frigate_laser_field_gate", (9.0, 0.0, 0.0), (E, N, U))]))
    if [k[-1].split(":")[-1] for k in thick] != ["dlc_hangar_forcefield_solid"]:
        fails.append(f"thick no-pass pieces built into the nav as solid: {[k[-1] for k in thick]}, want the hangar forcefield")
    T = terrain(get_map("reach_forge_halo"))
    for name, (east, west) in RAYS.items():
        if not T.los(east, west) or T.crosses_barrier(east, west) or T.crosses_barrier(west, east):
            fails.append(f"{name}: the test spot is not open before the piece ({east} - {west})")
    found = shields(PIECES)
    if len(found) != len(PIECES):
        fails.append(f"shields found {len(found)} of {len(PIECES)}")
    apply_shields(T, found)
    for name, (east, west) in RAYS.items():
        got = (not T.crosses_barrier(east, west), not T.crosses_barrier(west, east))
        if got != WANT[name]:
            fails.append(f"{name}: may walk east->west, west->east {got}, want {WANT[name]}")
        if T.los(east, west) or T.los(west, east):
            fails.append(f"{name}: a sight line through it is open (shots pass)")
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print("forge shields OK")


if __name__ == "__main__":
    main()
