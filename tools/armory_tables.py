"""The Armory of Reach and Halo 4 tied to the character model's pieces, for the profile view's 3D bots.

Two halves, read once per MCC install:
  - botcore's catalog log: what its roll picks from and what the game's own equip writes into an appearance block for
    every item and variant (the option chosen per armor byte). Reach (native/reach.cpp hr_log_catalog, s104+):
    "reach armory slot S: n items: raw:variants:word ..." and "reach armory map slot S item I raw R: vV[off=val ..]".
    Halo 4 (native/h4f.cpp f_log_catalog): "h4 armory slot S: n items: raw:variants:word [vV rR=P sR=P x=X] ..." (r: the
    region byte at +0x38 + R, s: +0x40 + R, x: +0x2B); botcore before s103 logged variants 0 and 1 only.
  - the map's customization table: per armor byte of the appearance block (0x38 + region) a list of options, each a
    list of (model region, permutation, mask) records, then lists of base records (the Spartan's, the female body, the
    Elite's). Mask: 1 male only, 2 female only (Reach's robot-arm chests' arms, Halo 4's female pieces), 4 on three
    Reach Elite sets, 0 always. Found by hand (docs/HANDOFF.md, docs/HANDOFF_profiles_oct28.md): a parent of
    blocks (count, pointer, def), options (name sid, count, pointer) and 12-byte records, a stored pointer v at
    (v << 2) + base.

Writes maps/_looks/<game>_armory.json (brain/armory.py rolls and dresses each bot from it, brain/looks.py export_view
writes the pieces into bot_looks.ini).

usage: python -I armory_tables.py [--game reach|h4|h2a|h3] [botcore log with the catalog] [MCC folder]
"""
import json
import os
import re
import struct
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
EXE = paths.map_tool("model2obj")       # (the map tools; checked in main)
MCC = paths.mcc()
# per game (MCC as of Oct 2026): the map, the table's parent (14 blocks of 12 bytes), the stored pointers' base, an
# option's size (Reach: name, count, pointer, 0; Halo 4: name, 0, count, pointer, def), the blocks that are lists of
# records, and the first helmet option the table must start with (checked: a changed map fails loudly instead of
# giving wrong pieces). Blocks 0-9 are the options of appearance bytes 0x38-0x41; elite_bytes: the bytes an Elite
# wears (Reach's Elite has its own set byte; elsewhere the Elite's options sit in the same bytes, told apart by mask)
GAMES = {
    "reach": dict(map=r"haloreach\maps\20_sword_slayer.map", parent=0x6619080, expand=0x50000000, entry=16,
                  lists={"female": 11, "base": 12, "elite_base": 13}, first=["head", "default", 0], elite_bytes=[0x3F],
                  log=os.path.join(ROOT, "native", "bin", "botcore_s104.log")),
    "h4": dict(map=r"halo4\maps\ca_warhouse.map", parent=0xa083188, expand=0x4FFF0000, entry=20,
               lists={"base": 10, "female": 11}, first=["armor_head", "spartan_iv", 0],
               log=os.path.join(ROOT, "native", "bin", "botcore_s99.log")),
    # H2A: no catalog (its look bytes are the table's values, set directly: maps/_looks/h2a.json): the table alone
    "h2a": dict(map=r"groundhog\maps\ca_lockout.map", parent=0x26666fc4, expand=0x7AC00000, entry=20,
                lists={"base": 10, "female": 11, "elite_base": 13}, first=["armor_head", "spartan_iv", 1], log=None),
}
BLOCKS = 14
# Halo 3 (construct.map, read; the other armor work found the same table in five maps and H3EK): two lists of
# "customized areas" (area sid, selections count, pointer, 0), the Spartan's 8 (configuration +0x46 helmet ... +0x4D
# backpack) and the Elite's 7 (+0x4E head ... +0x54 body), each selection (name sid, 0, bits count, pointer, 0) with
# 8-byte bits (region, permutation); pointers stored as v << 2
H3 = dict(map=r"halo3\maps\construct.map", spartan=(0x7a75078, 8, 0x46), elite=(0x7a75c2c, 7, 0x4E))


def read_h3_table(path, g=H3):
    """The Halo 3 table as read_table's: options keyed by appearance offset (configuration offset - 0x20) for both
    species, the bytes each species wears, no base lists (every region a piece of its own comes from an area)."""
    parent = g["spartan"][0]
    addr = int(subprocess.run([EXE, path, "--ptr", f"{parent:x}"], capture_output=True, text=True,
                              check=True).stdout.split()[1], 16)
    off_of = lambda v: (v << 2) - addr + parent
    data = open(path, "rb")

    def words(off, n):
        data.seek(off)
        return struct.unpack(f"<{n}I", data.read(4 * n))
    raw = {}
    for at, n, cfg in (g["spartan"], g["elite"]):
        for k in range(n):
            _, count, p, _ = words(at + 16 * k, 4)
            sels = [words(off_of(p) + 20 * s, 5) for s in range(count)]
            raw[cfg - 0x20 + k] = [[words(off_of(bp) + 8 * b, 2) for b in range(bc)] for _, _, bc, bp, _ in sels]
    names = names_of(path, {w for opts in raw.values() for opt in opts for r in opt for w in r} - {0})
    out = {"options": {str(k): [[[names[r], names[p], 0] for r, p in opt] for opt in opts] for k, opts in raw.items()},
           "spartan_bytes": [g["spartan"][2] - 0x20 + k for k in range(g["spartan"][1])],
           "elite_bytes": [g["elite"][2] - 0x20 + k for k in range(g["elite"][1])],
           "base": [], "female": [], "elite_base": []}
    first = out["options"][str(g["spartan"][2] - 0x20)][0]
    if first != [["helmet", "legacy", 0]]:
        sys.exit(f"{path}: the customization areas are not at {parent:#x} (its first helmet reads {first})")
    return out


def parse_log(lines, game="reach"):
    """(catalog, writes): catalog[slot] = [variant count per item]; writes[slot][item][variant] = {appearance offset:
    value} for the variants logged (None: the equip faulted; a variant past the list was not logged)."""
    catalog, writes = {}, {}
    tag = "reach" if game == "reach" else "h4"
    for line in lines:
        m = re.search(tag + r" armory slot (\d+): (\d+) items:(.*)", line)
        if m:
            slot, items = int(m.group(1)), []
            for it in re.finditer(r"(\d+):(\d+):[0-9a-f]{8}((?: \[v\d+[^\]]*\])*)", m.group(3)):
                items.append(int(it.group(2)))
                if game == "h4":                         # Halo 4: the variants' writes follow each item
                    vs = writes.setdefault(slot, {}).setdefault(len(items) - 1, [])
                    for v, body in re.findall(r"\[v(\d+)([^\]]*)\]", it.group(3)):
                        w = {}
                        for k, n, val in re.findall(r"([rsx])(\d*)=(\d+)", body):
                            w[{"r": 0x38, "s": 0x40, "x": 0x2B}[k] + (int(n) if n else 0)] = int(val)
                        vs.append(w)
            catalog[slot] = items
            continue
        m = re.search(r"reach armory map slot (\d+) item (\d+) raw \d+:(.*)", line)
        if m and game == "reach":
            vs = []
            for v, body in re.findall(r"v(\d+)\[([^\]]*)\]", m.group(3)):
                vs.append(None if body == "fault" else
                          {int(k, 16): int(x) for k, x in (kv.split("=") for kv in body.split())})
            writes.setdefault(int(m.group(1)), {})[int(m.group(2))] = vs
    slots = max(catalog) + 1 if catalog else 0
    return ([catalog.get(s, []) for s in range(slots)],
            [[writes.get(s, {}).get(i, []) for i in range(len(catalog.get(s, [])))] for s in range(slots)])


def names_of(path, sids):
    out = subprocess.run([EXE, path, "--names", ",".join(f"{s:x}" for s in sorted(sids))], capture_output=True,
                         text=True, check=True).stdout
    return {int(a, 16): b for a, b in (line.split(" ", 1) for line in out.splitlines() if " " in line)}


def read_table(path, g):
    """{"options": {appearance offset: [[(region, perm, mask)] per value]}, <list name>: [(region, perm, mask)]}."""
    parent = g["parent"]
    addr = int(subprocess.run([EXE, path, "--ptr", f"{parent:x}"], capture_output=True, text=True,
                              check=True).stdout.split()[1], 16)
    off_of = lambda v: (v << 2) + g["expand"] - addr + parent        # a stored pointer -> file offset
    data = open(path, "rb")

    def words(off, n):
        data.seek(off)
        return struct.unpack(f"<{n}I", data.read(4 * n))
    lists = {b: name for name, b in g["lists"].items()}
    raw = {}
    for b in range(BLOCKS):
        n, p, _ = words(parent + 12 * b, 3)
        if b in lists:                   # records
            raw[b] = [words(off_of(p) + 12 * r, 3) for r in range(n)]
        elif b < 10:                     # options
            opts = [words(off_of(p) + g["entry"] * k, g["entry"] // 4) for k in range(n)]
            cut = (lambda o: (o[1], o[2])) if g["entry"] == 16 else (lambda o: (o[2], o[3]))
            raw[b] = [[words(off_of(rp) + 12 * r, 3) for r in range(c)] for c, rp in map(cut, opts)]
    recs = [r for b, blk in raw.items() for r in (blk if b in lists else [x for opt in blk for x in opt])]
    names = names_of(path, {w for r in recs for w in r[:2]} - {0})
    rec = lambda r: [names[r[0]], names[r[1]], r[2]]
    out = {"options": {str(0x38 + b): [[rec(r) for r in opt if r[0]] for opt in blk]
                       for b, blk in sorted(raw.items()) if b not in lists}}
    out.update({lists[b]: [rec(r) for r in blk if r[0]] for b, blk in raw.items() if b in lists})
    first = out["options"].get("56", [[]])[0][:1]
    if first != [g["first"]]:
        sys.exit(f"{path}: the customization table is not at {parent:#x} (its first helmet reads {first})")
    return out


HOW = {
    "reach": "Reach's Armory catalog as botcore logged it (catalog: variants per item per slot, what native/reach.cpp "
             "hr_roll_armor picks from; writes: per slot, item and variant the appearance bytes the game's own equip "
             "sets, decimal offsets into the configuration's appearance block at +0x20) and the map's customization "
             "table (options: per appearance byte, per value, the model's (region, permutation, mask) pieces; mask 1 "
             "male only, 2 female only; female / base / elite_base: the female body, the Spartan's and the Elite's "
             "base pieces). Slots: 0 helmet, 1-2 shoulders, 3 chest, 4 wrist, 5 utility, 6 visor tint (byte 43), 7 "
             "knees (Reach's own name for the slot is paint_scheme), 8 armor effect, 9 Elite armor, 12 firefight voice "
             "(its equip faults outside a match).",
    "h4": "Halo 4's Armory catalog as botcore logged it (native/h4f.cpp f_log_catalog: catalog, writes as Reach's; "
          "variants not logged are missing, and a bot that rolls one shows no 3D look) and ca_warhouse.map's "
          "customization table (options per region byte 0x38 + region: 0 helmet with its visor, 1 chest, 3 / 4 "
          "shoulders, 5 arms, 6 legs, 8 armor effect; base / female: the techsuit). Slots: 0 helmet, 1 / 2 shoulders, "
          "3 chest, 4 legs, 5 arms (the roll mask 63).",
    "h2a": "Halo 2: Anniversary's customization table (ca_lockout.map; no catalog: maps/_looks/h2a.json sets these "
           "values directly): options per region byte 0x38 + region (0 helmet with its visor, 1 chest, 2 the Elite's "
           "whole sets, 3 / 4 shoulders, 5 forearms, 6 legs; mask 1 Spartan, 2 female Spartan, 0 the Elite's), base / "
           "female: the Spartan's techsuit, elite_base: the Elite's head and techsuit.",
    "h3": "Halo 3's customized areas (construct.map; no catalog: maps/_looks/h3.json sets these values directly): "
          "options keyed by appearance offset (configuration offset - 0x20): the Spartan's helmet, shoulders, chest, "
          "arms, legs, techsuit, backpack (spartan_bytes), the Elite's head, shoulders, chest, arms, legs, body "
          "(elite_bytes); each value's (region, permutation) pieces. Some of MCC's pieces are not in the maps' render "
          "model (el_blaster, el_extractor, el_knight, el_pilot, el_spectrum, el_strider, el_utility; the backpacks "
          "are a gear model of their own): the profile view draws those regions' base piece.",
}


def build(game="reach", log=None, mcc=MCC):
    if game == "h3":
        return dict({"how": "tools/armory_tables.py: " + HOW[game]}, **read_h3_table(os.path.join(mcc, H3["map"])))
    g = GAMES[game]
    out = {"how": "tools/armory_tables.py: " + HOW[game]}
    if g["log"]:
        out["catalog"], out["writes"] = parse_log(open(log or g["log"], encoding="utf-8", errors="replace"), game)
        if not out["catalog"]:
            sys.exit(f"{log or g['log']}: no {game} catalog lines (botcore writes them in a {game} match)")
    if "elite_bytes" in g:
        out["elite_bytes"] = g["elite_bytes"]
    return dict(out, **read_table(os.path.join(mcc, g["map"]), g))


if __name__ == "__main__":
    paths.need(EXE, "model2obj.exe (the map tools: tools/map_tools)")
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "reach"
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--game"]
    data = build(game, args[0] if args else None, args[1] if len(args) > 1 else MCC)
    out = os.path.join(ROOT, "maps", "_looks", f"{game}_armory.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    known = sum(1 for s in data.get("writes", []) for it in s for v in it if v is not None)
    cat = data.get("catalog", [])
    print(f"{out}: {sum(map(len, cat))} catalog items, {sum(map(sum, cat))} variants ({known} with their writes "
          f"logged), {sum(len(v) for v in data['options'].values())} options")
