"""Placed objects' real sizes from the editing kit's own collision models (tool.exe export-tag-to-xml), for the nav:
the level mesh (maps/<map>/source/bsp.obj) has none of the objects a map places (Invasion's force-field doors and
gates, crates, barriers, Forge pieces), so bots walked into them or tried to walk through one-way shields. Writes
maps/_shapes/<game>.json: {object name: {"min": [x, y, z], "max": [x, y, z], "material": first material name, "tag":
path}} in the object's own axes (x forward along its facing, y left, z up), world units, and
maps/_shapes/<game>_faces.json: every collision surface of each (faces), so a Forge piece goes into the nav by the
angle of each face, not as one solid box.

usage: python -I object_shapes.py [reach]      (every object name in the game's maps/*/objects.json)
"""
import glob
import json
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KITS = {"reach": paths.kit("HREK"), "h4": paths.kit("H4EK"),
        "h2a": paths.kit("H2AMPEK"), "h3": paths.kit("H3EK")}
PREFIX = {"reach": "reach_", "h4": "h4_", "h2a": "h2a_", "h3": "h3_"}
CACHE = os.path.join(ROOT, "logs", "shape_xml")
KINDS = (".crate", ".scenery", ".device_machine", ".device_control", ".machine", ".control", ".equipment")


def names(game):
    """Every placed object name in the game's map exports (netgame flags' "object", scenery / crates)."""
    out = set()
    for f in glob.glob(os.path.join(ROOT, "maps", PREFIX[game] + "*", "objects.json")):
        o = json.load(open(f, encoding="utf-8"))
        for key in ("netgame_flags", "scenery", "crates", "placed"):
            for it in o.get(key, []):
                n = it.get("object") or it.get("item") or it.get("name")
                if n:
                    out.add(n)
    pal = os.path.join(ROOT, "maps", "_shapes", game + "_forge_palette.json")   # Forge World's pieces (forge_palette.py)
    if os.path.exists(pal):
        out |= {o["object"] for o in json.load(open(pal, encoding="utf-8"))}
    every = os.path.join(ROOT, "maps", "_shapes", game + "_forge_all_items.json")   # the player's ALL ITEMS map, read
    if os.path.exists(every):                                                       # live (tools/forge_dump.py)
        out |= {it["name"].replace("\\", "/").rsplit("/", 1)[-1] for it in json.load(open(every, encoding="utf-8"))["items"]
                if it["type"] not in (0, 1, 2, 3, 5, 10)}    # (not bipeds, vehicles, weapons, equipment, sounds)
    return sorted(out)


def index_defs(kit):
    """{short name: object definition tag} (crate, scenery, machine, control, vehicle ...): their bounding radius is the
    object's own (read live by brain/forge.py to tell a Forge piece's kind)."""
    out = {}
    for ext in (".crate", ".scenery", ".device_machine", ".device_control", ".vehicle", ".weapon", ".equipment"):
        for p in glob.glob(os.path.join(kit, "tags", "**", "*" + ext), recursive=True):
            out.setdefault(os.path.splitext(os.path.basename(p))[0], p)
    return out


BOUND_R = re.compile(r'name="bounding radius" value="([-\d.e+]+)"')
BOUND_O = re.compile(r'name="bounding offset" value="([-\d.e+]+),([-\d.e+]+),([-\d.e+]+)"')


def index_tags(kit):
    """{object name: collision_model path}: every collision model in the kit's tags, by its file name."""
    out = {}
    for p in glob.glob(os.path.join(kit, "tags", "**", "*.collision_model"), recursive=True):
        out.setdefault(os.path.splitext(os.path.basename(p))[0], p)
    return out


def export(kit, tag):
    os.makedirs(CACHE, exist_ok=True)
    xml = os.path.join(CACHE, re.sub(r"[^\w]+", "_", os.path.relpath(tag, kit)) + ".xml")
    if not os.path.exists(xml) or os.path.getsize(xml) == 0:
        try:
            subprocess.run([os.path.join(kit, "tool.exe"), "export-tag-to-xml", os.path.abspath(tag), os.path.abspath(xml)],
                           cwd=kit, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:   # (a huge model: Hang 'Em High's grav lift tunnels hung the tool)
            print("timed out:", os.path.basename(tag), flush=True)
            return None
    return xml if os.path.exists(xml) and os.path.getsize(xml) else None


POINT = re.compile(r'name="point" value="([-\d.e+]+),([-\d.e+]+),([-\d.e+]+)"')
MATERIAL = re.compile(r'<field name="name" value="([^"]*)" type="string id"/>')


def shape(xml):
    """Bounding box of every collision vertex, and the first material's name (e.g. energy_shield_thick_for)."""
    text = open(xml, encoding="utf-8", errors="replace").read()
    pts = [tuple(float(v) for v in m.groups()) for m in POINT.finditer(text)]
    if not pts:
        return None
    mat = MATERIAL.search(text)
    return dict(min=[round(min(p[k] for p in pts), 3) for k in range(3)],
                max=[round(max(p[k] for p in pts), 3) for k in range(3)],
                material=mat.group(1) if mat else "")


def _blocks(parent):
    """{block name: [element...]}: a Reach XML block is a block field followed by its elements as siblings; Halo 4's and
    H2A's (H4EK, H2AMPEK) a <block name=...> holding its elements (every H4 / H2A face list came out empty)."""
    out, cur = {}, None
    for ch in parent:
        if ch.tag == "block":
            out.setdefault(ch.get("name", "").strip(), []).extend(e for e in ch if e.tag == "element")
            cur = None
        elif ch.tag == "field" and ch.get("type") == "block":
            cur = out.setdefault(ch.get("name"), [])
        elif ch.tag == "element" and cur is not None:
            cur.append(ch)
    return out


def _fields(e):
    return {f.get("name").strip(): f.get("value") for f in e if f.tag == "field"}


def faces(xml):
    """Every collision surface as (material name, [(x, y, z), ...]): the polygon walked round its edge ring (each edge
    names the surfaces on its left and right; a surface's ring goes start vertex -> forward edge while the surface is on
    the edge's left, end vertex -> reverse edge while on its right), outward by its winding (Forge World's ramp: the
    slope faces up, the bottom down). Each region's intact permutation ("default" or "base"; some list "destroyed"
    first: the Invasion bomb door, the battery), else its first; all its BSPs."""
    import xml.etree.ElementTree as ET
    text = open(xml, encoding="utf-8", errors="replace").read()     # (H4EK writes control characters into strings
    text = re.sub(r'="<([^"<>]*)>"', r'="\1"', re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text))   # and value="<..>")
    root = ET.fromstring(text)
    mats = [_fields(m).get("name", "") for m in _blocks(root).get("materials", [])]
    out = []
    for reg in _blocks(root).get("regions", []):
        perms = _blocks(reg).get("permutations", [])
        perm = next((p for p in perms if _fields(p).get("name") in ("default", "base")), perms[0] if perms else None)
        for bsp in _blocks(perm).get("bsps", []) if perm is not None else []:
            b = _blocks(bsp)
            V = [tuple(round(float(v), 4) for v in _fields(e)["point"].split(",")) for e in b.get("vertices", [])]
            E = [tuple(int(_fields(e)[k]) for k in ("start vertex", "end vertex", "forward edge", "reverse edge",
                                                     "left surface")) for e in b.get("edges", [])]
            for si, s in enumerate(b.get("surfaces", [])):
                f = _fields(s)
                ring, seen, e = [], set(), int(f["first edge"])
                while 0 <= e < len(E) and e not in seen:
                    seen.add(e)
                    sv, ev, fe, re_, left = E[e]
                    ring.append(V[sv] if left == si else V[ev])
                    e = fe if left == si else re_
                m = int(f["material"])
                if len(ring) >= 3:
                    out.append((mats[m] if 0 <= m < len(mats) else "", ring))
    return out


HALF = re.compile(r'name="half extents" value="([-\d.e+]+),([-\d.e+]+),([-\d.e+]+)"')
TRANS = re.compile(r'name="translation" value="([-\d.e+]+),([-\d.e+]+),([-\d.e+]+)"')
RADIUS = re.compile(r'name="radius" value="([-\d.e+]+)"')


def physics_shape(xml):
    """Bounding box of a physics model's box shapes (half extents + convex radius, at their translation): the props
    with no collision model (Reach's nut_blockers boxes and walls, Forge pieces)."""
    text = open(xml, encoding="utf-8", errors="replace").read()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for m in HALF.finditer(text):
        h = [float(v) for v in m.groups()]
        rads = list(RADIUS.finditer(text, max(0, m.start() - 400), m.start()))
        r = float(rads[-1].group(1)) if rads else 0.0
        t = TRANS.search(text, m.end())
        c = [float(v) for v in t.groups()] if t and t.start() - m.end() < 2500 else [0.0, 0.0, 0.0]
        for k in range(3):
            lo[k], hi[k] = min(lo[k], c[k] - h[k] - r), max(hi[k], c[k] + h[k] + r)
    if lo[0] > hi[0]:
        return None
    return dict(min=[round(v, 3) for v in lo], max=[round(v, 3) for v in hi], material="physics")


def index_physics(kit):
    out = {}
    for p in glob.glob(os.path.join(kit, "tags", "**", "*.physics_model"), recursive=True):
        out.setdefault(os.path.splitext(os.path.basename(p))[0], p)
    return out


def main(game="reach"):
    kit = KITS[game]
    tags = index_tags(kit)
    phys = index_physics(kit)
    defs = index_defs(kit)
    # every tag exported first, six tool.exe at a time (each takes seconds to start: Halo 4's and H2A's ~700 took hours
    # one by one); the loop below then reads the cache
    from concurrent.futures import ThreadPoolExecutor
    todo = [p for n in names(game) for p in (tags.get(n) or phys.get(n), defs.get(n)) if p]
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda t: export(kit, t), todo))
    out, missing, faced = {}, [], {}
    for n in names(game):
        tag = tags.get(n)
        xml = export(kit, tag) if tag else None
        s = shape(xml) if xml else None
        if s:
            faced[n] = [[mat, [round(v, 3) for p in ring for v in p]] for mat, ring in faces(xml)]
        if s is None and phys.get(n):                 # no collision model: the physics model's boxes
            tag = phys[n]
            xml = export(kit, tag)
            s = physics_shape(xml) if xml else None
        if s:
            s["tag"] = os.path.relpath(tag, os.path.join(kit, "tags")).replace("\\", "/")
            d = defs.get(n)
            dx = export(kit, d) if d else None
            if dx:                                    # the definition's bounding sphere (read live: brain/forge.py)
                head = open(dx, encoding="utf-8", errors="replace").read(20000)
                r, o = BOUND_R.search(head), BOUND_O.search(head)
                if r:
                    s["bound_r"] = round(float(r.group(1)), 4)
                if o:
                    s["bound_off"] = [round(float(v), 4) for v in o.groups()]
            out[n] = s
        else:
            missing.append(n)
    dst = os.path.join(ROOT, "maps", "_shapes")
    os.makedirs(dst, exist_ok=True)
    json.dump(dict(how=__doc__.split("\n\n")[0], shapes=out, no_collision=missing),
              open(os.path.join(dst, game + ".json"), "w", encoding="utf-8"), indent=1)
    json.dump(dict(how="Collision surfaces per object (object_shapes.py faces()): [material, [x, y, z, ...]] polygons "
                       "in the object's own axes, outward by their winding; for the nav face by face (brain/forge.py)",
                   faces=faced), open(os.path.join(dst, game + "_faces.json"), "w", encoding="utf-8"), separators=(",", ":"))
    print(f"{game}: {len(out)} shapes, {len(missing)} names without a collision model, {len(faced)} with faces")


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["reach"]))
