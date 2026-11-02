"""Build maps/<map>/ for Halo CE multiplayer maps from the official kit (HCEEK, tags extracted):
scenario XML + level mesh (tool.exe), objects.json, heightmap.npz, callouts.json (generated
landmark zones, tools/gen_zones.py, unless a hand-made one exists), topdown.png.

usage: python -I export_maps.py [map ...]      (default: all 19 MP maps)
"""
import os
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KIT = paths.kit("HCEEK")
MP_MAPS = ["beavercreek", "bloodgulch", "boardingaction", "carousel", "chillout", "damnation",
           "dangercanyon", "deathisland", "gephyrophobia", "hangemhigh", "icefields", "infinity",
           "longest", "prisoner", "putput", "ratrace", "sidewinder", "timberland", "wizard"]


def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("FAILED:", " ".join(args), "\n", r.stdout[-2000:], r.stderr[-2000:])
    return r


def export(name):
    out = os.path.abspath(os.path.join(ROOT, "maps", name))
    src = os.path.join(out, "source")
    os.makedirs(src, exist_ok=True)
    xml = os.path.join(src, f"{name}.scenario.xml")
    obj = os.path.join(src, f"{name}_bsp.obj")
    tool = os.path.join(KIT, "tool.exe")
    if not os.path.exists(xml):
        run([tool, "export-tag-to-xml", f"levels\\test\\{name}\\{name}.scenario", xml], cwd=KIT)
    if not os.path.exists(obj):
        r = run([tool, "export-structure-mesh-obj", f"levels\\test\\{name}\\{name}"], cwd=KIT)
        text = r.stdout
        if "\nv " not in text and not text.startswith("v "):
            print(name, "no mesh in tool output; first lines:", text[:300])
            return False
        open(obj, "w").write(text[text.find("v "):] if not text.startswith("v ") else text)
    py = [sys.executable, "-I"]
    run(py + [os.path.join(HERE, "scenario_extract.py"), xml, os.path.join(out, "objects.json")])
    run(py + [os.path.join(HERE, "heightmap.py"), obj, os.path.join(out, "objects.json"), out, "0.25"])
    calls = os.path.join(out, "callouts.json")
    if not os.path.exists(calls):
        run(py + [os.path.join(HERE, "gen_zones.py"), name])
    if os.path.exists(calls):
        run(py + [os.path.join(HERE, "heightmap.py"), obj, os.path.join(out, "objects.json"), out, "0.25", calls])
    ok = all(os.path.exists(os.path.join(out, f)) for f in ("objects.json", "heightmap.npz", "callouts.json"))
    print(name, "OK" if ok else "INCOMPLETE")
    return ok


if __name__ == "__main__":
    for m in sys.argv[1:] or MP_MAPS:
        export(m)
