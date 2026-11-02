"""Halo: Reach tag names by tag index (tools/reach_tag_names.py), against tag ids read live on the player's Forge World:
the old list (the names buffer in stored order) named 0x2669 a bitmap (airlock_field2) instead of the large shield
door, and 0x1e49 / 0x1e70 bitmaps too.

usage: python -I test_reach_tag_names.py      -> "reach tag names OK" (skipped without MCC's forge_halo.map)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reach_tag_names  # noqa: E402

LIVE = {0x20C2: "ff_column", 0x20EE: "ff_railing_2", 0x2654: "ff_shield_door_small", 0x2662: "ff_shield_door_medium",
        0x2669: "ff_shield_door_large", 0x262D: "ff_one_way_door_xsmall", 0x2633: "ff_one_way_door_garage",
        0x2639: "frigate_laser_field_small", 0x2641: "frigate_laser_field_med", 0x2647: "frigate_laser_field_wall",
        0x264D: "frigate_laser_field_gate", 0x2671: "dlc_hangar_shield_repair_s", 0x2678: "dlc_hangar_forcefield_small_solid",
        0x267F: "dlc_hangar_shield", 0x2686: "dlc_hangar_forcefield_solid", 0x1E49: "cov_barrier",
        0x1E70: "cov_portable_shield", 0x1EE1: "sandbag_wall"}


def main():
    if not os.path.exists(os.path.join(reach_tag_names.MCC, "haloreach", "maps", "forge_halo.map")):
        print("reach tag names OK (skipped: no forge_halo.map)")
        return
    names = reach_tag_names.cached("forge_halo")
    bad = {hex(i): names[i] if i < len(names) else None for i, want in LIVE.items()
           if i >= len(names) or names[i].rsplit("\\", 1)[-1] != want}
    if bad:
        print("FAIL")
        print(f"tag index -> name off: {bad}")
        sys.exit(1)
    print("reach tag names OK")


if __name__ == "__main__":
    main()
