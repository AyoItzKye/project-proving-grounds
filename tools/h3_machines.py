r"""Halo 3 maps' machines (doors, gates, lifts) into objects.json "placed" (kind "machines": name, pos, rot in degrees as
reach_export writes it, flags), from each map's scenario XML (maps/h3_*/source/scenario.xml), so the nav knows a door that starts shut and opens
only by a switch (brain/placed.py static_boxes: "does not operate automatically", not "initially open"). Live High
Ground Multi Flag, Nov 12: its base gate (deadlock_gate_v3) was open floor to the nav, and red's runners pressed into it
at (-6, 4, 12) for 14 minutes ("step down", "unstuck wiggle"): 0-0, one pickup. Only "placed" changes (the H3 exports
kept none); its other kinds are left as they were.

usage: python -I h3_machines.py [map ...]      (default: every maps/h3_* with a scenario.xml)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "maps")


def machines(xml):
    """[{name, pos, rot, flags, kind}] of a Halo 3 scenario XML's "machines" placements (their "machine palette")."""
    text = open(xml, encoding="utf-8", errors="replace").read()
    pal_at = text.find('<block name="machine palette"')
    pal_end = text.find("\n    </block>", pal_at)
    palette = [m.split(",")[0].rsplit("\\", 1)[-1] for m in
               re.findall(r'<field name="name" value="([^"]*)" type="tag reference"/>', text[pal_at:pal_end])]
    a = text.find('<block name="machines"')
    b = text.find("\n    </block>", a)
    out = []
    for el in re.split(r'\n        <element index="\d+"', text[a:b])[1:]:
        t = re.search(r'<field name="type" value=",(-?\d+)"', el)
        p = re.search(r'<field name="position" value="([^"]+)"', el)
        r = re.search(r'<field name="rotation" value="([^"]+)"', el)
        if not (t and p and r) or not 0 <= int(t.group(1)) < len(palette):
            continue
        flags = [f.strip() for f in re.findall(r'type="long flags">\s*([^<]+?)\s*</field>', el, re.S) for f in f.split("\n")]
        out.append(dict(kind="machines", name=palette[int(t.group(1))],
                        pos=[round(float(v), 4) for v in p.group(1).split(",")],
                        rot=[round(float(v), 4) for v in r.group(1).split(",")],
                        flags=", ".join(f for f in flags if f)))
    return out


def main(names):
    for d in names or sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "h3_*"))):
        xml, objs = os.path.join(ROOT, d, "source", "scenario.xml"), os.path.join(ROOT, d, "objects.json")
        if not (os.path.exists(xml) and os.path.exists(objs)):
            continue
        got = machines(xml)
        o = json.load(open(objs, encoding="utf-8"))
        o["placed"] = [it for it in o.get("placed", []) if it.get("kind") != "machines"] + got
        json.dump(o, open(objs, "w", encoding="utf-8"), indent=1)
        shut = [m["name"] for m in got if "does not operate automatically" in m["flags"] and "initially open" not in m["flags"]]
        print(f"{d}: {len(got)} machines, shut until a switch: {shut}")


if __name__ == "__main__":
    main(sys.argv[1:])
