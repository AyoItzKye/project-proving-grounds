"""Projectile speeds of Halo CE's weapons from the CE kit (tool.exe export-tag-to-xml): what bots
must lead with. Prints initial / final velocity (world units per second) and gravity scale.

usage: python -I ce_projectiles.py
"""
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

KIT = paths.kit("HCEEK")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "proj")
TAGS = [r"assault rifle\bullet", r"pistol\bullet", r"plasma pistol\bolt", r"plasma rifle\bolt",
        r"needler\mp_needle", r"sniper rifle\sniper bullet", r"rocket launcher\rocket", r"fuel rod gun\fuel rod",
        r"shotgun\pellet", r"flamethrower\flame", r"plasma_cannon\plasma_cannon"]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for p in TAGS:
        out = os.path.abspath(os.path.join(OUT, p.replace("\\", "_").replace(" ", "_") + ".xml"))
        subprocess.run([os.path.join(KIT, "tool.exe"), "export-tag-to-xml", "weapons\\" + p + ".projectile", out],
                       cwd=KIT, capture_output=True)
        if not os.path.exists(out):
            print(p, "export failed")
            continue
        t = open(out, errors="replace").read()
        get = lambda k: (re.search(r'name="%s"[^>]*>([^<]*)' % k, t) or [None, "?"])[1].strip()
        print(f"{p:32s} initial {get('initial velocity'):>12s} final {get('final velocity'):>12s} gravity {get('air gravity scale')}")
