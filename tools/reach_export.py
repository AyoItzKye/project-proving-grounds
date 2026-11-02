"""Build maps/reach_<map>/ for Halo: Reach multiplayer maps from the official kit (HREK, tags
extracted from HREK.7z): the level mesh (tool.exe export-structure-mesh-obj, same OBJ axes as the
CE kit), the scenario as XML, objects.json in the CE schema, heightmap.npz, callouts.json
(gen_zones.py) and topdown.png. Mirrors h3_export.py.

Reach places its multiplayer content as objects with multiplayer data (owner team defender = red 0,
attacker = blue 1, megalo label = the game type role):
  spawns     respawn_point / respawn_point_invisible scenery (neutral: Reach picks spawns by
             influence, so each is a slayer spawn for both teams; a CTF spawn for the team whose
             ctf_res_zone respawn zone holds it) and initial_spawn_point scenery (labels team_only,
             ffa_only; inf_spawn = infection, skipped)
  CTF flags  objects labelled ctf_flag_return (mp_flag_base crates): the flag sits on its stand
  others     every other labelled object becomes a netgame flag of that label (koth_hill,
             terr_object, oddball_ball, stp_flag, as_bomb, ...); teleporters by object name
  weapons    weapon placements, item = the brain's weapon name (ALIAS), tag = the palette name

The Reach XML differs from Halo 3's: a block is a <field type="block"> followed by its <element>s
as siblings, and the type field holds the palette name itself.

usage: python -I reach_export.py [map ...]   (default: all MP maps; folder names as under
       levels\\multi, levels\\multi\\dlc, levels\\dlc; output maps/reach_<scenario name>). Not forge_halo:
       Forge World's scenario has no CTF flags, weapons or team spawns (its content is in map variants).

--h2a / --h4: Halo 2 Anniversary (H2AMPEK, levels\\sway\\<map>) and Halo 4 (H4EK, levels\\multi|dlc\\<map>)
multiplayer, output maps/h2a_<map> / maps/h4_<map> (<map> = the game's .map file stem, e.g. ca_lockout).
Their XML is Halo 3 style (<block> elements, placements index a palette) and each level is split into
child scenarios (_spawns, _gamemodes, _ordnance, ...): the main scenario and every child it lists are
merged. Same labels as Reach (initial_spawn_point labelled team_spawn / ffa_spawn, ctf_flag_stand
labelled ctf_flag_return, ctf_res_zone respawn zones). Halo 4 places almost no weapons: they come as
ordnance, a "Drop sets" block (initial and random sets) whose ordnance list tag names one weapon per
drop point (scenery initial_drop_point / random_drop_point). The kits cannot export these level
meshes: the OBJ comes from the game's .map file (bsp2obj, the map tools), every structure BSP but the vista /
skybox ones. Big XMLs are cut to the blocks read here (<name>.slim.xml, kept); the full ones are
deleted after a successful export.
"""
import json
import re
import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KIT = paths.kit("HREK")
PREFIX = "reach_"
MCC = paths.mcc()
GAME_MAPS = None   # the game's .map folder (H2A / H4: the mesh comes from there)
for _flag, _kit, _prefix, _game in (("--h4", "H4EK", "h4_", "halo4"), ("--h2a", "H2AMPEK", "h2a_", "groundhog")):
    if _flag in sys.argv:
        KIT, PREFIX = os.path.join(os.path.dirname(KIT), _kit), _prefix
        GAME_MAPS = os.path.join(MCC, _game, "maps")
        sys.argv.remove(_flag)
MP_MAPS = ["multi/" + m for m in ("20_sword_slayer", "30_settlement", "35_island", "45_aftship", "45_launch_station",
                                  "50_panopticon", "52_ivory_tower", "70_boneyard")] + \
          ["multi/dlc/" + m for m in ("dlc_invasion", "dlc_medium", "dlc_slayer")] + \
          ["dlc/" + m for m in ("cex_beaver_creek", "cex_damnation", "cex_hangemhigh", "cex_headlong", "cex_prisoner",
                                "cex_timberland", "condemned", "trainingpreserve")]
if PREFIX == "h2a_":     # not the three Forge skyboxes
    MP_MAPS = ["sway/" + m for m in ("ca_ascension", "ca_coagulation", "ca_lockout", "ca_relic", "ca_sanctuary",
                                     "ca_warlock", "ca_zanzibar")]
elif PREFIX == "h4_":    # the game's MP .map files (not Spartan Ops ff* / dlc01_*, campaign m*) with a kit scenario
    MP_MAPS = []
    for _s in sorted(f[:-4] for f in os.listdir(GAME_MAPS) if f.endswith(".map")):
        if _s.startswith(("ff", "m", "campaign", "shared", "dlc01_")) or "forge" in _s:
            continue        # Forge canvases: no weapons or bases; their layouts are map variants
        _d = next((d for d in ("multi", "dlc") if os.path.exists(os.path.join(KIT, "tags", "levels", d, _s, _s + ".scenario"))), None)
        if _d:
            MP_MAPS.append(_d + "/" + _s)
        else:
            print(_s, "has no kit scenario: skipped")
TEAMS = {"defender": 0, "attacker": 1, "third party": 2, "fourth party": 3, "fifth party": 4, "sixth party": 5,
         "seventh party": 6, "eighth party": 7, "neutral": 8}
# Reach weapon palette name -> brain weapon name: brain/live.py TAG_ALIAS / brain_name (shared with the live reader)
sys.path.insert(0, ROOT)
from brain.live import TAG_ALIAS as ALIAS, brain_name  # noqa: E402,F401
KNOWN = {"dmr", "magnum", "assault_rifle", "sniper", "rockets", "shotgun", "sword", "needle_rifle", "plasma_pistol",
         "plasma_rifle", "needler", "grenade_launcher", "focus_rifle", "spartan_laser", "plasma_launcher",
         "concussion_rifle", "fuelrod", "gravity_hammer",
         # the rest of brain/bot.py WEAPON_RANGE's keys
         "battle_rifle", "beam_rifle", "brute_plasma_rifle", "brute_shot", "covenant_carbine", "excavator",
         "flamethrower", "missile_pod", "pistol", "sentinel_beam", "smg", "spike_rifle"}


SPAWN_POINTS = ("respawn_point", "respawn_point_invisible")


def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace", **kw)
    if r.returncode != 0:
        print("FAILED:", " ".join(args), "\n", r.stdout[-1500:], r.stderr[-1500:])
    return r


def parse(path):
    # tool.exe writes name=" <unknown>" for unnamed elements, script source like "(<= a 3)"
    # unescaped in attribute values and control characters in names (H2A "cr\x1f_territories"): not valid XML
    text = open(path, "rb").read().decode("utf-8", "replace").replace("<unknown>", "unknown")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r'="([^"]*)"', lambda m: '="%s"' % re.sub(r"&(?![a-z]+;|#)", "&amp;", m.group(1))
                  .replace("<", "&lt;").replace(">", "&gt;"), text)
    return ET.fromstring(text)


PLACED = ("scenery", "equipment", "weapons", "vehicles", "crates", "machines", "controls")
PALETTE = {k: k[:-1] + " palette" for k in PLACED}
PALETTE.update({"scenery": "scenery palette", "equipment": "equipment palette", "machines": "machine palette"})
KEEP = set(PLACED) | set(PALETTE.values()) | {"child scenarios", "structure bsps", "Drop sets"}


def slim(path):
    """H2A / H4: copy only the top-level blocks read here into <path minus .xml>.slim.xml (streamed:
    a decorator child can be a GB of XML)."""
    out = path[:-4] + ".slim.xml"
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
                keep = not line.startswith(b"    </block>")
        o.write(b"</tag>\n")
    return out


def items(root, kind):
    """[(palette short name, element)] of a placement block: Reach XML names the palette entry in the
    type field, Halo 3 style XML (H2A, H4) indexes the palette block (type ",<i>")."""
    if not any(c.tag == "block" for c in root):
        return [(fld(e, "type") or "NONE", e) for e in blk(root, kind)]
    pal = [(fld(e, "name") or "").split(",")[0].rsplit("\\", 1)[-1]
           for e in next((b for b in root if b.tag == "block" and b.get("name") == PALETTE[kind]), [])]
    out = []
    for e in next((b for b in root if b.tag == "block" and b.get("name") == kind), []):
        i = int((fld(e, "type") or ",-1").split(",")[-1] or -1)
        if 0 <= i < len(pal):
            out.append((pal[i], e))
    return out


ORDNANCE = {}    # ordnance list tag -> [ordnance names] (Halo 4)


def ordnance_list(tag, src):
    if tag not in ORDNANCE:
        xml = os.path.join(src, "ordnance_" + tag.rsplit("\\", 1)[-1] + ".xml")
        if not os.path.exists(xml):
            run([os.path.join(KIT, "tool.exe"), "export-tag-to-xml",
                 os.path.join(KIT, "tags", tag + ".scenario_ordnance_list"), xml], cwd=KIT)
        ORDNANCE[tag] = [] if not os.path.exists(xml) or not os.path.getsize(xml) else \
            [fld(e, "ordnance_name") or "" for b in parse(xml) if b.tag == "block" and b.get("name") == "Random ordnance drop list"
             for e in b]
        if not ORDNANCE[tag]:
            print("ordnance list missing from the kit:", tag)
    return ORDNANCE[tag]


def ordnance(root, src):
    """Halo 4 ordnance: [(ordnance name, drop point element, set kind)] of the initial and random drop
    sets (objective sets, flag 8, are game type drops). The i-th drop point gets the list's i-th entry;
    random sets only where they drop at every point they list."""
    scen = next((b for b in root if b.tag == "block" and b.get("name") == "scenery"), [])
    scen = list(scen)
    out = []
    for e in next((b for b in root if b.tag == "block" and b.get("name") == "Drop sets"), []):
        flags = int(fld(e, "drop set flags") or 0)
        tag = (fld(e, "Ordnance List") or "").split(",")[0]
        if not flags & 5 or not tag:
            continue
        names = ordnance_list(tag, src)
        pts = [int(x.get("value").split(",")[-1] or -1) for x in e.iter("field") if x.get("name") == "Drop point"]
        if not flags & 1 and int(fld(e, "count") or 1) < len(pts):
            continue        # a random set dropping at one of several points (Adrift: rockets / sword / ...): no fixed spot
        for k, i in enumerate(pts):
            if names and 0 <= i < len(scen):
                out.append((names[k % len(names)], scen[i], "initial" if flags & 1 else "random"))
    return out


def blk(root, name):
    """Elements of a top-level block: the <element> siblings after its <field type="block">."""
    out, on = [], False
    for c in root:
        if c.tag == "field":
            if on:
                break
            on = c.get("name") == name and c.get("type") == "block"
        elif on:
            out.append(c)
    return out


def fld(e, name):
    f = next((x for x in e.iter("field") if x.get("name") == name), None)
    return None if f is None else f.get("value")


def vec(s):
    return [round(float(v), 3) for v in s.split(",")]


def yaw(e):
    return round(float((fld(e, "rotation") or "0").split(",")[0]), 3)


def in_zone(p, z):
    """Inside a respawn zone's boundary (box / cylinder / sphere around its position)."""
    dx, dy, dz = p[0] - z["pos"][0], p[1] - z["pos"][1], p[2] - z["pos"][2]
    if not -z["down"] <= dz <= z["up"]:
        return False
    if z["shape"] == "box":       # ponytail: which of width / length runs along the yaw is unverified,
        h = max(z["w"], z["l"]) / 2   # so the box is taken as the square of the longer side
        a = math.radians(z["yaw"])
        u, v = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
        return abs(u) <= h and abs(v) <= h
    return math.hypot(dx, dy) <= z["w"] if z["shape"] == "cylinder" else math.dist((dx, dy, dz), (0, 0, 0)) <= z["w"]


FLOORS = None    # set by export() before scenario_objects: (floors, x0, y0, cell) of the map's heightmap


def on_floor(q):
    """Is there walkable floor within 1.5 units below / above q in the map's heightmap?"""
    if FLOORS is None:
        return True
    import numpy as np
    floors, x0, y0, cell = FLOORS
    j, i = int((q[1] - y0) / cell), int((q[0] - x0) / cell)
    if not (0 <= j < floors.shape[1] and 0 <= i < floors.shape[2]):
        return False
    col = floors[:, j, i]
    return bool(np.any(np.isfinite(col) & (np.abs(col - q[2]) < 1.5)))


def scenario_objects(xmls, dst):
    """xmls: the scenario XML, or a list of them (H2A / H4: the main scenario and its children)."""
    roots = [parse(x) for x in ([xmls] if isinstance(xmls, str) else xmls)]
    src = os.path.dirname(dst if isinstance(xmls, str) else xmls[0])
    out = {"netgame_flags": [], "equipment": [], "vehicles": [], "spawns": [], "scenery": []}
    unmapped = set()

    def team(e):
        return TEAMS.get(fld(e, "owner team") or "neutral", 8)

    def placed(kind):
        return [(n, e) for r in roots for n, e in items(r, kind) if n != "NONE" and fld(e, "position") is not None]

    for kind, key in (("weapons", "equipment"), ("equipment", "equipment"), ("vehicles", "vehicles")):
        for name, e in placed(kind):
            item = brain_name(name)
            if kind == "weapons" and item not in KNOWN:
                unmapped.add(name)
            out[key].append({"item": item, "tag": name, "path": name, "pos": vec(fld(e, "position")), "yaw": yaw(e),
                             "team": team(e), "games": ["all games"], "spawn_time": int(fld(e, "spawn time") or 0),
                             "unique": "unique spawn" in (fld(e, "spawn flags") or "")})
    for r in roots:                       # Halo 4 ordnance drops
        for name, e, kind in ordnance(r, src):
            item = brain_name(name)
            if not name.startswith(("ord_grenade", "ord_equip")) and item not in KNOWN:
                unmapped.add(name)
            out["equipment"].append({"item": item, "tag": name, "path": name, "pos": vec(fld(e, "position")),
                                     "yaw": yaw(e), "team": team(e), "games": ["all games"], "spawn_time": 0,
                                     "ordnance": kind})
    points, initial, zones, seen = [], [], {0: [], 1: []}, []
    out["placed"] = []                    # every placement, for the nav's solid objects (brain/placed.py)
    for kind in ("scenery", "crates", "controls", "machines"):
        for name, e in placed(kind):
            label = fld(e, "megalo label") or ""
            pos, t = vec(fld(e, "position")), team(e)
            seen.append(pos)
            if name not in SPAWN_POINTS and name not in ("initial_spawn_point", "respawn_zone", "named_location_area",
                                                         "firefight_respawn_zone", "mp_cinematic_camera"):
                rot = [float(v) for v in (fld(e, "rotation") or "0,0,0").split(",")[:3]]
                out["placed"].append({"name": name, "kind": kind, "pos": pos, "rot": [round(v, 3) for v in rot],
                                      "label": label, "flags": fld(e, "spawn flags") or "", "team": t})
            if name in SPAWN_POINTS or name == "firefight_respawn_zone":   # Firefight: the Spartans' respawns
                points.append((pos, yaw(e)))
            elif name == "initial_spawn_point":
                if label in ("team_only", "team_spawn") and t in (0, 1):     # H2A / H4: team_spawn, ffa_spawn
                    initial.append((pos, yaw(e), [t]))
                elif label in ("ffa_only", "ffa_spawn"):
                    initial.append((pos, yaw(e), [0, 1]))
            elif "respawn_zone" in name or label.startswith("ctf_res_zone") or name == "mp_cinematic_camera":
                # Sword Base, Beaver Creek: on hill beacons; H4 also labels anti-respawn zones ctf_res_zone
                if label == "ctf_res_zone" and t in (0, 1) and "anti" not in name:
                    zones[t].append({"pos": pos, "yaw": yaw(e), "shape": fld(e, "boundary shape"),
                                     "w": float(fld(e, "boundary width or radius") or 0),
                                     "l": float(fld(e, "boundary box length") or 0),
                                     "up": float(fld(e, "boundary positive height") or 0),
                                     "down": float(fld(e, "boundary negative height") or 0)})
            elif label == "ctf_flag_return":
                out["netgame_flags"].append({"type": "ctf - flag", "id": t, "team": t, "pos": pos, "facing": yaw(e)})
                out["netgame_flags"].append({"type": "CTF flag return", "id": t, "team": t, "pos": pos, "facing": yaw(e)})
            elif name.startswith("teleporter"):
                chan = fld(e, "teleporter channel") or "alpha"
                two = "2way" in name or "two_way" in name
                kinds = ["teleport from", "teleport to"] if two else \
                    ["teleport from"] if "sender" in name else ["teleport to"] if "rec" in name else []
                for k in kinds:
                    out["netgame_flags"].append({"type": k, "id": chan, "team": t, "pos": pos, "facing": yaw(e),
                                                 "two_way": two})
            elif label:
                f = {"type": label, "id": 0, "team": t, "pos": pos, "facing": yaw(e), "object": name}
                shape = fld(e, "boundary shape") or "unused"
                if shape != "unused":             # the objective's zone as the map sets it (hills, territories ...)
                    f["boundary"] = {"shape": shape, "w": float(fld(e, "boundary width or radius") or 0),
                                     "l": float(fld(e, "boundary box length") or 0),
                                     "up": float(fld(e, "boundary positive height") or 0),
                                     "down": float(fld(e, "boundary negative height") or 0)}
                out["netgame_flags"].append(f)
    if points and not any(f["type"] == "ctf - flag" for f in out["netgame_flags"]):
        # Firefight has no netgame flags: the players' base at their respawns, the "enemy base"
        # (the brain's map model wants two) at the placed object farthest from it
        home = points[0][0]
        far = max(seen, key=lambda q: math.dist(q, home) if on_floor(q) else -1)
        for t, q in ((0, home), (1, far)):
            out["netgame_flags"].append({"type": "ctf - flag", "id": t, "team": t, "pos": q, "facing": 0.0})
    # CTF spawns: the respawn points inside a team's ctf_res_zone; none -> the points nearer its flag
    ctf = {t: [p for p, _ in points if any(in_zone(p, z) for z in zones[t])] for t in (0, 1)}
    flag = {f["team"]: f["pos"] for f in out["netgame_flags"] if f["type"] == "ctf - flag" and f["team"] in (0, 1)}
    if (not ctf[0] or not ctf[1]) and len(flag) == 2:
        for t in (0, 1):
            ctf[t] = [p for p, _ in points if math.dist(p, flag[t]) < math.dist(p, flag[1 - t])]
    for p, f in points:
        for t in (0, 1):
            out["spawns"].append({"pos": p, "team": t, "facing": f, "games": ["slayer"] + (["ctf"] if p in ctf[t] else [])})
    for p, f, ts in initial:
        for t in ts:
            out["spawns"].append({"pos": p, "team": t, "facing": f, "games": ["slayer", "ctf"], "initial": True})
    json.dump(out, open(dst, "w"), indent=1)
    counts = {k: len(v) for k, v in out.items()}
    counts["ctf spawns"] = (len(ctf[0]), len(ctf[1]))
    return counts, sorted(unmapped)


def top_block(root, name):
    return next((b for b in root if b.tag == "block" and b.get("name") == name), [])


def kit_xml(tag, xml):
    """H2A / H4: a scenario tag as XML cut to the blocks read here (the .slim.xml path, None if the
    kit could not export it)."""
    out = xml[:-4] + ".slim.xml"
    if not os.path.exists(out):
        if not os.path.exists(xml) or os.path.getsize(xml) == 0:
            run([os.path.join(KIT, "tool.exe"), "export-tag-to-xml", os.path.join(KIT, "tags", tag + ".scenario"), xml],
                cwd=KIT)
        if not os.path.exists(xml) or os.path.getsize(xml) == 0:
            print("no XML for", tag)
            return None
        slim(xml)
    return out


def scenario_xmls(tag, src):
    """The main scenario and every child scenario it lists (H2A / H4 split a level into several)."""
    main = kit_xml(tag, os.path.join(src, "scenario.xml"))
    if main is None:
        return []
    out = [main]
    for e in top_block(parse(main), "child scenarios"):
        t = (fld(e, "tag") or "").split(",")[0]
        c = t and kit_xml(t, os.path.join(src, "scenario_" + t.rsplit("\\", 1)[-1] + ".xml"))
        if c:
            out.append(c)
    return out


def map_mesh(name, main, obj):
    """The level mesh from the game's .map file (bsp2obj, the map tools): every structure BSP the scenario lists
    but the vista / sky ones (Lockout's vista: mountains 1 km around), concatenated into one OBJ. Judged by what
    follows the map's name (the Forge skyboxes' only BSP is ca_forge_skybox01_bsp01)."""
    exe = paths.need(paths.map_tool("bsp2obj"), "bsp2obj.exe (the map tools: tools/map_tools)")
    mp = os.path.join(GAME_MAPS, name + ".map")
    bsps = [(fld(e, "structure bsp") or "").split(",")[0] for e in top_block(parse(main), "structure bsps")]
    own = lambda b: b.rsplit("\\", 1)[-1].lower().replace(name.lower(), "")
    keep = [b for b in bsps if b and not any(w in own(b) for w in ("vista", "sky"))]
    base = 0
    with open(obj + ".part", "w") as o:
        for b in keep:
            part = obj + ".one"
            print(name, run([exe, mp, part, b]).stdout.strip().splitlines()[-1:])
            n = 0
            for line in open(part):
                if line.startswith("v "):
                    o.write(line)
                    n += 1
                elif line.startswith("f "):
                    o.write("f " + " ".join(str(int(x) + base) for x in line.split()[1:]) + "\n")
            base += n
            os.remove(part)
    if base == 0:
        os.remove(obj + ".part")
        return False
    os.replace(obj + ".part", obj)
    return True


def export(folder):
    name = folder.rsplit("/", 1)[-1]
    out = os.path.abspath(os.path.join(ROOT, "maps", PREFIX + name))
    src = os.path.join(out, "source")
    os.makedirs(src, exist_ok=True)
    tool = os.path.join(KIT, "tool.exe")
    tag = "levels\\" + folder.replace("/", "\\") + "\\" + name
    xml = os.path.join(src, "scenario.xml")
    obj = os.path.join(src, "bsp.obj")
    if GAME_MAPS:                                   # H2A / H4
        xml = scenario_xmls(tag, src)
        if not xml:
            return False
        if not os.path.exists(obj) and not map_mesh(name, xml[0], obj):
            print(name, "no mesh from the .map file")
            return False
    elif not os.path.exists(xml) or os.path.getsize(xml) == 0:
        run([tool, "export-tag-to-xml", os.path.join(KIT, "tags", tag + ".scenario"), xml], cwd=KIT)
    if not os.path.exists(obj):
        lines = [ln for ln in run([tool, "export-structure-mesh-obj", tag], cwd=KIT).stdout.splitlines(True)
                 if ln.startswith(("v ", "f "))]
        if not lines:
            print(name, "no mesh in tool output")
            return False
        open(obj, "w").writelines(lines)
    objs = os.path.join(out, "objects.json")
    global FLOORS
    hm = os.path.join(out, "heightmap.npz")
    if folder.startswith("firefight/") and not os.path.exists(hm):
        # Firefight's made-up enemy base must stand on floor: make the heightmap first
        scenario_objects(xml, objs)
        run([sys.executable, "-I", os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25"])
    FLOORS = None
    if os.path.exists(hm):
        import numpy as np
        d = np.load(hm)
        FLOORS = (d["floors"], float(d["x0"]), float(d["y0"]), float(d["cell"]))
    counts, unmapped = scenario_objects(xml, objs)
    print(name, counts, "unmapped weapons:", unmapped or "none")
    py = [sys.executable, "-I"]
    run(py + [os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25"])
    calls = os.path.join(out, "callouts.json")
    if not os.path.exists(calls):
        r = run(py + [os.path.join(HERE, "gen_zones.py"), PREFIX + name])
        if r.returncode:
            print(name, "gen_zones:", (r.stdout + r.stderr).strip()[-300:])
    if os.path.exists(calls):
        run(py + [os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25", calls])
    ok = all(os.path.exists(os.path.join(out, f)) for f in ("objects.json", "heightmap.npz", "callouts.json"))
    print(name, "OK" if ok else "INCOMPLETE")
    if ok and GAME_MAPS:          # the full XMLs (up to GBs): the .slim.xml copies hold what is read here
        for f in os.listdir(src):
            if f.startswith("scenario") and f.endswith(".xml") and not f.endswith(".slim.xml"):
                os.remove(os.path.join(src, f))
    return ok


if __name__ == "__main__":
    for m in sys.argv[1:] or MP_MAPS:
        export(m)
