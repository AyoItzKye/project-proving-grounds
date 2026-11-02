"""Build maps/h3_<map>/ for Halo 3 multiplayer maps from the official kit (H3EK, tags extracted
from H3EK.7z with its bin\\x64\\7zr): the level mesh (tool.exe export-structure-mesh-obj, same OBJ
axes as the CE kit), the scenario as XML, objects.json in the CE schema, heightmap.npz,
callouts.json (gen_zones.py) and topdown.png.

Halo 3 places its multiplayer content as objects with multiplayer data (owner team defender =
red 0, attacker = blue 1, spawn time): weapons, equipment, vehicles; crates for CTF flag spawns,
teleporters; scenery for respawn points.

usage: python -I h3_export.py [map ...]      (default: all MP maps; folder names as in levels\\multi, levels\\dlc)
"""
import json
import math
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KIT = paths.kit("H3EK")
PREFIX = "h3_"
if "--odst" in sys.argv:          # Halo 3: ODST Firefight maps (same engine): python -I h3_export.py --odst atlas/h100
    KIT, PREFIX = paths.kit("H3ODSTEK"), "odst_"
    sys.argv.remove("--odst")
MP_MAPS = ["multi/" + m for m in ("chill", "construct", "cyberdyne", "deadlock", "guardian", "isolation", "riverworld",
                                  "salvation", "shrine", "snowbound", "zanzibar", "s3d_avalanche", "s3d_edge",
                                  "s3d_lockout", "s3d_powerhouse", "s3d_reactor", "s3d_sky_bridgenew", "s3d_turf",
                                  "s3d_waterfall")] + \
          ["dlc/" + m for m in ("armory", "bunkerworld", "chillout", "descent", "docks", "fortress", "ghosttown",
                                "lockout", "midship", "sandbox", "sidewinder", "spacecamp", "warehouse")]
TEAMS = {"defender": 0, "attacker": 1, "third": 2, "fourth": 3, "neutral": 8}


def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace", **kw)
    if r.returncode != 0:
        print("FAILED:", " ".join(args), "\n", r.stdout[-1500:], r.stderr[-1500:])
    return r


KEEP = {"scenery", "scenery palette", "vehicles", "vehicle palette", "equipment", "equipment palette", "weapons",
        "weapon palette", "player starting locations", "crates", "crate palette"}


def slim(path):
    """Campaign-sized scenarios (ODST's hub: a 1.2 GB XML) do not fit ElementTree: copy only the
    top-level blocks the exporter reads into <path>.slim.xml (streamed line by line)."""
    out = path + ".slim.xml"
    if os.path.exists(out):
        return out
    with open(path, "rb") as f, open(out, "wb") as o:
        o.write(f.readline())                       # <?xml ...?>
        root = f.readline()
        o.write(root)
        keep = False
        for line in f:
            if line.startswith(b'    <block name="'):
                keep = line.split(b'"')[1].decode() in KEEP
            if keep:
                o.write(line)
            if keep and line.startswith(b"    </block>"):
                keep = False
        o.write(b"</" + root.split()[0][1:].rstrip(b">") + b">\n")
    return out


def parse(path):
    if os.path.getsize(path) > 200_000_000:
        path = slim(path)
    # tool.exe writes name=" <unknown>" for unnamed elements, script source like "(<= a 3)"
    # unescaped in attribute values and control characters in names: not valid XML (as reach_export)
    text = open(path, "rb").read().decode("utf-8", "replace").replace("<unknown>", "unknown")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r'="([^"]*)"', lambda m: '="%s"' % re.sub(r"&(?![a-z]+;|#)", "&amp;", m.group(1))
                  .replace("<", "&lt;").replace(">", "&gt;"), text)
    return ET.fromstring(text)


def blk(root, name):
    return next((b for b in root if b.tag == "block" and b.get("name") == name), [])


def fld(e, name):
    """A field anywhere under an element (Halo 3 XML flattens structs into siblings)."""
    f = next((x for x in e.iter("field") if x.get("name") == name), None)
    return None if f is None else f.get("value")


def vec(s):
    return [round(float(v), 3) for v in s.split(",")]


def palette(root, name):
    return [(fld(e, "name") or "").split(",")[0] for e in blk(root, name)]


def placements(root, kind):
    """[(palette short name, element)] of a placement block (weapons, crates, ...)."""
    pal = palette(root, kind[:-1] + " palette" if not kind.endswith("y") else kind + " palette")
    out = []
    for e in blk(root, kind):
        i = int((fld(e, "type") or ",-1").split(",")[1])
        if 0 <= i < len(pal):
            out.append((pal[i].rsplit("\\", 1)[-1], e))
    return out


def scenario_objects(xml, dst):
    root = parse(xml)
    out = {"netgame_flags": [], "equipment": [], "vehicles": [], "spawns": [], "scenery": []}

    def team(e):
        return TEAMS.get(fld(e, "owner team") or "neutral", 8)

    for kind, key in (("weapons", "equipment"), ("equipment", "equipment"), ("vehicles", "vehicles")):
        pal = palette(root, {"weapons": "weapon palette", "equipment": "equipment palette", "vehicles": "vehicle palette"}[kind])
        for e in blk(root, kind):
            i = int((fld(e, "type") or ",-1").split(",")[1])
            if not 0 <= i < len(pal):
                continue
            out[key].append({"item": pal[i].rsplit("\\", 1)[-1], "path": pal[i], "pos": vec(fld(e, "position")),
                             "team": team(e), "games": ["all games"], "spawn_time": int(fld(e, "spawn time") or 0)})
    crate_pal = palette(root, "crate palette")
    for e in blk(root, "crates"):
        i = int((fld(e, "type") or ",-1").split(",")[1])
        if not 0 <= i < len(crate_pal):
            continue
        name = crate_pal[i].rsplit("\\", 1)[-1]
        pos, t = vec(fld(e, "position")), team(e)
        if name == "ctf_flag_spawn_point":
            out["netgame_flags"].append({"type": "ctf - flag", "id": t, "team": t, "pos": pos, "facing": 0.0})
        elif name == "ctf_flag_return_area":
            out["netgame_flags"].append({"type": "CTF flag return", "id": t, "team": t, "pos": pos, "facing": 0.0})
        elif name.startswith("teleporter"):
            chan = fld(e, "teleporter channel") or "alpha"
            kinds = {"teleporter_sender": ["teleport from"], "teleporter_reciever": ["teleport to"],
                     "teleporter_2way": ["teleport from", "teleport to"]}[name] if name in (
                "teleporter_sender", "teleporter_reciever", "teleporter_2way") else []
            for k in kinds:
                out["netgame_flags"].append({"type": k, "id": chan, "team": t, "pos": pos, "facing": 0.0, "two_way": name == "teleporter_2way"})
        elif name in ("koth_hill_static", "territory_static", "oddball_ball_spawn_point"):
            out["netgame_flags"].append({"type": name, "id": 0, "team": t, "pos": pos, "facing": 0.0})
    scen_pal = palette(root, "scenery palette")
    for e in blk(root, "scenery"):
        i = int((fld(e, "type") or ",-1").split(",")[1])
        if 0 <= i < len(scen_pal) and scen_pal[i].rsplit("\\", 1)[-1] in ("respawn_point", "slayer_initial_spawn_point",
                                                                          "ctf_initial_spawn_point", "respawn_point_invisible"):
            out["spawns"].append({"pos": vec(fld(e, "position")), "team": team(e) % 8,
                                  "facing": 0.0, "games": ["all games"]})
    for e in blk(root, "player starting locations"):
        if PREFIX == "odst_" and "survival" not in (e.findtext("field[@name='flags']") or ""):
            continue                     # ODST: only Firefight's starts ("survival mode" flag)
        out["spawns"].append({"pos": vec(fld(e, "position")), "team": 0, "facing": float(fld(e, "facing") or 0),
                              "games": ["all games"]})
    if PREFIX == "odst_" and out["spawns"]:
        # a campaign scenario holds the whole city: keep what is near Firefight's starts (the
        # heightmap covers the objects plus a margin)
        c = [sum(p["pos"][k] for p in out["spawns"]) / len(out["spawns"]) for k in range(3)]
        for key in ("equipment", "vehicles", "netgame_flags"):
            out[key] = [o for o in out[key] if math.dist(o["pos"][:2], c[:2]) < 70]
    if out["spawns"] and not any(f["type"] == "ctf - flag" for f in out["netgame_flags"]):
        # Firefight (ODST): no netgame flags; the brain's map model wants two bases: the players'
        # at their start, a made-up enemy one at the farthest placed weapon / equipment
        home = out["spawns"][0]["pos"]
        stuff = [o["pos"] for o in out["equipment"] + out["vehicles"]] or [home]
        far = max(stuff, key=lambda q: sum((a - b) ** 2 for a, b in zip(q, home)))
        for t, q in ((0, home), (1, far)):
            out["netgame_flags"].append({"type": "ctf - flag", "id": t, "team": t, "pos": q, "facing": 0.0})
        for p in list(out["spawns"]):
            out["spawns"].append(dict(p, team=1))
    json.dump(out, open(dst, "w"), indent=1)
    return {k: len(v) for k, v in out.items()}


def export(folder):
    name = folder.rsplit("/", 1)[-1]
    out = os.path.abspath(os.path.join(ROOT, "maps", PREFIX + name))
    src = os.path.join(out, "source")
    os.makedirs(src, exist_ok=True)
    os.makedirs(os.path.join(KIT, "data"), exist_ok=True)
    tool = os.path.join(KIT, "tool.exe")
    tag = "levels\\" + folder.replace("/", "\\") + "\\" + name
    xml = os.path.join(src, "scenario.xml")
    if not os.path.exists(xml) or os.path.getsize(xml) == 0:
        run([tool, "export-tag-to-xml", os.path.join(KIT, "tags", tag + ".scenario"), xml], cwd=KIT)
    obj = os.path.join(src, "bsp.obj")
    if not os.path.exists(obj) and PREFIX == "odst_":
        # the ODST kit's mesh export does BSP 0 only: every BSP from the game's own .map file
        # (bsp2obj, the map tools)
        exe = paths.need(paths.map_tool("bsp2obj"), "bsp2obj.exe (the map tools: tools/map_tools)")
        mp = os.path.join(paths.mcc(), "halo3odst", "maps", name + ".map")
        run([exe, mp, obj])
    if not os.path.exists(obj):
        text = run([tool, "export-structure-mesh-obj", tag], cwd=KIT).stdout
        i = text.find("\nv ")
        if i < 0:
            print(name, "no mesh in tool output:", text[:300])
            return False
        open(obj, "w").write(text[i + 1:])
    objs = os.path.join(out, "objects.json")
    print(name, scenario_objects(xml, objs))
    py = [sys.executable, "-I"]
    run(py + [os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25"])
    calls = os.path.join(out, "callouts.json")
    if not os.path.exists(calls):
        run(py + [os.path.join(HERE, "gen_zones.py"), PREFIX + name])
    if os.path.exists(calls):
        run(py + [os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25", calls])
    ok = all(os.path.exists(os.path.join(out, f)) for f in ("objects.json", "heightmap.npz", "callouts.json"))
    print(name, "OK" if ok else "INCOMPLETE")
    return ok


if __name__ == "__main__":
    for m in sys.argv[1:] or MP_MAPS:
        export(m)
