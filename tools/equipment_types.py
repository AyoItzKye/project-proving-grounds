"""Armor abilities from the editing kits' own tags (tool.exe export-tag-to-xml): which equipment type
block each one fills and its timing (activation mode, energy drain and recharge, warmup, charges).

In memory the game tells abilities apart the same way: the equipment definition holds one tag block
per type and the filled one is the ability (Reach: blocks from definition +0x28C, 12 bytes each,
ghidra/hr_ability_queries.c; Halo 4 / H2A: inside the "abilities" block, element +0x48 + 12 k,
ghidra/h4_type_accessor.c, h2a_type_accessor.c). Writes brain/equipment_tags.json: per game, the
type block -> ability kind map brain/live.py reads abilities with, and each kind's timing for the
brain's energy model (brain/equipment.py).

usage: python -I equipment_types.py [reach|h4|h2a ...]      (default: all three)
"""
import json
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "logs", "equip")
JSON = os.path.join(ROOT, "brain", "equipment_tags.json")
KITS = {"reach": "HREK", "h4": "H4EK", "h2a": "H2AMPEK"}
COMMON = paths.steam_common()
FIRST = "multiplayer powerup"        # the first type block (the one after "override camera")
# the multiplayer abilities, by tag (the kits also hold campaign and AI ones)
ABILITIES = {
    "reach": {"armor_lockup": "armor_lock", "active_camouflage": "active_camo", "drop_shield": "drop_shield",
              "evade": "evade", "hologram": "hologram", "jet_pack": "jetpack", "sprint": "sprint"},
    "h4": {"storm_active_shield": "hardlight_shield", "storm_auto_turret": "autosentry", "storm_active_camo": "active_camo",
           "storm_forerunner_vision": "promethean_vision", "storm_hologram": "hologram", "storm_jet_pack": "jetpack",
           "storm_regen_field": "regen_field", "storm_thruster_pack": "thruster", "sprint": "sprint"},
    "h2a": {"storm_active_camo": "active_camo", "hero_assist": "hero_assist"},
}
TIMING = ("warmup time", "duration", "cooldown time", "energy recovery time", "minimum activation energy",
          "activation energy cost", "active energy rate", "inactive energy rate", "charges", "activation mode")


def tags(kit):
    base = os.path.join(COMMON, kit, "tags")
    for d, _, files in os.walk(base):
        for f in files:
            if f.endswith(".equipment"):
                yield os.path.join(d, f)


BLOCK = re.compile(r'^( *)(?:<field name="([^"]+)" value="(\d+)" type="block"/?>|<block name="([^"]+)" count="(\d+)">)')


def types(lines):
    """The type blocks in order, (name, element count): from FIRST on, every block at its indent
    (Reach writes them as top-level fields; Halo 4 and H2A as <block> inside "abilities"), the
    contents of filled ones skipped, until something else appears at that indent."""
    out, indent = [], None
    for line in lines:
        m = BLOCK.match(line)
        depth = len(line) - len(line.lstrip(" "))
        if indent is None:
            if m and (m.group(2) or m.group(4)) == FIRST:
                indent = depth
            else:
                continue
        s = line.strip()
        if depth > indent or s in ("</block>", "</field>", "</element>") or s.startswith("<element"):
            continue                       # a filled block's contents (Reach puts them at the same indent)
        if not m or depth != indent:
            break
        out.append((m.group(2) or m.group(4), int(m.group(3) or m.group(5))))
    return out


def timing(lines):
    """The equipment timing fields: each one's occurrence nearest the "minimum activation energy"
    field (Reach keeps them at the top level; Halo 4 splits them between the top level and the
    abilities element)."""
    field = re.compile(r'<field name="([^"]+)" value="([^"]*)"')
    at = next((i for i, l in enumerate(lines) if 'name="minimum activation energy"' in l), None)
    if at is None:
        return {}
    best = {}
    for i, l in enumerate(lines):
        m = field.search(l)
        if m and m.group(1) in TIMING and (m.group(1) not in best or abs(i - at) < best[m.group(1)][0]):
            best[m.group(1)] = (abs(i - at), m.group(2))
    out = {}
    for k, (_, v) in best.items():
        try:
            out[k] = float(v) if k != "activation mode" else v
        except ValueError:
            out[k] = v
    return out


def main():
    games = sys.argv[1:] or list(KITS)
    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(JSON)) if os.path.exists(JSON) else {}
    for g in games:
        kit = os.path.join(COMMON, KITS[g])
        print(f"== {g} ({KITS[g]})")
        kinds = {}
        for path in sorted(tags(KITS[g])):
            rel = os.path.relpath(path, os.path.join(kit, "tags"))
            name = os.path.basename(rel)[:-10]
            if not re.search(r"equipment|powerup", rel, re.I):
                continue
            xml = os.path.join(OUT, f"{g}_" + re.sub(r"[\\/ ]", "_", rel)[:-10] + ".xml")
            if not os.path.exists(xml):
                subprocess.run([os.path.join(kit, "tool.exe"), "export-tag-to-xml", os.path.abspath(path),
                                os.path.abspath(xml)], cwd=kit, capture_output=True, timeout=120)
            if not os.path.exists(xml):
                continue
            lines = open(xml, errors="replace").read().splitlines()
            filled = [k for k, (n, c) in enumerate(types(lines)) if c]
            kind = ABILITIES[g].get(name)
            if kind and rel.startswith("objects\\equipment") and filled:
                kinds[kind] = dict(tag=rel[:-10], blocks=filled, **{k.replace(" ", "_"): v for k, v in timing(lines).items()})
                print(f"  {kind:18} blocks {filled}  {timing(lines)}")
        data[g] = kinds
    json.dump(data, open(JSON, "w"), indent=1, sort_keys=True)
    print("wrote", os.path.relpath(JSON, ROOT))


if __name__ == "__main__":
    main()
