"""Turn a scenario exported with `tool.exe export-tag-to-xml` into a compact JSON of the
multiplayer objects bots care about: netgame flags (CTF stands, teleporters...), weapon and
powerup spawns, vehicles, player spawns and scenery (rocks, trees).

usage: python -I scenario_extract.py <scenario.xml> <out.json>
"""
import json
import sys
import xml.etree.ElementTree as ET


def block(root, name):
    return next((b for b in root.findall("block") if b.attrib.get("name", "").lower() == name), [])


def field(el, name):
    f = next((x for x in el if x.attrib.get("name") == name), None)
    return None if f is None else (f.text or "").strip()


def ref(el, name):
    f = next((x for x in el if x.tag == "tag_reference" and x.attrib.get("name") == name), None)
    return None if f is None else (f.text or "").strip()


def point(s):
    return [round(float(v), 3) for v in s.split(",")] if s else None


def enum(s):
    return s.split(",", 1)[1] if s and "," in s else s


def palette(root, name):
    return [ref(e, "name") for e in block(root, name)]


def main(src, dst):
    root = ET.parse(src).getroot()
    out = {"netgame_flags": [], "equipment": [], "vehicles": [], "spawns": [], "scenery": []}
    for e in block(root, "netgame flags"):
        out["netgame_flags"].append({"type": enum(field(e, "type")), "id": int(field(e, "usage id") or 0),
                                     "pos": point(field(e, "position")), "facing": float(field(e, "facing") or 0)})
    for e in block(root, "netgame equipment"):
        out["equipment"].append({"item": ref(e, "item collection"), "pos": point(field(e, "position")),
                                 "games": [enum(field(e, f"type {i}")) for i in range(4) if enum(field(e, f"type {i}")) not in (None, "none")],
                                 "spawn_time": int(field(e, "spawn time") or 0)})
    vpal = palette(root, "vehicle palette")
    for e in block(root, "vehicles"):
        i = int(next(x for x in e if x.tag == "block_index").attrib["index"])
        out["vehicles"].append({"vehicle": vpal[i] if 0 <= i < len(vpal) else None, "pos": point(field(e, "position")),
                                "team": int(field(e, "multiplayer team index") or 0),
                                "yaw": float((field(e, "rotation") or "0").split(",")[0])})
    for e in block(root, "player starting locations"):
        out["spawns"].append({"pos": point(field(e, "position")), "team": int(field(e, "team index") or 0),
                              "facing": float(field(e, "facing") or 0),
                              "games": [enum(field(e, f"type {i}")) for i in range(4) if enum(field(e, f"type {i}")) not in (None, "none")]})
    spal = palette(root, "scenery palette")
    for e in block(root, "scenery"):
        i = int(next(x for x in e if x.tag == "block_index").attrib["index"])
        out["scenery"].append({"scenery": spal[i] if 0 <= i < len(spal) else None, "pos": point(field(e, "position"))})
    json.dump(out, open(dst, "w"), indent=1)
    for k, v in out.items():
        print(k, len(v))


if __name__ == "__main__":
    main(*sys.argv[1:3])
