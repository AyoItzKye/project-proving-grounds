"""Halo: Reach Forge World's map-variant palette (the forge_halo scenario's "map variant palettes": every object a map
variant can place) to maps/_shapes/reach_forge_palette.json: [{palette, name, object}] (object = the tag's short name),
and add those names to the shapes (tools/object_shapes.py reads this list too), so Forge pieces read live in a match
(brain/forge.py) get their box.

usage: python -I forge_palette.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
XML = os.path.join(ROOT, "maps", "reach_forge_halo", "source", "scenario.xml")
OUT = os.path.join(ROOT, "maps", "_shapes", "reach_forge_palette.json")


def main():
    text = open(XML, encoding="utf-8", errors="replace").read()
    start = text.find('<field name="map variant palettes"')
    end = text.find('<field name="map variant palettes compatibility"', start)
    block = text[start:end]
    out, pal = [], None
    for line in block.splitlines():
        m = re.match(r'\s{4}<element index="\d+" name="([^"]*)">', line)
        if m:
            pal = m.group(1)
            continue
        m = re.search(r'<field name="object" value="([^"]*)" type="tag reference"/>', line)
        if m and m.group(1):
            out.append(dict(palette=pal, object=m.group(1).rsplit("\\", 1)[-1]))
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"{len(out)} palette objects in {len({o['palette'] for o in out})} palettes -> {OUT}")


if __name__ == "__main__":
    main()
