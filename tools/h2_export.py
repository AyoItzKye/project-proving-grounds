"""Build maps/h2_<map>/ for Halo 2 multiplayer maps from the official kit (H2EK, tags extracted
from H2EK.7z): the scenario and structure BSP as XML (tool.exe export-tag-to-xml), the level's
collision geometry as OBJ (collision BSP + every instanced geometry placement, in the CE kit's OBJ
axes so tools/heightmap.py reads it unchanged), objects.json in the CE schema
(tools/scenario_extract.py), heightmap.npz, callouts.json (gen_zones.py) and topdown.png.

usage: python -I h2_export.py [map ...]      (default: all MP maps; names as in tags\\scenarios\\multi)
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KIT = paths.kit("H2EK")
# scenario folder under tags\scenarios\multi (the .map file name is the last part)
MP_MAPS = ["ascension", "backwash", "halo/beavercreek", "burial_mounds", "halo/coagulation", "colossus",
           "containment", "cyclotron", "deltatap", "halo/derelict", "dune", "elongation",
           "marathon/foundation", "marathon/gemini", "headlong", "halo/highplains", "lockout", "midship",
           "needle", "street_sweeper", "triplicate", "turf", "halo/warlock", "waterworks", "zanzibar"]


def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("FAILED:", " ".join(args), "\n", r.stdout[-2000:], r.stderr[-2000:])
    return r


def blk(e, name):
    return next((b for b in e if b.tag == "block" and b.get("name") == name), [])


def fld(e, name):
    f = next((x for x in e if x.tag == "field" and x.get("name") == name), None)
    return None if f is None else (f.text or "").strip()


def vec(s):
    return [float(v) for v in s.split(",")]


def parse(path):
    """tool.exe writes script text as is (cp1252 quotes in Backwash's scripts): not valid UTF-8."""
    return ET.fromstring(open(path, "rb").read().decode("utf-8", "replace"))


def collision_polys(bsp):
    """Polygons (lists of points) of a collision BSP block element: each surface walks its edge
    ring (an edge whose left surface is this one runs start->end, else end->start)."""
    edges = [[int(fld(e, n)) for n in ("start vertex", "end vertex", "forward edge", "reverse edge", "left surface")]
             for e in blk(bsp, "edges")]
    verts = [vec(fld(e, "point")) for e in blk(bsp, "vertices")]
    out = []
    for s, e in enumerate(blk(bsp, "surfaces")):
        first = cur = int(fld(e, "first edge"))
        poly = []
        for _ in range(64):
            sv, ev, fwd, rev, left = edges[cur]
            if left == s:
                poly.append(verts[sv]); cur = fwd
            else:
                poly.append(verts[ev]); cur = rev
            if cur == first:
                break
        if len(poly) >= 3:
            out.append(poly)
    return out


def bsp_obj(bsp_xml, obj_path):
    root = parse(bsp_xml)
    polys = collision_polys(blk(root, "collision bsp")[0])
    defs = [collision_polys(d) for d in blk(root, "instanced geometries definitions")]
    for inst in blk(root, "instanced geometry instances"):
        di = int(next(x for x in inst if x.tag == "block_index").get("index"))
        if not 0 <= di < len(defs):
            continue
        k = float(fld(inst, "scale") or 1) or 1.0
        f, l, u, p = (vec(fld(inst, n)) for n in ("forward", "left", "up", "position"))
        for poly in defs[di]:
            polys.append([[p[j] + k * (x * f[j] + y * l[j] + z * u[j]) for j in range(3)] for x, y, z in poly])
    with open(obj_path, "w") as o:
        n = 0
        for poly in polys:
            for x, y, z in poly:
                o.write(f"v {x:.4f} {z:.4f} {-y:.4f}\n")      # CE kit OBJ axes (x, z, -y)
            for i in range(1, len(poly) - 1):
                o.write(f"f {n + 1} {n + i + 1} {n + i + 2}\n")
            n += len(poly)
    return len(polys)


# H2 netgame flag types -> the CE names brain/maps.py reads
FLAG_TYPES = {"CTF flag spawn": "ctf - flag", "Teleporter (src)": "teleport from", "Teleporter (dest)": "teleport to"}


def enum(s):
    return s.split(",", 1)[1] if s and "," in s else s


def scenario_objects(xml, dst):
    root = parse(xml)
    out = {"netgame_flags": [], "equipment": [], "vehicles": [], "spawns": [], "scenery": []}
    for e in blk(root, "netgame flags"):
        typ = enum(fld(e, "type"))
        team = int((fld(e, "team designator") or "8").split(",")[0])
        ident = team if typ == "CTF flag spawn" else int(fld(e, "identifier") or 0)
        out["netgame_flags"].append({"type": FLAG_TYPES.get(typ, typ), "id": ident, "team": team,
                                     "pos": vec(fld(e, "position")), "facing": float(fld(e, "facing") or 0)})
    for e in blk(root, "netgame equipment"):
        ref = next((x for x in e if x.tag == "tag_reference"), None)
        item = (ref.text or "").strip() if ref is not None else ""
        entry = {"item": item.rsplit("\\", 1)[-1], "path": item, "pos": vec(fld(e, "position")),
                 "games": [g for g in (enum(fld(e, f"type {i}")) for i in range(4)) if g not in (None, "none")],
                 "spawn_time": int(fld(e, "spawn time (in seconds, 0 = default)") or 0)}
        (out["vehicles"] if ref is not None and ref.get("type") == "vehc" else out["equipment"]).append(entry)
    for e in blk(root, "player starting locations"):
        out["spawns"].append({"pos": vec(fld(e, "position")), "team": int((fld(e, "team designator") or "0").split(",")[0]),
                              "facing": float(fld(e, "facing") or 0),
                              "games": [g for g in (enum(fld(e, f"type {i}")) for i in range(4)) if g not in (None, "none")]})
    json.dump(out, open(dst, "w"), indent=1)
    return {k: len(v) for k, v in out.items()}


def export(folder):
    name = folder.rsplit("/", 1)[-1]
    out = os.path.abspath(os.path.join(ROOT, "maps", "h2_" + name))
    src = os.path.join(out, "source")
    os.makedirs(src, exist_ok=True)
    os.makedirs(os.path.join(KIT, "data"), exist_ok=True)      # tool.exe refuses to start without it
    tag = os.path.join(KIT, "tags", "scenarios", "multi", *folder.split("/"), name)
    tool = os.path.join(KIT, "tool.exe")
    files = {}
    for ext, short in (("scenario", "scenario.xml"), ("scenario_structure_bsp", "bsp.xml")):
        files[ext] = os.path.join(src, short)
        if not os.path.exists(files[ext]) or os.path.getsize(files[ext]) == 0:
            path = f"{tag}.{ext}"
            if ext == "scenario_structure_bsp":     # the scenario names its BSP (Turf: turf_bsp0)
                bsps = blk(parse(files["scenario"]), "structure bsps")
                r = next((x for x in bsps[0] if x.tag == "tag_reference" and x.get("name") == "structure bsp"), None) if len(bsps) else None
                if r is not None and r.text:
                    path = os.path.join(KIT, "tags", r.text.strip() + "." + ext)
            run([tool, "export-tag-to-xml", path, files[ext]], cwd=KIT)
        if not os.path.exists(files[ext]) or os.path.getsize(files[ext]) == 0:
            print(name, "no", ext, "export")
            return False
    obj = os.path.join(src, "bsp.obj")
    print(name, "polygons", bsp_obj(files["scenario_structure_bsp"], obj))
    objs = os.path.join(out, "objects.json")
    print(name, scenario_objects(files["scenario"], objs))
    py = [sys.executable, "-I"]
    run(py + [os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25"])
    calls = os.path.join(out, "callouts.json")
    if not os.path.exists(calls):
        run(py + [os.path.join(HERE, "gen_zones.py"), "h2_" + name])
    if os.path.exists(calls):
        run(py + [os.path.join(HERE, "heightmap.py"), obj, objs, out, "0.25", calls])
    ok = all(os.path.exists(os.path.join(out, f)) for f in ("objects.json", "heightmap.npz", "callouts.json"))
    print(name, "OK" if ok else "INCOMPLETE")
    return ok


if __name__ == "__main__":
    for m in sys.argv[1:] or MP_MAPS:
        export(m)
