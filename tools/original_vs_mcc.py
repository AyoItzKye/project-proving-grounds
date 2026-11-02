"""Which of MCC's own customization items are original and which are MCC additions, per game, for the bot armor
toggles.

MCC names every customization item it gates in Data/UI/unlockdb.xml (eUnlockItemId_CUSTOMIZATION_<game>_<slot>_<name>).
This matches those names against the player's list of each game's original content (maps/_looks/original_content.json,
docs/research/13) and writes maps/_looks/mcc_items.json: for each game, the MCC ids that are original (with the
the player's item name) and the ones that are MCC additions. What MCC's list holds differs by game:
- Reach: every original item AND the additions (MCC gates all Reach armor behind its season pass)
- Halo 3, Halo 2 Anniversary, CE, Halo 2: additions only (their original items are always unlocked, so not listed)
- Halo 4: the original DLC sets (Mark V, ODST, Ricochet) plus additions; its armor effects are all additions
- ODST: each character as separate helmet-on / helmet-off items (one original character each), plus additions
An MCC item the player's list does not name counts as an addition; open cases are printed.

usage: python -I original_vs_mcc.py [unlockdb.xml]   (default: the game's untouched copy, Data/UI/unlockdb.xml.orig)
"""
import json
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from brain import paths  # noqa: E402  (where MCC, the mod kits and Visual Studio are)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GAME = paths.mcc()
ORIGINAL = os.path.join(ROOT, "maps", "_looks", "original_content.json")
OUT = os.path.join(ROOT, "maps", "_looks", "mcc_items.json")
PREFIX = {"H1": "ce", "H1S2": "ce", "H1S7": "ce", "H2": "h2", "H2A": "h2a", "H3": "h3", "H3E": "h3", "ODST": "odst",
          "HR": "reach", "H4": "h4"}
PREFIX.update({f"H3S{k}": "h3" for k in range(1, 10)})
# Reach: MCC's slot word -> the player's slot
HR_SLOT = {"Helmet": "helmet", "Chest": "chest", "LeftShoulder": "left_shoulder", "RightShoulder": "right_shoulder",
           "Wrist": "wrist", "Utility": "utility", "KneeGuards": "knee_guards", "VisorColor": "visor",
           "ArmorEffect": "armor_effect", "FirefightVoice": "firefight_voice", "Elite": "elite_armor", "Spartan": "gender"}
# names MCC spells differently (normalised: lower case, letters and digits only)
ALIAS = {"reach": {"mjolnirmkv": "markv", "mjolnirmkvi": "markvi", "evac": "evac", "default": "none",
                   "flames": "legendaryflaminghelmet", "blueflames": "eternalblueflames", "fieldmarshall": "fieldmarshal",
                   "jorges052": "jorge", "juns266": "jun", "emiles239": "emile", "kats320": "kat", "carters259": "carter",
                   "auntiedotai": "auntiedot", "cortanaai": "cortana", "johns117": "johns117", "gysgtstacker": "gysgtstacker",
                   "gysgtbuck": "gysgtbuck", "sgtmajjohnson": "sgtmajjohnson"},
         "odst": {"rookie": "therookie", "johnson": "sgtaveryjohnson"}}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def owner_names(game, data):
    """{(slot or None, normalised name): the player's item name} for one game; a Reach helmet's variants as base + variant."""
    out = {}
    for slot, s in data["games"][game]["slots"].items():
        for it in s.get("items", []):
            n = it["name"]
            key = norm(n.split(" (")[0]) if game == "reach" and slot in ("left_shoulder", "right_shoulder") and n.startswith("Default") else norm(n)
            out[(slot, key)] = n
            for v in it.get("variants", []):
                out[(slot, key + norm(v["name"]))] = f"{n} / {v['name']}"
            if game == "reach" and slot == "helmet":
                out[(slot, key + "base")] = n
    return out


H4_PIECES = {"Helmet", "Chest", "LeftShoulder", "RightShoulder", "Arms", "Legs"}


def classify(mcc_id, game, names):
    """("original", the player's item name), ("mcc", None) for an MCC addition, or ("unlisted", None) for a kind of item
    the player's list has no names for (Reach colors). Matching stays within a slot: CE's season-2 visor colors share
    names with CE's armor colors, and Halo 3's MCC backpack "Katana" with the original Katana chest (first run)."""
    parts = mcc_id.split("_")
    if game == "reach":
        if parts[1] == "Color":
            return "unlisted", None
        if parts[1] == "Species":
            return "original", f"species {parts[2]}"
        slot = HR_SLOT.get(parts[1])
        rest = parts[2:]
        if slot is None or (rest and rest[0] in ("POSE", "Rifle")) or (rest and rest[-1] == "RoboArm"):
            return "mcc", None
        if slot == "gender":
            name = {"Male": "Male", "Female": "Female"}.get(rest[0]) if rest else None
            return ("original", name) if name else ("mcc", None)
        key = norm("".join(rest))
        if slot == "helmet" and len(rest) == 2:
            key = ALIAS["reach"].get(norm(rest[0]), norm(rest[0])) + norm(rest[1])
        elif slot != "armor_effect" or key != "default":       # "Default" is "None" only among armor effects
            key = ALIAS["reach"].get(key, key) if key != "default" else key
        else:
            key = "none"
        name = names.get((slot, key))
        return ("original", name) if name else ("mcc", None)
    if game == "odst":
        if "BUGSPLATTERED" in parts or "INJURED" in parts:
            return "mcc", None
        base = norm("".join(p for p in parts[1:] if p not in ("WITH", "HELMET")))
        base = ALIAS["odst"].get(base, base)
        name = names.get(("character", base))
        return ("original", name) if name else ("mcc", None)
    if game == "h4" and parts[1] in H4_PIECES:                  # its original DLC sets are in MCC's list
        name = names.get(("armor_set", norm("".join(parts[2:]))))
        return ("original", name) if name else ("mcc", None)
    return "mcc", None                                          # CE, H2, H2A, H3: originals are never listed


def build(xml_text, data):
    ids = sorted(set(re.findall(r"eUnlockItemId_CUSTOMIZATION_([A-Za-z0-9_]+)", xml_text)))
    games = {}
    for i in ids:
        game = PREFIX.get(i.split("_")[0])
        if game is None:
            continue
        g = games.setdefault(game, {"original": {}, "mcc": [], "unlisted": []})
        kind, name = classify(i, game, owner_names(game, data))
        if kind == "original":
            g["original"][i] = name
        else:
            g[kind].append(i)
    for game, g in games.items():
        named = set(g["original"].values())
        g["original_not_in_mcc_list"] = sorted(set(owner_names(game, data).values()) - named)
    return games


def selftest(data):
    xml = "\n".join(f'<Unlock id="eUnlockItemId_CUSTOMIZATION_{i}"/>' for i in (
        "HR_Helmet_MjolnirMKV_Base", "HR_Helmet_EVA_UAHUL3", "HR_Helmet_Mariner_OPTREX", "HR_Chest_CollarBreacherR",
        "HR_Chest_TacticalRecon_RoboArm", "HR_ArmorEffect_Flames", "HR_ArmorEffect_Default", "HR_Elite_FieldMarshall",
        "HR_Elite_POSE_KNEEL", "HR_FirefightVoice_JorgeS052", "HR_LeftShoulder_Default", "ODST_BUCK_WITH_HELMET",
        "ODST_ROMEO_INJURED", "H4_Helmet_MARK_V", "H4_Helmet_OLYMPUS", "H3_Helmet_Belos_Base", "HR_Chest_Default",
        "HR_Color_Steel", "H1S2_VISOR_RED", "H3E_Backpack_Katana"))
    g = build(xml, data)
    assert g["reach"]["original"] == {
        "HR_Helmet_MjolnirMKV_Base": "Mark V", "HR_Helmet_EVA_UAHUL3": "EVA / UA/HUL[3]",
        "HR_Chest_CollarBreacherR": "Collar/Breacher [R]", "HR_ArmorEffect_Flames": "Legendary (Flaming Helmet)",
        "HR_ArmorEffect_Default": "None", "HR_Elite_FieldMarshall": "Field Marshal", "HR_FirefightVoice_JorgeS052": "Jorge",
        "HR_LeftShoulder_Default": "Default (Mark V [B])", "HR_Chest_Default": "Default"}, g["reach"]["original"]
    assert sorted(g["reach"]["mcc"]) == ["HR_Chest_TacticalRecon_RoboArm", "HR_Elite_POSE_KNEEL", "HR_Helmet_Mariner_OPTREX"]
    assert g["reach"]["unlisted"] == ["HR_Color_Steel"]
    assert g["odst"]["original"] == {"ODST_BUCK_WITH_HELMET": "Buck"} and g["odst"]["mcc"] == ["ODST_ROMEO_INJURED"]
    assert g["h4"]["original"] == {"H4_Helmet_MARK_V": "Mark V"} and g["h4"]["mcc"] == ["H4_Helmet_OLYMPUS"]
    assert g["h3"]["mcc"] == ["H3E_Backpack_Katana", "H3_Helmet_Belos_Base"] and g["ce"]["mcc"] == ["H1S2_VISOR_RED"]


def main():
    data = json.load(open(ORIGINAL, encoding="utf-8"))
    selftest(data)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else next(p for p in (os.path.join(GAME, "Data", "UI", "unlockdb.xml.orig"),
                                                 os.path.join(GAME, "Data", "UI", "unlockdb.xml")) if os.path.exists(p))
    games = build(open(path, encoding="utf-8").read(), data)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"source": os.path.basename(path), "how": __doc__.split("\n\n")[1].replace("\n", " "), "games": games},
                  f, indent=1)
    for game, g in sorted(games.items()):
        print(f"{game:6} original {len(g['original']):4}  MCC additions {len(g['mcc']):4}  original items not in MCC's "
              f"list {len(g['original_not_in_mcc_list'])}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
