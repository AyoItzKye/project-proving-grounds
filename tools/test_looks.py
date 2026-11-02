"""Bots' own armor (Reach, botcore s74): brain/looks.py gives a layout with "roll" as ("roll", seed, slot mask, none
mask), the same every match for a bot and different between bots; botctl.add_bot packs it as native/shared.h expects
(cmd_look_game = game | HB_LOOK_ROLL, cmd_look[0..3] = seed, [4..5] = mask, [6..7] = none mask, v10), the clan
tag in cmd_clan and the MCC emblem in cmd_emblem (v11); a byte look still packs as before. The bot profiles as the
Settings tab's re-roll writes them (experience=, effects=none|rare|common|frequent, bot=name,seed,clan): no effects at
none, then more bots per level.

usage: python -I test_looks.py      -> "looks OK"
"""
import json
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import botctl  # noqa: E402
from brain import looks  # noqa: E402


def main():
    fails = []
    d = tempfile.mkdtemp()
    prof = os.path.join(d, "bot_profiles.ini")
    bots = looks.profiles(prof)
    os.makedirs(os.path.join(d, "looks"))
    json.dump({"roll": 255}, open(os.path.join(d, "looks", "reach.json"), "w"))
    a, b = (looks.look(n, "reach", prof, os.path.join(d, "looks")) for n, _ in bots[:2])
    if a[0] != "roll" or a[2] != 255 or a != looks.look(bots[0][0], "reach", prof, os.path.join(d, "looks")) or a[1] == b[1]:
        fails.append(f"rolls {a} {b}: want ('roll', seed, 255), stable per bot, different between bots")
    # the bot editor (Settings tab): a 4th field of hand-set values wins over the roll; <game>.seed gives the game a
    # new roll; <game>.species names the game's species field; the clan tag still reads as the 3rd field
    name = bots[0][0]
    lines = open(prof, encoding="utf-8").read().splitlines()
    lines = [l + ",h3.species=1;h3.primary=7;reach.seed=3" if l.startswith(f"bot={name},") else l for l in lines]
    open(prof, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    real = os.path.join(HERE, "..", "maps", "_looks")
    off, vals = looks.look(name, "h3", prof, real)
    at = {f["name"]: f["at"] for f in json.load(open(os.path.join(real, "h3.json")))["fields"]}
    if vals.get(at["model"] - off) != 1 or vals.get(at["primary"] - off) != 7 or at["helmet"] - off in vals:
        fails.append(f"h3 hand-set look not worn: {vals} (want model 1 = Elite, primary 7, no Spartan helmet)")
    if looks.look(name, "reach", prof, os.path.join(d, "looks"))[1] == a[1]:
        fails.append("reach.seed did not give a new roll")
    if looks.clan_of(name, prof) != next(c for n, _, c in looks.read_profiles(prof)[0] if n == name) or "=" in looks.clan_of(name, prof):
        fails.append("clan tag read wrong with a 4th field")
    # the clan tags: one list in two languages, kept the same (native/bots_panel.cpp CLAN_TAGS)
    import re
    src = open(os.path.join(HERE, "..", "native", "bots_panel.cpp"), encoding="utf-8").read()
    block = src[src.index("static const char* CLAN_TAGS[] = {"):]
    block = block[:block.index("};")]
    if re.findall(r'"([^"]*)"', block) != looks.CLAN_TAGS:
        fails.append("clan tags differ between brain/looks.py and native/bots_panel.cpp")
    # ... and the gamertag parts (brain/names.py), every two-part name within the game's 15 characters
    from brain import names
    for key in ("FIRST", "SECOND", "WORDS"):
        b = src[src.index(f"static const char* {key}[] = {{"):]
        if re.findall(r'"([^"]*)"', b[:b.index("};")]) != getattr(names, key):
            fails.append(f"gamertag parts {key} differ between brain/names.py and native/bots_panel.cpp")
    if max(map(len, names.FIRST)) + max(map(len, names.SECOND)) > 15 or max(map(len, names.WORDS)) > 12:
        fails.append("a gamertag part makes names over the game's 15 characters")
    sent = []
    botctl.command = lambda m, cmd, arg, timeout=5.0: sent.append((cmd, arg)) or {}
    m = bytearray(botctl.SIZE)
    botctl.add_bot(m, 3, 1, "Tester", "reach", look=("roll", 0xDEADBEEF, 0x00FF))
    game, off = struct.unpack_from("<II", m, botctl.OFF_LOOK)
    seed, mask = struct.unpack_from("<IH", m, botctl.OFF_LOOK + 8)
    if (game, seed, mask) != (botctl.GAME_ID["reach"] | botctl.LOOK_ROLL, 0xDEADBEEF, 0xFF) or not sent:
        fails.append(f"roll packed as game {game:#x} seed {seed:#x} mask {mask:#x}")
    m = bytearray(botctl.SIZE)
    botctl.add_bot(m, 3, 1, "Tester", "reach", look=(0x40, {0x18: 7}))
    game, off = struct.unpack_from("<II", m, botctl.OFF_LOOK)
    if (game, off, m[botctl.OFF_LOOK + 8 + 0x18], m[botctl.OFF_LOOK + 72 + 0x18]) != (botctl.GAME_ID["reach"], 0x40, 7, 1):
        fails.append("a byte look no longer packs as before")
    # the shipped Reach mask: the Elite armor slot (9: its catalog writes the Elite set; the player Invasion: every
    # Elite in the same armor when only 0-7 were) rolled, never slot 8 (armor effects) or 12 (the Firefight voice, its
    # equip faulted every roll), and the whole mask fits botctl's 16-bit field
    real = looks.look(bots[0][0], "reach", prof)
    if (real[0] != "roll" or not real[2] >> 9 & 1 or real[2] >> 8 & 1 or real[2] >> 12 & 1 or real[2] >> 16
            or real[2] & 0xFF != 0xFF):
        fails.append(f"maps/_looks/reach.json mask {real[2]:#x}: want slots 0-7 and 9 (Elite armor), not 8 or 12")
    if real[3] != 1 << 8:                       # effects off: the effect slot set to none, not left as the player's
        fails.append(f"Reach none mask {real[3]:#x} with effects off: want slot 8 (owner, Oct 24: bots copied the flames)")
    # the re-roll's file (native/bots_panel.cpp profiles_reroll writes bot=%s,%u,%s after experience= and effects=)
    # effects none / rare / common / frequent, and the first build's 0 / 1 (none / common): 60 bots
    worn = {}
    json.dump({"roll": 255, "effects": [8]}, open(os.path.join(d, "looks", "reach.json"), "w"))
    for fx, level in (("none", "none"), ("rare", "rare"), ("common", "common"), ("frequent", "frequent"),
                      ("0", "none"), ("1", "common")):
        rr = os.path.join(d, f"rerolled_{fx}.ini")
        with open(rr, "w", encoding="utf-8") as f:
            f.write(f"; header\nexperience=modern\neffects={fx}\n")
            f.writelines(f"bot=Bot{k},{1000 + k},{'TBK' if k % 2 else ''}\n" for k in range(60))
        got, st = looks.read_profiles(rr)
        if (st != {"experience": "modern", "effects": level, "species": "mixed", "elites": None} or len(got) != 60
                or looks.clan_of("bot3", rr) != "TBK"
                or looks.clan_of("Bot4", rr) != "" or looks.clan_of("Nobody", rr) != ""):
            fails.append(f"re-rolled profiles (effects={fx}) read as {st}, {got[:3]}")
        ls = [looks.look(f"Bot{k}", "reach", rr, os.path.join(d, "looks")) for k in range(60)]
        wear = [x for x in ls if x[2] >> 8 & 1]
        if any((x[3] == 0) != (x in wear) or x[3] not in (0, 1 << 8) for x in ls):
            fails.append(f"effects {fx}: a bot both rolls and blanks the effect slot, none masks {[x[3] for x in ls]}")
        worn[fx] = len(wear)
    if not (worn["none"] == worn["0"] == 0 < worn["rare"] < worn["common"] == worn["1"] < worn["frequent"] < 60):
        fails.append(f"bots wearing an effect by level (of 60): {worn}")
    if not (2 <= worn["rare"] <= 12 and 12 <= worn["common"] <= 30 and 30 <= worn["frequent"] <= 52):
        fails.append(f"effect shares far from 1 in 10 / 1 in 3 / 2 in 3: {worn}")
    # Halo 3 (maps/_looks/h3.json: the map's customization table): Original = only original sets on helmet, shoulders
    # and chest, arms / legs / techsuit / backpack at 0; Modern = every selection of the table; the Bungie chests (1,
    # 13) only on a bot that wears an effect; Elite pieces only on Elites; one window from the primary colour
    h3 = json.load(open(os.path.join(HERE, "..", "maps", "_looks", "h3.json"), encoding="utf-8"))
    orig = {f["name"]: f.get("original") for f in h3["fields"]}
    for exp, fx in (("original", "none"), ("original", "frequent"), ("modern", "common")):
        pf = os.path.join(d, f"h3_{exp}_{fx}.ini")
        with open(pf, "w", encoding="utf-8") as f:
            f.write(f"experience={exp}\neffects={fx}\n" + "".join(f"bot=Bot{k},{5000 + k},\n" for k in range(80)))
        got = [looks.look(f"Bot{k}", "h3", pf) for k in range(80)]
        flames = sum(1 for off, b in got if b.get(73 - off) in (1, 13))
        elites = sum(1 for off, b in got if b.get(60 - off) == 1)
        for off, b in got:
            a = {off + k: v for k, v in b.items()}
            if off != 57 or max(a) - off >= 64:
                fails.append(f"h3 look window {off}..{max(a)}")
                break
            spartan = a[60] == 0
            if spartan == (81 in a) or spartan != (70 in a):
                fails.append(f"h3: Spartan / Elite pieces mixed up {a}")
                break
            if exp == "original" and spartan and (a[74] or a[75] or a[76] or a[77] or a[70] not in orig["helmet"]
                                                 or a[71] not in orig["left_shoulder"] or a[73] not in orig["chest"]):
                fails.append(f"h3 Original wears a piece the game did not ship: {a}")
                break
            if exp == "modern" and spartan and not (a[70] <= 68 and a[71] <= 61 and a[73] <= 55 and a[74] <= 32
                                                    and a[75] <= 37 and a[76] <= 16 and a[77] <= 25):
                fails.append(f"h3 Modern past the table's end: {a}")
                break
            # a piece with no geometry draws nothing
            if spartan and any(a[f["at"]] in f.get("no_geometry", ()) for f in h3["fields"] if f["at"] in a):
                fails.append(f"h3 rolled a piece with no geometry: {a}")
                break
        if (fx == "none" and flames) or (fx == "frequent" and not flames) or not 5 <= elites <= 30:
            fails.append(f"h3 {exp} effects {fx}: {flames} Flaming Head chests, {elites} Elites of 80")
    # the profile editor's Halo 3 pickers offer no piece with no geometry either (native/bots_panel.cpp)
    cpp = open(os.path.join(HERE, "..", "native", "bots_panel.cpp"), encoding="utf-8").read()
    empty = {f["name"]: set(f.get("no_geometry", ())) for f in h3["fields"]}
    for arr, field in (("H3_HELMET", "helmet"), ("H3_SHOULDER", "left_shoulder"), ("H3_CHEST", "chest"),
                       ("H3_ARMS", "arms"), ("H3_LEGS", "legs"), ("H3_SUIT", "techsuit"), ("H3_BACKPACK", "backpack")):
        a = cpp.find("static const piece %s[] = {" % arr)
        vals = {int(v) for v in re.findall(r"\{(\d+), \"", cpp[a:cpp.index("};", a)])} if a >= 0 else set()
        if not vals or vals & empty.get(field, set()):
            fails.append(f"{arr}: missing, or offers pieces with no geometry {sorted(vals & empty.get(field, set()))}")
    m = bytearray(botctl.SIZE)
    botctl.add_bot(m, 3, 1, "Tester", "reach", look=("roll", 1, 0xFF, 1 << 8), clan="TBK", emblem=(29, 555, 1, 2, 22))
    if (struct.unpack_from("<H", m, botctl.OFF_LOOK + 14)[0] != 1 << 8
            or m[botctl.OFF_CLAN:botctl.OFF_CLAN + 16].decode("utf-16-le").rstrip("\0") != "TBK"
            or struct.unpack_from("<5H", m, botctl.OFF_EMBLEM) != (29, 555, 1, 2, 22)):
        fails.append("none mask, clan tag or emblem not packed (cmd_look[6..7], cmd_clan, cmd_emblem)")
    # Halo 4 / Reach colours and visor after the roll: n at cmd_look[9], (u16 offset, u8 value) pairs from [10]
    botctl.add_bot(m, 3, 1, "Tester", "h4", look=("roll", 1, 0x3F, 0, 2, [(75, 16), (73, 7)]))
    body = m[botctl.OFF_LOOK + 8:botctl.OFF_LOOK + 72]
    if body[8] != 2 or body[9] != 2 or struct.unpack_from("<HBHB", body, 10) != (73, 7, 75, 16):
        fails.append(f"roll extras not packed: {bytes(body[8:16]).hex()}")
    modern = looks.read_profiles(looks.PROFILES)[1]["experience"] == "modern"
    for g, at, top in (("h4", (73, 74, 75), (29, 29, 16)), ("reach", (73, 74, 76), (29, 29, 1))):   # (Reach +0x4C gender)
        lay = json.load(open(os.path.join(HERE, "..", "maps", "_looks", g + ".json"), encoding="utf-8"))["fields"]
        mcc = {f["at"]: f["mcc"] for f in lay if "mcc" in f}
        for name, _ in looks.profiles(looks.PROFILES):
            r = looks.look(name, g)          # (Modern: an MCC item by its table index over the roll, maps/_looks mcc;
            over = {k[len(g) + 1:]: v for k, v in looks.overrides_of(name).items() if k.startswith(g + ".")}
            hand = {a for f in lay if "mcc" in f and f["name"] in over for a in [f["at"]] + f.get("also_at", [])}
            extra = {k: v for k, v in r[5].items() if k in mcc and k not in hand} if len(r) == 6 else {}
            if (len(r) != 6 or sorted(set(r[5]) - set(extra) - hand) != list(at)   # a piece set by hand laid as set)
                    or any(not 0 <= r[5][a] <= t for a, t in zip(at, top))
                    or any(v not in mcc[k] for k, v in extra.items()) or (extra and not modern)):
                fails.append(f"{g} roll extras for {name}: {r}")
                break
    shared =open(os.path.join(HERE, "..", "native", "shared.h")).read()
    if f"sizeof(hb_shared) == {botctl.SIZE}" not in shared:
        fails.append(f"botctl.SIZE {botctl.SIZE} is not native/shared.h's hb_shared size")
    # Invasion respawns: the Reach spawn-check hook (spawnhook.cpp) is always on, over the function's own first bytes,
    # and clears a bot's co-op spawning byte (s76: it spawns on time; s139's choice made for it waited 6 s in 136 of
    # 303 spawns); where it spawns is the brain's pick, moved there on its first tick over the teleport's checked first
    # bytes (reach.cpp hr_spawn_moves; tools/test_honor_spawn.py)
    native = os.path.join(HERE, "..", "native")
    spec, reach = (open(os.path.join(native, f)).read() for f in ("spawnhook.cpp", "reach.cpp"))
    if ("spawnhook_watch" not in spec or "hr_bot_solo_spawn(player);" not in spec or "HR_SHOULD_SPAWN_HEAD" not in spec
            or "if (gg) gg[0x38C + (size_t)index * 0xF0] = 0;" not in reach
            or "memcmp(g_hr + HR_TELEPORT, HR_TELEPORT_HEAD, sizeof HR_TELEPORT_HEAD)" not in reach
            or "hr_spawn_moves(tls, fr," not in reach):
        fails.append("Invasion bot respawn: hook not always on, the co-op byte not cleared for bots, or the spawn move "
                     "not over the teleport's checked first bytes")
    # the player's original-content list (docs/research/13) as data: every table's row count, every tag known, the
    # modes
    data = json.load(open(looks.ORIGINAL, encoding="utf-8"))
    want = {("ce", "armor_color"): 18, ("h2", "primary_color"): 18, ("h2a", "spartan_set"): 3, ("h2a", "elite_set"): 3,
            ("h3", "spartan_helmet"): 11, ("h3", "spartan_chest"): 9, ("h3", "spartan_shoulders"): 8,
            ("h3", "elite_helmet"): 5, ("h3", "elite_chest"): 5, ("h3", "elite_shoulders"): 5, ("odst", "character"): 7,
            ("reach", "helmet"): 21, ("reach", "left_shoulder"): 16, ("reach", "right_shoulder"): 16, ("reach", "chest"): 20,
            ("reach", "wrist"): 6, ("reach", "utility"): 6, ("reach", "knee_guards"): 4, ("reach", "visor"): 5,
            ("reach", "armor_effect"): 7, ("reach", "firefight_voice"): 12, ("reach", "elite_armor"): 8,
            ("h4", "armor_set"): 42, ("h4", "forearms"): 10, ("h4", "armor_skin"): 44}
    for (g, s), n in want.items():
        items = data["games"][g]["slots"][s]["items"]
        if len(items) != n:
            fails.append(f"{g} {s}: {len(items)} items, the source lists {n}")
    tags = {it.get("tag") for game in data["games"].values() for sl in game["slots"].values()
            for it in sl.get("items", []) + [v for i in sl.get("items", []) for v in i.get("variants", [])]}
    if not tags <= {"default", "unlock", "promo", "staff"}:
        fails.append(f"unknown tags {tags}")
    strict, excl = (looks.original_items("reach", "armor_effect", m) for m in ("strict", "exclusives"))
    if ("Legendary (Flaming Helmet)" in strict or "Eternal (blue flames)" in strict or len(excl) != 7
            or strict[0] != "None" or looks.original_items("reach", "armor_effect", "mcc") is not None):
        fails.append(f"Reach armor effects by mode: strict {strict}, exclusives {excl}")
    if ("Recon / UA/HUL(3)" in looks.original_items("reach", "helmet") or "Recon" not in looks.original_items("h3", "spartan_helmet", "exclusives")
            or "Recon" in looks.original_items("h3", "spartan_helmet") or len(looks.original_items("h4", "legs")) != 10):
        fails.append("strict / exclusives filtering of variants, staff items or a same_as slot")
    import original_vs_mcc                      # MCC's own item ids sorted into original / addition (its self-test)
    original_vs_mcc.selftest(data)
    experiences(fails, d)
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("looks OK")


def experiences(fails, d):
    """. Every game and field: the Original list within the Modern one; 1000 Original bots per game, effects on, never
    wear a Modern-only value (byte games: each field as rolled and as sent; Reach / Halo 4: no MCC item over the
    Armory roll, no MCC effect); values set by hand under Modern are not worn under Original; the Settings tab's
    pickers list the Original values first, then Modern's, by the names in maps/_looks."""
    import re
    lk = os.path.join(HERE, "..", "maps", "_looks")
    layouts = {g: json.load(open(os.path.join(lk, g + ".json"), encoding="utf-8")) for g in ("ce", "h2", "h3", "h2a", "reach", "h4")}
    for g, lay in layouts.items():
        for f in lay.get("fields", []):
            if "original" in f and not set(looks.choices(f["original"])) <= set(looks.choices(f.get("modern", f["original"]))):
                fails.append(f"{g} {f['name']}: Original values not all in Modern")
            if "effect" in f and "original" in f and not set(f["effect"]) <= set(looks.choices(f.get("modern", f["original"]))):
                fails.append(f"{g} {f['name']}: an effect value Modern does not hold")
            if "mcc" in f and not lay.get("roll"):
                fails.append(f"{g} {f['name']}: an MCC item over a roll in a game with no roll")
    names = [f"Rule{k}" for k in range(1000)]          # not in the file: each its own seed (crc32 of the name)
    for exp in ("original", "modern"):
        pf = os.path.join(d, f"rule_{exp}.ini")
        with open(pf, "w", encoding="utf-8") as fh:
            fh.write(f"experience={exp}\neffects=frequent\nbot=Keeper,7,\n")
        for g, lay in layouts.items():
            fields, mcc_worn, fx_worn = lay.get("fields", []), 0, 0
            for n in names:
                r = looks.look(n, g, pf, lk)
                if lay.get("roll"):
                    extra = {f["at"]: f for f in fields if "mcc" in f and f["at"] in r[5]}
                    mcc_worn += bool(extra)
                    eb = lay.get("effect_byte")
                    fx_worn += bool(eb and r[4] != eb["none"])
                    if exp == "original" and (extra or (eb and eb.get("modern_only") and r[4] != eb["none"])):
                        fails.append(f"{g} Original bot {n} wears MCC content over the Armory roll: {r}")
                        break
                    if any(r[5][a] not in f["mcc"] for a, f in extra.items()):
                        fails.append(f"{g} MCC item outside its list: {r}")
                        break
                    continue
                worn = looks.resolved(n, g, None, pf, lk)
                sent, want = {r[0] + k: v for k, v in r[1].items()}, {}
                for f in fields:                 # the bytes the fields write, in order (a later field over an earlier)
                    if f["name"] in worn:
                        want[f["at"]] = worn[f["name"]]
                bad = [f["name"] for f in fields if f["name"] in worn and worn[f["name"]] not in looks.allowed(f, exp == "modern")]
                if sent != want or bad:
                    fails.append(f"{g} {exp} bot {n}: {bad or 'sent bytes differ from the roll'} {worn}")
                    break
            if lay.get("roll") and exp == "modern" and any("mcc" in f for f in fields) and not mcc_worn:
                fails.append(f"{g} Modern: no bot of 1000 wears an MCC item")
            if lay.get("effect_byte") and exp == "modern" and not fx_worn:
                fails.append(f"{g} Modern, effects frequent: no bot of 1000 wears an effect")
    # set by hand under Modern (the bot editor), then the player switched to
    # Original
    for exp in ("original", "modern"):
        pf = os.path.join(d, f"hand_{exp}.ini")
        with open(pf, "w", encoding="utf-8") as fh:
            fh.write(f"experience={exp}\neffects=none\nbot=Hand,99,,h3.species=0;h3.helmet=60;h3.visor=22;h3.backpack=5;"
                     "h3.chest=13;h2a.species=0;h2a.helmet=1;h2a.chest=7;h2a.forearms=2\n")
        h3, h2a = looks.resolved("Hand", "h3", None, pf, lk), looks.resolved("Hand", "h2a", None, pf, lk)
        set_h3 = {"helmet": 60, "visor": 22, "backpack": 5, "chest": 13}
        if exp == "modern" and ({k: h3[k] for k in set_h3} != set_h3 or (h2a["chest"], h2a["forearms"]) != (7, 2)):
            fails.append(f"Modern does not wear what was set by hand: {h3} {h2a}")
        if exp == "original" and (h3["helmet"] == 60 or h3["visor"] != 1 or h3["backpack"] != 0 or h3["chest"] != 13
                                  or not h2a["helmet"] == h2a["chest"] == h2a["forearms"] == 1):
            fails.append(f"Original wears a Modern item or a mixed set set by hand: {h3} {h2a}")
    # Reach / Halo 4 pieces set by hand: laid over the Armory roll by their table index where the experience allows
    # them, and the profile view wears them
    for exp in ("original", "modern"):
        pf = os.path.join(d, f"hand_roll_{exp}.ini")
        with open(pf, "w", encoding="utf-8") as fh:
            fh.write(f"experience={exp}\neffects=none\nbot=Hand,99,,reach.species=0;reach.helmet=45;reach.left_shoulder=15;"
                     "reach.visor=4;reach.chest=20;reach.armor_effect=3;h4.gender=1;h4.helmet=87;h4.legs=5;"
                     "h4.armor_effect=2\n")
        hr, h4 = looks.look("Hand", "reach", pf, lk)[5], looks.look("Hand", "h4", pf, lk)[5]
        # (Reach's effect is its 2010 Armory's, both its bytes; Halo 4's MCC's: Modern only)
        want_hr = {88: 45, 89: 15, 75: 4, 96: 3, 97: 3} | ({91: 20} if exp == "modern" else {})
        want_h4 = {76: 1, 94: 5} | ({88: 87, 96: 2} if exp == "modern" else {})
        if any(hr.get(k) != v for k, v in want_hr.items()) or any(h4.get(k) != v for k, v in want_h4.items()) or (
                exp == "original" and (hr.get(91) == 20 or h4.get(88) == 87 or 96 in h4)):
            fails.append(f"{exp}: Reach / Halo 4 pieces set by hand not laid over the roll as allowed: {hr} {h4}")
        view_hr, view_h4 = looks.armory_view("Hand", "reach", pf, lk)[0], looks.armory_view("Hand", "h4", pf, lk)[0]
        if "head:bungie" not in view_hr or "female_techsuit" not in view_h4 or (exp == "modern") != ("olympus" in view_h4):
            fails.append(f"{exp}: the profile view does not wear the pieces set by hand: {view_hr[:120]} {view_h4[:120]}")
        if "armor_effect=" not in view_hr or "armor_effect=" not in view_h4:   # (each one's rolled effect, for the editor)
            fails.append(f"{exp}: the profile view does not name the rolled armor effects: {view_hr[:80]} {view_h4[:80]}")
    # the re-roll's species choice: every game with the choice, the view's roll and the bytes botcore is sent alike; no
    # line: each game's mix
    for line, lo, hi in (("", 20, 90), ("species=spartans\n", 0, 0), ("species=elites\n", 200, 200),
                         ("species=mixed\nelites=50\n", 70, 130), ("species=mixed\nelites=0\n", 0, 0)):
        pf = os.path.join(d, "species.ini")
        with open(pf, "w", encoding="utf-8") as fh:
            fh.write("experience=modern\neffects=none\n" + line + "".join(f"bot=S{k},{7000 + k},\n" for k in range(200)))
        got = {g: sum(1 for k in range(200) if looks.resolved(f"S{k}", g, None, pf, lk)[sf] == 1)
               for g, sf in (("h2", "species"), ("h3", "model"), ("h2a", "species"))}
        got["reach"] = sum(looks.reach_species(f"S{k}", pf) for k in range(200))
        sent = 0
        for k in range(200):
            off, b = looks.look(f"S{k}", "h3", pf, lk)
            sent += b.get(60 - off) == 1
        if any(not lo <= n <= hi for n in got.values()) or sent != got["h3"]:
            fails.append(f"species {line.strip() or 'unset'}: Elites of 200 {got}, Halo 3 bytes sent {sent}")
    # the Settings tab's pickers (native/bots_panel.cpp, native/look_names.h): Original values first (the count the
    # picker shows under Original), then Modern's, each named as maps/_looks names it
    src = "".join(open(os.path.join(HERE, "..", "native", f), encoding="utf-8").read() for f in ("bots_panel.cpp", "look_names.h"))
    gen = [(f"ED_{'REACH' if g == 'reach' else 'H4'}_{f['name'].upper()}", g, f["name"]) for g in ("reach", "h4")
           for f in layouts[g]["fields"] if "catalog" in f and "names" in f and f["name"] != "gender"]
    for arr, g, field in gen + [("H3_HELMET", "h3", "helmet"), ("H3_SHOULDER", "h3", "left_shoulder"), ("H3_CHEST", "h3", "chest"),
                          ("H3_ELITE", "h3", "elite_helmet"), ("H3_ELITE", "h3", "elite_left_shoulder"),
                          ("H3_ELITE", "h3", "elite_right_shoulder"), ("H3_ELITE", "h3", "elite_piece_51"),
                          ("H3_ELITE_LIMB", "h3", "elite_piece_52"), ("H3_ELITE_LIMB", "h3", "elite_legs"),
                          ("CE_VISOR", "ce", "visor"), ("H3_VISOR", "h3", "visor"), ("H3_BACKPACK", "h3", "backpack"),
                          ("H2A_HELMET", "h2a", "helmet"), ("H2A_CHEST", "h2a", "chest"),
                          ("H2A_SHOULDER", "h2a", "shoulder_a"), ("H2A_LIMB", "h2a", "forearms")]:
        block = src[src.index(f"static const piece {arr}[] = {{"):]
        items = [(int(v), s) for v, s in re.findall(r'\{(\d+), "([^"]*)"\}', block[:block.index("};")])]
        f = next(x for x in layouts[g]["fields"] if x["name"] == field)
        orig, mod = looks.choices(f["original"]), looks.choices(f["modern"])
        m = re.search(rf"\b{arr}_ORIGINAL = (\d+)", src)
        first = int(m.group(1)) if m else len(orig)
        if (sorted(v for v, _ in items[:first]) != sorted(orig) or sorted(v for v, _ in items) != sorted(mod)
                or any(f["names"][v] != s for v, s in items)):
            fails.append(f"bots_panel.cpp {arr}: not the Original values first, then Modern's, named as {g}.json")


if __name__ == "__main__":
    main()
