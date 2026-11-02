"""The names of every armor piece the Settings tab's bot editor offers in Halo: Reach and Halo 4, in each game's own
words and order. The editing kits' Armory (HREK / H4EK ui\\supply_depot.cookie_purchase_globals, exported with the
kit's tool.exe, the English text from its string list tag's own data) lists the catalog botcore rolls from in the
same order (docs/HANDOFF_armor_oct28.md); each item is tied to the customization table value the game's own equip
writes for it (maps/_looks/<game>_armory.json "writes", botcore's catalog log), and MCC's additions keep the names
reach.json / h4.json give them ("mcc_names").

Writes each armor field's "original" (the 2010 / 2012 Armory's values), "modern" (MCC's too), "names" (per table
value) into maps/_looks/reach.json and h4.json, adding the slots botcore lays over its roll only when set by hand in
the editor (mcc: []), and native/look_names.h: the editor's lists, the Original values first in the Armory's order,
then MCC's (tools/test_looks.py checks both agree).

usage: python -I look_names.py [--steam <a steamapps\\common folder>]"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
LOOKS = os.path.join(ROOT, "maps", "_looks")
STEAM = sys.argv[sys.argv.index("--steam") + 1] if "--steam" in sys.argv else paths.steam_common()
CACHE = os.path.join(ROOT, "logs", "kit")
KITS = {"reach": ("HREK", r"ui\cui\strings\start_menu_player_strings.multilingual_unicode_string_list"),
        "h4": ("H4EK", r"ui\strings\player_customization.multilingual_unicode_string_list")}
# per game: editor field, catalog slot, appearance byte (configuration offset = byte + 0x20), the kit's block
SLOTS = {
    "reach": [("helmet", 0, 56, "helmet purchasable families"), ("left_shoulder", 1, 57, "left shoulder purchasable families"),
              ("right_shoulder", 2, 58, "right shoulder purchasable families"), ("chest", 3, 59, "chest purchasable families"),
              ("wrist", 4, 60, "wrist purchasable families"), ("utility", 5, 61, "utility purchasable families"),
              ("visor", 6, 43, "visor tint purchasable families"), ("knees", 7, 62, "paint scheme purchasable families"),
              ("elite_armor", 9, 63, "elite armor purchasable families"),
              ("armor_effect", 8, 64, "armor effect purchasable families")],
    "h4": [("helmet", 0, 56, "Helmet purchasable appearance families"),
           ("left_shoulder", 1, 59, "Left shoulder purchasable appearance families"),
           ("right_shoulder", 2, 60, "Right shoulder purchasable appearance families"),
           ("chest", 3, 57, "Chest purchasable appearance families"), ("legs", 4, 62, "Legs purchasable appearance families"),
           ("arms", 5, 61, "Arms purchasable appearance families"),
           ("visor", 13, 43, "Visor tint purchasable appearance families")]}
# Reach's kit names are its menu's capitals; the player's list (mcc_items.json, MCC's ids) writes them as MCC
# does
HR_SLOT = {"helmet": "Helmet", "left_shoulder": "LeftShoulder", "right_shoulder": "RightShoulder", "chest": "Chest",
           "wrist": "Wrist", "utility": "Utility", "visor": "VisorColor", "knees": "KneeGuards", "elite_armor": "Elite",
           "armor_effect": "ArmorEffect"}
HR_ALIAS = {("ArmorEffect", "LEGENDARY"): "FLAMES", ("ArmorEffect", "ETERNAL"): "BLUEFLAMES"}   # (MCC's ids for them)
# Reach's armor effect writes two bytes, +0x40 and +0x41 (both armor_fx: HREK objects\characters\spartans\fx\armor_fx
# armor_fx.effect: 1 head_fire, 2 head_fire_bungie, 3 cupid_heart, 4 bugs + pestilence gas, 5 thunder_cloud and
# lightning; 6 only in armor_fx_death.effect, the confetti)
ALSO = {("reach", "armor_effect"): [65]}
# Halo 4's armor effect is its own byte, configuration +0x60 (H4EK globals "spartan armor effect selections"), MCC's
# addition: Modern only, laid only when set by hand (the roll's own pick is brain/looks.py's effect byte)
H4_EFFECTS = ["None", "Legendary", "Eternal", "Heart Attack", "Pestilence", "Inclement Weather", "Birthday Party"]
SMALL = {"of", "and"}


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def kit_xml(game, tag):
    """The kit tag exported to XML (cached in logs/kit), bytes XML cannot hold left out."""
    kit, _ = KITS[game]
    out = os.path.join(CACHE, f"{game}_{os.path.basename(tag).split('.')[0]}.xml")
    if not os.path.exists(out):
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run([os.path.join(STEAM, kit, "tool.exe"), "export-tag-to-xml", os.path.join(STEAM, kit, "tags", tag),
                        out], cwd=os.path.join(STEAM, kit), capture_output=True, check=True)
    raw = open(out, "rb").read().decode("utf-8", "replace")
    return ET.fromstring("".join(c for c in raw if c in "\t\n\r" or " " <= c <= "\ud7ff" or "\ue000" <= c <= "\ufffd"))


def strings(game):
    """{string id: English} from the string list tag: its data blob found by where its offsets' strings end."""
    kit, tag = KITS[game]
    refs = []
    for el in kit_xml(game, tag).iter("element"):
        f = {x.get("name"): x.get("value") for x in el.findall("field")}
        if "string id" in f and "english offset" in f:
            refs.append((f["string id"], int(f["english offset"])))
    data = open(os.path.join(STEAM, kit, "tags", tag), "rb").read()
    probe, top = sorted({o for _, o in refs if o > 0})[:80], max(o for _, o in refs)
    p = next((p for p in range(len(data) - top) if all(data[p + o - 1] == 0 for o in probe)), None)
    if p is None:
        sys.exit(f"{game}: the string list's data not found")
    return {sid: data[p + o:data.index(b"\0", p + o)].decode("utf-8") for sid, o in refs if o >= 0}


def blocks(node):
    """[(block name, [elements])] at this level, either export style (HREK: a block field, then its elements; H4EK:
    <block name count> holding them)."""
    out = []
    for el in node:
        if el.tag == "block":
            out.append((el.get("name"), el.findall("element")))
        elif el.tag == "field" and el.get("type") == "block":
            out.append((el.get("name"), []))
        elif el.tag == "element" and out:
            out[-1][1].append(el)
    return out


def armory(game):
    """{kit block: [(family title, [item display names])]} in the Armory's order."""
    S = strings(game)
    root = kit_xml(game, r"ui\supply_depot.cookie_purchase_globals")
    top = blocks(root)
    items = []
    for name, els in top:
        if name in ("purchasable items", "purchasable appearance items"):
            for el in els:
                f = {x.get("name"): x.get("value") for x in el.findall("field")}
                items.append((el.get("name"), S.get(f.get("display name", ""), "").strip()))
    by_name = dict(items)
    out = {}
    for name, els in top:
        if "families" not in name:
            continue
        fams = []
        for fam in els:
            f = {x.get("name"): x.get("value") for x in fam.findall("field")}
            names = []
            for _, its in blocks(fam):
                for it in its:
                    ref = next((x.get("value") for x in it.iter("field") if x.get("name") == "item reference"), "")
                    names.append(items[int(ref[1:])][1] if ref.startswith(",") else by_name.get(ref or it.get("name"), ""))
            fams.append((S.get(f.get("display title", ""), "").strip(), names))
        out[name] = fams
    return out


def reach_case(s):
    """A Reach menu name as MCC and the player's list write it: words in capitals, acronyms kept."""
    keep = {"UA", "HUL", "CBRN", "CNM", "FC", "HU", "RS", "EOD", "EVA", "JFO", "ODST", "CQC", "CQB", "HP", "LRP",
            "TACPAD", "UGPS", "FJ", "PARA", "GUNGNIR", "HAZOP", "NXRA", "I", "II", "III", "V", "VI", "B", "C", "R", "W",
            "MK", "MJOLNIR"}
    def word(w):
        core = re.sub(r"[^A-Za-z]", "", w)
        if not core or core.upper() in keep or any(ch.isdigit() for ch in w):
            return w.replace("NXRA", "NxRA").replace("MK.", "Mk.")
        return w[0] + w[1:].lower() if w.lower() not in SMALL else w.lower()
    return " ".join("/".join("-".join(word(p) for p in part.split("-")) for part in tok.split("/")) for tok in s.split(" "))


def build(game):
    lay_path = os.path.join(LOOKS, game + ".json")
    lay = json.load(open(lay_path, encoding="utf-8"))
    t = json.load(open(os.path.join(LOOKS, game + "_armory.json"), encoding="utf-8"))
    kit = armory(game)
    mcc = json.load(open(os.path.join(LOOKS, "mcc_items.json"), encoding="utf-8"))["games"]
    owner = {}
    if game == "reach":                       # (slot, family, variant) -> the player's / MCC's name, by MCC's ids
        for key, nm in mcc["reach"]["original"].items():
            parts = key.split("_")
            if len(parts) >= 3:
                owner[(parts[1], norm(parts[2]), norm(parts[3]) if len(parts) > 3 else "")] = nm
    fields = {f["name"]: f for f in lay["fields"]}
    lists = []
    for name, slot, byte, block in SLOTS[game]:
        opts = len(t["options"].get(str(byte), [])) if str(byte) in t["options"] else 0
        writes = t["writes"][slot]
        names, order = {}, []
        fams = kit[block]
        for i, nv in enumerate(t["catalog"][slot]):
            title, items = fams[i] if len(fams) == len(t["catalog"][slot]) else fams[0]
            for v in range(nv):
                w = writes[i][v] if i < len(writes) and v < len(writes[i]) else None
                if not w or str(byte) not in w:
                    continue
                val = w[str(byte)]
                k = v if len(fams) == len(t["catalog"][slot]) else sum(t["catalog"][slot][:i]) + v
                item = items[k] if k < len(items) else ""
                if game == "reach":
                    fam_key = norm(title) if len(fams) > 1 else norm(item)
                    fam_key = HR_ALIAS.get((HR_SLOT[name], fam_key), fam_key)
                    var_key = norm(item) if len(fams) > 1 else ""
                    nm = owner.get((HR_SLOT[name], fam_key, var_key)) or owner.get((HR_SLOT[name], fam_key, ""))
                    if not nm:
                        nm = reach_case(title if len(fams) > 1 and item.upper() == "BASE" else
                                        f"{title} / {item}" if len(fams) > 1 else item)
                else:
                    nm = item
                names[val], order = nm, order + [val]
        f = fields.get(name)
        extra = list(f.get("mcc", [])) if f else []
        for val, nm in zip(extra, f.get("mcc_names", []) if f else []):
            names[val] = nm.replace(" (robot arm)", " [R]")
        size = max(list(names) + [opts - 1]) + 1
        spec = {"original": sorted(order), "modern": sorted(order + extra), "names": [names.get(v) for v in range(size)]}
        if f is None:                          # laid over the roll only when set by hand (botcore lays any byte)
            f = {"name": name, "at": byte + 0x20, "catalog": len(order), "mcc": []}
            lay["fields"].append(f)
        if (game, name) in ALSO:
            spec["also_at"] = [b + 0x20 for b in ALSO[(game, name)]]
        f.update(spec)
        lists.append((name, order, extra, names))
    if game == "h4":                           # Halo 4's female Spartans: config +0x4C as Reach's (its colours and
        if "gender" not in fields:             # visor sit where Reach's do), laid only when set by hand
            lay["fields"].append({"name": "gender", "at": 76, "catalog": 2, "mcc": [], "original": [0, 1],
                                  "modern": [0, 1], "names": ["Male", "Female"]})
        fx = {"name": "armor_effect", "at": 0x60, "catalog": 1, "mcc": [], "original": [0],
              "modern": list(range(len(H4_EFFECTS))), "names": H4_EFFECTS}
        if "armor_effect" in fields:
            fields["armor_effect"].update(fx)
        else:
            lay["fields"].append(fx)
        lists.append(("armor_effect", [0], list(range(1, len(H4_EFFECTS))), dict(enumerate(H4_EFFECTS))))
    tmp = lay_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dump(lay))
    os.replace(tmp, lay_path)
    return lists


def dump(lay):
    """The layout JSON one field per line, as the files are kept."""
    head = ",\n ".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in lay.items() if k != "fields")
    rows = ",\n  ".join(json.dumps(f, ensure_ascii=False) for f in lay["fields"])
    return "{" + head + ',\n "fields": [\n  ' + rows + "\n ]\n}\n"


def header(all_lists):
    out = ["// Generated by tools/look_names.py (do not edit): the bot editor's Reach and Halo 4 armor lists, each value",
           "// the customization table index botcore lays over the game's own Armory roll, named as the game's Armory names",
           "// it (the editing kits' supply_depot tag), the Original values first in the Armory's order, then MCC's",
           "#pragma once"]
    for game, lists in all_lists:
        for name, order, extra, names in lists:
            arr = f"ED_{'REACH' if game == 'reach' else 'H4'}_{name.upper()}"
            cells = [f'{{{v}, "{names[v]}"}}' for v in order + extra]
            lines, cur = [], f"static const piece {arr}[] = {{ "
            for c in cells:
                if len(cur) + len(c) + 2 > 118:
                    lines.append(cur.rstrip())
                    cur = "    "
                cur += c + ", "
            lines.append(cur.rstrip(", ") + " };")
            out += lines + [f"static const int {arr}_ORIGINAL = {len(order)};"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    done = [(g, build(g)) for g in ("reach", "h4")]
    with open(os.path.join(ROOT, "native", "look_names.h"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header(done))
    for g, lists in done:
        print(g, ", ".join(f"{n} {len(o)}+{len(e)}" for n, o, e, _ in lists))
