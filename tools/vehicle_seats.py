"""Seats of Halo: Reach's multiplayer vehicles and their turrets, from the editing kit's tags (HREK tool.exe
export-tag-to-xml): per vehicle, its seats in tag order [index, label, ai seat type, flags]. A seat's index is what the
game's enter-seat interaction takes (ghidra/hr_interactions.c FUN_180051278: slot type 5/6/9, seat at +4, vehicle at
+8). The Warthog's gun is its own vehicle (warthog_chaingun / _gauss / _rocket / _troop) riding on it, so a gunner
enters that turret's seat. -> maps/_shapes/reach_seats.json

usage: python -I vehicle_seats.py
"""
import json
import os
import re
import subprocess
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HREK = paths.kit("HREK")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "maps", "_shapes", "reach_seats.json")
TAGS = ["human/warthog/warthog", "human/warthog/weapons/warthog_chaingun/warthog_chaingun",
        "human/warthog/weapons/warthog_gauss/warthog_gauss", "human/warthog/weapons/warthog_rocket/warthog_rocket",
        "human/warthog/weapons/warthog_troop/warthog_troop", "human/mongoose/mongoose", "human/scorpion/scorpion",
        "human/scorpion/turrets/scorpion_anti_infantry/scorpion_anti_infantry",
        "human/scorpion/turrets/scorpion_cannon/scorpion_cannon", "human/falcon/falcon",
        "human/falcon/turrets/falcon_side_gun_left/falcon_side_gun_left",
        "human/falcon/turrets/falcon_side_gun_right/falcon_side_gun_right",
        "human/falcon/turrets/falcon_side_grenade_left/falcon_side_grenade_left",
        "human/falcon/turrets/falcon_side_grenade_right/falcon_side_grenade_right",
        "human/falcon/turrets/falcon_chin_gun/falcon_chin_gun", "human/turrets/machinegun/machinegun",
        "covenant/ghost/ghost", "covenant/banshee/banshee", "covenant/wraith/wraith",
        "covenant/wraith/turrets/wraith_anti_infantry/wraith_anti_infantry",
        "covenant/wraith/turrets/wraith_mortar/wraith_mortar", "covenant/revenant/revenant",
        "covenant/revenant/turrets/revenant_plasma_turret/revenant_plasma_turret",
        "covenant/turrets/plasma_turret/plasma_turret_mounted", "covenant/turrets/shade/shade"]
SEAT = re.compile(r'<element index="(\d+)" name="([^"]*)">\s*<field name="flags" value="([^"]*)"', re.S)


def seats(xml):
    body = xml[xml.index('<field name="seats" value='):]
    out = []
    for m in SEAT.finditer(body):
        k = int(m.group(1))
        if k != len(out):            # (the block's own elements only: nested blocks start their own count at 0)
            continue
        rest = body[m.end():]
        ai = re.search(r'name="ai seat type" value="([^"]*)"', rest)
        out.append([k, m.group(2), ai.group(1) if ai else "?", m.group(3)])
    return out


def main():
    table = {}
    tmp = tempfile.mkdtemp()
    for t in TAGS:
        src = os.path.join(HREK, "tags", "objects", "vehicles", *t.split("/")) + ".vehicle"
        dst = os.path.join(tmp, os.path.basename(t) + ".xml")
        subprocess.run([os.path.join(HREK, "tool.exe"), "export-tag-to-xml", src, dst], cwd=HREK,
                       capture_output=True, timeout=120)
        if not os.path.exists(dst):
            print("no export:", t)
            continue
        table[os.path.basename(t)] = seats(open(dst, encoding="utf-8", errors="replace").read())
        print(os.path.basename(t), [(k, label, ai) for k, label, ai, _ in table[os.path.basename(t)]])
    json.dump(table, open(OUT, "w", encoding="utf-8"), indent=1)
    print("->", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
